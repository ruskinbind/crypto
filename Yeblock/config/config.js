require("dotenv").config();
const { _isArray } = require("../utils/utils.js");

const settings = {
  BASE_URL: process.env.BASE_URL ? process.env.BASE_URL : "https://www.yeblock.com/api",
  ORIGIN: process.env.ORIGIN ? process.env.ORIGIN : "https://www.yeblock.com",
  REFERER: process.env.REFERER ? process.env.REFERER : "https://www.yeblock.com/",

  AUTO_CHECKIN: process.env.AUTO_CHECKIN ? process.env.AUTO_CHECKIN.toLowerCase() === "true" : true,
  SKIP_UNVERIFIED_EMAIL: process.env.SKIP_UNVERIFIED_EMAIL ? process.env.SKIP_UNVERIFIED_EMAIL.toLowerCase() === "true" : true,
  CHECKIN_COOLDOWN_HOURS: process.env.CHECKIN_COOLDOWN_HOURS ? parseFloat(process.env.CHECKIN_COOLDOWN_HOURS) : 24,
  SHOW_ASSETS: process.env.SHOW_ASSETS ? process.env.SHOW_ASSETS.toLowerCase() === "true" : true,

  TOKEN_REFRESH_SKEW: process.env.TOKEN_REFRESH_SKEW ? parseInt(process.env.TOKEN_REFRESH_SKEW) : 60,

  USE_PROXY: process.env.USE_PROXY ? process.env.USE_PROXY.toLowerCase() === "true" : false,
  MAX_THEADS: process.env.MAX_THEADS ? parseInt(process.env.MAX_THEADS) : 10,
  MAX_THEADS_NO_PROXY: process.env.MAX_THEADS_NO_PROXY ? parseInt(process.env.MAX_THEADS_NO_PROXY) : 10,
  TIME_SLEEP: process.env.TIME_SLEEP ? parseInt(process.env.TIME_SLEEP) : 360,

  DELAY_BETWEEN_REQUESTS: process.env.DELAY_BETWEEN_REQUESTS && _isArray(process.env.DELAY_BETWEEN_REQUESTS) ? JSON.parse(process.env.DELAY_BETWEEN_REQUESTS) : [1, 5],
  DELAY_START_BOT: process.env.DELAY_START_BOT && _isArray(process.env.DELAY_START_BOT) ? JSON.parse(process.env.DELAY_START_BOT) : [1, 10],
};

module.exports = settings;
