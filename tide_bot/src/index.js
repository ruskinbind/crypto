import pLimit from 'p-limit';
import config from './core/config.js';
import { log, logSystem, printBanner, shortWallet, randomDelay, friendlyError } from './core/logger.js';
import { loadAccounts, loadProxies, assignProxy } from './utils/fileLoader.js';
import { createKeypair, getBalance, getOwnedObjects } from './services/wallet.js';
import { getFingerprint } from './services/deviceFingerprint.js';
import { claimFaucet, claimFaucetMulti, resetSuilearnState } from './services/faucet.js';
import { depositSUI, claimRewards, mintPass, borrowSUI, repayLoan, loanCycle, tradeCycle, tradePass, crossTrade, ensureSUI, setAllAccounts } from './services/tideOnchain.js';
import { getUserPoints, applyReferral, getActiveListing } from './services/tideApi.js';
import { CONTRACTS } from './core/config.js';
import { rescueBulk, rescueSUI as rescueSUIFn, consolidateSUI } from './services/suiRescue.js';
import { destroyPool } from './services/powPool.js';
import { getActiveApiKey } from './services/captcha.js';

let _allAccountsRef = null;

async function farmAccount(accountData, total, proxies) {
  const accIdx = accountData.index;
  let keypair, address, wallet, proxy, proxyObj;

  try {
    keypair = createKeypair(accountData);
    address = keypair.getPublicKey().toSuiAddress();
    wallet = shortWallet(address);

    proxyObj = assignProxy(accIdx, proxies);
    proxy = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;

    let { balanceSUI } = await getBalance(address);
    const userInfo = await getUserPoints(address).catch(() => null);
    const pts = userInfo?.data || userInfo;
    if (pts) {
      log(accIdx, total, wallet, proxy, `💰 ${balanceSUI.toFixed(4)} SUI | ⭐ ${pts.totalPoints ?? 0} điểm | 🏅 ${pts.tier || '?'} #${pts.rank || '?'}/${pts.totalUsers || '?'} | 📊 D:${pts.stats?.deposits ?? 0} C:${pts.stats?.claims ?? 0} T:${pts.stats?.trades ?? 0} L:${pts.stats?.loans ?? 0} | ⚡ ${pts.multipliers?.current ?? 1}x`, 'info');
    } else {
      log(accIdx, total, wallet, proxy, `💰 Số dư: ${balanceSUI.toFixed(4)} SUI`, 'info');
    }

    if (config.referral?.enabled && config.referral?.code) {
      try {
        const refRes = await applyReferral(address);
        if (refRes?.success && refRes?.data?.linked) {
          log(accIdx, total, wallet, proxy, `🔗 Referral OK: đã liên kết với ${config.referral.code}`, 'success');
        }
      } catch (e) {
        const msg = e.response?.data?.message || e.response?.data?.error || e.message || '';
        if (!msg.toLowerCase().includes('already')) {
          log(accIdx, total, wallet, proxy, `⚠️ Referral: ${msg}`, 'warn');
        }
      }
    }

    if (config.features.faucet && balanceSUI < 1) {
      await claimFaucetMulti(address, accIdx, total, wallet, proxyObj);
      await new Promise(r => setTimeout(r, 3000));
      await randomDelay(config.delay.min, config.delay.max);
    }

    const listing = (config.features.deposit || config.features.mintPass)
      ? await getActiveListing(address, proxyObj).catch(() => null)
      : null;
    const listingFinalized = listing && (listing.state === 'FINALIZED' || listing.state === 'RELEASED');

    if (config.features.deposit) {
      if (listingFinalized) {
        log(accIdx, total, wallet, proxy, `⏭️ Listing #${listing.listingNumber || 1} đã FINALIZED — bỏ qua deposit`, 'warn');
      } else {
        const hasSUI = await ensureSUI(keypair, config.deposit.amountSUI + 0.1, accIdx, total, wallet, proxy, proxyObj);
        if (hasSUI) {
          const depResult = await depositSUI(keypair, config.deposit.amountSUI, accIdx, total, proxy);
          if (depResult.success) await randomDelay(config.delay.min, config.delay.max);
        } else {
          log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua deposit - không đủ SUI sau faucet', 'warn');
        }
      }
    }

    if (config.features.mintPass) {
      if (listingFinalized) {
        log(accIdx, total, wallet, proxy, `⏭️ Listing #${listing.listingNumber || 1} đã FINALIZED — bỏ qua mint`, 'warn');
      } else {
        const hasSUI = await ensureSUI(keypair, 1.1, accIdx, total, wallet, proxy, proxyObj);
        if (hasSUI) {
          const mintResult = await mintPass(keypair, accIdx, total, proxy);
          if (mintResult.success) await randomDelay(config.delay.min, config.delay.max);
        } else {
          log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua mint - không đủ SUI sau faucet', 'warn');
        }
      }
    }

    if (config.features.tradePass) {
      await tradeCycle(keypair, accIdx, total, proxy, proxyObj);
      await randomDelay(config.delay.min, config.delay.max);
    }

    if (config.features.borrow) {
      await loanCycle(keypair, accIdx, total, proxy);
      await randomDelay(config.delay.min, config.delay.max);
    }

    if (config.features.claimRewards) {
      const passes = await getOwnedObjects(address, CONTRACTS.supporterPassType).catch(() => []);
      if (passes && passes.length > 0) {
        const claimResult = await claimRewards(keypair, accIdx, total, proxy, passes);
        if (claimResult.success) await randomDelay(config.delay.min, config.delay.max);
      } else {
        log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua claim - không có thẻ nào', 'warn');
      }
    }

    try {
      const { balanceSUI: finalBalance } = await getBalance(address);
      const points = await getUserPoints(address, proxyObj).catch(() => null);
      const pointsStr = points?.total_points != null ? ` | ⭐ Điểm: ${points.total_points}` : '';
      log(accIdx, total, wallet, proxy, `📊 Tổng kết: 💰 Số dư: ${finalBalance.toFixed(4)} SUI${pointsStr}`, 'success');
    } catch { }

    log(accIdx, total, wallet, proxy, '🎉 Hoàn tất chu kỳ farming', 'success');

  } catch (err) {
    const errMsg = friendlyError(err.message);
    log(accIdx, total, wallet || '-', proxy || null, `❌ Lỗi farming: ${errMsg}`, 'error');
  }
}

function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

async function runFarmingCycle(accounts, proxies, cycleNumber) {
  resetSuilearnState();
  const ordered = config.randomOrder ? shuffleArray(accounts) : accounts;
  const total = ordered.length;
  logSystem(`🔄 Bắt đầu chu kỳ farming #${cycleNumber} | ${total} tài khoản${config.randomOrder ? ' (ngẫu nhiên)' : ''}`, 'info');

  const limit = pLimit(config.threads || 5);

  const tasks = ordered.map(acc =>
    limit(() => farmAccount(acc, total, proxies))
  );

  await Promise.allSettled(tasks);

  logSystem(`✅ Hoàn tất chu kỳ #${cycleNumber}`, 'success');

  if (config.features.crossTrade !== false && config.features.tradePass && ordered.length >= 2) {
    const crossRepeat = config.marketplace?.crossRepeat || 3;
    logSystem(`🔄 Bắt đầu giao dịch chéo giữa ${ordered.length} tài khoản (${crossRepeat} lần)`, 'info');

    const keypairs = ordered.map(acc => ({
      keypair: createKeypair(acc),
      accIdx: acc.index,
      proxy: (() => {
        const p = assignProxy(acc.index, proxies);
        return p ? `${p.host}:${p.port}` : null;
      })()
    }));

    for (let round = 1; round <= crossRepeat; round++) {
      logSystem(`🔄 Giao dịch chéo lần ${round}/${crossRepeat}`, 'info');

      for (let i = 0; i < keypairs.length - 1; i++) {
        const a = keypairs[i];
        const b = keypairs[i + 1];
        await crossTrade(
          a.keypair, b.keypair,
          a.accIdx, b.accIdx,
          total,
          a.proxy, b.proxy
        );
        await new Promise(r => setTimeout(r, 3000));
      }

      if (round < crossRepeat) {
        await new Promise(r => setTimeout(r, 5000));
      }
    }

    logSystem(`✅ Giao dịch chéo hoàn tất`, 'success');
  }
}

async function faucetOnlyAccount(accountData, total, proxies) {
  const accIdx = accountData.index;
  let keypair, address, wallet, proxy;

  try {
    keypair = createKeypair(accountData);
    address = keypair.getPublicKey().toSuiAddress();
    wallet = shortWallet(address);

    const proxyObj = assignProxy(accIdx, proxies);
    proxy = proxyObj ? `${proxyObj.host}:${proxyObj.port}` : null;

    const { balanceSUI } = await getBalance(address);
    const userInfo = await getUserPoints(address, proxyObj).catch(() => null);
    const pts = userInfo?.data || userInfo;
    if (pts) {
      log(accIdx, total, wallet, proxy, `💰 ${balanceSUI.toFixed(4)} SUI | ⭐ ${pts.totalPoints ?? 0} điểm | 🏅 ${pts.tier || '?'} #${pts.rank || '?'}/${pts.totalUsers || '?'} | 📊 D:${pts.stats?.deposits ?? 0} C:${pts.stats?.claims ?? 0} T:${pts.stats?.trades ?? 0} L:${pts.stats?.loans ?? 0} | ⚡ ${pts.multipliers?.current ?? 1}x`, 'info');
    } else {
      log(accIdx, total, wallet, proxy, `💰 Số dư: ${balanceSUI.toFixed(4)} SUI`, 'info');
    }

    if (config.referral?.enabled && config.referral?.code) {
      try {
        const refRes = await applyReferral(address, proxyObj);
        if (refRes?.success && refRes?.data?.linked) {
          log(accIdx, total, wallet, proxy, `🔗 Referral OK: đã liên kết với ${config.referral.code}`, 'success');
        }
      } catch (e) {
        const msg = e.response?.data?.message || e.response?.data?.error || e.message || '';
        if (!msg.toLowerCase().includes('already')) {
          log(accIdx, total, wallet, proxy, `⚠️ Referral: ${msg}`, 'warn');
        }
      }
    }

    await claimFaucetMulti(address, accIdx, total, wallet, proxyObj);

    await new Promise(r => setTimeout(r, 3000));
    const { balanceSUI: after } = await getBalance(address);
    log(accIdx, total, wallet, proxy, `✅ Số dư sau faucet: ${after.toFixed(4)} SUI`, 'success');

  } catch (err) {
    const errMsg = friendlyError(err.message);
    log(accIdx, total, wallet || '-', proxy || null, `❌ Faucet lỗi: ${errMsg}`, 'error');
  }
}

async function runFaucetOnly(accounts, proxies) {
  const ordered = config.randomOrder ? shuffleArray(accounts) : accounts;
  const total = ordered.length;
  logSystem(`💧 Bắt đầu chế độ FAUCET | ${total} tài khoản${config.randomOrder ? ' (ngẫu nhiên)' : ''}`, 'info');

  const limit = pLimit(config.threads || 5);
  const tasks = ordered.map(acc =>
    limit(() => faucetOnlyAccount(acc, total, proxies))
  );
  await Promise.allSettled(tasks);

  logSystem('✅ Hoàn tất faucet tất cả tài khoản', 'success');
}

const isFaucetOnly = process.argv.includes('--faucet');
const isCollectMode = process.argv.includes('--collect');

async function main() {
  printBanner();

  logSystem('⚙️ Đã tải cấu hình', 'success');

  if (isFaucetOnly) {
    logSystem('💧 Chế độ: CHỈ FAUCET', 'info');
  } else if (isCollectMode) {
    logSystem('📦 Chế độ: GOM SUI về 1 ví', 'info');
  } else {
    const enabledFeatures = Object.entries(config.features)
      .filter(([, v]) => v)
      .map(([k]) => k)
      .join(', ');
    logSystem(`🔧 Tính năng: ${enabledFeatures}`, 'info');
  }

  if (config.referral?.enabled && config.referral?.code) {
    logSystem(`🔗 Referral: ${config.referral.code}`, 'success');
  }

  const accounts = loadAccounts();
  if (accounts.length === 0) {
    logSystem('❌ Không tìm thấy tài khoản trong accounts.txt. Vui lòng thêm private key hoặc seed phrase.', 'error');
    process.exit(1);
  }
  logSystem(`👥 Đã tải ${accounts.length} tài khoản`, 'success');

  setAllAccounts(accounts);
  _allAccountsRef = accounts;

  const proxies = loadProxies();
  if (proxies.length > 0) {
    logSystem(`🌐 Đã tải ${proxies.length} proxy`, 'success');
  } else if (config.proxy.enabled) {
    logSystem('⚠️ Proxy bật nhưng proxy.txt trống hoặc không tìm thấy', 'warn');
  }

  if (isFaucetOnly) {
    if (!getActiveApiKey()) {
      logSystem('❌ Cần captcha API key trong config.json để chạy faucet!', 'error');
      process.exit(1);
    }
    await runFaucetOnly(accounts, proxies);
    return;
  }

  if (isCollectMode) {
    const collectCfg = config.collect || {};
    const opts = {
      targetIndex: collectCfg.targetIndex || 0,
      targetAddress: collectCfg.targetAddress || undefined,
      minKeep: collectCfg.minKeep ?? 0.01,
    };
    const toArg = process.argv.find(a => a.startsWith('--to='));
    if (toArg) opts.targetAddress = toArg.split('=')[1];
    const keepArg = process.argv.find(a => a.startsWith('--keep='));
    if (keepArg) opts.minKeep = parseFloat(keepArg.split('=')[1]) || 0.01;

    await consolidateSUI(accounts, opts);
    return;
  }

  if (config.features.faucet && !getActiveApiKey()) {
    logSystem('⚠️ Tính năng faucet bật nhưng chưa có captcha API key. Faucet sẽ bị bỏ qua.', 'warn');
  }

  let cycle = 1;

  while (true) {
    await runFarmingCycle(accounts, proxies, cycle);
    cycle++;

    if (!config.features.dailyLoop) {
      logSystem('📊 Tổng kết: Hoàn tất. dailyLoop = false → dừng bot.', 'info');
      break;
    }

    const hours = config.schedule.intervalHours || 24;
    logSystem(`⏳ Nghỉ ${hours} giờ trước chu kỳ tiếp...`, 'info');
    await new Promise(r => setTimeout(r, hours * 60 * 60 * 1000));
  }
}

process.on('uncaughtException', (err) => {
  logSystem(`❌ Lỗi không xử lý: ${err.message}`, 'error');
});

process.on('unhandledRejection', (reason) => {
  logSystem(`❌ Promise rejection: ${reason}`, 'error');
});

process.on('exit', () => { try { destroyPool(); } catch {} });
process.on('SIGINT', () => { destroyPool(); process.exit(0); });
process.on('SIGTERM', () => { destroyPool(); process.exit(0); });

main().catch(err => {
  logSystem(`❌ Lỗi khởi chạy: ${err.message}`, 'error');
  destroyPool();
  process.exit(1);
});
