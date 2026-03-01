import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '../..');
const DATA_DIR = path.join(ROOT_DIR, 'data');
const FP_PATH = path.join(DATA_DIR, 'fingerprints.json');

class SeededRandom {
  constructor(seed) {
    this.hash = crypto.createHash('sha256').update(seed).digest();
    this.index = 0;
  }

  next() {
    const i = this.index % 32;
    this.index++;
    if (this.index >= 32) {
      this.hash = crypto.createHash('sha256').update(this.hash).digest();
      this.index = 0;
    }
    return this.hash[i] / 256;
  }

  nextInt(min, max) {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  pick(arr) {
    return arr[this.nextInt(0, arr.length - 1)];
  }

  pickWeighted(items) {
    const totalWeight = items.reduce((sum, i) => sum + i.weight, 0);
    let r = this.next() * totalWeight;
    for (const item of items) {
      r -= item.weight;
      if (r <= 0) return item.value;
    }
    return items[items.length - 1].value;
  }
}

const OS_DATA = [
  { value: { name: 'Windows', versions: ['10.0', '11.0'], platform: 'Win32' }, weight: 70 },
  { value: { name: 'macOS', versions: ['14.0', '14.5', '15.0', '15.2', '15.4', '16.0'], platform: 'MacIntel' }, weight: 25 },
  { value: { name: 'Linux', versions: ['x86_64', 'x86_64'], platform: 'Linux x86_64' }, weight: 5 }
];

const BROWSER_DATA = [
  { value: { name: 'Chrome', minVer: 128, maxVer: 136 }, weight: 65 },
  { value: { name: 'Edge', minVer: 128, maxVer: 136 }, weight: 20 },
  { value: { name: 'Firefox', minVer: 128, maxVer: 138 }, weight: 10 },
  { value: { name: 'Safari', minVer: 17, maxVer: 19 }, weight: 5 }
];

const SCREEN_RESOLUTIONS = [
  '1920x1080', '2560x1440', '1366x768', '1536x864',
  '1440x900', '1680x1050', '2560x1600', '3840x2160',
  '1280x720', '1600x900'
];

const GPU_VENDORS = ['Google Inc. (NVIDIA)', 'Google Inc. (AMD)', 'Google Inc. (Intel)'];
const GPU_RENDERERS = [
  'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)',
  'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)',
  'ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)',
  'ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0)',
  'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0)',
  'ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)',
  'Apple GPU',
  'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)'
];

function generateFingerprint(walletAddress) {
  const rng = new SeededRandom(walletAddress);

  const osData = rng.pickWeighted(OS_DATA);
  const osVersion = rng.pick(osData.versions);

  const browserData = rng.pickWeighted(BROWSER_DATA);
  const browserVersion = rng.nextInt(browserData.minVer, browserData.maxVer);
  const browserMinor = rng.nextInt(0, 9);

  const resolution = rng.pick(SCREEN_RESOLUTIONS);
  const [width, height] = resolution.split('x').map(Number);
  const colorDepth = rng.pick([24, 32]);
  const pixelRatio = rng.pick([1, 1.25, 1.5, 2]);

  const cpuCores = rng.pick([4, 6, 8, 12, 16]);
  const ram = rng.pick([4, 8, 16, 32]);
  const touchPoints = rng.pick([0, 0, 0, 1, 5, 10]);

  const gpuVendor = rng.pick(GPU_VENDORS);
  const gpuRenderer = rng.pick(GPU_RENDERERS);

  const canvasHash = crypto.createHash('md5')
    .update(`canvas_${walletAddress}_salt`)
    .digest('hex');

  const audioHash = crypto.createHash('md5')
    .update(`audio_${walletAddress}_salt`)
    .digest('hex')
    .slice(0, 16);

  let userAgent = '';
  if (browserData.name === 'Chrome') {
    if (osData.name === 'Windows') {
      userAgent = `Mozilla/5.0 (Windows NT ${osVersion}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${browserVersion}.0.${rng.nextInt(5000, 6999)}.${rng.nextInt(50, 199)} Safari/537.36`;
    } else if (osData.name === 'macOS') {
      const macVer = osVersion.replace('.', '_');
      userAgent = `Mozilla/5.0 (Macintosh; Intel Mac OS X ${macVer}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${browserVersion}.0.${rng.nextInt(5000, 6999)}.${rng.nextInt(50, 199)} Safari/537.36`;
    } else {
      userAgent = `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${browserVersion}.0.${rng.nextInt(5000, 6999)}.${rng.nextInt(50, 199)} Safari/537.36`;
    }
  } else if (browserData.name === 'Edge') {
    userAgent = `Mozilla/5.0 (Windows NT ${osVersion}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${browserVersion}.0.${rng.nextInt(5000, 6999)}.${rng.nextInt(50, 199)} Safari/537.36 Edg/${browserVersion}.0.${rng.nextInt(2000, 2999)}.${rng.nextInt(50, 99)}`;
  } else if (browserData.name === 'Firefox') {
    if (osData.name === 'Windows') {
      userAgent = `Mozilla/5.0 (Windows NT ${osVersion}; Win64; x64; rv:${browserVersion}.0) Gecko/20100101 Firefox/${browserVersion}.0`;
    } else {
      userAgent = `Mozilla/5.0 (X11; Linux x86_64; rv:${browserVersion}.0) Gecko/20100101 Firefox/${browserVersion}.0`;
    }
  } else if (browserData.name === 'Safari') {
    const macVer = (osData.versions[0] || '14.0').replace('.', '_');
    userAgent = `Mozilla/5.0 (Macintosh; Intel Mac OS X ${macVer}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/${browserVersion}.${browserMinor} Safari/605.1.15`;
  }

  return {
    device: {
      os: osData.name,
      osVersion,
      platform: osData.platform
    },
    browser: {
      name: browserData.name,
      version: `${browserVersion}.${browserMinor}`
    },
    screen: {
      width,
      height,
      colorDepth,
      pixelRatio
    },
    hardware: {
      cpuCores,
      ram,
      touchPoints
    },
    webgl: {
      vendor: gpuVendor,
      renderer: gpuRenderer
    },
    canvas: canvasHash,
    audio: audioHash,
    userAgent
  };
}

function loadFingerprintStore() {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (fs.existsSync(FP_PATH)) {
      return JSON.parse(fs.readFileSync(FP_PATH, 'utf-8'));
    }
  } catch { /* bỏ qua */ }
  return {};
}

let _fpCache = null;
let _fpDirty = false;
let _fpSaveTimer = null;

function getFpCache() {
  if (!_fpCache) {
    _fpCache = loadFingerprintStore();
  }
  return _fpCache;
}

function scheduleSave() {
  if (_fpSaveTimer) return;
  _fpSaveTimer = setTimeout(() => {
    _fpSaveTimer = null;
    if (_fpDirty && _fpCache) {
      try {
        if (!fs.existsSync(DATA_DIR)) {
          fs.mkdirSync(DATA_DIR, { recursive: true });
        }
        fs.writeFileSync(FP_PATH, JSON.stringify(_fpCache, null, 2), 'utf-8');
        _fpDirty = false;
      } catch { /* bỏ qua */ }
    }
  }, 2000);
}

process.on('exit', () => {
  if (_fpDirty && _fpCache) {
    try {
      if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
      fs.writeFileSync(FP_PATH, JSON.stringify(_fpCache, null, 2), 'utf-8');
    } catch { /* bỏ qua */ }
  }
});

export function getFingerprint(walletAddress) {
  const store = getFpCache();

  if (store[walletAddress]) {
    return store[walletAddress];
  }

  const fp = generateFingerprint(walletAddress);
  store[walletAddress] = fp;
  _fpDirty = true;
  scheduleSave();

  return fp;
}

export function getFingerprintHeaders(walletAddress) {
  const fp = getFingerprint(walletAddress);
  const browserVer = fp.browser.version.split('.')[0];
  const browserName = fp.browser.name;

  let secChUa = '';
  if (browserName === 'Chrome') {
    secChUa = `"Chromium";v="${browserVer}", "Google Chrome";v="${browserVer}", "Not-A.Brand";v="99"`;
  } else if (browserName === 'Edge') {
    secChUa = `"Chromium";v="${browserVer}", "Microsoft Edge";v="${browserVer}", "Not-A.Brand";v="99"`;
  } else if (browserName === 'Safari') {
    secChUa = `"Safari";v="${browserVer}", "Not-A.Brand";v="99"`;
  }

  const headers = {
    'User-Agent': fp.userAgent,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Ch-Ua-Platform': `"${fp.device.os}"`,
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
  };

  if (secChUa) {
    headers['Sec-Ch-Ua'] = secChUa;
  }

  return headers;
}

export default { getFingerprint, getFingerprintHeaders };
