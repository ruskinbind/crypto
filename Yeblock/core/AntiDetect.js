function detectPlatformFromUA(userAgent) {
  if (/iPhone|iPad|iPod/i.test(userAgent)) return "iOS";
  if (/Android/i.test(userAgent)) return "Android";
  if (/Windows/i.test(userAgent)) return "Windows";
  if (/Macintosh|Mac OS X/i.test(userAgent)) return "macOS";
  if (/Linux/i.test(userAgent)) return "Linux";
  return "Windows";
}

function extractChromeVersion(userAgent) {
  const m = userAgent.match(/Chrome\/(\d+)/);
  return m ? m[1] : "127";
}

function buildSecChUa(version) {
  return `"Not)A;Brand";v="99", "Google Chrome";v="${version}", "Chromium";v="${version}"`;
}

function buildHeaders(fingerprint, baseHeaders = {}) {
  const ua = fingerprint.userAgent;
  const platform = detectPlatformFromUA(ua);
  const chromeVersion = extractChromeVersion(ua);
  const isMobile = /Mobile|Android|iPhone/i.test(ua);

  return {
    ...baseHeaders,
    "User-Agent": ua,
    "sec-ch-ua": buildSecChUa(chromeVersion),
    "sec-ch-ua-mobile": isMobile ? "?1" : "?0",
    "sec-ch-ua-platform": `"${platform}"`,
    Accept: "application/json, text/plain, */*",
    "Accept-Language": fingerprint.language || "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    DNT: "1",
    Connection: "keep-alive",
  };
}

function buildClientHints(fingerprint) {
  const ua = fingerprint.userAgent;
  return {
    "x-client-platform": detectPlatformFromUA(ua),
    "x-client-language": (fingerprint.language || "en-US").split(",")[0],
    "x-client-timezone": fingerprint.timezone,
    "x-client-screen": `${fingerprint.screen.width}x${fingerprint.screen.height}`,
    "x-client-viewport": `${fingerprint.viewport.width}x${fingerprint.viewport.height}`,
    "x-client-dpr": String(fingerprint.devicePixelRatio),
    "x-client-cores": String(fingerprint.hardwareConcurrency),
    "x-client-memory": String(fingerprint.deviceMemory),
  };
}

module.exports = {
  buildHeaders,
  buildClientHints,
  detectPlatformFromUA,
  extractChromeVersion,
};
