const axios = require("axios");
const { ethers } = require("ethers");
const readline = require("readline");
const FormData = require("form-data");
const fs = require("fs");
const path = require("path");
const { Readable } = require("stream");
const { wrapper } = require("axios-cookiejar-support");
const { CookieJar } = require("tough-cookie");
const { SiweMessage } = require("siwe");
const { HttpsProxyAgent } = require("https-proxy-agent");
const { SocksProxyAgent } = require("socks-proxy-agent");

const colors = {
  reset: "\x1b[0m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  white: "\x1b[37m",
  magenta: "\x1b[35m",
  bold: "\x1b[1m",
  blue: "\x1b[34m",
  dim: "\x1b[2m",
};

const logger = {
  info: (msg) => console.log(`${colors.bold}${colors.blue}[INFO]${colors.reset} ${colors.white}${msg}${colors.reset}`),
  warn: (msg) => console.log(`${colors.bold}${colors.yellow}[WARN]${colors.reset} ${colors.yellow}${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.bold}${colors.red}[ERROR]${colors.reset} ${colors.red}${msg}${colors.reset}`),
  success: (msg) => console.log(`${colors.bold}${colors.green}[OK]${colors.reset} ${colors.green}${msg}${colors.reset}`),
  loading: (msg) => console.log(`${colors.bold}${colors.cyan}[...]${colors.reset} ${colors.cyan}${msg}${colors.reset}`),
  step: (msg) => console.log(`${colors.bold}${colors.magenta}>>>${colors.reset} ${colors.white}${msg}${colors.reset}`),
  banner: () => {
    console.clear();
    console.log("");
    console.log(`${colors.bold}${colors.cyan}========================================${colors.reset}`);
    console.log(`${colors.bold}${colors.magenta}       DATAHAVEN AUTO BOT${colors.reset}`);
    console.log(`${colors.bold}${colors.yellow}       CREATED BY KAZUHA VIP ONLY${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}========================================${colors.reset}`);
    console.log("");
  },
  menu: () => {
    console.log(`${colors.bold}${colors.cyan}----------------------------------------${colors.reset}`);
    console.log(`${colors.bold}${colors.white}              MAIN MENU${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}----------------------------------------${colors.reset}`);
  },
  divider: () => {
    console.log(`${colors.dim}${colors.cyan}----------------------------------------${colors.reset}`);
  },
};

const USER_AGENTS = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
];

function pickUA() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

(function suppressPolkadotWarnings() {
  const origWarn = console.warn.bind(console);
  const origError = console.error.bind(console);

  let suppressBlock = false;
  let suppressUntil = 0;

  const shouldSuppress = (msg) => {
    if (!msg) return false;
    const s = String(msg);
    if (s.includes("has multiple versions, ensure that there is only one installed.")) return true;
    if (s.includes("Either remove and explicitly install matching versions or dedupe")) return true;
    if (s.includes("The following conflicting packages were found:")) return true;
    if (/^\s*(cjs|esm)\s+\d+/.test(s)) return true;
    if (s.includes("node_modules/@polkadot/")) return true;
    if (s.startsWith("@polkadot/")) return true;
    return false;
  };

  console.warn = (...args) => {
    const joined = args.map(String).join(" ");
    if (shouldSuppress(joined)) {
      suppressBlock = true;
      suppressUntil = Date.now() + 1500;
      return;
    }
    if (suppressBlock && Date.now() < suppressUntil && shouldSuppress(joined)) return;
    if (suppressBlock && Date.now() >= suppressUntil) suppressBlock = false;
    return origWarn(...args);
  };

  console.error = (...args) => {
    const joined = args.map(String).join(" ");
    if (shouldSuppress(joined)) return;
    return origError(...args);
  };
})();

const CHAIN_ID = 55931;
const RPC_URL = "https://services.datahaven-testnet.network/testnet";
const BACKEND_URL = "https://deo-dh-backend.testnet.datahaven-infra.network";
const CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000404";

const MSP_ID = "0x0000000000000000000000000000000000000000000000000000000000000001";
const VALUE_PROP_ID = "0x628a23c7aa64902e13f63ffdd0725e07723745f84cabda048d901020d200da1e";

const DEFAULT_REPLICATION_LEVEL = 5;
const DEFAULT_REPLICAS = 1;

const IMAGES_DIR = path.join(__dirname, "images");
const PROXIES_FILE = path.join(__dirname, "proxies.txt");
const PV_FILE = path.join(__dirname, "pv.txt");

const CAMPHAVEN_URL = "https://camphaven.xyz";
const ABSINTHE_GQL_URL = "https://gql3.absinthe.network/v1/graphql";
const CLIENT_SEASON = "d2ct-npic";
const POINT_SOURCE_ID = "09b99963-757e-46fa-8b79-95d1cdbed7d5";

const IFACE = new ethers.Interface([
  "function createBucket(bytes32 mspId, bytes name, bool isPrivate, bytes32 valuePropId)",
  "function issueStorageRequest(bytes32 bucketId, bytes fileName, bytes32 fingerprint, uint64 size, bytes32 mspId, bytes[] peerIds, uint8 replicationLevel, uint32 replicas)",
]);

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const question = (q) => new Promise((resolve) => rl.question(q, resolve));
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let PROXIES = [];
let PROXY_INDEX = -1;
let ACTIVE_PROXY_URL = null;
let ACTIVE_PROXY_AGENT = null;

function isLikelyPort(s) {
  const n = Number(s);
  return Number.isInteger(n) && n > 0 && n <= 65535;
}

function parseProxyLine(line) {
  const raw = String(line || "").trim();
  if (!raw) return null;
  if (raw.startsWith("#")) return null;

  let s = raw;
  const hasScheme = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(s);

  if (!hasScheme) {
    if (s.includes("@")) {
      s = `http://${s}`;
    } else {
      const parts = s.split(":");
      if (parts.length === 2 && isLikelyPort(parts[1])) {
        s = `http://${s}`;
      } else if (parts.length === 4) {
        const [p0, p1, p2, p3] = parts;
        if (isLikelyPort(p1) && !isLikelyPort(p3)) {
          s = `http://${p2}:${p3}@${p0}:${p1}`;
        } else if (!isLikelyPort(p1) && isLikelyPort(p3)) {
          s = `http://${p0}:${p1}@${p2}:${p3}`;
        } else if (isLikelyPort(p1) && isLikelyPort(p3)) {
          s = `http://${p2}:${p3}@${p0}:${p1}`;
        } else {
          s = `http://${raw}`;
        }
      } else {
        s = `http://${raw}`;
      }
    }
  }

  let u;
  try {
    u = new URL(s);
  } catch (_) {
    return null;
  }

  const proto = u.protocol.replace(":", "").toLowerCase();
  const allowed = new Set(["http", "https", "socks", "socks4", "socks5", "socks5h"]);
  if (!allowed.has(proto)) return null;
  if (!u.hostname) return null;
  if (!u.port) return null;
  if (!isLikelyPort(u.port)) return null;

  return u.toString();
}

function maskProxy(proxyUrl) {
  try {
    const u = new URL(proxyUrl);
    if (u.username || u.password) {
      const masked = new URL(proxyUrl);
      masked.username = u.username ? "***" : "";
      masked.password = u.password ? "***" : "";
      return masked.toString();
    }
    return proxyUrl;
  } catch (_) {
    return proxyUrl;
  }
}

function createProxyAgent(proxyUrl) {
  const u = new URL(proxyUrl);
  const proto = u.protocol.replace(":", "").toLowerCase();
  if (proto.startsWith("socks")) return new SocksProxyAgent(proxyUrl);
  return new HttpsProxyAgent(proxyUrl);
}

function setActiveProxy(proxyUrl) {
  if (!proxyUrl) {
    ACTIVE_PROXY_URL = null;
    ACTIVE_PROXY_AGENT = null;
    return;
  }
  ACTIVE_PROXY_URL = proxyUrl;
  ACTIVE_PROXY_AGENT = createProxyAgent(proxyUrl);
}

function loadProxiesFromFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      PROXIES = [];
      setActiveProxy(null);
      return;
    }

    const raw = fs.readFileSync(filePath, "utf8");
    const lines = raw.split(/\r?\n/);
    const parsed = lines.map(parseProxyLine).filter(Boolean);

    PROXIES = parsed;
    if (PROXIES.length === 0) {
      setActiveProxy(null);
      return;
    }

    PROXY_INDEX = -1;
    rotateProxy();
  } catch (e) {
    PROXIES = [];
    setActiveProxy(null);
  }
}

function rotateProxy() {
  if (!Array.isArray(PROXIES) || PROXIES.length === 0) {
    setActiveProxy(null);
    return null;
  }
  PROXY_INDEX = (PROXY_INDEX + 1) % PROXIES.length;
  const p = PROXIES[PROXY_INDEX];
  setActiveProxy(p);
  return p;
}

function withProxyAxiosConfig(config = {}) {
  if (!ACTIVE_PROXY_AGENT) return config;
  return {
    ...config,
    proxy: false,
    httpAgent: ACTIVE_PROXY_AGENT,
    httpsAgent: ACTIVE_PROXY_AGENT,
  };
}

function normalizeBytes32(hexish) {
  if (!hexish) throw new Error("Missing bytes32 value");
  let v = String(hexish).toLowerCase();
  if (!v.startsWith("0x")) v = "0x" + v;
  if (v.length !== 66) throw new Error(`Invalid bytes32 length: ${v.length} (${v})`);
  return v;
}

function normalizeBytes32Loose(hexish) {
  if (!hexish) throw new Error("Missing bytes32 value");
  let v = String(hexish).toLowerCase();
  if (v.startsWith("0x")) v = v.slice(2);
  if (!/^[0-9a-f]+$/.test(v)) throw new Error(`Invalid hex: ${hexish}`);
  if (v.length > 64) throw new Error(`Invalid bytes32 length: ${v.length} (${hexish})`);
  v = v.padStart(64, "0");
  return "0x" + v;
}

function normalizeAddress(addr) {
  if (!addr) throw new Error("Missing address");
  const a = String(addr);
  if (!/^0x[0-9a-fA-F]{40}$/.test(a)) throw new Error(`Invalid address: ${addr}`);
  return ethers.getAddress(a);
}

function backendHeaders(extra = {}) {
  return {
    accept: "application/json",
    "accept-language": "en-US,en;q=0.8",
    Referer: "https://datahaven.app/",
    "user-agent": pickUA(),
    ...extra,
  };
}

function to0xHex(value) {
  if (!value) throw new Error("Empty value");
  if (typeof value?.then === "function") {
    throw new Error("to0xHex() received a Promise. Make sure the value is awaited first.");
  }
  if (typeof value === "string") {
    return value.startsWith("0x") ? value : "0x" + value;
  }
  if (typeof value.toHex === "function") {
    return value.toHex();
  }
  if (value instanceof Uint8Array || Buffer.isBuffer(value)) {
    return "0x" + Buffer.from(value).toString("hex");
  }
  if (typeof value.toString === "function") {
    const s = String(value.toString());
    if (s.startsWith("0x")) return s;
    if (/^[0-9a-fA-F]+$/.test(s)) return "0x" + s;
  }
  throw new Error(`Unsupported hex-like type: ${Object.prototype.toString.call(value)}`);
}

function scaleCompact(n) {
  const bn = BigInt(n);
  if (bn < 0n) throw new Error("scaleCompact: negative not allowed");

  const TWO_6 = 1n << 6n;
  const TWO_14 = 1n << 14n;
  const TWO_30 = 1n << 30n;

  if (bn < TWO_6) return Buffer.from([Number((bn << 2n) & 0xffn)]);
  if (bn < TWO_14) {
    const v = Number((bn << 2n) + 1n);
    const b = Buffer.alloc(2);
    b.writeUInt16LE(v, 0);
    return b;
  }
  if (bn < TWO_30) {
    const v = Number((bn << 2n) + 2n);
    const b = Buffer.alloc(4);
    b.writeUInt32LE(v, 0);
    return b;
  }

  let tmp = bn;
  const bytes = [];
  while (tmp > 0n) {
    bytes.push(Number(tmp & 0xffn));
    tmp >>= 8n;
  }
  const len = bytes.length;
  const prefix = Number(((BigInt(len) - 4n) << 2n) + 3n);
  return Buffer.from([prefix, ...bytes]);
}

let _shCore = null;
let _wasmReady = false;
let TypeRegistry = null;

async function tryLoadStoragehubSdkOrExit() {
  if (_shCore) return _shCore;
  try {
    require.resolve("@storagehub-sdk/core");
    _shCore = await import("@storagehub-sdk/core");
    return _shCore;
  } catch (_) {
    logger.error(`Cannot find package '@storagehub-sdk/core'.`);
    logger.warn(`Please install: npm i @storagehub-sdk/core @polkadot/types`);
    process.exit(1);
  }
}

async function ensureWasm() {
  if (_wasmReady) return;
  const core = await tryLoadStoragehubSdkOrExit();
  if (!TypeRegistry) {
    ({ TypeRegistry } = require("@polkadot/types"));
  }
  await core.initWasm();
  _wasmReady = true;
}

async function fileManagerFromBuffer(buffer) {
  await ensureWasm();
  const { FileManager } = _shCore;
  if (typeof Readable.toWeb !== "function") throw new Error("Node >= 18 required.");
  return new FileManager({
    size: buffer.length,
    stream: () => Readable.toWeb(Readable.from(buffer)),
  });
}

async function fingerprintHexFromBuffer(buffer) {
  const fm = await fileManagerFromBuffer(buffer);
  const fp = await Promise.resolve(fm.getFingerprint());
  return normalizeBytes32Loose(to0xHex(fp));
}

async function computeFileKeyFromBuffer({ uploaderAddress, bucketId32, fileName, buffer }) {
  await ensureWasm();
  const fm = await fileManagerFromBuffer(buffer);
  const registry = new TypeRegistry();
  const owner = registry.createType("AccountId20", normalizeAddress(uploaderAddress));
  const bucketIdH256 = registry.createType("H256", normalizeBytes32(bucketId32));
  const fileKey = await fm.computeFileKey(owner, bucketIdH256, fileName);
  const fk = await Promise.resolve(fileKey);
  return normalizeBytes32Loose(to0xHex(fk));
}

async function dailyCheckinLogin(wallet) {
  try {
    logger.loading("Connecting to CampHaven...");

    const jar = new CookieJar();
    const client = wrapper(
      axios.create(
        withProxyAxiosConfig({
          jar,
          withCredentials: true,
          timeout: 60_000,
          maxRedirects: 5,
          validateStatus: (s) => s >= 200 && s < 500,
        })
      )
    );

    await jar.setCookie(`client-season=${CLIENT_SEASON}; Path=/; Secure; SameSite=Lax`, CAMPHAVEN_URL);
    await jar.setCookie(`domain=${encodeURIComponent(CAMPHAVEN_URL)}; Path=/; Secure; SameSite=Lax`, CAMPHAVEN_URL);
    await jar.setCookie(`redirect-origin=${encodeURIComponent(CAMPHAVEN_URL)}; Path=/; Secure; SameSite=Lax`, CAMPHAVEN_URL);
    await jar.setCookie(
      `__Secure-authjs.callback-url=${encodeURIComponent("https://boost.absinthe.network")}; Path=/; Secure; SameSite=None`,
      CAMPHAVEN_URL
    );

    const csrfRes = await client.get(
      `${CAMPHAVEN_URL}/api/auth/csrf`,
      withProxyAxiosConfig({
        headers: {
          accept: "*/*",
          "accept-language": "en-US,en;q=0.6",
          Referer: `${CAMPHAVEN_URL}/home`,
          Origin: CAMPHAVEN_URL,
          "user-agent": pickUA(),
        },
      })
    );

    const csrfToken = csrfRes?.data?.csrfToken;
    if (!csrfToken) throw new Error("Failed to get CSRF token");

    await client.get(
      `${CAMPHAVEN_URL}/api/auth/providers`,
      withProxyAxiosConfig({
        headers: {
          accept: "*/*",
          "accept-language": "en-US,en;q=0.6",
          Referer: `${CAMPHAVEN_URL}/home`,
          Origin: CAMPHAVEN_URL,
          "user-agent": pickUA(),
        },
      })
    );

    const domain = "camphaven.xyz";
    const issuedAt = new Date().toISOString();

    const siwe = new SiweMessage({
      domain,
      address: wallet.address,
      statement: "Please sign with your account",
      uri: CAMPHAVEN_URL,
      version: "1",
      chainId: 1,
      nonce: csrfToken,
      issuedAt,
      resources: ["connector://io.rabby"],
    });

    const message = siwe.prepareMessage();
    const signature = await wallet.signMessage(message);

    const body = new URLSearchParams({
      message,
      redirect: "false",
      signature,
      csrfToken,
      callbackUrl: `${CAMPHAVEN_URL}/home`,
    }).toString();

    logger.loading("Signing message...");
    await client.post(
      `${CAMPHAVEN_URL}/api/auth/callback/credentials`,
      body,
      withProxyAxiosConfig({
        headers: {
          accept: "*/*",
          "accept-language": "en-US,en;q=0.6",
          "content-type": "application/x-www-form-urlencoded",
          "x-auth-return-redirect": "1",
          Referer: `${CAMPHAVEN_URL}/home`,
          Origin: CAMPHAVEN_URL,
          "user-agent": pickUA(),
        },
      })
    );

    await delay(1500);

    const sessionRes = await client.get(
      `${CAMPHAVEN_URL}/api/auth/session`,
      withProxyAxiosConfig({
        headers: {
          accept: "*/*",
          "accept-language": "en-US,en;q=0.6",
          Referer: `${CAMPHAVEN_URL}/home`,
          Origin: CAMPHAVEN_URL,
          "cache-control": "no-store",
          "user-agent": pickUA(),
        },
      })
    );

    const sessionData = sessionRes?.data;
    if (!sessionData?.user?.id || !sessionData?.token) {
      throw new Error("Session not established");
    }

    const { token } = sessionData;
    const userId = sessionData.user.id;

    const checkinPayload = {
      operationName: "upsertDailyCheckin",
      variables: {
        object: {
          user_id: userId,
          client_season: CLIENT_SEASON,
          point_source_id: POINT_SOURCE_ID,
          status: "SUCCESS",
        },
      },
      query: `mutation upsertDailyCheckin($object: DailyCheckinInput!) {
        daily_checkin(point_source_data: $object) { id __typename }
      }`,
    };

    logger.loading("Claiming daily check-in...");
    const checkinRes = await axios.post(
      ABSINTHE_GQL_URL,
      checkinPayload,
      withProxyAxiosConfig({
        headers: {
          accept: "application/json",
          "accept-language": "en-US,en;q=0.6",
          authorization: `Bearer ${token}`,
          "content-type": "application/json",
          Referer: `${CAMPHAVEN_URL}/`,
          "user-agent": pickUA(),
        },
        timeout: 60_000,
      })
    );

    if (checkinRes?.data?.data?.daily_checkin?.id) {
      logger.success("Daily check-in claimed successfully!");
      return true;
    }

    if (checkinRes?.data?.errors) {
      const errMsg = checkinRes.data.errors[0]?.message || "Unknown error";
      if (errMsg.includes("already")) {
        logger.warn("Already claimed today");
        return true;
      }
      throw new Error(errMsg);
    }

    logger.warn("Unexpected response from check-in");
    return false;
  } catch (error) {
    logger.error(`Daily check-in failed: ${error.message}`);
    return false;
  }
}

async function authenticateOnce(wallet) {
  const headers = backendHeaders({ "content-type": "application/json" });

  const nonceRes = await axios.post(
    `${BACKEND_URL}/auth/nonce`,
    { address: wallet.address, chainId: CHAIN_ID, domain: "datahaven.app", uri: "https://datahaven.app" },
    withProxyAxiosConfig({ headers, timeout: 60_000 })
  );

  const message = nonceRes?.data?.message;
  if (!message) throw new Error("Nonce response missing message.");

  const signature = await wallet.signMessage(message);

  let verifyRes;
  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    try {
      verifyRes = await axios.post(
        `${BACKEND_URL}/auth/verify`,
        { message, signature },
        withProxyAxiosConfig({ headers, timeout: 60_000 })
      );
      break;
    } catch (err) {
      attempts++;
      const isInvalidNonce = err?.response?.status === 401 && err?.response?.data?.error === "Invalid nonce";
      if (isInvalidNonce && attempts < maxAttempts) {
        await delay(500);
        continue;
      }
      throw err;
    }
  }

  const token = verifyRes?.data?.token;
  if (!token) throw new Error("Verify response missing token.");
  return token;
}

async function authenticate(wallet) {
  let retries = 0;
  const maxRetries = 5;

  while (retries < maxRetries) {
    try {
      return await authenticateOnce(wallet);
    } catch (err) {
      const status = err?.response?.status;
      const data = err?.response?.data;

      if (status === 401 && data?.error === "Invalid nonce" && retries < maxRetries - 1) {
        retries++;
        await delay(2000);
        continue;
      }
      throw err;
    }
  }

  throw new Error("Authentication failed after max retries");
}

async function getBuckets(token) {
  const res = await axios.get(
    `${BACKEND_URL}/buckets`,
    withProxyAxiosConfig({
      headers: { ...backendHeaders(), authorization: `Bearer ${token}` },
      timeout: 60_000,
    })
  );
  return res.data;
}

async function findBucketIdByName(token, name) {
  const buckets = await getBuckets(token);
  const hit = (Array.isArray(buckets) ? buckets : []).find((b) => b?.name === name);
  return hit?.bucketId ? normalizeBytes32(hit.bucketId) : null;
}

async function getMspInfoFromBackend() {
  const res = await axios.get(
    `${BACKEND_URL}/info`,
    withProxyAxiosConfig({
      headers: backendHeaders(),
      timeout: 60_000,
    })
  );
  return res.data;
}

function extractPeerIDs(multiaddresses) {
  return [...new Set((multiaddresses ?? []).map((addr) => String(addr).split("/p2p/").pop()).filter(Boolean))];
}

function buildFileMetadata({ uploaderAddress, bucketId32, fileName, sizeBytes, fingerprint32 }) {
  const addrBytes = Buffer.from(normalizeAddress(uploaderAddress).slice(2), "hex");
  const bucketBytes = Buffer.from(normalizeBytes32(bucketId32).slice(2), "hex");
  const nameBytes = Buffer.from(fileName, "utf8");
  const fpBytes = Buffer.from(normalizeBytes32(fingerprint32).slice(2), "hex");

  return Buffer.concat([
    scaleCompact(addrBytes.length),
    addrBytes,
    scaleCompact(bucketBytes.length),
    bucketBytes,
    scaleCompact(nameBytes.length),
    nameBytes,
    scaleCompact(sizeBytes),
    fpBytes,
  ]);
}

async function uploadToBackend({ token, bucketId32, fileKey32, uploaderAddress, fileName, buffer, sizeBytes, fingerprint32 }) {
  const bucketId = normalizeBytes32(bucketId32);
  const fileKey = normalizeBytes32(fileKey32);

  const fileMetadata = buildFileMetadata({
    uploaderAddress,
    bucketId32: bucketId,
    fileName,
    sizeBytes,
    fingerprint32,
  });

  const form = new FormData();
  form.append("file_metadata", fileMetadata, { filename: "file_metadata", contentType: "application/octet-stream" });
  form.append("file", buffer, { filename: "file", contentType: "application/octet-stream" });

  const url = `${BACKEND_URL}/buckets/${bucketId}/upload/${fileKey}`;

  const res = await axios.put(
    url,
    form,
    withProxyAxiosConfig({
      headers: { ...backendHeaders(), authorization: `Bearer ${token}`, ...form.getHeaders() },
      timeout: 180_000,
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
      validateStatus: (s) => s >= 200 && s < 500,
    })
  );

  if (res.status >= 400) {
    throw new Error(`Backend upload failed HTTP ${res.status}: ${JSON.stringify(res.data)}`);
  }

  return res.data;
}

async function waitBackendReadyLimited(token, bucketId32, fileKey32, maxChecks = 10, intervalMs = 3000) {
  const bucketId = normalizeBytes32(bucketId32);
  const fileKey = normalizeBytes32(fileKey32);

  let lastStatus = null;

  for (let attempt = 1; attempt <= maxChecks; attempt++) {
    try {
      const res = await axios.get(
        `${BACKEND_URL}/buckets/${bucketId}/info/${fileKey}`,
        withProxyAxiosConfig({
          headers: { ...backendHeaders(), authorization: `Bearer ${token}` },
          timeout: 60_000,
          validateStatus: (s) => s >= 200 && s < 500,
        })
      );

      if (res.status === 200 && res?.data?.status) {
        lastStatus = String(res.data.status);
        if (lastStatus.toLowerCase() === "ready") return { ok: true, data: res.data };
      }
    } catch (e) {
      // ignore
    }

    if (attempt < maxChecks) {
      await delay(intervalMs);
    }
  }

  return { ok: false, lastStatus };
}

async function createBucketOnChain(wallet, bucketName) {
  logger.loading(`Creating bucket: ${bucketName}`);

  const data = IFACE.encodeFunctionData("createBucket", [
    normalizeBytes32(MSP_ID),
    ethers.toUtf8Bytes(bucketName),
    false,
    normalizeBytes32(VALUE_PROP_ID),
  ]);

  const tx = await wallet.sendTransaction({ to: CONTRACT_ADDRESS, data, gasLimit: 1_000_000 });
  logger.info(`TX: ${tx.hash}`);

  const receipt = await tx.wait();
  
  if (receipt.status === 0) {
    throw new Error("Transaction reverted - bucket name may already exist or invalid parameters");
  }

  logger.success(`Bucket created! Gas used: ${receipt.gasUsed.toString()}`);
  return tx.hash;
}

function extractBucketIdFromReceipt(receipt) {
  const logs = Array.isArray(receipt?.logs) ? receipt.logs : [];
  for (const lg of logs) {
    try {
      if (!lg?.address) continue;
      if (lg.address.toLowerCase() !== CONTRACT_ADDRESS.toLowerCase()) continue;
      const topics = lg?.topics || [];
      if (topics.length >= 2) {
        return normalizeBytes32(topics[1]);
      }
    } catch (_) {}
  }
  return null;
}

function extractFileKeyFromReceipt(receipt, expectedBucketId32) {
  const wantBucket = normalizeBytes32(expectedBucketId32).toLowerCase();
  const logs = Array.isArray(receipt?.logs) ? receipt.logs : [];
  for (const lg of logs) {
    try {
      if (!lg?.address) continue;
      if (lg.address.toLowerCase() !== CONTRACT_ADDRESS.toLowerCase()) continue;
      const topics = lg?.topics || [];
      if (topics.length < 4) continue;
      const topicBucket = String(topics[3]).toLowerCase();
      if (topicBucket !== wantBucket) continue;
      return normalizeBytes32(topics[2]);
    } catch (_) {}
  }
  return null;
}

async function issueStorageRequest(wallet, bucketId, fileName, fingerprint, fileSize) {
  const cleanBucketId = normalizeBytes32(bucketId);
  const cleanFingerprint = normalizeBytes32(fingerprint);

  let peerIds = [];
  try {
    const info = await getMspInfoFromBackend();
    peerIds = extractPeerIDs(info?.multiaddresses);
    if (!peerIds.length) throw new Error("No peer IDs found from /info");
  } catch (e) {
    peerIds = ["12D3KooWNEor6iiEAbZhCXqJbXibdjethDY8oeDoieVVxpZhQcW1"];
  }

  const data = IFACE.encodeFunctionData("issueStorageRequest", [
    cleanBucketId,
    ethers.toUtf8Bytes(fileName),
    cleanFingerprint,
    BigInt(fileSize),
    normalizeBytes32(MSP_ID),
    peerIds.map((p) => ethers.toUtf8Bytes(p)),
    DEFAULT_REPLICATION_LEVEL,
    DEFAULT_REPLICAS,
  ]);

  const tx = await wallet.sendTransaction({ to: CONTRACT_ADDRESS, data, gasLimit: 1_000_000 });
  logger.info(`TX: ${tx.hash}`);

  const receipt = await tx.wait();
  
  if (receipt.status === 0) {
    throw new Error("Storage request transaction reverted");
  }

  logger.success(`Storage request confirmed! Gas: ${receipt.gasUsed.toString()}`);

  const fileKey = extractFileKeyFromReceipt(receipt, cleanBucketId);
  if (!fileKey) throw new Error("Could not extract fileKey from receipt logs");

  return { txHash: tx.hash, fileKey };
}

async function getRandomImage() {
  const response = await axios.get(
    "https://picsum.photos/800/600",
    withProxyAxiosConfig({
      responseType: "arraybuffer",
      maxRedirects: 5,
      timeout: 60_000,
      headers: { "user-agent": pickUA() },
    })
  );

  const buffer = Buffer.from(response.data);
  const fileName = `img_${Date.now()}_${Math.random().toString(16).slice(2, 8)}.jpg`;
  const fingerprint = await fingerprintHexFromBuffer(buffer);

  return { buffer, size: buffer.length, name: fileName, fingerprint };
}

function listFilesInImagesDir() {
  if (!fs.existsSync(IMAGES_DIR)) return [];
  const entries = fs.readdirSync(IMAGES_DIR, { withFileTypes: true });
  return entries
    .filter((e) => e.isFile())
    .map((e) => e.name)
    .filter((n) => !n.startsWith("."))
    .filter((n) => [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"].includes(path.extname(n).toLowerCase()))
    .sort((a, b) => a.localeCompare(b));
}

async function pickImageFromImagesFolder() {
  const files = listFilesInImagesDir();
  if (files.length === 0) {
    throw new Error(`No images found in ./images folder`);
  }

  console.log("");
  logger.divider();
  console.log(`${colors.bold}${colors.white}FILES IN ./images:${colors.reset}`);
  logger.divider();
  files.forEach((f, i) => console.log(`${colors.bold}${colors.cyan}${i + 1}${colors.reset} ${colors.white}${f}${colors.reset}`));
  console.log("");

  const pick = (await question(`${colors.bold}${colors.yellow}Enter file number: ${colors.reset}`)).trim();
  const idx = parseInt(pick, 10) - 1;
  if (Number.isNaN(idx) || idx < 0 || idx >= files.length) throw new Error("Invalid selection.");

  const fileName = files[idx];
  const abs = path.join(IMAGES_DIR, fileName);
  const buffer = fs.readFileSync(abs);

  const fingerprint = await fingerprintHexFromBuffer(buffer);
  logger.success(`Selected: ${fileName}`);

  return { buffer, size: buffer.length, name: fileName, fingerprint };
}

function loadPrivateKeys() {
  if (!fs.existsSync(PV_FILE)) {
    throw new Error(`pv.txt not found. Create it with private keys (one per line).`);
  }

  const raw = fs.readFileSync(PV_FILE, "utf8");
  const lines = raw.split(/\r?\n/);

  const pks = lines
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"))
    .map((pk) => (pk.startsWith("0x") ? pk : `0x${pk}`));

  if (pks.length === 0) {
    throw new Error("No private keys found in pv.txt");
  }
  return pks;
}

function uniqueFileName(originalName, i, walletIndex) {
  const ext = path.extname(originalName) || "";
  const base = path.basename(originalName, ext) || "file";
  return `${base}_${Date.now()}_w${walletIndex + 1}_t${i + 1}${ext}`;
}

function printBucketsList(buckets) {
  if (!Array.isArray(buckets) || buckets.length === 0) {
    console.log(`${colors.bold}${colors.yellow}No buckets found.${colors.reset}`);
    return;
  }

  logger.divider();
  console.log(`${colors.bold}${colors.white}YOUR BUCKETS:${colors.reset}`);
  logger.divider();
  buckets.forEach((b, i) => {
    const name = b?.name ?? "(no-name)";
    console.log(`${colors.bold}${colors.cyan}${i + 1}${colors.reset} ${colors.white}${name}${colors.reset}`);
  });
  console.log("");
}

function printStatus(walletCount, proxyCount) {
  console.log(`${colors.bold}${colors.white}Wallets: ${colors.green}${walletCount}${colors.reset}`);
  if (proxyCount > 0) {
    console.log(`${colors.bold}${colors.white}Proxies: ${colors.green}${proxyCount}${colors.reset}`);
  } else {
    console.log(`${colors.bold}${colors.white}Proxies: ${colors.yellow}None${colors.reset}`);
  }
  console.log("");
}

async function menuDailyCheckin(wallets) {
  logger.banner();
  console.log(`${colors.bold}${colors.white}DAILY CHECK-IN${colors.reset}`);
  logger.divider();
  console.log("");

  for (let i = 0; i < wallets.length; i++) {
    if (PROXIES.length > 0) rotateProxy();

    const wallet = wallets[i];
    logger.step(`Wallet ${i + 1}/${wallets.length}: ${wallet.address}`);

    await dailyCheckinLogin(wallet);
    console.log("");

    if (i < wallets.length - 1) await delay(1000);
  }

  logger.success("Daily check-in completed for all wallets");
}

async function menuCreateBucket(wallets, provider) {
  logger.banner();
  console.log(`${colors.bold}${colors.white}CREATE BUCKET${colors.reset}`);
  logger.divider();
  console.log("");

  const bucketName = (await question(`${colors.bold}${colors.yellow}Enter bucket name: ${colors.reset}`)).trim();
  if (!bucketName) throw new Error("Bucket name cannot be empty");

  for (let i = 0; i < wallets.length; i++) {
    if (PROXIES.length > 0) rotateProxy();

    const wallet = wallets[i];
    logger.step(`Wallet ${i + 1}/${wallets.length}: ${wallet.address}`);

    try {
      const data = IFACE.encodeFunctionData("createBucket", [
        normalizeBytes32(MSP_ID),
        ethers.toUtf8Bytes(bucketName),
        false,
        normalizeBytes32(VALUE_PROP_ID),
      ]);

      logger.loading(`Creating bucket: ${bucketName}`);
      
      const tx = await wallet.sendTransaction({ to: CONTRACT_ADDRESS, data, gasLimit: 1_000_000 });
      logger.info(`TX: ${tx.hash}`);

      const receipt = await tx.wait();
      
      if (receipt.status === 0) {
        logger.error("Transaction reverted - bucket name may already exist");
      } else {
        logger.success(`Bucket created! Gas used: ${receipt.gasUsed.toString()}`);
        
        const newBucketId = extractBucketIdFromReceipt(receipt);
        if (newBucketId) {
          logger.info(`Bucket ID: ${newBucketId}`);
        }
      }
    } catch (e) {
      logger.error(`Failed: ${e.message}`);
    }

    console.log("");
    if (i < wallets.length - 1) await delay(1000);
  }

  logger.success("Bucket creation completed for all wallets");
}

async function menuUpload(wallets, provider) {
  logger.banner();
  console.log(`${colors.bold}${colors.white}UPLOAD FILES${colors.reset}`);
  logger.divider();
  console.log("");

  const cntRaw = (await question(`${colors.bold}${colors.yellow}How many uploads per wallet: ${colors.reset}`)).trim();
  const txCount = parseInt(cntRaw, 10);
  if (Number.isNaN(txCount) || txCount < 1) throw new Error("Invalid count");

  console.log("");
  console.log(`${colors.bold}${colors.cyan}1${colors.reset} ${colors.white}Random image from internet${colors.reset}`);
  console.log(`${colors.bold}${colors.cyan}2${colors.reset} ${colors.white}Pick from ./images folder${colors.reset}`);
  console.log("");

  const srcChoice = (await question(`${colors.bold}${colors.yellow}Select source (1/2): ${colors.reset}`)).trim();
  if (srcChoice !== "1" && srcChoice !== "2") throw new Error("Invalid choice");

  let baseImage = null;
  if (srcChoice === "2") {
    baseImage = await pickImageFromImagesFolder();
  }

  for (let wIdx = 0; wIdx < wallets.length; wIdx++) {
    if (PROXIES.length > 0) rotateProxy();

    const wallet = wallets[wIdx];

    logger.banner();
    logger.step(`Wallet ${wIdx + 1}/${wallets.length}: ${wallet.address}`);
    console.log("");

    try {
      logger.loading("Authenticating...");
      const token = await authenticate(wallet);
      logger.success("Authenticated");

      const buckets = await getBuckets(token);
      printBucketsList(buckets);

      if (!Array.isArray(buckets) || buckets.length === 0) {
        logger.warn("No buckets found. Skipping wallet.");
        continue;
      }

      const pickBucket = (await question(`${colors.bold}${colors.yellow}Select bucket number: ${colors.reset}`)).trim();
      const bIdx = parseInt(pickBucket, 10) - 1;
      if (Number.isNaN(bIdx) || bIdx < 0 || bIdx >= buckets.length) throw new Error("Invalid bucket selection");

      const selectedBucket = buckets[bIdx];
      const bucketId = normalizeBytes32(selectedBucket.bucketId);
      logger.success(`Using bucket: ${selectedBucket.name}`);
      console.log("");

      for (let t = 0; t < txCount; t++) {
        if (PROXIES.length > 0) rotateProxy();

        logger.step(`Upload ${t + 1}/${txCount}`);

        try {
          let fileObj;
          if (srcChoice === "1") {
            logger.loading("Fetching random image...");
            fileObj = await getRandomImage();
            logger.success(`Downloaded: ${(fileObj.size / 1024).toFixed(1)} KB`);
          } else {
            const name = uniqueFileName(baseImage.name, t, wIdx);
            const buffer = baseImage.buffer;
            const fingerprint = await fingerprintHexFromBuffer(buffer);
            fileObj = {
              buffer,
              size: buffer.length,
              fingerprint,
              name,
            };
            logger.info(`Using: ${name}`);
          }

          logger.loading("Computing file key...");
          const computedFileKey = await computeFileKeyFromBuffer({
            uploaderAddress: wallet.address,
            bucketId32: bucketId,
            fileName: fileObj.name,
            buffer: fileObj.buffer,
          });

          logger.loading("Issuing storage request...");
          const { fileKey: receiptFileKey, txHash } = await issueStorageRequest(
            wallet,
            bucketId,
            fileObj.name,
            fileObj.fingerprint,
            fileObj.size
          );

          const fileKeyToUse = computedFileKey || receiptFileKey;

          logger.loading("Waiting for MSP to be ready...");
          await delay(5000);

          logger.loading("Uploading to backend...");
          await uploadToBackend({
            token,
            bucketId32: bucketId,
            fileKey32: fileKeyToUse,
            uploaderAddress: wallet.address,
            fileName: fileObj.name,
            buffer: fileObj.buffer,
            sizeBytes: fileObj.size,
            fingerprint32: fileObj.fingerprint,
          });

          logger.loading("Waiting for confirmation...");
          const st = await waitBackendReadyLimited(token, bucketId, fileKeyToUse, 10, 3000);
          if (st.ok) {
            logger.success(`Upload ${t + 1}/${txCount} completed successfully`);
          } else {
            logger.warn(`Upload ${t + 1}/${txCount} status: ${st.lastStatus || "pending"}`);
          }
        } catch (uploadErr) {
          logger.error(`Upload ${t + 1} failed: ${uploadErr.message}`);
        }

        console.log("");
        if (t < txCount - 1) await delay(3000);
      }
    } catch (e) {
      logger.error(`Wallet failed: ${e.message}`);
    }

    if (wIdx < wallets.length - 1) {
      console.log("");
      await delay(1000);
    }
  }

  logger.success("Upload completed for all wallets");
}

async function main() {
  loadProxiesFromFile(PROXIES_FILE);
  await tryLoadStoragehubSdkOrExit();

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const privateKeys = loadPrivateKeys();
  const wallets = privateKeys.map((pk) => new ethers.Wallet(pk, provider));

  while (true) {
    logger.banner();
    printStatus(wallets.length, PROXIES.length);
    logger.menu();
    console.log("");
    console.log(`${colors.bold}${colors.cyan}1${colors.reset} ${colors.white}Claim Daily Check-in${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}2${colors.reset} ${colors.white}Create Bucket${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}3${colors.reset} ${colors.white}Upload Files${colors.reset}`);
    console.log(`${colors.bold}${colors.cyan}4${colors.reset} ${colors.white}Exit${colors.reset}`);
    console.log("");

    const choice = (await question(`${colors.bold}${colors.yellow}Select option: ${colors.reset}`)).trim();

    try {
      if (choice === "1") {
        await menuDailyCheckin(wallets);
      } else if (choice === "2") {
        await menuCreateBucket(wallets, provider);
      } else if (choice === "3") {
        await menuUpload(wallets, provider);
      } else if (choice === "4") {
        logger.success("Goodbye!");
        break;
      } else {
        logger.warn("Invalid option. Please select 1-4.");
      }
    } catch (e) {
      logger.error(e.message);
    }

    console.log("");
    await question(`${colors.bold}${colors.cyan}Press Enter to continue...${colors.reset}`);
  }

  rl.close();
  process.exit(0);
}

main();