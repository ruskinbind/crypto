const fs = require("fs");
const path = require("path");
const colors = require("colors");
require("dotenv").config();

function _isArray(obj) {
  if (Array.isArray(obj) && obj.length > 0) return true;
  try {
    const parsed = JSON.parse(obj);
    return Array.isArray(parsed) && parsed.length > 0;
  } catch {
    return false;
  }
}

async function sleep(seconds = null) {
  if (seconds && typeof seconds === "number") return new Promise((resolve) => setTimeout(resolve, +seconds * 1000));

  let range = [1, 5];
  if (seconds && Array.isArray(seconds)) range = seconds;

  const [min, max] = range;
  return new Promise((resolve) => {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    setTimeout(resolve, delay * 1000);
  });
}

function getRandomNumber(min, max) {
  return parseFloat((Math.random() * (max - min) + min).toFixed(6));
}

function getRandomElement(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function loadData(file) {
  try {
    const filePath = path.resolve(__dirname, "../data", file);
    const datas = fs
      .readFileSync(filePath, "utf8")
      .replace(/\r/g, "")
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#"));
    return datas;
  } catch {
    return [];
  }
}

function decodeJwt(token) {
  try {
    const payload = String(token).split(".")[1];
    if (!payload) return null;
    return JSON.parse(Buffer.from(payload.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"));
  } catch {
    return null;
  }
}

function formatDuration(ms) {
  const total = Math.max(0, Math.ceil(ms / 60000));
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return hours > 0 ? `${hours}h${String(minutes).padStart(2, "0")}m` : `${minutes}m`;
}

function log(msg, type = "info") {
  switch (type) {
    case "success":
      console.log(`[*] ${msg}`.green);
      break;
    case "custom":
      console.log(`[*] ${msg}`.magenta);
      break;
    case "error":
      console.log(`[!] ${msg}`.red);
      break;
    case "warning":
      console.log(`[*] ${msg}`.yellow);
      break;
    default:
      console.log(`[*] ${msg}`.blue);
  }
}

module.exports = {
  _isArray,
  sleep,
  getRandomNumber,
  getRandomElement,
  loadData,
  decodeJwt,
  formatDuration,
  log,
};
