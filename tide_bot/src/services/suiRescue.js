import { Transaction } from '@mysten/sui/transactions';
import { createKeypair, getBalance, getClient, signAndExecute } from './wallet.js';
import { loadAccounts } from '../utils/fileLoader.js';
import { log, logSystem, shortWallet } from '../core/logger.js';
import config from '../core/config.js';

let _rescueCache = null;
let _rescueCacheTime = 0;
const CACHE_TTL = 60_000; 
export async function scanAllWallets(accounts) {
  const results = [];

  const BATCH = 10;
  for (let i = 0; i < accounts.length; i += BATCH) {
    const batch = accounts.slice(i, i + BATCH);
    const balances = await Promise.allSettled(
      batch.map(async (acc) => {
        const keypair = createKeypair(acc);
        const address = keypair.getPublicKey().toSuiAddress();
        const { balanceSUI, totalBalance } = await getBalance(address);
        return {
          index: acc.index,
          keypair,
          address,
          balanceSUI,
          totalBalance,
          wallet: shortWallet(address),
        };
      })
    );

    for (const result of balances) {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      }
    }
  }

  results.sort((a, b) => b.balanceSUI - a.balanceSUI);
  return results;
}

async function getWalletSnapshot(accounts) {
  const now = Date.now();
  if (_rescueCache && (now - _rescueCacheTime) < CACHE_TTL) {
    return _rescueCache;
  }
  _rescueCache = await scanAllWallets(accounts);
  _rescueCacheTime = now;
  return _rescueCache;
}

export function invalidateRescueCache() {
  _rescueCache = null;
  _rescueCacheTime = 0;
}

async function transferSUI(donorKeypair, recipientAddress, amountSUI) {
  try {
    const amountMIST = BigInt(Math.floor(amountSUI * 1e9));
    const tx = new Transaction();

    const [coin] = tx.splitCoins(tx.gas, [amountMIST]);
    tx.transferObjects([coin], recipientAddress);

    tx.setGasBudget(10_000_000); // 0.01 SUI gas budget

    const result = await signAndExecute(donorKeypair, tx);
    const status = result?.effects?.status?.status;

    if (status === 'success') {
      return { success: true, digest: result.digest };
    } else {
      const errMsg = result?.effects?.status?.error || 'Unknown error';
      return { success: false, error: errMsg };
    }
  } catch (err) {
    return { success: false, error: err.message };
  }
}

function findBestDonor(wallets, recipientAddress, neededSUI) {
  const rescueConfig = config.rescue || {};
  const reserveBalance = rescueConfig.reserveBalance || 1.0;

  for (const w of wallets) {
    if (w.address === recipientAddress) continue;

    const surplus = w.balanceSUI - reserveBalance - 0.02;
    if (surplus >= neededSUI) {
      return {
        donor: w,
        transferAmount: neededSUI,
      };
    }
  }


  return null;
}

export async function rescueSUI(recipientAddress, neededSUI, accIdx, total, wallet, proxy, accounts) {
  const rescueConfig = config.rescue || {};
  if (rescueConfig.enabled === false) {
    return { success: false, error: 'Rescue bị tắt' };
  }

  const { balanceSUI } = await getBalance(recipientAddress);
  if (balanceSUI >= neededSUI) {
    return { success: true, transferred: 0 };
  }

  const shortfall = neededSUI - balanceSUI + 0.05; // Thêm 0.05 SUI buffer cho gas
  log(accIdx, total, wallet, proxy, `🆘 Rescue: cần thêm ${shortfall.toFixed(4)} SUI (có ${balanceSUI.toFixed(4)}/${neededSUI} SUI)`, 'info');

  const wallets = await getWalletSnapshot(accounts);

  const donorThreshold = 0.1;
  const richWallets = wallets.filter(w => 
    w.address !== recipientAddress && 
    (w.balanceSUI - (rescueConfig.reserveBalance || 1.0) - 0.02) > donorThreshold
  );
  if (richWallets.length === 0) {
    log(accIdx, total, wallet, proxy, `❌ Rescue: không tìm thấy ví nào có SUI dư (reserve=${rescueConfig.reserveBalance || 1.0})`, 'warn');
    return { success: false, error: 'Không có ví donor' };
  }

  log(accIdx, total, wallet, proxy, `🔍 Rescue: tìm thấy ${richWallets.length} ví có surplus, top: ${richWallets[0].wallet}(${richWallets[0].balanceSUI.toFixed(2)} SUI)`, 'info');

  const match = findBestDonor(wallets, recipientAddress, shortfall);
  if (!match) {
    log(accIdx, total, wallet, proxy, `❌ Rescue: ${richWallets.length} ví có surplus nhưng không đủ cho ${shortfall.toFixed(4)} SUI`, 'warn');
    return { success: false, error: 'Không đủ surplus' };
  }

  const { donor, transferAmount } = match;
  log(accIdx, total, wallet, proxy,
    `🔄 Rescue: chuyển ${transferAmount.toFixed(4)} SUI từ ${donor.wallet} (${donor.balanceSUI.toFixed(4)} SUI)`,
    'info'
  );

  const result = await transferSUI(donor.keypair, recipientAddress, transferAmount);

  if (result.success) {
    log(accIdx, total, wallet, proxy,
      `✅ Rescue OK: +${transferAmount.toFixed(4)} SUI từ ${donor.wallet} | TX: ${result.digest}`,
      'success'
    );
    invalidateRescueCache();

    await new Promise(r => setTimeout(r, 3000));

    // Verify
    const { balanceSUI: afterBalance } = await getBalance(recipientAddress);
    log(accIdx, total, wallet, proxy, `💰 Balance sau rescue: ${afterBalance.toFixed(4)} SUI`, 'info');

    return { success: afterBalance >= neededSUI, transferred: transferAmount };
  } else {
    log(accIdx, total, wallet, proxy,
      `❌ Rescue thất bại: ${result.error}`,
      'error'
    );
    return { success: false, error: result.error };
  }
}

export async function rescueBulk(accounts) {
  const rescueConfig = config.rescue || {};
  if (rescueConfig.enabled === false) return;

  const minBalance = rescueConfig.minBalance || 1.0;
  const reserveBalance = rescueConfig.reserveBalance || 1.0;

  logSystem('🆘 Rescue: đang scan tất cả ví...', 'info');

  const wallets = await scanAllWallets(accounts);
  const total = wallets.length;

  const poorWallets = wallets.filter(w => w.balanceSUI < minBalance);
  const richWallets = wallets.filter(w => (w.balanceSUI - reserveBalance - 0.02) > 0.1);

  const totalSUI = wallets.reduce((s, w) => s + w.balanceSUI, 0);
  logSystem(
    `📊 Rescue scan: ${total} ví | 💰 Tổng: ${totalSUI.toFixed(2)} SUI | ` +
    `🟢 Giàu (>${reserveBalance} SUI): ${richWallets.length} | 🔴 Thiếu (<${minBalance} SUI): ${poorWallets.length}`,
    'info'
  );

  if (richWallets.length > 0) {
    const top5 = richWallets.slice(0, 5).map(w => `${w.wallet}(${w.balanceSUI.toFixed(2)})`).join(', ');
    logSystem(`💎 Top ví giàu: ${top5}`, 'info');
  }

  if (poorWallets.length === 0) {
    logSystem('✅ Rescue: tất cả ví đều có đủ SUI', 'success');
    return;
  }

  if (richWallets.length === 0) {
    logSystem('❌ Rescue: không có ví nào đủ giàu để cứu', 'error');
    return;
  }

  let rescueCount = 0;
  let totalTransferred = 0;

  const walletMap = new Map(wallets.map(w => [w.address, { ...w }]));

  for (const poor of poorWallets) {
    const needed = minBalance - poor.balanceSUI + 0.05; // +buffer cho gas

    const sortedDonors = [...walletMap.values()]
      .filter(w => w.address !== poor.address)
      .sort((a, b) => b.balanceSUI - a.balanceSUI);

    const match = findBestDonorFromList(sortedDonors, needed, reserveBalance, rescueConfig.maxTransfer || 5.0);
    if (!match) {
      log(poor.index, total, poor.wallet, null,
        `⏭️ Rescue: không tìm được donor cho ${needed.toFixed(4)} SUI`,
        'warn'
      );
      continue;
    }

    const { donor, transferAmount } = match;
    log(poor.index, total, poor.wallet, null,
      `🔄 Rescue: ${donor.wallet} (${donor.balanceSUI.toFixed(4)}) → ${poor.wallet} | ${transferAmount.toFixed(4)} SUI`,
      'info'
    );

    const result = await transferSUI(donor.keypair, poor.address, transferAmount);

    if (result.success) {
      rescueCount++;
      totalTransferred += transferAmount;

      const donorEntry = walletMap.get(donor.address);
      if (donorEntry) donorEntry.balanceSUI -= transferAmount + 0.01;      const poorEntry = walletMap.get(poor.address);
      if (poorEntry) poorEntry.balanceSUI += transferAmount;

      log(poor.index, total, poor.wallet, null,
        `✅ Rescue OK: +${transferAmount.toFixed(4)} SUI | TX: ${result.digest}`,
        'success'
      );

      await new Promise(r => setTimeout(r, 2000));
    } else {
      log(poor.index, total, poor.wallet, null,
        `❌ Rescue thất bại: ${result.error}`,
        'error'
      );
    }
  }

  invalidateRescueCache();

  if (rescueCount > 0) {
    logSystem(`✅ Rescue hoàn tất: ${rescueCount}/${poorWallets.length} ví | +${totalTransferred.toFixed(4)} SUI`, 'success');
  } else {
    logSystem(`⚠️ Rescue: không chuyển được cho ví nào`, 'warn');
  }
}

function findBestDonorFromList(sortedDonors, neededSUI, reserveBalance, maxTransfer) {
  const actualNeeded = Math.min(neededSUI, maxTransfer);

  for (const w of sortedDonors) {
    const surplus = w.balanceSUI - reserveBalance - 0.02;
    if (surplus >= actualNeeded) {
      return { donor: w, transferAmount: actualNeeded };
    }
  }

  const minUseful = 0.1;
  for (const w of sortedDonors) {
    const surplus = w.balanceSUI - reserveBalance - 0.02;
    if (surplus >= minUseful) {
      return { donor: w, transferAmount: Math.min(surplus, actualNeeded) };
    }
  }

  return null;
}


export async function consolidateSUI(accounts, options = {}) {
  const {
    targetIndex = 0,
    targetAddress: targetAddrOverride,
    minKeep = 0.01,
  } = options;

  logSystem('📦 Bắt đầu gom SUI về 1 ví...', 'info');

  const wallets = await scanAllWallets(accounts);
  const total = wallets.length;

  if (total === 0) {
    logSystem('⚠️ Gom SUI: không có ví nào để gom', 'warn');
    return { success: false, error: 'Không có ví' };
  }

  let targetWallet;
  if (targetAddrOverride) {
    targetWallet = wallets.find(w => w.address === targetAddrOverride);
    if (!targetWallet) {
      targetWallet = { address: targetAddrOverride, wallet: shortWallet(targetAddrOverride), balanceSUI: 0, index: '?' };
    }
  } else {
    const targetAcc = accounts[targetIndex];
    if (!targetAcc) {
      logSystem(`❌ Gom SUI: không tìm thấy ví đích index ${targetIndex}`, 'error');
      return { success: false, error: 'Target index invalid' };
    }
    const kp = createKeypair(targetAcc);
    const addr = kp.getPublicKey().toSuiAddress();
    targetWallet = wallets.find(w => w.address === addr) || { address: addr, wallet: shortWallet(addr), balanceSUI: 0, index: targetAcc.index };
  }

  const targetAddr = targetWallet.address;

  const totalSUI = wallets.reduce((s, w) => s + w.balanceSUI, 0);
  const sourceWallets = wallets.filter(w => w.address !== targetAddr && w.balanceSUI > minKeep + 0.02);

  logSystem(`🎯 Ví đích gom: ${targetWallet.wallet} (hiện có ${targetWallet.balanceSUI?.toFixed(4) || 0} SUI)`, 'info');
  logSystem(
    `📊 Gom scan: ${total} ví | 💰 Tổng: ${totalSUI.toFixed(4)} SUI | ` +
    `📤 Gom từ: ${sourceWallets.length} ví | 🎯 Đích: ${targetWallet.wallet}`,
    'info'
  );

  if (sourceWallets.length === 0) {
    logSystem('⚠️ Gom SUI: không có ví nào để gom (tất cả đã ở ví đích hoặc balance quá thấp)', 'warn');
    return { success: true, collected: 0, from: 0 };
  }

  let collectedCount = 0;
  let collectedSUI = 0;

  for (const src of sourceWallets) {
    const sendable = src.balanceSUI - minKeep - 0.01; // trừ gas (~0.01 SUI)
    if (sendable < 0.01) {
      log(src.index, total, src.wallet, null, `⏭️ Bỏ qua gom - balance quá thấp (${src.balanceSUI.toFixed(4)} SUI)`, 'warn');
      continue;
    }

    log(src.index, total, src.wallet, null,
      `💸 Chuyển ${sendable.toFixed(4)} SUI → ví chính ${targetWallet.wallet}`,
      'info'
    );

    try {
      const result = await transferSUI(src.keypair, targetAddr, sendable);

      if (result.success) {
        collectedCount++;
        collectedSUI += sendable;
        log(src.index, total, src.wallet, null,
          `✅ Gom OK: +${sendable.toFixed(4)} SUI → ${targetWallet.wallet} | TX: ${result.digest}`,
          'success'
        );
      } else {
        log(src.index, total, src.wallet, null,
          `❌ Gom thất bại: ${result.error}`,
          'error'
        );
      }
    } catch (err) {
      log(src.index, total, src.wallet, null,
        `❌ Gom thất bại: ${err.message}`,
        'error'
      );
    }

    await new Promise(r => setTimeout(r, 2000));
  }

  try {
    await new Promise(r => setTimeout(r, 3000));
    const { balanceSUI: finalBalance } = await getBalance(targetAddr);
    logSystem(
      `✅ Gom SUI hoàn tất: ${collectedCount}/${sourceWallets.length} ví | ` +
      `+${collectedSUI.toFixed(4)} SUI | 💰 Ví đích: ${finalBalance.toFixed(4)} SUI`,
      'success'
    );
  } catch {
    logSystem(
      `✅ Gom SUI hoàn tất: ${collectedCount}/${sourceWallets.length} ví | +${collectedSUI.toFixed(4)} SUI`,
      'success'
    );
  }

  return { success: collectedCount > 0, collected: collectedSUI, from: collectedCount };
}

export default { rescueSUI, rescueBulk, scanAllWallets, invalidateRescueCache, consolidateSUI };