const fs = require("fs");
const path = require("path");
const { storageDir } = require("../utils/storage");
const { decodeJwt } = require("../utils/utils");

class TokenStore {
  constructor(dirName = "tokens") {
    this.dir = storageDir(dirName);
  }

  #fileFor(account) {
    const safe = String(account).replace(/[^a-zA-Z0-9_\-]/g, "_");
    return path.join(this.dir, `${safe}.json`);
  }

  load(account) {
    try {
      const data = JSON.parse(fs.readFileSync(this.#fileFor(account), "utf8"));
      if (data?.account !== account) return null;
      return data;
    } catch {
      return null;
    }
  }

  save(account, { token, refreshToken, expiresIn }) {
    const expiresAt = TokenStore.expiryOf(token) || Date.now() + (Number(expiresIn) || 1800) * 1000;
    const data = { account, token, refreshToken, expiresAt };
    try {
      fs.writeFileSync(this.#fileFor(account), JSON.stringify(data, null, 2));
    } catch {}
    return data;
  }

  remove(account) {
    try {
      fs.unlinkSync(this.#fileFor(account));
    } catch {}
  }

  static expiryOf(token) {
    const exp = decodeJwt(token)?.exp;
    return exp ? exp * 1000 : null;
  }

  static isExpired(token, skewSeconds = 60) {
    const expiresAt = TokenStore.expiryOf(token);
    if (!expiresAt) return true;
    return Date.now() + skewSeconds * 1000 >= expiresAt;
  }
}

module.exports = TokenStore;
