const crypto = require("crypto");
const UserAgent = require("user-agents");

const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Los_Angeles",
  "America/Denver",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "Europe/Madrid",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Asia/Hong_Kong",
  "Asia/Bangkok",
  "Asia/Ho_Chi_Minh",
  "Asia/Seoul",
  "Australia/Sydney",
];

const LANGUAGES = [
  "en-US,en;q=0.9",
  "en-GB,en;q=0.9",
  "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
  "fr-FR,fr;q=0.9,en;q=0.8",
  "de-DE,de;q=0.9,en;q=0.8",
  "es-ES,es;q=0.9,en;q=0.8",
  "ja-JP,ja;q=0.9,en;q=0.8",
];

const WEBGL_VENDORS = [
  {
    vendor: "Google Inc. (Intel)",
    renderer: "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
  },
  {
    vendor: "Google Inc. (Intel)",
    renderer: "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
  },
  {
    vendor: "Google Inc. (NVIDIA)",
    renderer: "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
  },
  {
    vendor: "Google Inc. (NVIDIA)",
    renderer: "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
  },
  {
    vendor: "Google Inc. (AMD)",
    renderer: "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)",
  },
  {
    vendor: "Apple Inc.",
    renderer: "Apple GPU",
  },
];

const FONT_POOL = [
  "Arial",
  "Helvetica",
  "Times New Roman",
  "Courier New",
  "Verdana",
  "Georgia",
  "Palatino",
  "Garamond",
  "Bookman",
  "Comic Sans MS",
  "Trebuchet MS",
  "Arial Black",
  "Impact",
  "Tahoma",
  "Segoe UI",
  "Roboto",
  "Open Sans",
  "Lato",
  "Noto Sans",
  "Calibri",
  "Cambria",
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function pickMany(arr, min, max) {
  const count = Math.floor(Math.random() * (max - min + 1)) + min;
  const shuffled = [...arr].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

function randomHex(len) {
  return crypto.randomBytes(len).toString("hex");
}

function buildUserAgent(options = {}) {
  const { deviceCategory = "desktop", chromeOnly = false } = options;
  const base = { deviceCategory, platform: /Win64|Win32/ };
  if (!chromeOnly) return new UserAgent(base);
  for (let i = 0; i < 50; i++) {
    const ua = new UserAgent(base);
    const s = ua.toString();
    if (/Chrome\/\d+/.test(s) && !/Edg|OPR|Firefox|SamsungBrowser/.test(s)) return ua;
  }
  return new UserAgent({ ...base, userAgent: /Chrome\/1\d\d\.0\.0\.0 Safari/ });
}

function generateFingerprint(options = {}) {
  const ua = buildUserAgent({ deviceCategory: options.deviceCategory, chromeOnly: options.chromeOnly });
  const data = ua.data;
  const webgl = pick(WEBGL_VENDORS);
  const isMobile = (data.deviceCategory || "").toLowerCase() === "mobile";

  return {
    userAgent: ua.toString(),
    deviceId: randomHex(16),
    csrfToken: crypto.randomUUID(),
    appName: data.appName || "Netscape",
    appVersion: data.appVersion || "5.0",
    platform: data.platform || "Win32",
    vendor: data.vendor || "Google Inc.",
    deviceCategory: data.deviceCategory || "desktop",
    oscpu: data.oscpu || null,
    pluginsLength: data.pluginsLength || 0,
    screen: {
      width: data.screenWidth || 1920,
      height: data.screenHeight || 1080,
      availWidth: data.screenWidth || 1920,
      availHeight: (data.screenHeight || 1080) - 40,
      colorDepth: 24,
      pixelDepth: 24,
    },
    viewport: {
      width: data.viewportWidth || 1280,
      height: data.viewportHeight || 720,
    },
    devicePixelRatio: pick([1, 1.25, 1.5, 2]),
    hardwareConcurrency: pick([4, 6, 8, 12, 16]),
    deviceMemory: pick([4, 8, 16]),
    maxTouchPoints: isMobile ? pick([5, 10]) : 0,
    timezone: pick(TIMEZONES),
    timezoneOffset: new Date().getTimezoneOffset(),
    language: pick(LANGUAGES),
    languages: ["en-US", "en"],
    webgl: {
      vendor: webgl.vendor,
      renderer: webgl.renderer,
    },
    canvasHash: randomHex(16),
    audioHash: randomHex(16),
    fontsHash: randomHex(16),
    fonts: pickMany(FONT_POOL, 8, 16),
    cookieEnabled: true,
    doNotTrack: pick(["1", null]),
    sessionId: randomHex(8),
    createdAt: Date.now(),
  };
}

module.exports = { generateFingerprint };
