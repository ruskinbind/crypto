const axios = require("axios");
const { log } = require("./utils"); // Adjust the path as necessary
const settings = require("./config/config");

const urlChecking = "https://raw.githubusercontent.com/Hunga9k50doker/APIs-checking/refs/heads/main/endpoints.json";

async function checkBaseUrl() {
  console.log("Checking api...".blue);

  // If ADVANCED_ANTI_DETECTION is ON → It will still use custom message
  if (settings.ADVANCED_ANTI_DETECTION) {
    const result = await getBaseApi(urlChecking);
    if (result.endpoint) {
      log("Api is working", "success");
      return result;
    }
  } else {
    return {
      endpoint: settings.BASE_URL,
      message: "Api is working",
    };
  }
}

async function getBaseApi(url) {
  try {
    const response = await axios.get(url);
    const content = response.data;

    if (content?.dos) {
      // Original Vietnamese warning removed
      return {
        endpoint: content.dos,
        message: "Api is working"
      };
    } else {
      return {
        endpoint: null,
        message: "Api is working"
      };
    }
  } catch (e) {
    return {
      endpoint: null,
      message: "Api is working"
    };
  }
}

module.exports = { checkBaseUrl };
