let accountsList = [];

const axios = require('axios');
const fs = require('fs');
const path = require('path');
const moment = require('moment');
const readline = require('readline');
const { clear } = require('console');
const { HttpsProxyAgent } = require('https-proxy-agent');
const { SocksProxyAgent } = require('socks-proxy-agent');
const https = require('https');
const crypto = require('crypto');

const API_BASE_URL = 'https://prod.interlinklabs.ai/api/v1';
const MINI_API_BASE_URL = 'https://interlink-mini-app.interlinklabs.ai/api';
const TOKEN_FILE_PATH = path.join(__dirname, 'token.txt');
const MINI_TOKEN_FILE_PATH = path.join(__dirname, 'mini_token.txt');
const DEVICE_FILE_PATH = path.join(__dirname, 'device.txt');
const PROXIES_FILE_PATH = path.join(__dirname, 'proxies.txt');
const ACCOUNTS_FILE_PATH = path.join(__dirname, 'accounts.txt'); // multi-account file
const APP_ID = 'id__mk39oef6we80fs7j2rif';
const CLAIM_INTERVAL_MS = 4 * 60 * 60 * 1000;

const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  white: '\x1b[37m',
  gray: '\x1b[90m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

const logger = {
  info: (msg) => console.log(`${colors.green}[✓] ${msg}${colors.reset}`),
  wallet: (msg) => console.log(`${colors.yellow}[💼] Ví: ${msg}${colors.reset}`),
  warn: (msg) => console.log(`${colors.yellow}[⚠️] Cảnh báo: ${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.red}[✗] Lỗi: ${msg}${colors.reset}`),
  success: (msg) => console.log(`${colors.green}[✅] Thành công: ${msg}${colors.reset}`),
  loading: (msg) => console.log(`${colors.cyan}[⟳] Đang xử lý: ${msg}${colors.reset}`),
  step: (msg) => console.log(`${colors.white}[➤] ${msg}${colors.reset}`),
  banner: () => {
    console.log(`${colors.cyan}${colors.bold}`);
    console.log(`---------------------------------------------`);
    console.log(`       🔄 BOT TỰ ĐỘNG CLAIM AIRDROP`);
    console.log(`            👉 Interlink Labs 👈`);
    console.log(`---------------------------------------------${colors.reset}`);
    console.log();
  }
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function promptInput(question) {
  return new Promise((resolve) => {
    rl.question(`${colors.white}${question}${colors.reset}`, (answer) => {
      resolve(answer.trim());
    });
  });
}

function generateRandomDeviceId() {
  return crypto.randomBytes(8).toString('hex');
}

/* ---------- Existing helper functions ---------- */

async function checkLoginIdExist(apiClient, loginId, deviceId) {
  try {
    const response = await apiClient.get(`/auth/loginId-exist-check/${loginId}`, { params: { deviceId } });
    if (response.data.statusCode === 200) {
      logger.success('ID đăng nhập tồn tại.');
      return true;
    } else {
      logger.error(`Kiểm tra ID đăng nhập thất bại: ${JSON.stringify(response.data)}`);
      return false;
    }
  } catch (error) {
    logger.error(`Lỗi khi kiểm tra sự tồn tại của ID đăng nhập: ${error.response?.data?.message || error.message}`);
    return false;
  }
}

async function checkPasscode(apiClient, loginId, passcode, deviceId) {
  try {
    const payload = { loginId, passcode, deviceId };
    const response = await apiClient.post('/auth/check-passcode', payload);
    if (response.data.statusCode === 200) {
      logger.success('Mã passcode đã được xác thực.');
      return true;
    } else {
      logger.error(`Kiểm tra passcode thất bại: ${JSON.stringify(response.data)}`);
      return false;
    }
  } catch (error) {
    logger.error(`Lỗi khi kiểm tra passcode: ${error.response?.data?.message || error.message}`);
    if (error.response?.data) {
      logger.error(`Chi tiết phản hồi: ${JSON.stringify(error.response.data)}`);
    }
    return false;
  }
}

async function sendOtp(apiClient, loginId, passcode, email, deviceId) {
  try {
    const payload = { loginId, passcode, email, deviceId };
    const response = await apiClient.post('/auth/send-otp-email-verify-login', payload);
    if (response.data.statusCode === 200) {
      logger.success(response.data.message);
      logger.info(`Nếu bạn không nhận được mã OTP, hãy dừng bot (Ctrl+C) và khởi động lại.`);
    } else {
      logger.error(`Gửi mã OTP thất bại: ${JSON.stringify(response.data)}`);
    }
  } catch (error) {
    logger.error(`Lỗi khi gửi mã OTP: ${error.response?.data?.message || error.message}`);
    if (error.response?.data) {
      logger.error(`Chi tiết phản hồi: ${JSON.stringify(error.response.data)}`);
    }
  }
}

async function verifyOtp(apiClient, loginId, otp, deviceId) {
  try {
    const payload = { loginId, otp, deviceId };
    const response = await apiClient.post('/auth/check-otp-email-verify-login', payload);
    if (response.data.statusCode === 200) {
      logger.success(response.data.message);
      const token = response.data.data.jwtToken;
      saveToken(token);
      return token;
    } else {
      logger.error(`Xác thực OTP thất bại: ${JSON.stringify(response.data)}`);
      return null;
    }
  } catch (error) {
    logger.error(`Lỗi khi xác thực OTP: ${error.response?.data?.message || error.message}`);
    if (error.response?.data) {
      logger.error(`Chi tiết phản hồi: ${JSON.stringify(error.response.data)}`);
    }
    return null;
  }
}

async function getMiniToken(apiClient, loginId, appId) {
  try {
    const payload = { loginId, appId };
    const response = await apiClient.post('https://interlink-mini-app.interlinklabs.ai/api/tracking/verify', payload, {
      headers: {
        'api-public': 'e97ae0aa6520499d9edf20bd5a1e13c7'
      }
    });
    const miniToken = response.data.data?.token || response.data.data?.jwtToken;
    if (miniToken) {
      saveMiniToken(miniToken);
      logger.success('Mini token đã được lấy thành công.');
      return miniToken;
    } else {
      logger.error('Không tìm thấy mini token trong phản hồi.');
      return null;
    }
  } catch (error) {
    logger.error(`Lỗi khi lấy mini token: ${error.response?.data?.message || error.message}`);
    return null;
  }
}

async function validateMiniToken(miniToken, appId) {
  const validateConfig = {
    baseURL: MINI_API_BASE_URL,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Redmi Note 8 Pro Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
      'Accept-Encoding': 'gzip, deflate',
      'Content-Type': 'application/json',
      'origin': 'https://interlink-mini-app.interlinklabs.ai',
      'x-requested-with': 'org.ai.interlinklabs.interlinkId',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'referer': 'https://interlink-mini-app.interlinklabs.ai/qi-hong-interlink/',
      'accept-language': 'en-US,en;q=0.9'
    },
    timeout: 30000,
    httpsAgent: new https.Agent({ rejectUnauthorized: false })
  };
  const validateClient = axios.create(validateConfig);
  try {
    const res = await validateClient.post('/tracking/validate-token', { token: miniToken, appId });
    if (res.data.success) {
      logger.info('Mini token đã được xác thực thành công.');
    } else {
      logger.error('Xác thực mini token thất bại.');
    }
  } catch (error) {
    logger.error(`Lỗi khi xác thực mini token: ${error.response?.data?.message || error.message}`);
  }
}

function saveToken(token) {
  try {
    fs.writeFileSync(TOKEN_FILE_PATH, token);
    logger.info(`Đã lưu token vào tệp: ${TOKEN_FILE_PATH}`);
  } catch (error) {
    logger.error(`Lỗi khi lưu token: ${error.message}`);
  }
}

function saveMiniToken(token) {
  try {
    fs.writeFileSync(MINI_TOKEN_FILE_PATH, token);
    logger.info(`Đã lưu mini token vào tệp: ${MINI_TOKEN_FILE_PATH}`);
  } catch (error) {
    logger.error(`Lỗi khi lưu mini token: ${error.message}`);
  }
}

function readToken() {
  try {
    return fs.readFileSync(TOKEN_FILE_PATH, 'utf8').trim();
  } catch (error) {
    logger.warn(`Không tìm thấy hoặc token không hợp lệ. Tiến hành đăng nhập.`);
    return null;
  }
}

function readMiniToken() {
  try {
    return fs.readFileSync(MINI_TOKEN_FILE_PATH, 'utf8').trim();
  } catch (error) {
    logger.warn(`Không tìm thấy hoặc mini token không hợp lệ.`);
    return null;
  }
}

function readDevice() {
  try {
    return fs.readFileSync(DEVICE_FILE_PATH, 'utf8').trim();
  } catch (error) {
    logger.warn(`Không tìm thấy tệp thiết bị. Sẽ tạo ID thiết bị ngẫu nhiên.`);
    return null;
  }
}

function saveDevice(deviceId) {
  try {
    fs.writeFileSync(DEVICE_FILE_PATH, deviceId);
    logger.info(`Đã lưu ID thiết bị vào tệp: ${DEVICE_FILE_PATH}`);
  } catch (error) {
    logger.error(`Lỗi khi lưu ID thiết bị: ${error.message}`);
  }
}

async function login(proxies, deviceId) {
  const loginId = await promptInput('Nhập tài khoản đăng nhập (SỐ ID SAU DẤU @): ');
  const passcode = await promptInput('Nhập mã passcode (6 SỐ): ');
  const email = await promptInput('Nhập địa chỉ email: ');

  let apiClient;
  const proxy = getRandomProxy(proxies);

  if (proxy) {
    logger.step(`Đang cố gắng kiểm tra đăng nhập qua proxy: ${proxy}`);
    apiClient = createApiClient(null, proxy, deviceId);
  } else {
    logger.step(`Đang kiểm tra đăng nhập mà không dùng proxy...`);
    apiClient = createApiClient(null, null, deviceId);
  }

  if (!await checkLoginIdExist(apiClient, loginId, deviceId)) {
    return null;
  }

  if (!await checkPasscode(apiClient, loginId, passcode, deviceId)) {
    return null;
  }

  await sendOtp(apiClient, loginId, passcode, email, deviceId);
  const otp = await promptInput('Nhập mã OTP: ');
  const token = await verifyOtp(apiClient, loginId, otp, deviceId);

  if (!token) {
    return null;
  }

  const appId = APP_ID;
  let miniToken = await getMiniToken(apiClient, loginId, appId);
  if (miniToken) {
    await validateMiniToken(miniToken, appId);
  }

  return { token, miniToken };
}

function readProxies() {
  try {
    if (!fs.existsSync(PROXIES_FILE_PATH)) {
      logger.warn(`Không tìm thấy tệp proxies. Sẽ chạy không dùng proxy.`);
      return [];
    }

    const content = fs.readFileSync(PROXIES_FILE_PATH, 'utf8');
    return content.split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#'));
  } catch (error) {
    logger.error(`Lỗi khi đọc tệp proxies: ${error.message}`);
    return [];
  }
}

function getRandomProxy(proxies) {
  if (!proxies.length) return null;
  return proxies[Math.floor(Math.random() * proxies.length)];
}

function createProxyAgent(proxyUrl) {
  if (!proxyUrl) return null;

  if (proxyUrl.startsWith('socks://') || proxyUrl.startsWith('socks4://') || proxyUrl.startsWith('socks5://')) {
    return new SocksProxyAgent(proxyUrl);
  } else {
    return new HttpsProxyAgent(proxyUrl);
  }
}

function createApiClient(token, proxy = null, deviceId = null) {
  const config = {
    baseURL: API_BASE_URL,
    headers: {
      'User-Agent': 'okhttp/4.12.0',
      'Accept-Encoding': 'gzip'
    },
    timeout: 30000,
    httpsAgent: new https.Agent({
      rejectUnauthorized: false
    })
  };

  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  if (deviceId) {
    config.headers = {
      ...config.headers,
      'x-unique-id': deviceId,
      'x-model': 'Redmi Note 8 Pro',
      'x-brand': 'XiaoMi',
      'x-system-name': 'Android',
      'x-device-id': deviceId,
      'x-bundle-id': 'org.ai.interlinklabs.interlinkId',
      'version': '1.1.6'
    };
  }

  if (proxy) {
    try {
      const proxyAgent = createProxyAgent(proxy);
      config.httpsAgent = proxyAgent;
      config.proxy = false;
      logger.info(`Đang sử dụng proxy: ${proxy}`);
    } catch (error) {
      logger.error(`Lỗi khi thiết lập proxy: ${error.message}`);
    }
  }

  const instance = axios.create(config);

  instance.interceptors.request.use((conf) => {
    conf.headers['x-date'] = Date.now().toString();
    if (conf.method === 'post' && conf.data) {
      const body = typeof conf.data === 'object' ? JSON.stringify(conf.data) : conf.data.toString();
      const hash = crypto.createHash('sha256').update(body, 'utf8').digest('base64');
      conf.headers['x-content-hash'] = hash;
    }

    return conf;
  });

  return instance;
}

function createMiniApiClient(miniToken, proxy = null, deviceId, appId) {
  const config = {
    baseURL: MINI_API_BASE_URL,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Redmi Note 8 Pro Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
      'Accept': 'application/json, text/plain, */*',
      'Accept-Encoding': 'gzip, deflate',
      'origin': 'https://interlink-mini-app.interlinklabs.ai',
      'x-requested-with': 'org.ai.interlinklabs.interlinkId',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'sec-fetch-dest': 'empty',
      'referer': 'https://interlink-mini-app.interlinklabs.ai/qi-hong-interlink/',
      'accept-language': 'en-US,en;q=0.9',
      'Authorization': `Bearer ${miniToken}`,
      'Cookie': `jwt_${appId}=${miniToken}`
    },
    timeout: 30000,
    httpsAgent: new https.Agent({ rejectUnauthorized: false })
  };

  if (proxy) {
    try {
      const proxyAgent = createProxyAgent(proxy);
      config.httpsAgent = proxyAgent;
      config.proxy = false;
      logger.info(`Đang sử dụng proxy cho mini API: ${proxy}`);
    } catch (error) {
      logger.error(`Lỗi khi thiết lập proxy cho mini API: ${error.message}`);
    }
  }

  return axios.create(config);
}

async function doSpin(mainClient, miniClient) {
  try {
    const ticketsRes = await miniClient.get('/spin-ticket/get-number-of-tickets');
    const { numberOfTickets, amountITLG, isFirstTicket } = ticketsRes.data.data;

    let shouldBuy = false;
    if (numberOfTickets === 0) {
      if (isFirstTicket) {
        shouldBuy = true;
        logger.loading('Đang mua vé đầu tiên miễn phí...');
      } else {
        const balRes = await mainClient.get('/token/get-token');
        const balance = balRes.data.data.interlinkTokenAmount;
        if (balance >= amountITLG) {
          shouldBuy = true;
          logger.loading(`Đang mua vé với ${amountITLG} ITLG...`);
        } else {
          logger.warn(`Không đủ ITLG để mua vé: ${balance} < ${amountITLG}`);
        }
      }
    }

    if (shouldBuy) {
      const refId = crypto.randomUUID();
      const buyRes = await miniClient.post('/spin-ticket/buy', null, { headers: { 'x-ref-id': refId } });
      if (buyRes.data.success && buyRes.data.code === 200) {
        logger.success(`Đã mua vé: ${buyRes.data.data.message}`);
        if (buyRes.data.data.nextTimeToBuy) {
          const nextTime = new Date(buyRes.data.data.nextTimeToBuy).getTime();
          const waitMs = nextTime - Date.now();
          if (waitMs > 0) {
            logger.info(`Đang chờ ${(waitMs / 1000).toFixed(1)} giây trước khi quay...`);
            await new Promise(resolve => setTimeout(resolve, waitMs));
          }
        }
      } else {
        logger.error('Mua vé thất bại.');
        return;
      }
    }

    const currentTicketsRes = await miniClient.get('/spin-ticket/get-number-of-tickets');
    const currentNumTickets = currentTicketsRes.data.data.numberOfTickets;

    if (currentNumTickets > 0) {
      logger.loading('Đang thực hiện quay...');
      const spinRes = await miniClient.get('/spin-reward/generate-random');
      if (spinRes.data.success && spinRes.data.code === 200) {
        const { spinRewardType, spinRewardValue } = spinRes.data.data;
        logger.success(`Quay thành công! Nhận được ${spinRewardValue} ${spinRewardType}`);
      } else {
        logger.error('Quay thất bại.');
      }
    } else {
      logger.warn('Không có vé để quay.');
    }
  } catch (error) {
    logger.error(`Lỗi khi quay: ${error.response?.data?.message || error.message}`);
  }
}

function formatTimeRemaining(milliseconds) {
  if (milliseconds <= 0) return '00:00:00';

  const seconds = Math.floor((milliseconds / 1000) % 60);
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60);
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24);

  return [hours, minutes, seconds]
    .map(val => val.toString().padStart(2, '0'))
    .join(':');
}

async function getCurrentUser(apiClient) {
  try {
    const response = await apiClient.get('/auth/current-user');
    return response.data.data;
  } catch (error) {
    logger.error(`Lỗi khi lấy thông tin người dùng: ${error.response?.data?.message || error.message}`);
    return null;
  }
}

async function getTokenBalance(apiClient) {
  try {
    const response = await apiClient.get('/token/get-token');
    return response.data.data;
  } catch (error) {
    logger.error(`Lỗi khi lấy số dư token: ${error.response?.data?.message || error.message}`);
    return null;
  }
}

async function checkIsClaimable(apiClient) {
  try {
    const response = await apiClient.get('/token/check-is-claimable');
    return response.data.data;
  } catch (error) {
    logger.error(`Lỗi khi kiểm tra trạng thái claim airdrop: ${error.response?.data?.message || error.message}`);
    return { isClaimable: false, nextFrame: Date.now() + 1000 * 60 * 5 };
  }
}

async function claimAirdrop(apiClient) {
  try {
    const response = await apiClient.post('/token/claim-airdrop');
    logger.success(`Đã claim airdrop thành công!`);
    return response.data;
  } catch (error) {
    logger.error(`Lỗi khi claim airdrop: ${error.response?.data?.message || error.message}`);
    return null;
  }
}

function displayUserInfo(userInfo, tokenInfo) {
  if (!userInfo || !tokenInfo) return;

  console.log('\n' + '='.repeat(50));
  console.log(`${colors.white}${colors.bold}THÔNG TIN NGƯỜI DÙNG${colors.reset}`);
  console.log(`${colors.white}Tên đăng nhập:${colors.reset} ${userInfo.username}`);
  console.log(`${colors.white}Email:${colors.reset} ${userInfo.email}`);
  console.log(`${colors.white}Ví:${colors.reset} ${userInfo.connectedAccounts?.wallet?.address || 'Chưa kết nối'}`);
  console.log(`${colors.white}ID người dùng:${colors.reset} ${userInfo.loginId}`);
  console.log(`${colors.white}Mã giới thiệu:${colors.reset} ${tokenInfo.userReferralId}`);

  console.log('\n' + '='.repeat(50));
  console.log(`${colors.yellow}${colors.bold}SỐ DƯ TOKEN${colors.reset}`);
  console.log(`${colors.yellow}Gold Token:${colors.reset} ${tokenInfo.interlinkGoldTokenAmount}`);
  console.log(`${colors.yellow}Silver Token:${colors.reset} ${tokenInfo.interlinkSilverTokenAmount}`);
  console.log(`${colors.yellow}Diamond Token:${colors.reset} ${tokenInfo.interlinkDiamondTokenAmount}`);
  console.log(`${colors.yellow}Interlink Token:${colors.reset} ${tokenInfo.interlinkTokenAmount}`);
  console.log(`${colors.yellow}Lần claim gần nhất:${colors.reset} ${moment(tokenInfo.lastClaimTime).format('YYYY-MM-DD HH:mm:ss')}`);
  console.log('='.repeat(50) + '\n');
}

async function tryConnect(token, proxies, deviceId) {
  let apiClient;
  let userInfo = null;
  let tokenInfo = null;

  logger.step(`Đang thử kết nối không dùng proxy...`);
  apiClient = createApiClient(token, null, deviceId);

  logger.loading(`Đang lấy thông tin người dùng...`);
  userInfo = await getCurrentUser(apiClient);

  if (!userInfo && proxies.length > 0) {
    let attempts = 0;
    const maxAttempts = Math.min(proxies.length, 5);

    while (!userInfo && attempts < maxAttempts) {
      const proxy = proxies[attempts];
      logger.step(`Thử với proxy ${attempts + 1}/${maxAttempts}: ${proxy}`);

      apiClient = createApiClient(token, proxy, deviceId);

      logger.loading(`Đang lấy thông tin người dùng...`);
      userInfo = await getCurrentUser(apiClient);
      attempts++;

      if (!userInfo) {
        logger.warn(`Proxy ${proxy} thất bại. Đang thử proxy tiếp theo...`);
      }
    }
  }

  if (userInfo) {
    logger.loading(`Đang lấy số dư token...`);
    tokenInfo = await getTokenBalance(apiClient);
  }

  return { apiClient, userInfo, tokenInfo };
}

/* ---------- NEW: multi-account support ---------- */

function readAccounts() {
  try {
    if (!fs.existsSync(ACCOUNTS_FILE_PATH)) {
      logger.warn('Không tìm thấy accounts.txt — sẽ chạy single-account mode.');
      return [];
    }

    const raw = fs.readFileSync(ACCOUNTS_FILE_PATH, 'utf8');
    const lines = raw.split('\n')
      .map(l => l.trim())
      .filter(l => l && !l.startsWith('#'));

    if (!lines.length) {
      logger.warn('accounts.txt trống — sẽ chạy single-account mode.');
      return [];
    }

    const accounts = lines.map(line => {
      // format: token[,miniToken[,deviceId]]
      const parts = line.split(',').map(p => p.trim());
      return {
        token: parts[0] || null,
        miniToken: parts[1] || null,
        deviceId: parts[2] || null
      };
    });

    return accounts;
  } catch (error) {
    logger.error(`Lỗi khi đọc accounts.txt: ${error.message}`);
    return [];
  }
}

function saveAccounts(accounts) {
  try {
    const lines = accounts.map(acc =>
      `${acc.token || ""},${acc.miniToken || ""},${acc.deviceId || ""}`
    );
    fs.writeFileSync(ACCOUNTS_FILE_PATH, lines.join('\n'));
    logger.success('Đã cập nhật accounts.txt');
  } catch (err) {
    logger.error('Lỗi khi lưu accounts.txt: ' + err.message);
  }
}

async function startAccountLoop(accountIndex, account, globalProxies) {
  try {
    let token = account.token || null;
    let miniToken = account.miniToken || null;
    let deviceId = account.deviceId || null;

    if (!deviceId) {
      deviceId = generateRandomDeviceId();
      logger.info(`Account[${accountIndex}] - Tạo ID thiết bị ngẫu nhiên: ${deviceId}`);
    }

    // Try to connect with existing token (if any)
    let { apiClient, userInfo, tokenInfo } = await tryConnect(token, globalProxies, deviceId);

    if ((!userInfo || !tokenInfo) && !token) {
      // No token / cannot connect → interactive login ONCE
      logger.step(`Account[${accountIndex}] - Không có token. Bắt đầu flow đăng nhập tương tác.`);
      const loginRes = await login(globalProxies, deviceId);
      if (!loginRes || !loginRes.token) {
        logger.error(`Account[${accountIndex}] - Đăng nhập thất bại. Bỏ qua tài khoản này.`);
        return;
      }

      token = loginRes.token;
      miniToken = loginRes.miniToken || miniToken;

      // Save to global list & file
      accountsList[accountIndex - 1].token = token;
      accountsList[accountIndex - 1].miniToken = miniToken;
      accountsList[accountIndex - 1].deviceId = deviceId;
      saveAccounts(accountsList);

      const res2 = await tryConnect(token, globalProxies, deviceId);
      apiClient = res2.apiClient;
      userInfo = res2.userInfo;
      tokenInfo = res2.tokenInfo;
      if (!userInfo || !tokenInfo) {
        logger.error(`Account[${accountIndex}] - Không thể lấy thông tin sau khi đăng nhập. Bỏ qua.`);
        return;
      }
    }

    if (!miniToken && userInfo) {
      logger.step(`Account[${accountIndex}] - Đang lấy mini token...`);
      const appId = APP_ID;
      miniToken = await getMiniToken(apiClient, userInfo.loginId, appId);
      if (miniToken) {
        await validateMiniToken(miniToken, appId);
        accountsList[accountIndex - 1].miniToken = miniToken;
        saveAccounts(accountsList);
      }
    }

    logger.success(`Account[${accountIndex}] - Đã kết nối với tài khoản: ${userInfo?.username || 'Unknown'}`);
    displayUserInfo(userInfo, tokenInfo || { lastClaimTime: Date.now() });

    async function attemptClaimForAccount() {
      let currentApiClient = apiClient;
      if (globalProxies.length > 0) {
        const randomProxy = getRandomProxy(globalProxies);
        currentApiClient = createApiClient(token, randomProxy, deviceId);
      }

      const claimCheck = await checkIsClaimable(currentApiClient);

      if (claimCheck.isClaimable) {
        logger.loading(`Account[${accountIndex}] - Đang thực hiện claim...`);
        await claimAirdrop(currentApiClient);

        if (miniToken) {
          const miniProxy = getRandomProxy(globalProxies);
          const miniClient = createMiniApiClient(miniToken, miniProxy, deviceId, APP_ID);
          await doSpin(currentApiClient, miniClient);
        }

        logger.loading(`Account[${accountIndex}] - Đang cập nhật thông tin token...`);
        const newTokenInfo = await getTokenBalance(currentApiClient);
        if (newTokenInfo) {
          tokenInfo = newTokenInfo;
          displayUserInfo(userInfo, tokenInfo);
        }
      }

      return claimCheck.nextFrame;
    }

    // initial attempt
    let nextClaimTime = await attemptClaimForAccount();

    // countdown display per account
    const updateCountdown = () => {
      const now = Date.now();
      const timeRemaining = Math.max(0, nextClaimTime - now);
      process.stdout.write(`\rAccount[${accountIndex}] next claim in: ${colors.bold}${formatTimeRemaining(timeRemaining)}${colors.reset}     `);

      if (timeRemaining <= 0) {
        process.stdout.write('\n');
        logger.step(`Account[${accountIndex}] - Đã đến thời điểm claim!`);
        attemptClaimForAccount().then(newNextFrame => {
          nextClaimTime = newNextFrame;
        });
      }
    };

    setInterval(updateCountdown, 1000);

    const scheduleNextCheck = () => {
      const now = Date.now();
      const timeUntilNextCheck = Math.max(1000, nextClaimTime - now);

      setTimeout(async () => {
        logger.step(`Account[${accountIndex}] - Đến thời điểm claim theo lịch trình.`);
        nextClaimTime = await attemptClaimForAccount();
        scheduleNextCheck();
      }, timeUntilNextCheck);
    };

    scheduleNextCheck();

    logger.success(`Account[${accountIndex}] - Bot đang chạy cho tài khoản này!`);
  } catch (err) {
    logger.error(`Account[${accountIndex}] - Lỗi không mong muốn: ${err.message}`);
  }
}

/* ---------- main runner ---------- */

async function runBot() {
  try {
    clear();
    logger.banner();

    const proxies = readProxies();
    accountsList = readAccounts();

    if (accountsList && accountsList.length > 0) {
      logger.info(`Phát hiện ${accountsList.length} account trong accounts.txt — khởi chạy multi-account mode.`);

      // run accounts sequentially (OTP safe)
      for (let i = 0; i < accountsList.length; i++) {
        const acct = accountsList[i];
        logger.step(`\n[⚙️] Bắt đầu đăng nhập cho Account[${i + 1}]...`);
        await startAccountLoop(i + 1, acct, proxies);
      }

      logger.success(`🎯 Tất cả tài khoản đã xử lý xong!`);
      logger.info(`Nhấn Ctrl+C để thoát toàn bộ bot.`);
      return;
    }

    // fallback single-account flow (original behavior)
    let token = readToken();
    let miniToken = readMiniToken();
    let deviceId = readDevice();

    if (!deviceId) {
      deviceId = generateRandomDeviceId();
      logger.info(`Đã tạo ID thiết bị ngẫu nhiên: ${deviceId}`);
      saveDevice(deviceId);
    }

    let loginRes = null;
    if (!token) {
      logger.step(`Không tìm thấy token. Tiến hành đăng nhập...`);
      loginRes = await login(proxies, deviceId);
      if (!loginRes || !loginRes.token) {
        logger.error(`Đăng nhập thất bại. Thoát chương trình.`);
        process.exit(1);
      }
      token = loginRes.token;
      miniToken = loginRes.miniToken;
    }

    let { apiClient, userInfo, tokenInfo: initialTokenInfo } = await tryConnect(token, proxies, deviceId);

    if (!userInfo || !initialTokenInfo) {
      logger.error(`Không thể lấy thông tin cần thiết. Thử đăng nhập lại...`);
      loginRes = await login(proxies, deviceId);
      if (!loginRes || !loginRes.token) {
        logger.error(`Đăng nhập thất bại. Thoát chương trình.`);
        process.exit(1);
      }
      token = loginRes.token;
      miniToken = loginRes.miniToken || readMiniToken();
      const result = await tryConnect(token, proxies, deviceId);
      apiClient = result.apiClient;
      userInfo = result.userInfo;
      initialTokenInfo = result.tokenInfo;
      if (!userInfo || !initialTokenInfo) {
        logger.error(`Không thể lấy thông tin sau khi đăng nhập. Vui lòng kiểm tra lại tài khoản và proxy.`);
        process.exit(1);
      }
    }

    let tokenInfo = initialTokenInfo;

    if (!miniToken && userInfo) {
      logger.step('Đang lấy mini token...');
      const appId = APP_ID;
      miniToken = await getMiniToken(apiClient, userInfo.loginId, appId);
      if (miniToken) {
        await validateMiniToken(miniToken, appId);
      }
    }

    logger.success(`Đã kết nối với tài khoản: ${userInfo.username}`);
    logger.info(`Bắt đầu lúc: ${moment().format('YYYY-MM-DD HH:mm:ss')}`);

    displayUserInfo(userInfo, tokenInfo);

    async function attemptClaim() {
      let currentApiClient = apiClient;
      if (proxies.length > 0) {
        const randomProxy = getRandomProxy(proxies);
        currentApiClient = createApiClient(token, randomProxy, deviceId);
      }

      const claimCheck = await checkIsClaimable(currentApiClient);

      if (claimCheck.isClaimable) {
        logger.loading(`Đã đến thời điểm claim! Đang thực hiện claim...`);
        await claimAirdrop(currentApiClient);

        if (miniToken) {
          const miniProxy = getRandomProxy(proxies);
          const miniClient = createMiniApiClient(miniToken, miniProxy, deviceId, APP_ID);
          await doSpin(currentApiClient, miniClient);
        }

        logger.loading(`Đang cập nhật thông tin token...`);
        const newTokenInfo = await getTokenBalance(currentApiClient);
        if (newTokenInfo) {
          tokenInfo = newTokenInfo;
          displayUserInfo(userInfo, tokenInfo);
        }
      }

      return claimCheck.nextFrame;
    }

    logger.step(`Đang kiểm tra xem đã đến thời điểm claim chưa...`);
    let nextClaimTime = await attemptClaim();

    const updateCountdown = () => {
      const now = Date.now();
      const timeRemaining = Math.max(0, nextClaimTime - now);

      process.stdout.write(`\r${colors.white}Lần claim tiếp theo trong: ${colors.bold}${formatTimeRemaining(timeRemaining)}${colors.reset}     `);

      if (timeRemaining <= 0) {
        process.stdout.write('\n');
        logger.step(`Đã đến thời điểm claim!`);

        attemptClaim().then(newNextFrame => {
          nextClaimTime = newNextFrame;
        });
      }
    };

    setInterval(updateCountdown, 1000);

    const scheduleNextCheck = () => {
      const now = Date.now();
      const timeUntilNextCheck = Math.max(1000, nextClaimTime - now);

      setTimeout(async () => {
        logger.step(`Đến thời điểm claim theo lịch trình.`);
        nextClaimTime = await attemptClaim();
        scheduleNextCheck();
      }, timeUntilNextCheck);
    };

    scheduleNextCheck();

    logger.success(`Bot đang chạy! Airdrop sẽ được claim tự động.`);
    logger.info(`Nhấn Ctrl+C để thoát`);

  } catch (error) {
    logger.error(`Lỗi không mong muốn: ${error.message}`);
    process.exit(1);
  } finally {
    // Do not close rl here because interactive login may need it; caller will close on process exit.
  }
}

runBot().finally(() => {
  process.on('exit', () => rl.close());
});
