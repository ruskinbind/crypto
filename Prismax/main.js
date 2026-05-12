const fs = require("fs");
const path = require("path");
const axios = require("axios");
const colors = require("colors");
const { HttpsProxyAgent } = require("https-proxy-agent");
const readline = require("readline");
const user_agents = require("./config/userAgents");
const settings = require("./config/config.js");
const { sleep, loadData, getRandomNumber, saveToken, isTokenExpired, saveJson, getRandomElement, generateId } = require("./utils/utils.js");
const { checkBaseUrl } = require("./utils/checkAPI.js");
const { headers } = require("./core/header.js");
const { showBanner } = require("./core/banner.js");
const localStorage = require("./localStorage.json");
const ethers = require("ethers");
const { PromisePool } = require("@supercharge/promise-pool");
const refcodes = loadData("reffCodes.txt");
const { Impit } = require("impit");
const UserAgent = require("user-agents");
const { solveCaptcha } = require("./utils/captcha.js");
const ContractSv = require("./services/contract.js");
const dayjs = require("dayjs");
const { FetchRequest } = require("ethers");
const messages = loadData("messages.txt");

class ClientAPI {
  constructor(itemData, accountIndex, proxy) {
    this.headers = headers;
    this.baseURL = settings.BASE_URL;
    this.baseURL_v2 = settings.BASE_URL_V2;
    this.localItem = null;
    this.itemData = itemData;
    this.accountIndex = accountIndex;
    this.proxy = proxy;
    this.proxyIP = null;
    this.session_name = null;
    this.session_user_agents = this.#load_session_data();
    this.token = null;
    this.identity_token = null;
    this.localStorage = localStorage;
    this.provider = null;
    this.sepoProvider = null;
    this.wallet = new ethers.Wallet(this.itemData.privateKey);
    this.refCode = getRandomElement(refcodes) || settings.REF_CODE;
    this.sessionCookie = null;
    this.impit = new Impit({
      browser: "chrome",
      ignoreTlsErrors: true,
      maxRedirects: 3,
      headers: this.headers,
      ...(settings.USE_PROXY && this.proxy ? { proxyUrl: this.proxy } : {}),
    });
  }

  #load_session_data() {
    try {
      const filePath = path.join(process.cwd(), "session_user_agents.json");
      const data = fs.readFileSync(filePath, "utf8");
      return JSON.parse(data);
    } catch (error) {
      if (error.code === "ENOENT") {
        return {};
      } else {
        throw error;
      }
    }
  }

  #get_user_agent() {
    if (this.session_user_agents[this.session_name]) {
      return this.session_user_agents[this.session_name];
    }
    const agent = new UserAgent({
      deviceCategory: "desktop",
    }).random();
    const newUserAgent = agent.toString();
    this.session_user_agents[this.session_name] = newUserAgent;
    this.#save_session_data(this.session_user_agents);
    return newUserAgent;
  }

  #save_session_data(session_user_agents) {
    const filePath = path.join(process.cwd(), "session_user_agents.json");
    fs.writeFileSync(filePath, JSON.stringify(session_user_agents, null, 2));
  }

  #get_platform(userAgent) {
    const platformPatterns = [
      { pattern: /iPhone/i, platform: "ios" },
      { pattern: /Android/i, platform: "android" },
      { pattern: /iPad/i, platform: "ios" },
    ];

    for (const { pattern, platform } of platformPatterns) {
      if (pattern.test(userAgent)) {
        return platform;
      }
    }

    return "Unknown";
  }

  #set_headers() {
    const platform = this.#get_platform(this.#get_user_agent());
    this.headers["sec-ch-ua"] = `Not)A;Brand";v="99", "${platform} WebView";v="127", "Chromium";v="127`;
    this.headers["sec-ch-ua-platform"] = platform;
    this.headers["User-Agent"] = this.#get_user_agent();
  }

  createUserAgent() {
    try {
      this.session_name = this.itemData.address;
      this.#get_user_agent();
    } catch (error) {
      this.log(`Can't create user agent: ${error.message}`, "error");
      return;
    }
  }

  async log(msg, type = "info") {
    const accountPrefix = `[PRISMAX][${this.accountIndex + 1}][${this.itemData.address}]`;
    let ipPrefix = "[Local IP]";
    if (settings.USE_PROXY) {
      ipPrefix = this.proxyIP ? `[${this.proxyIP}]` : "[Unknown IP]";
    }
    let logMessage = "";

    switch (type) {
      case "success":
        logMessage = `${accountPrefix}${ipPrefix} ${msg}`.green;
        break;
      case "error":
        logMessage = `${accountPrefix}${ipPrefix} ${msg}`.red;
        break;
      case "warning":
        logMessage = `${accountPrefix}${ipPrefix} ${msg}`.yellow;
        break;
      case "custom":
        logMessage = `${accountPrefix}${ipPrefix} ${msg}`.magenta;
        break;
      default:
        logMessage = `${accountPrefix}${ipPrefix} ${msg}`.blue;
    }
    console.log(logMessage);
  }

  async checkProxyIP() {
    try {
      const proxyAgent = new HttpsProxyAgent(this.proxy);
      const response = await axios.get("https://api.ipify.org?format=json", { httpsAgent: proxyAgent });
      if (response.status === 200) {
        this.proxyIP = response.data.ip;
        return response.data.ip;
      } else {
        throw new Error(`Cannot check proxy IP. Status code: ${response.status}`);
      }
    } catch (error) {
      throw new Error(`Error checking proxy IP: ${error.message}`);
    }
  }

  async makeRequest(
    url,
    method,
    data = {},
    options = {
      retries: 5,
      isAuth: false,
      extraHeaders: {},
      refreshToken: null,
    }
  ) {
    if (!url || typeof url !== "string") {
      throw new Error("URL must be a valid string");
    }
    if (!["GET", "POST", "PUT", "DELETE", "PATCH"].includes(method.toUpperCase())) {
      throw new Error("Invalid HTTP method");
    }

    const { retries = 5, isAuth = false, extraHeaders = {}, refreshToken = null } = options;

    const headers = {
      ...this.headers,
      // ...(!isAuth && this.localItem.hash_code ? { authorization: `Bearer ${this.localItem.hash_code}` } : {}),
      ...extraHeaders,
    };

    const proxyAgent = settings.USE_PROXY ? new HttpsProxyAgent(this.proxy) : null;

    const fetchOptions = {
      method: method.toUpperCase(),
      headers,
      timeout: 120000,
      ...(proxyAgent ? { agent: proxyAgent } : {}),
      ...(method.toLowerCase() !== "get" ? { body: JSON.stringify(data) } : {}),
    };

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await this.impit.fetch(url, fetchOptions);
        const jsonResponse = await response.json();
        return {
          responseHeader: response.headers,
          status: response.status,
          success: true,
          data: jsonResponse?.data || jsonResponse,
          error: null,
        };
      } catch (error) {
        const errorStatus = error.status || 500;
        const errorMessage = error?.response?.data?.error || error?.response?.data || error.message;

        if (errorStatus >= 400 && errorStatus < 500) {
          if (errorStatus === 401) {
            const token = await this.getValidToken(url.includes("sessions") ? true : false);
            if (!token) {
              return { success: false, status: errorStatus, error: "Failed to refresh token", data: null };
            }
            this.token = token;
            return await this.makeRequest(url, method, data, options);
          }
          if (errorStatus === 400) {
            return { success: false, status: errorStatus, error: errorMessage, data: null };
          }
          if (errorStatus === 429) {
            return { success: false, status: errorStatus, error: "You've reached daily limitation", data: null };
          }
          return { success: false, status: errorStatus, error: errorMessage, data: null };
        }

        if (attempt === retries) {
          return { success: false, status: errorStatus, error: errorMessage, data: null };
        }

        await sleep(5);
      }
    }

    return { success: false, status: 500, error: "Request failed after retries", data: null };
  }

  extractSessionId(headers) {
    try {
      const setCookies = headers.get ? headers.get("set-cookie") : headers["set-cookie"];
      if (setCookies) {
        const cookiesArray = Array.isArray(setCookies) ? setCookies : setCookies.split(", ");
        const cookieStr = cookiesArray.map((c) => c.split(";")[0]).join("; ");
        return cookieStr;
      }
    } catch (error) {}
    return null;
  }

  async registerUser() {
    this.log(`SolvingCaptcha...`);
    const captchaToken = await solveCaptcha();
    if (!captchaToken) {
      this.log(`Can't solve captcha token`, "warning");
      return { success: false };
    }
    return this.makeRequest(`${settings.BASE_URL}/get-users?wallet_address=${this.itemData.address}&recaptcha_token=${captchaToken}&chain=base`, "get");
  }

  async getUserData() {
    return await this.checkin();
  }

  async getMess() {
    return await this.makeRequest(`${settings.BASE_URL}/signin?address=${this.itemData.address}`, "get");
  }
  async auth() {
    return await this.registerUser();
  }

  async getTasks() {
    return this.makeRequest(`${settings.BASE_URL}/quests`, "get");
  }

  async doTasks(id) {
    return this.makeRequest(`${settings.BASE_URL}/quests?quest_id=${id}`, "post");
  }

  async faucet() {
    const res = await this.makeRequest(`https://nft-api.x1.one/testnet/faucet?address=${this.itemData.address}`, "get");
    return res;
  }

  async submitQuiz() {
    this.log(`Solving captcha...`);
    const captchaToken = await solveCaptcha();
    if (!captchaToken) {
      this.log(`Can't solve captcha token`, "warning");
      return { success: false };
    }
    const res = await this.makeRequest(`${settings.BASE_URL}/quiz/submit`, "post", {
      userid: this.localItem.userid,
      correct_answers: 5,
      total_questions: 5,
      recaptchaToken: captchaToken,
    });
    return res;
  }

  async checkQuiz() {
    const res = await this.makeRequest(`${settings.BASE_URL}/quiz/check-status?userid=${this.localItem.userid}`, "get");
    return res;
  }

  async checkin() {
    const res = await this.makeRequest(
      `${settings.BASE_URL}/daily-login-points`,
      "post",
      {
        wallet_address: this.itemData.address,
        chain: "base",
        user_local_date: dayjs(new Date()).format("YYYY-MM-DD"),
      },
      {
        extraHeaders: {
          authorization: `Bearer ${this.localItem.hash_code}`,
        },
      }
    );
    if (res?.data?.msg == "User not found") {
      this.log(`Registing new user...`);
      const resReg = await this.registerUser();
      if (!res.success) {
        this.log(`Register failed: ${JSON.stringify(resReg.data)}`, "warning");
        return { success: false };
      } else if (res.success && res.data.userid) {
        await saveJson(
          this.session_name,
          JSON.stringify({
            ...res.data,
          }),
          "localStorage.json"
        );
        this.localItem = res.data;
      }
    }
    return res;
  }

  async getBalance() {
    const res = await this.makeRequest(`${settings.BASE_URL}/get-point-transactions?wallet_address=${this.itemData.address}&chain=base`, "get");
    return res;
  }

  async chat({ user_id, message }) {
    const res = await this.makeRequest(`${settings.BASE_URL}/check-comment-reward`, "post", {
      user_id,
      message,
    });
    return res;
  }

  checkcOverTime(last_completed_at) {
    if (!last_completed_at) return false;

    const lastCompletedDate = new Date(last_completed_at);
    const currentDate = new Date();
    const diffInHours = (currentDate - lastCompletedDate) / (1000 * 60 * 60);
    return diffInHours >= 24;
  }

  async handleQuiz() {
    const resCheck = await this.checkQuiz();
    if (!resCheck.success) {
      this.log(`Check quiz status failed: ${resCheck.error}`, "warning");
      return;
    }

    const isCompleted = resCheck.data.completed;
    if (isCompleted) {
      this.log(`You have completed the quiz`, "warning");
      return;
    }
    this.log(`Submitting quiz...`);
    const resSubmit = await this.submitQuiz();
    if (resSubmit.success && resSubmit.status == 200) {
      this.log(`Submit quiz success!`, "success");
    } else {
      this.log(`Submit quiz failed: ${JSON.stringify(resSubmit.data || resSubmit.error)}`, "warning");
    }
  }

  async handleOnchain() {
    const { provider, wallet } = await this.connectRPC({
      rpc_url: settings.RPC_URL,
      chain_id: settings.CHAIN_ID,
      name: "Base mainet",
    });

    if (!provider || !wallet) {
      this.log(`Cannot connect to RPC onchain`, "error");
      return;
    }
    const sv = new ContractSv({
      wallet,
      provider,
      log: (mess, type) => this.log(mess, type),
    });
    await sv.checkBalances();
  }

  async handleTasks() {
    this.log(`Starting tasks...`);
    const resCheckin = await this.checkin();
    if (resCheckin.data) {
      const { already_claimed_daily } = resCheckin.data;
      if (already_claimed_daily) {
        return this.log(`You checked in today`, "warning");
      } else {
        return this.log(`Chekin success`, "success");
      }
    }
  }

  async getValidToken(isNew = false) {
    const existingToken = this.token;
    let loginRes = { success: false, data: null };
    // const { isExpired: isExp, expirationDate } = isTokenExpired(existingToken);
    // this.log(`Access token status: ${isExp ? "Expired".yellow : "Valid".green} | Acess token exp: ${expirationDate}`);

    if (existingToken && !isNew) {
      this.log("Using valid token", "success");
      return existingToken;
    }

    this.log("No found token or experied, trying get new token...", "warning");

    if (!loginRes?.data) {
      this.log(`Getting new token...`);
      loginRes = await this.auth();
    }

    const data = loginRes.data;
    if (data?.hash_code) {
      await saveJson(
        this.session_name,
        JSON.stringify({
          ...data,
        }),
        "localStorage.json"
      );
      this.localItem = data;
      return data?.hash_code;
    }
    this.log(`Can't get new token | ${JSON.stringify(loginRes)}...`, "warning");
    return null;
  }

  async handleQuest() {
    const mess = getRandomElement(messages);
    this.log(`Sending mess ${mess}`);
    let retries = 2;
    while (retries > 0) {
      retries--;
      const res = await this.chat({
        user_id: this.localItem.userid,
        message: mess,
      });
      if (res.data) {
        if (res.data.already_rewarded_today) {
          return this.log(`Point added today`, "warning");
        } else if (res.data.points_awarded > 0) {
          return this.log(`Reward points chat: ${res.data.points_awarded}`, "success");
        }
      }
      await sleep(4);
    }
  }

  async handleSyncData() {
    this.log(`Sync data...`);
    let userData = { success: false, data: null, status: 0 },
      retries = 0;
    do {
      userData = await this.getUserData();
      if (userData?.success) break;
      retries++;
    } while (retries < 1 && userData.status !== 400);
    if (userData?.success) {
      {
        const { total_points, userid, already_claimed_daily } = userData.data;
        if (!already_claimed_daily) {
          this.log(`Checkin success`, "success");
        } else {
          this.log(`Checked in today`, "warning");
        }
        const refCode = this.localItem.referral_code;
        this.log(`Points: ${total_points || 0} Ref_code: ${refCode || ""}`, "custom");
      }
    } else {
      this.log("Can't sync new data...skipping", "warning");
    }
    return userData;
  }
  async connectRPC({ rpc_url, chain_id, name }) {
    try {
      const fetchReq = new FetchRequest(rpc_url);

      if (settings.USE_PROXY && this.proxy) {
        const agent = new HttpsProxyAgent(this.proxy);

        fetchReq.getUrlFunc = FetchRequest.createGetUrlFunc({
          agent: agent,
        });
      }

      const provider = new ethers.JsonRpcProvider(
        fetchReq,
        {
          chainId: Number(chain_id),
          name: name,
        },
        { staticNetwork: true }
      );

      const wallet = new ethers.Wallet(this.itemData.privateKey, provider);

      const block = await provider.getBlockNumber();
      if (block === null || block === undefined) throw new Error(`Can't get block`);

      this.log(`Connected block ${block} via Proxy`, "success");

      return { provider, wallet };
    } catch (error) {
      this.log(`Can't connect RPC of chain ${name} | ${error.message}`, "error");
      return { provider: null, wallet: null };
    }
  }

  async runAccount() {
    const accountIndex = this.accountIndex;
    this.session_name = this.itemData.address;
    this.localItem = JSON.parse(this.localStorage[this.session_name] || "{}");
    this.token = this.localItem?.hash_code;

    // this.#set_headers();
    if (settings.USE_PROXY) {
      try {
        this.proxyIP = await this.checkProxyIP();
      } catch (error) {
        this.log(`Cannot check proxy IP: ${error.message}`, "warning");
        return;
      }
    }
    const timesleep = getRandomNumber(settings.DELAY_START_BOT[0], settings.DELAY_START_BOT[1]);
    console.log(`=========Tài khoản ${accountIndex + 1} | ${this.proxyIP || "Local IP"} | Bắt đầu sau ${timesleep} giây...`.green);
    await sleep(timesleep);

    try {
      const token = await this.getValidToken();
      if (!token) return;
      this.token = token;

      try {
        await this.handleOnchain();
      } catch (error) {}

      const userData = await this.handleSyncData();

      if (userData.success) {
        await this.handleQuest();
        await sleep(3);
        await this.handleQuiz();
        await sleep(1);
      } else {
        this.log("Can't get use info...skipping", "error");
      }
    } catch (error) {}
  }
}

async function main() {
  console.clear();
  showBanner();
  const privateKeys = loadData("privateKeys.txt");
  const proxies = loadData("proxy.txt");

  if (privateKeys.length == 0 || (privateKeys.length > proxies.length && settings.USE_PROXY)) {
    console.log("Số lượng proxy và data phải bằng nhau.".red);
    console.log(`Data: ${privateKeys.length}`);
    console.log(`Proxy: ${proxies.length}`);
    process.exit(1);
  }
  if (!settings.USE_PROXY) {
    console.log(`You are running bot without proxies!!!`.yellow);
  }
  let maxThreads = settings.USE_PROXY ? settings.MAX_THEADS : settings.MAX_THEADS_NO_PROXY;

  const data = privateKeys.map((val, index) => {
    const prvk = val.startsWith("0x") ? val : `0x${val}`;
    const wallet = new ethers.Wallet(prvk);
    const item = {
      address: wallet.address.toLowerCase(),
      privateKey: prvk,
    };
    new ClientAPI(item, index, proxies[index]).createUserAgent();
    return item;
  });
  await sleep(1);

  while (true) {
    const { results, errors } = await PromisePool.withConcurrency(maxThreads)
      .for(data)
      .process(async (itemData, index, pool) => {
        try {
          const to = new ClientAPI(itemData, index, proxies[index % proxies.length]);
          await Promise.race([to.runAccount(), new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 24 * 60 * 60 * 1000))]);
        } catch (error) {
          console.log("err", error.message);
        } finally {
        }
      });
    await sleep(5);
    console.log(`Completed all account | Waiting ${settings.TIME_SLEEP} minutes to new circle`.magenta);
    await sleep(settings.TIME_SLEEP * 60);
  }
}

main().catch((error) => {
  console.log("Lỗi rồi:", error);
  process.exit(1);
});
