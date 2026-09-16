const fs = require("fs");
const path = require("path");

// All local cache (fingerprints, tokens, mint cooldowns, faucet records) lives under
// one localstorage/ folder instead of separate *_data folders in the project root.
const BASE = path.join(process.cwd(), "localstorage");

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
  return p;
}

// One-time move of an old root-level folder into localstorage/<sub>.
function migrate(oldName, sub) {
  try {
    const oldPath = path.join(process.cwd(), oldName);
    const newPath = path.join(BASE, sub);
    if (fs.existsSync(oldPath) && !fs.existsSync(newPath)) {
      ensureDir(BASE);
      fs.renameSync(oldPath, newPath);
    }
  } catch (error) {}
}

function storageDir(sub, legacyOldName) {
  if (legacyOldName) migrate(legacyOldName, sub);
  return ensureDir(path.join(BASE, sub));
}

module.exports = { BASE, storageDir };
