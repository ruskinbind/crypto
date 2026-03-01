import axios from 'axios';
import config from '../core/config.js';
import { FAUCET_CONFIG } from '../core/config.js';


const SERVICES = {
  '2captcha': {
    createUrl: 'https://api.2captcha.com/createTask',
    resultUrl: 'https://api.2captcha.com/getTaskResult',
    turnstileType: 'TurnstileTaskProxyless',
    hcaptchaType: 'HCaptchaTaskProxyless'
  },
  'capmonster': {
    createUrl: 'https://api.capmonster.cloud/createTask',
    resultUrl: 'https://api.capmonster.cloud/getTaskResult',
    turnstileType: 'TurnstileTaskProxyless',
    hcaptchaType: 'HCaptchaTaskProxyless'
  },
  'capsolver': {
    createUrl: 'https://api.capsolver.com/createTask',
    resultUrl: 'https://api.capsolver.com/getTaskResult',
    turnstileType: 'AntiTurnstileTaskProxyLess',
    hcaptchaType: 'HCaptchaEnterpriseTaskProxyLess'
  }
};

async function createTask(apiKey, service, taskType, websiteURL, websiteKey) {
  const svc = SERVICES[service];
  if (!svc) throw new Error(`Service captcha không hỗ trợ: ${service}`);

  const payload = {
    clientKey: apiKey,
    task: {
      type: taskType,
      websiteURL,
      websiteKey
    }
  };

  let res;
  try {
    res = await axios.post(svc.createUrl, payload, { timeout: 30000 });
  } catch (e) {
    const detail = e.response?.data ? JSON.stringify(e.response.data).slice(0, 300) : e.message;
    throw new Error(`Captcha create lỗi (${e.response?.status || 'network'}): ${detail}`);
  }

  if (res.data.errorId && res.data.errorId !== 0) {
    throw new Error(`Captcha create lỗi: ${res.data.errorDescription || res.data.errorCode}`);
  }

  return res.data.taskId;
}

async function getTaskResult(apiKey, taskId, service, maxWait = 120000) {
  const svc = SERVICES[service];
  const startTime = Date.now();

  while (Date.now() - startTime < maxWait) {
    await new Promise(r => setTimeout(r, 5000));

    const res = await axios.post(svc.resultUrl, {
      clientKey: apiKey,
      taskId: taskId
    }, { timeout: 15000 });

    if (res.data.errorId && res.data.errorId !== 0) {
      throw new Error(`Captcha result lỗi: ${res.data.errorDescription || res.data.errorCode}`);
    }

    if (res.data.status === 'processing') continue;

    if (res.data.status === 'ready') {
      return res.data.solution.token || res.data.solution.gRecaptchaResponse;
    }
  }

  throw new Error('Captcha timeout - không nhận được kết quả sau ' + (maxWait / 1000) + 's');
}

function getActiveApiKey() {
  const { service } = config.captcha;
  const keyMap = {
    '2captcha': config.captcha.apiKey2Captcha,
    'capmonster': config.captcha.apiKeyCapmonster,
    'capsolver': config.captcha.apiKeyCapslover
  };
  return keyMap[service] || config.captcha.apiKey || '';
}

export async function solveTurnstile() {
  const { service } = config.captcha;
  const apiKey = getActiveApiKey();
  if (!apiKey) throw new Error(`Chưa cấu hình API key cho "${service}" trong config.json`);

  const svc = SERVICES[service];
  if (!svc) throw new Error(`Service "${service}" không hỗ trợ. Chọn: 2captcha, capmonster, capsolver`);

  const taskId = await createTask(apiKey, service, svc.turnstileType, 'https://faucet.sui.io/', FAUCET_CONFIG.turnsiteSiteKey);
  return await getTaskResult(apiKey, taskId, service);
}

export { getActiveApiKey };

export default { solveTurnstile };
