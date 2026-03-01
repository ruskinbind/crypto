import axios from 'axios';
import { HttpsProxyAgent } from 'https-proxy-agent';
import { SocksProxyAgent } from 'socks-proxy-agent';
import pLimit from 'p-limit';
import os from 'os';
import config from '../core/config.js';
import { FAUCET_CONFIG } from '../core/config.js';
import { solveTurnstile } from './captcha.js';
import { getFingerprintHeaders } from './deviceFingerprint.js';
import { log, logSystem, friendlyError } from '../core/logger.js';
import { getBalance } from './wallet.js';
import { solvePoWParallel, getPoolSize } from './powPool.js';

const _poolSize = getPoolSize();
const _faucetLimit = pLimit(_poolSize);
logSystem(`⛏️ PoW Pool: ${_poolSize} workers (${os.cpus().length} CPU cores) — faucet đa luồng ON`, 'success');

// ===== SUILEARN STATE =====
const _suilearnExhaustedIPs = new Set();

export function resetSuilearnState() {
  _suilearnExhaustedIPs.clear();
}

// ===== PROXY =====
function createProxyAgent(proxyObj) {
  if (!proxyObj || !proxyObj.url) return null;
  const proto = proxyObj.protocol || 'http';
  if (proto.startsWith('socks')) return new SocksProxyAgent(proxyObj.url);
  return new HttpsProxyAgent(proxyObj.url);
}

function getIPKey(proxyObj) {
  return proxyObj ? proxyObj.url : '__direct__';
}


// ===== SUILEARN FAUCET (no captcha, no PoW) =====
async function claimSuiLearn(address, accIdx, total, walletShort, proxyObj) {
  const ipKey = getIPKey(proxyObj);
  if (_suilearnExhaustedIPs.has(ipKey)) {
    return { success: false, skip: true, error: 'SuiLearn exhausted for this IP' };
  }

  const proxyDisplay = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;
  const agent = createProxyAgent(proxyObj);
  const axiosOpts = agent ? { httpAgent: agent, httpsAgent: agent } : {};

  let balBefore = 0;
  try { balBefore = (await getBalance(address)).balanceSUI; } catch (_) {}

  const t0 = Date.now();
  log(accIdx, total, walletShort, proxyDisplay, `🚰 [SuiLearn] Claiming faucet...`, 'info');

  const headers = {
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
    'next-action': '60e6c10ffef14e992a7908d7fcdba0acee13af4e16',
    'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
    'Origin': 'https://faucet.suilearn.io',
    'Referer': 'https://faucet.suilearn.io/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  };

  const body = JSON.stringify([address, 'sui']);

  let res;
  try {
    res = await axios.post('https://faucet.suilearn.io/', body, {
      headers,
      timeout: 30000,
      ...axiosOpts,
      transformResponse: [(data) => data],
    });
  } catch (e) {
    const status = e.response?.status;
    if (status === 429) {
      _suilearnExhaustedIPs.add(ipKey);
      return { success: false, error: '[SuiLearn] HTTP 429 Rate limited', rateLimited: true, errorType: 'ratelimit' };
    }
    log(accIdx, total, walletShort, proxyDisplay, `⚠️ [SuiLearn] ${e.message}`, 'warn');
    return { success: false, error: `[SuiLearn] ${e.message}`, errorType: 'network' };
  }

  const t1 = Date.now();
  const elapsed = ((t1 - t0) / 1000).toFixed(1);
  const text = (res.data || '').toString();

  let parsed = null;
  try {
    const match = text.match(/^1:(.*)/m);
    if (match) parsed = JSON.parse(match[1]);
  } catch (_) {}

  if (parsed) {
    if (parsed.success === false) {
      const remaining = parsed.remaining ?? 0;
      const msg = parsed.message || 'Unknown error';
      if (remaining <= 0 || msg.toLowerCase().includes('rate limit') || msg.toLowerCase().includes('limit')) {
        _suilearnExhaustedIPs.add(ipKey);
        log(accIdx, total, walletShort, proxyDisplay, `⚠️ [SuiLearn] ${msg}`, 'warn');
        return { success: false, error: `[SuiLearn] ${msg}`, rateLimited: true, errorType: 'ratelimit' };
      }
      log(accIdx, total, walletShort, proxyDisplay, `❌ [SuiLearn] ${msg}`, 'error');
      return { success: false, error: `[SuiLearn] ${msg}`, errorType: 'unknown' };
    }

    if (parsed.success === true) {
      const remaining = parsed.remaining ?? '?';
      const digest = parsed.digest || '';
      const txLink = digest ? ` | TX: ${digest}` : '';

      let amountSUI = 0;
      try {
        await new Promise(r => setTimeout(r, 3000));
        const balAfter = (await getBalance(address)).balanceSUI;
        amountSUI = Math.max(0, balAfter - balBefore);
      } catch (_) {}

      const amountStr = amountSUI > 0 ? ` | +${amountSUI.toFixed(4)} SUI` : '';
      log(accIdx, total, walletShort, proxyDisplay, `✅ [SuiLearn] Claim OK (${elapsed}s)${amountStr} | Còn lại: ${remaining}/5${txLink}`, 'success');
      return { success: true, amount: amountSUI, source: 'SuiLearn', digest };
    }
  }

  if (res.status === 200 && text.length > 0) {
    log(accIdx, total, walletShort, proxyDisplay, `✅ [SuiLearn] Claim OK (${elapsed}s)`, 'success');
    return { success: true, amount: 0, source: 'SuiLearn' };
  }

  log(accIdx, total, walletShort, proxyDisplay, `❌ [SuiLearn] Response không xác định: ${text.substring(0, 200)}`, 'error');
  return { success: false, error: `[SuiLearn] Unexpected response`, errorType: 'unknown' };
}


async function claimSuiOfficial(address, accIdx, total, walletShort, proxyObj) {
  const proxyDisplay = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;
  const agent = createProxyAgent(proxyObj);
  const axiosOpts = agent ? { httpAgent: agent, httpsAgent: agent } : {};
  const t0 = Date.now();

  log(accIdx, total, walletShort, proxyDisplay, `🔑 Đang giải Turnstile... [${config.captcha?.service || 'capsolver'}]`, 'info');
  let turnstileToken;
  try {
    turnstileToken = await solveTurnstile();
  } catch (e) {
    throw new Error(`[CAPTCHA] ${e.message}`);
  }
  const t1 = Date.now();
  log(accIdx, total, walletShort, proxyDisplay, `✅ Turnstile OK (${((t1 - t0) / 1000).toFixed(1)}s)`, 'success');

  const fpHeaders = getFingerprintHeaders(address);
  const headers = {
    ...fpHeaders,
    'Content-Type': 'application/json',
    'Origin': 'https://faucet.sui.io',
    'Referer': 'https://faucet.sui.io/',
    'X-Turnstile-Token': turnstileToken
  };

  const maxPowRetries = 2;
  for (let powTry = 0; powTry <= maxPowRetries; powTry++) {
    let challengeRes;
    try {
      challengeRes = await axios.post(FAUCET_CONFIG.challengeUrl, null, {
        headers: { ...headers, 'Content-Length': '0' },
        timeout: 60000,
        ...axiosOpts
      });
    } catch (e) {
      throw new Error(`[CHALLENGE] ${e.message}`);
    }
    const t2 = Date.now();

    const { challenge: challengeObj, signature } = challengeRes.data;
    const challengeStr = challengeObj?.challenge;
    const difficulty = challengeObj?.difficulty || 6;

    if (!challengeStr || !signature) {
      throw new Error(`Challenge thiếu dữ liệu: challenge=${!!challengeStr}, signature=${!!signature}`);
    }

    log(accIdx, total, walletShort, proxyDisplay, `⛏️ Đang giải PoW (difficulty: ${difficulty})...`, 'info');
    
    let powResult;
    try {
      powResult = await solvePoWParallel(challengeObj.ts, difficulty, challengeStr);
    } catch (e) {
      if (e.message.includes('PoW timeout') && powTry < maxPowRetries) {
        log(accIdx, total, walletShort, proxyDisplay, `⏳ PoW timeout (${powTry + 1}/${maxPowRetries}) → lấy challenge mới...`, 'warn');
        continue;
      }
      throw new Error(`[POW] ${e.message}`);
    }

    const t3 = Date.now();
    const powTime = (t3 - t2) / 1000;
    log(accIdx, total, walletShort, proxyDisplay, `✅ PoW OK (${powTime.toFixed(1)}s, nonce: ${powResult.nonce})`, 'success');

    const totalElapsed = (t3 - t0) / 1000;
    if (totalElapsed > 55) {
      throw new Error(`[CLAIM] ChallengeExpired — tổng thời gian ${totalElapsed.toFixed(0)}s > 55s, bỏ qua để tránh lãng phí request`);
    }

    const claimBody = {
      FixedAmountRequest: {
        recipient: address,
        solution: {
          hash: powResult.hash,
          nonce: powResult.nonce,
          challenge: challengeObj,
          signature
        }
      }
    };

    let faucetRes;
    try {
      faucetRes = await axios.post(FAUCET_CONFIG.gasUrl, claimBody, {
        headers,
        timeout: 60000,
        ...axiosOpts
      });
    } catch (e) {
      throw new Error(`[CLAIM] ${e.response?.status || ''} ${e.response?.data ? JSON.stringify(e.response.data).slice(0, 300) : e.message}`);
    }
    const t4 = Date.now();

    return parseClaimResponse(faucetRes, t0, t4, accIdx, total, walletShort, proxyDisplay, 'SUI Official');
  }

  throw new Error('[POW] Hết số lần thử PoW — challenge liên tục timeout');
}

function parseClaimResponse(faucetRes, t0, t4, accIdx, total, walletShort, proxyDisplay, source) {
  const fData = faucetRes.data;

  if (fData?.status?.Failure) {
    const failMsg = typeof fData.status.Failure === 'object'
      ? Object.values(fData.status.Failure)[0]
      : fData.status.Failure;
    throw new Error(failMsg);
  }

  if (fData?.transferredGasObjects || fData?.coins_sent || fData?.ok) {
    const amount = fData.transferredGasObjects
      ? fData.transferredGasObjects.reduce((sum, o) => sum + (o.amount || 0), 0)
      : fData.coins_sent
        ? fData.coins_sent.reduce((sum, o) => sum + (o.amount || 0), 0)
        : 0;
    const amountSUI = amount / 1e9;
    const txDigest = fData.transferredGasObjects?.[0]?.transferTxDigest
      || fData.coins_sent?.[0]?.transferTxDigest
      || '';
    const txLink = txDigest ? ` | TX: ${txDigest}` : '';
    log(accIdx, total, walletShort, proxyDisplay, `✅ [${source}] +${amountSUI} SUI (${((t4 - t0) / 1000).toFixed(1)}s)${txLink}`, 'success');
    return { success: true, amount: amountSUI, source };
  }

  if (faucetRes.status === 200 || faucetRes.status === 202) {
    log(accIdx, total, walletShort, proxyDisplay, `✅ [${source}] Claim thành công (${((t4 - t0) / 1000).toFixed(1)}s)`, 'success');
    return { success: true, amount: 0, source };
  }

  throw new Error(`${source} trả về status: ${faucetRes.status}`);
}

function classifyFaucetError(errMsg) {
  const s = (errMsg || '').toLowerCase();
  
  if (s.includes('challengeexpired') || s.includes('challenge expired'))
    return 'expired';
  if (s.includes('429') || s.includes('too many') || s.includes('rate'))
    return 'ratelimit';
  if (s.includes('timeout') || s.includes('etimedout') || s.includes('econnreset') 
      || s.includes('econnrefused') || s.includes('socket hang up') || s.includes('fetch failed'))
    return 'network';
  if (s.includes('proxy') || s.includes('connect'))
    return 'proxy';
  if (s.includes('captcha') || s.includes('turnstile'))
    return 'captcha';
  
  return 'unknown';
}

export async function claimFaucet(address, accIdx, total, walletShort, proxyObj) {
  const proxyDisplay = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;

  const slResult = await claimSuiLearn(address, accIdx, total, walletShort, proxyObj);

  const officialResult = await _faucetLimit(async () => {
    try {
      return await claimSuiOfficial(address, accIdx, total, walletShort, proxyObj);
    } catch (err) {
      const errMsg = friendlyError(err.message);
      const errorType = classifyFaucetError(err.message);
      const isWarn = errorType === 'ratelimit' || errorType === 'expired';
      log(accIdx, total, walletShort, proxyDisplay, `❌ Faucet Official thất bại: ${errMsg}`, isWarn ? 'warn' : 'error');
      return { 
        success: false, 
        error: errMsg, 
        rateLimited: errorType === 'ratelimit',
        errorType 
      };
    }
  });

  const slOK = slResult.success;
  const ofOK = officialResult.success;

  if (slOK && ofOK) {
    const totalAmount = (slResult.amount || 0) + (officialResult.amount || 0);
    log(accIdx, total, walletShort, proxyDisplay, `🎉 Cả 2 faucet OK → +${totalAmount.toFixed(4)} SUI (SuiLearn + Official)`, 'success');
    return { success: true, amount: totalAmount, source: 'SuiLearn + Official' };
  }
  if (slOK) return slResult;
  if (ofOK) return officialResult;

  return officialResult;
}

export async function claimFaucetMulti(address, accIdx, total, walletShort, proxyObj) {
  const proxyDisplay = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;
  const maxClaims = config.faucet?.maxClaims || 5;
  const delayBetween = config.faucet?.delayBetween || 5000;
  let totalClaimed = 0;
  let successCount = 0;
  let consecutiveErrors = 0;
  let expiredCount = 0;

  log(accIdx, total, walletShort, proxyDisplay, `🚰 Bắt đầu nhận faucet (tối đa ${maxClaims} lần)`, 'info');

  for (let i = 1; i <= maxClaims; i++) {
    log(accIdx, total, walletShort, proxyDisplay, `🔄 Faucet lần ${i}/${maxClaims}`, 'info');

    const result = await claimFaucet(address, accIdx, total, walletShort, proxyObj);

    if (result.success) {
      successCount++;
      consecutiveErrors = 0;
      expiredCount = 0; 
      totalClaimed += result.amount || 0;
      const src = result.source ? ` (${result.source})` : '';
      let balStr = '';

      await new Promise(r => setTimeout(r, 5000));
      try {
        let bal = await getBalance(address);
        if (bal.balanceSUI < 0.001 && result.amount > 0) {
          await new Promise(r => setTimeout(r, 5000));
          bal = await getBalance(address);
        }
        balStr = ` | 💰 Số dư: ${bal.balanceSUI.toFixed(4)} SUI`;
      } catch (_) {}
      log(accIdx, total, walletShort, proxyDisplay, `✅ Faucet ${i}/${maxClaims} OK${src}${balStr}`, 'success');
    } else {
      consecutiveErrors++;
      const errorType = result.errorType || 'unknown';

      if (result.rateLimited || errorType === 'ratelimit') {
        log(accIdx, total, walletShort, proxyDisplay, `⏹️ Bị giới hạn tần suất → dừng faucet`, 'warn');
        break;
      }

      if (errorType === 'expired') {
        expiredCount++;
        if (expiredCount >= 3) {
          log(accIdx, total, walletShort, proxyDisplay, `⏹️ Challenge hết hạn ${expiredCount} lần liên tục → faucet đang quá tải, dừng`, 'warn');
          break;
        }
        log(accIdx, total, walletShort, proxyDisplay, `⚠️ Challenge hết hạn (${expiredCount}/3) → đợi thêm rồi thử lại...`, 'warn');
        i--;
        await new Promise(r => setTimeout(r, delayBetween * 2));
        continue;
      }

      if (errorType === 'captcha') {
        log(accIdx, total, walletShort, proxyDisplay, `⏹️ Lỗi captcha → dừng faucet`, 'error');
        break;
      }

      if ((errorType === 'network' || errorType === 'proxy') && consecutiveErrors >= 2) {
        log(accIdx, total, walletShort, proxyDisplay, `⏹️ ${consecutiveErrors} lỗi mạng/proxy liên tiếp → dừng faucet`, 'warn');
        break;
      }

      if (consecutiveErrors >= 3) {
        log(accIdx, total, walletShort, proxyDisplay, `⏹️ ${consecutiveErrors} lỗi liên tiếp → dừng faucet`, 'warn');
        break;
      }

      log(accIdx, total, walletShort, proxyDisplay, `❌ Faucet ${i}/${maxClaims} lỗi (${errorType}) | ${result.error}`, 'error');
    }

    if (i < maxClaims) {
      await new Promise(r => setTimeout(r, delayBetween));
    }
  }

  log(accIdx, total, walletShort, proxyDisplay, `📊 Kết quả faucet: ${successCount}/${maxClaims} thành công | +${totalClaimed.toFixed(4)} SUI`, successCount > 0 ? 'success' : 'warn');
  return { success: successCount > 0, totalClaimed, successCount };
}

export default { claimFaucet, claimFaucetMulti, resetSuilearnState };
