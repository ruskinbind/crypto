const Logger = require("./Logger");
const SessionManager = require("./SessionManager");
const HttpClient = require("./HttpClient");
const { buildHeaders, buildClientHints } = require("./AntiDetect");

class ClientBase {
  constructor({
    accountIndex = 0,
    proxy = null,
    useProxy = false,
    sessionFile = "session_fingerprints.json",
    baseHeaders = {},
    logPrefix = "BOT",
    deviceCategory = null,
    sendClientHints = false,
    address = "",
  } = {}) {
    this.accountIndex = accountIndex;
    this.proxy = proxy;
    this.useProxy = useProxy;
    this.proxyIP = null;
    this.sessionId = null;
    this.fingerprint = null;
    this.baseHeaders = baseHeaders;
    this.headers = { ...baseHeaders };
    this.deviceCategory = deviceCategory;
    this.sendClientHints = sendClientHints;

    this.sessions = new SessionManager(sessionFile);
    this.logger = new Logger({
      prefix: logPrefix,
      accountIndex,
      useProxy,
      address,
      getProxyIP: () => this.proxyIP,
    });
    this.http = null;
  }

  log(msg, type) {
    this.logger.log(msg, type);
  }

  setSession(sessionId, options = {}) {
    this.sessionId = String(sessionId);
    this.fingerprint = this.sessions.getOrCreate(this.sessionId, {
      deviceCategory: this.deviceCategory,
      ...options,
    });
    const builtHeaders = buildHeaders(this.fingerprint, this.baseHeaders);
    this.headers = this.sendClientHints ? { ...builtHeaders, ...buildClientHints(this.fingerprint) } : builtHeaders;

    // Reuse the existing HTTP client — each new instance holds a native TLS client that leaks
    if (this.http) {
      this.http.setHeaders(this.headers);
    } else {
      this.http = new HttpClient({
        headers: this.headers,
        proxy: this.proxy,
        useProxy: this.useProxy,
      });
    }
    return this.fingerprint;
  }

  setExtraHeaders(extra = {}) {
    const clean = Object.fromEntries(Object.entries(extra).filter(([, v]) => v != null));
    this.headers = { ...this.headers, ...clean };
    if (this.http) this.http.setHeaders(this.headers);
  }

  async checkProxyIP() {
    if (!this.useProxy || !this.proxy) return null;
    if (!this.http) {
      this.http = new HttpClient({
        headers: this.headers,
        proxy: this.proxy,
        useProxy: this.useProxy,
      });
    }
    this.proxyIP = await this.http.checkProxyIP();
    return this.proxyIP;
  }

  async makeRequest(url, method, data = {}, options = {}) {
    if (!this.http) {
      throw new Error("HTTP client not initialized. Call setSession() first.");
    }
    return this.http.request(url, method, data, options);
  }
}

module.exports = ClientBase;
