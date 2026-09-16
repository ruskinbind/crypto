const colors = require("colors");
const { PromisePool } = require("@supercharge/promise-pool");
const settings = require("./config/config.js");
const { sleep, loadData, getRandomNumber, formatDuration } = require("./utils/utils.js");
const { showBanner } = require("./core/banner.js");
const ClientBase = require("./core/ClientBase.js");
const TokenStore = require("./core/TokenStore.js");
const { encryptLoginPayload } = require("./core/Crypto.js");

const BASE_URL = settings.BASE_URL;

class YeblockClient extends ClientBase {
  constructor(itemData, accountIndex, proxy) {
    super({
      accountIndex,
      proxy,
      useProxy: settings.USE_PROXY,
      sessionFile: "yeblock_fingerprints.json",
      baseHeaders: {
        "Content-Type": "application/json",
        Origin: settings.ORIGIN,
        Referer: settings.REFERER,
      },
      logPrefix: "Yeblock",
      address: itemData.email,
      deviceCategory: "desktop",
      sendClientHints: false,
    });

    this.itemData = itemData;
    this.account = itemData.email;
    this.password = itemData.password;
    this.token = null;
    this.refreshToken = null;
    this.store = new TokenStore("yeblock_tokens");
  }

  async makeRequest(url, method, data = {}, options = {}) {
    const { isAuth = false, extraHeaders = {}, _retry = false } = options;
    const auth = !isAuth && this.token ? { Authorization: `Bearer ${this.token}` } : {};

    const result = await super.makeRequest(url, method, data, {
      ...options,
      extraHeaders: { ...auth, ...extraHeaders },
    });

    if (result?.status === 401 && !isAuth && !_retry) {
      this.log("Access token rejected, renewing session...", "warning");
      const token = await this.renewAuth();
      if (!token) return result;
      await sleep(1);
      return this.makeRequest(url, method, data, { ...options, _retry: true });
    }

    return result;
  }

  async getPublicKey() {
    const res = await super.makeRequest(`${BASE_URL}/users/login/public-key`, "post", {}, { isAuth: true });
    const keyId = res?.data?.keyId ?? res?.data?.KeyId;
    const publicKeyPem = res?.data?.publicKeyPem ?? res?.data?.PublicKeyPem;
    if (!res?.success || !keyId || !publicKeyPem) {
      this.log(`Cannot fetch login public key: ${res?.error || "Unknown"}`, "warning");
      return null;
    }
    return { keyId, publicKeyPem };
  }

  async login() {
    const key = await this.getPublicKey();
    if (!key) return null;

    let payload;
    try {
      payload = encryptLoginPayload({ accountOrEmail: this.account, password: this.password }, key.publicKeyPem, key.keyId);
    } catch (error) {
      this.log(`Cannot encrypt login payload: ${error.message}`, "error");
      return null;
    }

    const res = await super.makeRequest(`${BASE_URL}/users/login`, "post", payload, { isAuth: true });
    const token = res?.data?.token;
    if (!res?.success || !token) {
      this.log(`Login failed: ${res?.error || "Unknown"}`, "error");
      return null;
    }

    this.token = token;
    this.refreshToken = res.data.refreshToken;
    this.store.save(this.account, { token, refreshToken: this.refreshToken, expiresIn: res.data.expiresIn });
    this.log("Login success", "success");
    return token;
  }

  async refreshSession() {
    if (!this.refreshToken || TokenStore.isExpired(this.refreshToken, settings.TOKEN_REFRESH_SKEW)) return null;

    const res = await super.makeRequest(`${BASE_URL}/users/refresh`, "post", {}, { isAuth: true, extraHeaders: { refresh_token: this.refreshToken } });
    const token = res?.data?.token;
    if (!res?.success || !token) {
      this.log(`Token refresh failed: ${res?.error || "Unknown"}`, "warning");
      return null;
    }

    this.token = token;
    this.refreshToken = res.data.refreshToken || this.refreshToken;
    this.store.save(this.account, { token, refreshToken: this.refreshToken, expiresIn: res.data.expiresIn });
    this.log("Token refreshed", "success");
    return token;
  }

  async renewAuth() {
    const token = await this.refreshSession();
    if (token) return token;
    this.store.remove(this.account);
    this.token = null;
    this.refreshToken = null;
    return this.login();
  }

  async ensureAuth() {
    const cached = this.store.load(this.account);
    if (cached?.token && !TokenStore.isExpired(cached.token, settings.TOKEN_REFRESH_SKEW)) {
      this.token = cached.token;
      this.refreshToken = cached.refreshToken;
      this.log(`Using cached token | Expires in ${formatDuration(cached.expiresAt - Date.now())}`, "custom");
      return this.token;
    }

    if (cached?.refreshToken) {
      this.refreshToken = cached.refreshToken;
      const token = await this.refreshSession();
      if (token) return token;
    }

    return this.login();
  }

  async getProfile() {
    const res = await this.makeRequest(`${BASE_URL}/users/me`, "get");
    return res?.success ? res.data : null;
  }

  async getAssets() {
    const res = await this.makeRequest(`${BASE_URL}/users/me/assets`, "get");
    return res?.success ? res.data : null;
  }

  async getEmailStatus() {
    const res = await this.makeRequest(`${BASE_URL}/users/me/email/verification-status`, "get");
    return res?.success ? res.data : null;
  }

  async getLastCheckIn() {
    const res = await this.makeRequest(`${BASE_URL}/users/me/check-in/last-time`, "get");
    if (!res?.success) return null;
    const value = Number(res.data);
    return Number.isFinite(value) && value > 0 ? value : 0;
  }

  async checkIn() {
    return this.makeRequest(`${BASE_URL}/users/me/check-in`, "post", {});
  }

  async handleCheckin(emailStatus) {
    if (!settings.AUTO_CHECKIN) return;

    if (settings.SKIP_UNVERIFIED_EMAIL && emailStatus && emailStatus.emailVerified !== true) {
      this.log("Email not verified, skipping check-in", "warning");
      return;
    }

    const lastTime = await this.getLastCheckIn();
    const cooldownMs = settings.CHECKIN_COOLDOWN_HOURS * 3600 * 1000;
    if (lastTime && Date.now() - lastTime < cooldownMs) {
      const remaining = lastTime + cooldownMs - Date.now();
      this.log(`Check-in on cooldown | Next in ${formatDuration(remaining)}`, "warning");
      return;
    }

    const res = await this.checkIn();
    if (res?.success && res.data?.checkInTime) {
      this.log(`Check-in done | +${res.data.rewardPoints} points`, "success");
    } else {
      this.log(`Check-in failed: ${res?.error || "Unknown"}`, "warning");
    }
  }

  async runAccount() {
    this.setSession(this.account, { chromeOnly: true });

    if (settings.USE_PROXY) {
      try {
        this.proxyIP = await this.checkProxyIP();
      } catch (error) {
        this.log(`Cannot check proxy IP: ${error.message}`, "warning");
        return;
      }
    }

    const timesleep = getRandomNumber(settings.DELAY_START_BOT[0], settings.DELAY_START_BOT[1]);
    console.log(`=========Account ${this.accountIndex + 1} | ${this.proxyIP || "Local IP"} | Starting in ${timesleep}s...`.green);
    await sleep(timesleep);

    try {
      const token = await this.ensureAuth();
      if (!token) return;

      const profile = await this.getProfile();
      if (!profile) {
        this.log("Cannot load profile", "warning");
        return;
      }
      if (profile.isBanned) {
        this.log(`Account is banned: ${profile.banReason || "no reason"}`, "error");
        return;
      }

      const emailStatus = await this.getEmailStatus();
      const assets = settings.SHOW_ASSETS ? await this.getAssets() : null;
      const points = assets ? Number(assets.points).toFixed(4) : "-";
      this.log(`Nickname: ${profile.nickName || "-"} | Points: ${points} | Power: ${assets?.power ?? "-"} | Ref: ${profile.inviteCode || "-"} | Verified: ${emailStatus?.emailVerified ?? "-"}`, "custom");

      await sleep(settings.DELAY_BETWEEN_REQUESTS);
      await this.handleCheckin(emailStatus);
    } catch (error) {
      this.log(error.message, "error");
    }
  }
}

function parseAccounts(lines) {
  const accounts = [];
  for (const line of lines) {
    const sep = line.indexOf("|");
    if (sep < 0) {
      console.log(`Invalid account line (expected email|password): ${line}`.yellow);
      continue;
    }
    const email = line.slice(0, sep).trim();
    const password = line.slice(sep + 1).trim();
    if (!email || !password) {
      console.log(`Invalid account line (expected email|password): ${line}`.yellow);
      continue;
    }
    accounts.push({ email, password });
  }
  return accounts;
}

async function main() {
  console.clear();
  showBanner();

  const accounts = parseAccounts(loadData("accounts.txt"));
  const proxies = loadData("proxy.txt");

  if (accounts.length === 0) {
    console.log("No accounts in data/accounts.txt (format: email|password)".red);
    process.exit(1);
  }
  if (settings.USE_PROXY && proxies.length === 0) {
    console.log("USE_PROXY=true but data/proxy.txt is empty".red);
    process.exit(1);
  }
  if (!settings.USE_PROXY) {
    console.log("You are running bot without proxies!!!".yellow);
  }

  const maxThreads = settings.USE_PROXY ? settings.MAX_THEADS : settings.MAX_THEADS_NO_PROXY;
  const clients = accounts.map((itemData, index) => new YeblockClient(itemData, index, proxies[index % proxies.length]));

  while (true) {
    await PromisePool.withConcurrency(maxThreads)
      .for(clients)
      .process(async (client) => {
        let timeoutId = null;
        try {
          await Promise.race([
            client.runAccount(),
            new Promise((_, reject) => {
              timeoutId = setTimeout(() => reject(new Error("Timeout")), 60 * 60 * 1000);
            }),
          ]);
        } catch (error) {
          console.log(`err ${error.message}`.red);
        } finally {
          if (timeoutId) clearTimeout(timeoutId);
        }
      });
    await sleep(5);
    console.log(`Completed all accounts | Waiting ${settings.TIME_SLEEP} minutes to new circle`.magenta);
    await sleep(settings.TIME_SLEEP * 60);
  }
}

process.on("unhandledRejection", (reason) => {
  const msg = (reason?.message || String(reason)).toLowerCase();
  const isNetworkNoise =
    msg.includes("504") ||
    msg.includes("gateway") ||
    msg.includes("server_error") ||
    msg.includes("timeout") ||
    msg.includes("socket hang up") ||
    msg.includes("econnreset") ||
    msg.includes("etimedout") ||
    msg.includes("fetch failed") ||
    msg.includes("network");
  if (isNetworkNoise) return;
  console.log(`[WARN] Unhandled rejection: ${reason?.message || reason}`);
});

module.exports = { YeblockClient, BASE_URL };

if (require.main === module) {
  main().catch((error) => {
    console.log("Fatal error:", error);
    process.exit(1);
  });
}
