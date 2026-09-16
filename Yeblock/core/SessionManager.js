const fs = require("fs");
const path = require("path");
const { generateFingerprint } = require("./Fingerprint");
const { storageDir } = require("../utils/storage");

// Previously this class loaded ONE shared JSON file containing every account's
// fingerprint into memory (this.data), and rewrote the whole file on every save.
// At thousands of accounts, each SessionManager instance held a full copy of that
// ever-growing file, and every write re-serialized it entirely — memory and I/O
// cost scaled with total account count (O(n) per instance, O(n^2) across all
// instances), which is what caused OOM crashes regardless of thread count.
// Now each account gets its own small file, so cost per account is O(1).
class SessionManager {
  constructor(filename = "session_fingerprints.json") {
    const base = filename.replace(/\.json$/i, "");
    this.dir = storageDir(base, `${base}_data`);
    this.#migrateLegacyFile(path.join(process.cwd(), filename));
  }

  #fileFor(sessionId) {
    const safe = String(sessionId).replace(/[^a-zA-Z0-9_\-]/g, "_");
    return path.join(this.dir, `${safe}.json`);
  }

  // One-time split of the old monolithic file into per-account files, if present.
  #migrateLegacyFile(legacyPath) {
    try {
      if (!fs.existsSync(legacyPath)) return;
      const data = JSON.parse(fs.readFileSync(legacyPath, "utf8"));
      for (const [key, value] of Object.entries(data)) {
        const dest = this.#fileFor(key);
        if (!fs.existsSync(dest)) fs.writeFileSync(dest, JSON.stringify(value, null, 2));
      }
      fs.renameSync(legacyPath, `${legacyPath}.migrated`);
    } catch {
      // best-effort; on failure sessions are simply regenerated per account
    }
  }

  getOrCreate(sessionId, options = {}) {
    const file = this.#fileFor(sessionId);
    try {
      const fp = JSON.parse(fs.readFileSync(file, "utf8"));
      if (fp && fp.userAgent) return fp;
    } catch {}
    const fingerprint = generateFingerprint(options);
    fs.writeFileSync(file, JSON.stringify(fingerprint, null, 2));
    return fingerprint;
  }

  get(sessionId) {
    try {
      return JSON.parse(fs.readFileSync(this.#fileFor(sessionId), "utf8"));
    } catch {
      return null;
    }
  }

  set(sessionId, fingerprint) {
    fs.writeFileSync(this.#fileFor(sessionId), JSON.stringify(fingerprint, null, 2));
  }

  remove(sessionId) {
    try {
      fs.unlinkSync(this.#fileFor(sessionId));
    } catch {}
  }
}

module.exports = SessionManager;
