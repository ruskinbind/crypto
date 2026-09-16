const { Impit } = require("impit");
const { HttpsProxyAgent } = require("https-proxy-agent");
const axios = require("axios");
const settings = require("../config/config");

function extractError(json, fallback = "unknown") {
  const err = json?.error;
  if (typeof err === "string" && err) return err;
  if (err && typeof err === "object") return err.message || err.details || err.code || JSON.stringify(err);
  return json?.message || fallback;
}

class HttpClient {
  constructor({ headers = {}, proxy = null, useProxy = false, timeout = 120000, browser = "chrome" } = {}) {
    this.headers = headers;
    this.proxy = proxy;
    this.useProxy = useProxy;
    this.timeout = timeout;
    this.browser = browser;
    this.impit = this.#createImpit(headers);
  }

  #createImpit(headers) {
    return new Impit({
      browser: this.browser,
      proxyUrl: this.useProxy ? this.proxy : undefined,
      ignoreTlsErrors: true,
      headers,
    });
  }

  setHeaders(headers) {
    // Only rebuild the native client when headers actually changed
    const changed = JSON.stringify(headers) !== JSON.stringify(this.headers);
    this.headers = headers;
    if (changed) this.impit = this.#createImpit(headers);
  }

  async checkProxyIP() {
    if (!this.useProxy || !this.proxy) return null;
    const proxyAgent = new HttpsProxyAgent(this.proxy);
    const response = await axios.get("https://api.ipify.org?format=json", {
      httpsAgent: proxyAgent,
      timeout: 30000,
    });
    if (response.status !== 200) {
      throw new Error(`Cannot check proxy IP. Status code: ${response.status}`);
    }
    return response.data.ip;
  }

  async request(
    url,
    method,
    data = {},
    options = {
      retries: 5,
      isAuth: false,
      extraHeaders: {},
      refreshToken: null,
    },
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
      ...extraHeaders,
    };

    const proxyAgent = settings.USE_PROXY && this.proxy ? new HttpsProxyAgent(this.proxy) : null;
    const fetchOptions = {
      method: method.toUpperCase(),
      headers,
      credentials: "include",
      timeout: 120000,
      ...(proxyAgent ? { agent: proxyAgent } : {}),
      ...(method.toLowerCase() !== "get" ? { body: JSON.stringify(data) } : {}),
    };
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await this.impit.fetch(url, fetchOptions);
        const httpStatus = response.status;
        let jsonResponse;
        try {
          jsonResponse = await response.json();
        } catch {
          const detail = httpStatus >= 500 ? `server error page (HTTP ${httpStatus})` : `non-JSON response (HTTP ${httpStatus})`;
          console.log(`[Retry ${attempt}/${retries}] ${url} returned a ${detail}`);
          if (attempt === retries) {
            return { success: false, status: httpStatus, error: detail, data: null };
          }
          await new Promise((r) => setTimeout(r, 5000));
          continue;
        }

        const resolvedStatus = jsonResponse?.status || httpStatus;

        if (resolvedStatus === 401) {
          return { success: false, status: 401, error: extractError(jsonResponse, "Unauthorized"), data: null, responseHeader: response.headers };
        }
        if (resolvedStatus === 403) {
          return { success: false, status: 403, error: extractError(jsonResponse, "Forbidden"), data: null, responseHeader: response.headers };
        }
        if (resolvedStatus >= 400) {
          return { success: false, status: resolvedStatus, error: extractError(jsonResponse), data: null, responseHeader: response.headers };
        }

        return {
          responseHeader: response.headers,
          status: httpStatus,
          success: true,
          data: jsonResponse?.data || jsonResponse,
          error: null,
        };
      } catch (error) {
        const errorStatus = error.status || 500;
        const rawMessage = error?.response?.data?.error || error?.response?.data || error.message || String(error);
        const errorHeaders = error?.response?.headers || null;

        // Detect transient network errors (TLS EOF, connection reset, timeout)
        const isTransient =
          typeof rawMessage === "string" &&
          (rawMessage.includes("UnexpectedEof") ||
            rawMessage.includes("close_notify") ||
            rawMessage.includes("connection closed") ||
            rawMessage.includes("Connection reset") ||
            rawMessage.includes("ECONNRESET") ||
            rawMessage.includes("ECONNREFUSED") ||
            rawMessage.includes("ETIMEDOUT") ||
            rawMessage.includes("socket hang up") ||
            rawMessage.includes("SendRequest"));

        const errorMessage = isTransient ? "Network error (transient), retrying..." : rawMessage;

        if (errorStatus >= 400 && errorStatus < 500) {
          if (errorStatus === 429) {
            return { success: false, status: errorStatus, error: "You've reached daily limitation", data: null, responseHeader: errorHeaders };
          }
          return { success: false, status: errorStatus, error: rawMessage, data: null, responseHeader: errorHeaders };
        }

        if (attempt === retries) {
          return { success: false, status: errorStatus, error: rawMessage, data: null };
        }

        const delay = isTransient ? 3000 : 5000;
        console.log(`[Retry ${attempt}/${retries}] ${errorMessage}`);
        await new Promise((r) => setTimeout(r, delay));
      }
    }

    return { success: false, status: 500, error: "Request failed after retries", data: null };
  }
}

module.exports = HttpClient;
