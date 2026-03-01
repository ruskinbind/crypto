import { Transaction } from '@mysten/sui/transactions';
import { CONTRACTS } from '../core/config.js';
import config from '../core/config.js';
import { getClient, signAndExecute, getOwnedObjects, getSuiCoins, getBalance } from './wallet.js';
import { log, friendlyError, shortWallet } from '../core/logger.js';
import { randomDelay } from '../core/logger.js';
import { claimFaucetMulti } from './faucet.js';
import { getCheapestListings, getMarketplace } from './tideApi.js';
import { rescueSUI } from './suiRescue.js';

import { getActiveApiKey } from './captcha.js';

let _allAccounts = null;
export function setAllAccounts(accounts) {
  _allAccounts = accounts;
}

const _buyingListings = new Set();
const _deadListings = new Set();
 
setInterval(() => { _deadListings.clear(); }, 5 * 60 * 1000);

export async function ensureSUI(keypair, neededSUI, accIdx, total, wallet, proxy, proxyObj) {
  const address = keypair.getPublicKey().toSuiAddress();
  const { balanceSUI } = await getBalance(address);

  if (balanceSUI >= neededSUI) return true;

  let faucetWorked = false;

  if (getActiveApiKey()) {
    log(accIdx, total, wallet, proxy, `🚰 Thiếu SUI (${balanceSUI.toFixed(4)}/${neededSUI} SUI) → tự động faucet`, 'info');
    const faucetResult = await claimFaucetMulti(address, accIdx, total, wallet, proxyObj);
    await new Promise(r => setTimeout(r, 3000));

    const { balanceSUI: afterFaucet } = await getBalance(address);
    if (afterFaucet >= neededSUI) {
      log(accIdx, total, wallet, proxy, `✅ Đã faucet đủ: ${afterFaucet.toFixed(4)} SUI`, 'success');
      return true;
    }

    faucetWorked = faucetResult.successCount > 0;
    if (faucetWorked) {
      log(accIdx, total, wallet, proxy, `⚠️ Faucet xong nhưng vẫn thiếu: ${afterFaucet.toFixed(4)}/${neededSUI} SUI`, 'warn');
    } else {
      log(accIdx, total, wallet, proxy, `⚠️ Faucet hoàn toàn thất bại → chuyển sang rescue`, 'warn');
    }
  } else {
    log(accIdx, total, wallet, proxy, `⏭️ Thiếu SUI (${balanceSUI.toFixed(4)}/${neededSUI} SUI) → thử rescue (không có captcha key)`, 'warn');
  }
  if (config.rescue?.enabled !== false && _allAccounts && _allAccounts.length > 1) {
    log(accIdx, total, wallet, proxy, `🆘 Thử rescue từ ví khác (cần ${neededSUI.toFixed(2)} SUI)...`, 'info');
    const rescueResult = await rescueSUI(address, neededSUI, accIdx, total, wallet, proxy, _allAccounts);
    if (rescueResult.success) {
      const { balanceSUI: afterRescue } = await getBalance(address);
      if (afterRescue >= neededSUI) {
        return true;
      }
      log(accIdx, total, wallet, proxy, `⚠️ Rescue xong nhưng vẫn thiếu: ${afterRescue.toFixed(4)}/${neededSUI.toFixed(2)} SUI`, 'warn');
    }
  }

  const { balanceSUI: finalBalance } = await getBalance(address);
  return finalBalance >= neededSUI;
}

export async function buyPassFromMarketplace(keypair, accIdx, total, wallet, proxy, proxyObj) {
  const address = keypair.getPublicKey().toSuiAddress();
  const maxBuyPrice = config.marketplace?.maxBuyPrice || 5_000_000_000;

  try {
    log(accIdx, total, wallet, proxy, '🛒 Tìm pass rẻ nhất trên sàn để mua...', 'info');

    const allListings = await getCheapestListings(address, Number.MAX_SAFE_INTEGER, 500, proxyObj);
    if (!allListings || allListings.length === 0) {
      log(accIdx, total, wallet, proxy, `⏭️ Không tìm thấy pass nào trên sàn`, 'warn');
      return { success: false, error: 'Không có listing' };
    }

    const candidates = allListings.filter(l => {
      const id = l.id || l.objectId;
      return !_deadListings.has(id) && !_buyingListings.has(id);
    });

    if (candidates.length === 0) {
      log(accIdx, total, wallet, proxy, `⏭️ Tất cả listing đều đã dead hoặc đang mua`, 'warn');
      return { success: false, error: 'Không có listing khả dụng' };
    }

    const client = getClient();
    let validListings = [];
    let deletedCount = 0;
    const BATCH_SIZE = 50;

    for (let i = 0; i < candidates.length; i += BATCH_SIZE) {
      const batch = candidates.slice(i, i + BATCH_SIZE);
      const ids = batch.map(l => l.id || l.objectId);

      try {
        const objects = await client.multiGetObjects({ ids, options: { showType: true } });
        for (let j = 0; j < objects.length; j++) {
          const id = batch[j].id || batch[j].objectId;
          if (objects[j].data && !objects[j].error) {
            validListings.push(batch[j]);
          } else {
            _deadListings.add(id);
            deletedCount++;
          }
        }
      } catch {
        for (const listing of batch) {
          const id = listing.id || listing.objectId;
          try {
            const obj = await client.getObject({ id, options: { showType: true } });
            if (obj.data && !obj.error) {
              validListings.push(listing);
            } else {
              _deadListings.add(id);
              deletedCount++;
            }
          } catch {
            _deadListings.add(id);
            deletedCount++;
          }
        }
      }
      if (validListings.length >= 20) break;
    }

    log(accIdx, total, wallet, proxy,
      `📊 On-chain: ${validListings.length} valid, ${deletedCount} deleted/${candidates.length}`,
      'info'
    );

    if (validListings.length === 0) {
      log(accIdx, total, wallet, proxy, `❌ Tất cả listing đều đã bị xóa/mua on-chain`, 'error');
      return { success: false, error: 'Tất cả listing đã xóa on-chain' };
    }

    validListings.sort((a, b) => Number(a.price || a.priceMist || 0) - Number(b.price || b.priceMist || 0));
    const affordable = validListings.filter(l => Number(l.price || l.priceMist || 0) <= maxBuyPrice);
    const cheapestValid = Number(validListings[0].price || validListings[0].priceMist) / 1e9;

    if (affordable.length === 0) {
      log(accIdx, total, wallet, proxy,
        `⏭️ Listing rẻ nhất valid: ${cheapestValid.toFixed(2)} SUI > maxBuyPrice (${maxBuyPrice / 1e9} SUI). Hãy tăng maxBuyPrice`,
        'warn'
      );
      return { success: false, error: `Giá thấp nhất ${cheapestValid.toFixed(2)} SUI > max ${maxBuyPrice / 1e9}` };
    }

    log(accIdx, total, wallet, proxy,
      `📋 ${affordable.length} listing valid ≤ ${maxBuyPrice / 1e9} SUI, rẻ nhất: ${(Number(affordable[0].price || affordable[0].priceMist) / 1e9).toFixed(4)} SUI`,
      'info'
    );

    let buyAttempts = 0;
    const MAX_ATTEMPTS = 10;

    for (const listing of affordable) {
      if (buyAttempts >= MAX_ATTEMPTS) {
        log(accIdx, total, wallet, proxy, `⏭️ Đã thử ${MAX_ATTEMPTS} listing, dừng`, 'warn');
        break;
      }
      const listingId = listing.id || listing.objectId;

      if (_buyingListings.has(listingId) || _deadListings.has(listingId)) continue;
      _buyingListings.add(listingId);

      const price = Number(listing.price || listing.priceMist);
      const priceSUI = price / 1e9;

      try {
        const neededSUI = priceSUI + 0.05;
        const hasSUI = await ensureSUI(keypair, neededSUI, accIdx, total, wallet, proxy, proxyObj);
        if (!hasSUI) {
          _buyingListings.delete(listingId);
          log(accIdx, total, wallet, proxy, `⏭️ Không đủ SUI để mua pass (cần ${neededSUI.toFixed(2)} SUI)`, 'warn');
          return { success: false, error: 'Thiếu SUI' };
        }

        log(accIdx, total, wallet, proxy, `🛍️ Mua listing ${listingId.slice(0, 10)}... | giá: ${priceSUI} SUI`, 'info');
        const buyResult = await buyAndTake(keypair, listingId, price, accIdx, total, proxy);
        if (buyResult.success) {
          _deadListings.add(listingId);
          return { success: true, digest: buyResult.digest, price: priceSUI };
        }
        _buyingListings.delete(listingId);
        _deadListings.add(listingId);
        buyAttempts++;
        await randomDelay(500, 1000);
      } catch {
        _buyingListings.delete(listingId);
        _deadListings.add(listingId);
        buyAttempts++;
        continue;
      }
    }

    log(accIdx, total, wallet, proxy, '❌ Không mua được pass nào sau nhiều lần thử', 'error');
    return { success: false, error: 'Tất cả listing lỗi' };
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Mua pass từ sàn lỗi | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function depositSUI(keypair, amountSUI, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);
  const amountMist = BigInt(Math.floor(amountSUI * 1e9));

  try {
    log(accIdx, total, wallet, proxy, `📥 Deposit ${amountSUI} SUI`, 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000); // 0.01 SUI gas budget

    const [depositCoin] = tx.splitCoins(tx.gas, [tx.pure.u64(amountMist)]);

    const [resultObj] = tx.moveCall({
      target: `${CONTRACTS.corePackage}::listing::deposit`,
      arguments: [
        tx.object(CONTRACTS.listing),
        tx.object(CONTRACTS.registry),
        tx.object(CONTRACTS.depositPool),
        tx.object(CONTRACTS.tideConfig),
        depositCoin,
        tx.object(CONTRACTS.clock)
      ]
    });

    tx.transferObjects([resultObj], address);

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Deposit thành công | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      const errMsg = result.effects?.status?.error || 'Không rõ lỗi';
      throw new Error(errMsg);
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Deposit thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function claimRewards(keypair, accIdx, total, proxy, prefetchedPasses) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    const passes = prefetchedPasses || await getOwnedObjects(address, CONTRACTS.supporterPassType);

    if (!passes || passes.length === 0) {
      log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua claim - không có thẻ nào', 'warn');
      return { success: false, error: 'Không có pass' };
    }

    log(accIdx, total, wallet, proxy, `🎁 Đang claim rewards | 🎫 Đang có ${passes.length} passes`, 'info');

    let claimedCount = 0;
    let lastDigest = null;

    for (const passObj of passes) {
      try {
        const passId = passObj.data?.objectId;
        if (!passId) continue;

        const tx = new Transaction();
        tx.setSender(address);
        tx.setGasBudget(10_000_000);

        const [claimedCoin] = tx.moveCall({
          target: `${CONTRACTS.corePackage}::listing::claim`,
          arguments: [
            tx.object(CONTRACTS.listing),
            tx.object(CONTRACTS.registry),
            tx.object(CONTRACTS.tideConfig),
            tx.object(passId)
          ]
        });

        tx.transferObjects([claimedCoin], address);

        const result = await signAndExecute(keypair, tx);

        if (result.effects?.status?.status === 'success') {
          claimedCount++;
          lastDigest = result.digest;
          log(accIdx, total, wallet, proxy, `✅ Claim pass #${claimedCount} thành công | TX: ${result.digest}`, 'success');
        }

        await randomDelay(1000, 2000);
      } catch { }
    }

    if (claimedCount > 0) {
      log(accIdx, total, wallet, proxy, `✅ Claim rewards hoàn tất | ${claimedCount}/${passes.length} passes`, 'success');
      return { success: true, claimed: claimedCount, digest: lastDigest };
    } else {
      log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua claim - không có thưởng mới', 'warn');
      return { success: false, error: 'Không có rewards' };
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Claim rewards thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function mintPass(keypair, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    log(accIdx, total, wallet, proxy, '🎫 Đang mint pass', 'info');

    const mintAmountMist = BigInt(1_000_000_000); // 1 SUI tối thiểu

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    const [paymentCoin] = tx.splitCoins(tx.gas, [tx.pure.u64(mintAmountMist)]);

    const [passObj] = tx.moveCall({
      target: `${CONTRACTS.corePackage}::listing::deposit`,
      arguments: [
        tx.object(CONTRACTS.listing),
        tx.object(CONTRACTS.registry),
        tx.object(CONTRACTS.depositPool),
        tx.object(CONTRACTS.tideConfig),
        paymentCoin,
        tx.object(CONTRACTS.clock)
      ]
    });

    tx.transferObjects([passObj], address);

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Mint pass thành công | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      throw new Error(result.effects?.status?.error || 'Mint thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Mint pass thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function borrowSUI(keypair, accIdx, total, proxy, prefetchedPasses) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    const client = getClient();
    const vaultObj = await client.getObject({ id: CONTRACTS.loanVault, options: { showContent: true } });
    if (vaultObj.data?.content?.fields?.paused === true) {
      log(accIdx, total, wallet, proxy, '⏭️ Borrow đang tạm dừng — LoanVault paused', 'warn');
      return { success: false, error: 'LoanVault paused' };
    }

    const passes = prefetchedPasses || await getOwnedObjects(address, CONTRACTS.supporterPassType);

    if (!passes || passes.length === 0) {
      log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua borrow - không có thẻ để thế chấp', 'warn');
      return { success: false, error: 'Không có pass' };
    }

    const borrowAmountMist = BigInt(Math.floor((config.loan?.borrowAmount || 0.5) * 1e9));
    const passId = passes[0].data?.objectId;
    log(accIdx, total, wallet, proxy, `🏦 Đang borrow ${Number(borrowAmountMist) / 1e9} SUI...`, 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    const borrowCallResult = tx.moveCall({
      target: `${CONTRACTS.loansPackage}::loan_vault::borrow`,
      arguments: [
        tx.object(CONTRACTS.loanVault),
        tx.object(CONTRACTS.listing),
        tx.object(CONTRACTS.registry),
        tx.object(CONTRACTS.depositPool),
        tx.object(passId),
        tx.pure.u64(borrowAmountMist)
      ]
    });

    tx.transferObjects([borrowCallResult[0]], address); // LoanReceipt
    tx.transferObjects([borrowCallResult[1]], address); // Coin<SUI>

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Borrow thành công ${Number(borrowAmountMist) / 1e9} SUI | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      throw new Error(result.effects?.status?.error || 'Borrow thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Borrow thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

// ===== TRẢ NỢ =====
export async function repayLoan(keypair, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    const receipts = await getOwnedObjects(address, CONTRACTS.loanReceiptType);

    if (!receipts || receipts.length === 0) {
      log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua repay - không có khoản vay', 'warn');
      return { success: false, error: 'Không có LoanReceipt' };
    }

    const receiptId = receipts[0].data?.objectId;
    log(accIdx, total, wallet, proxy, `💳 Đang trả nợ loan...`, 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    const borrowAmount = BigInt(Math.floor((config.loan?.borrowAmount || 0.5) * 1e9));
    const repayAmount = borrowAmount * 2n;
    const [paymentCoin] = tx.splitCoins(tx.gas, [tx.pure.u64(repayAmount)]);

    const [changeCoin] = tx.moveCall({
      target: `${CONTRACTS.loansPackage}::loan_vault::repay`,
      arguments: [
        tx.object(CONTRACTS.loanVault),
        tx.object(receiptId),
        paymentCoin
      ]
    });

    const [returnedPass] = tx.moveCall({
      target: `${CONTRACTS.loansPackage}::loan_vault::withdraw_collateral`,
      arguments: [
        tx.object(CONTRACTS.loanVault),
        tx.object(receiptId)
      ]
    });

    tx.transferObjects([changeCoin, returnedPass], address);

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Repay loan thành công | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      throw new Error(result.effects?.status?.error || 'Repay thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Repay loan thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function loanCycle(keypair, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);
  const repeatCount = config.loan?.repeatCount || 3;
  let successCount = 0;

  try {
    const client = getClient();
    const vaultObj = await client.getObject({ id: CONTRACTS.loanVault, options: { showContent: true } });
    if (vaultObj.data?.content?.fields?.paused === true) {
      log(accIdx, total, wallet, proxy, '⏭️ Borrow đang tạm dừng — LoanVault paused', 'warn');
      return { success: false, error: 'LoanVault paused' };
    }

    log(accIdx, total, wallet, proxy, `🔄 Bắt đầu chu kỳ vay (${repeatCount} lần)`, 'info');

    for (let i = 1; i <= repeatCount; i++) {
      const passes = await getOwnedObjects(address, CONTRACTS.supporterPassType);
      if (!passes || passes.length === 0) {
        log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua borrow - không có thẻ để thế chấp', 'warn');
        break;
      }

      const borrowResult = await borrowSUI(keypair, accIdx, total, proxy, passes);
      if (!borrowResult.success) break;
      successCount++;

      await randomDelay(3000, 5000);

      const repayResult = await repayLoan(keypair, accIdx, total, proxy);
      if (!repayResult.success) break;
      successCount++;

      if (i < repeatCount) {
        await randomDelay(config.delay.min, config.delay.max);
      }
    }

    log(accIdx, total, wallet, proxy, `📊 Chu kỳ vay: ${successCount} thao tác thành công / ${repeatCount} lần`, successCount > 0 ? 'success' : 'warn');
    return { success: successCount > 0 };
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Chu kỳ vay lỗi | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function listForSale(keypair, passObjectId, priceMist, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    log(accIdx, total, wallet, proxy, `📋 Đăng bán pass lên sàn | giá: ${Number(priceMist) / 1e9} SUI`, 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    tx.moveCall({
      target: `${CONTRACTS.marketplacePackage}::marketplace::list_for_sale`,
      arguments: [
        tx.object(CONTRACTS.marketplace),
        tx.object(passObjectId),
        tx.pure.u64(BigInt(priceMist))
      ]
    });

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      let saleListingId = null;
      if (result.objectChanges) {
        const created = result.objectChanges.find(
          c => c.type === 'created' && c.objectType?.includes('SaleListing')
        );
        if (created) saleListingId = created.objectId;
      }
      log(accIdx, total, wallet, proxy, `✅ Đăng bán pass thành công | TX: ${digest}`, 'success');
      return { success: true, digest, saleListingId };
    } else {
      throw new Error(result.effects?.status?.error || 'Đăng bán thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Đăng bán pass thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function buyAndTake(keypair, saleListingId, priceMist, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    log(accIdx, total, wallet, proxy, `🛒 Mua pass từ sàn | giá: ${Number(priceMist) / 1e9} SUI`, 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    const [paymentCoin] = tx.splitCoins(tx.gas, [tx.pure.u64(BigInt(priceMist))]);

    tx.moveCall({
      target: `${CONTRACTS.marketplacePackage}::marketplace::buy_and_take`,
      arguments: [
        tx.object(CONTRACTS.marketplace),
        tx.object(CONTRACTS.treasuryVault),
        tx.object(saleListingId),
        paymentCoin
      ]
    });

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Mua pass thành công | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      throw new Error(result.effects?.status?.error || 'Mua thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Mua pass thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function delistPass(keypair, saleListingId, accIdx, total, proxy) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);

  try {
    log(accIdx, total, wallet, proxy, '🗑️ Gỡ bán pass', 'info');

    const tx = new Transaction();
    tx.setSender(address);
    tx.setGasBudget(10_000_000);

    const [delistedPass] = tx.moveCall({
      target: `${CONTRACTS.marketplacePackage}::marketplace::delist`,
      arguments: [
        tx.object(CONTRACTS.marketplace),
        tx.object(saleListingId)
      ]
    });

    tx.transferObjects([delistedPass], address);

    const result = await signAndExecute(keypair, tx);
    const digest = result.digest;

    if (result.effects?.status?.status === 'success') {
      log(accIdx, total, wallet, proxy, `✅ Gỡ bán thành công | TX: ${digest}`, 'success');
      return { success: true, digest };
    } else {
      throw new Error(result.effects?.status?.error || 'Gỡ bán thất bại');
    }
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Gỡ bán thất bại | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

async function findOwnSaleListing(address, proxyObj) {
  try {
    const data = await getMarketplace(address, proxyObj);
    const listings = data?.data?.listings || [];
    return listings.find(l => l.seller === address) || null;
  } catch {
    return null;
  }
}

export async function tradeCycle(keypair, accIdx, total, proxy, proxyObj) {
  const address = keypair.getPublicKey().toSuiAddress();
  const wallet = shortWallet(address);
  const repeatCount = config.marketplace?.repeatCount || 5;
  const sellPrice = config.marketplace?.sellPrice || 999_000_000_000; // 999
  let successCount = 0;

  try {
    let passes = await getOwnedObjects(address, CONTRACTS.supporterPassType);
    if (!passes || passes.length === 0) {
      log(accIdx, total, wallet, proxy, '🛒 Chưa có thẻ → tìm mua từ sàn...', 'info');
      const buyResult = await buyPassFromMarketplace(keypair, accIdx, total, wallet, proxy, proxyObj);
      if (!buyResult.success) {
        log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua trade - không mua được thẻ từ sàn', 'warn');
        return { success: false, error: 'Không có pass' };
      }
      await randomDelay(2000, 4000);
      passes = await getOwnedObjects(address, CONTRACTS.supporterPassType);
      if (!passes || passes.length === 0) {
        log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua trade - không có thẻ sau mua', 'warn');
        return { success: false, error: 'Không có pass' };
      }
    }

    log(accIdx, total, wallet, proxy, `🔄 Bắt đầu chu kỳ giao dịch: list→delist (${repeatCount} lần)`, 'info');

    for (let i = 1; i <= repeatCount; i++) {
      const hasSUI = await ensureSUI(keypair, 0.05, accIdx, total, wallet, proxy, proxyObj);
      if (!hasSUI) {
        log(accIdx, total, wallet, proxy, '⏭️ Hết SUI, dừng trade cycle', 'warn');
        break;
      }

      log(accIdx, total, wallet, proxy, `🔄 G.dịch lần ${i}/${repeatCount}`, 'info');

      const currentPasses = await getOwnedObjects(address, CONTRACTS.supporterPassType);
      if (!currentPasses || currentPasses.length === 0) {
        log(accIdx, total, wallet, proxy, '⏭️ Bỏ qua trade - không có thẻ', 'warn');
        break;
      }

      const passId = currentPasses[0].data?.objectId;

      const minPrice = Math.floor(sellPrice * 0.7);
      const maxPrice = Math.floor(sellPrice * 1.3);
      const randomPrice = Math.floor(Math.random() * (maxPrice - minPrice + 1)) + minPrice;

      const listResult = await listForSale(keypair, passId, randomPrice, accIdx, total, proxy);
      if (!listResult.success) break;
      successCount++;

      await randomDelay(2000, 4000);

      let delistOk = false;
      if (listResult.saleListingId) {
        const delistResult = await delistPass(keypair, listResult.saleListingId, accIdx, total, proxy);
        delistOk = delistResult.success;
      } else {
        const myListing = await findOwnSaleListing(address, proxyObj);
        if (myListing) {
          const delistResult = await delistPass(keypair, myListing.id, accIdx, total, proxy);
          delistOk = delistResult.success;
        } else {
          log(accIdx, total, wallet, proxy, '⚠️ Không tìm thấy listing để gỡ bán', 'warn');
        }
      }

      if (!delistOk) {
        log(accIdx, total, wallet, proxy, '⚠️ Gỡ bán thất bại (pass có thể đã bị mua) → thử mua pass mới...', 'warn');
        await randomDelay(2000, 4000);
        const reBuy = await buyPassFromMarketplace(keypair, accIdx, total, wallet, proxy, proxyObj);
        if (!reBuy.success) {
          log(accIdx, total, wallet, proxy, '⏭️ Không mua lại được pass → dừng trade cycle', 'warn');
          break;
        }
        await randomDelay(2000, 4000);
      }

      if (i < repeatCount) {
        await randomDelay(config.delay.min, config.delay.max);
      }
    }

    log(accIdx, total, wallet, proxy, `📊 Chu kỳ giao dịch: ${successCount} list thành công / ${repeatCount} lần `, successCount > 0 ? 'success' : 'warn');
    return { success: successCount > 0 };
  } catch (err) {
    log(accIdx, total, wallet, proxy, `❌ Chu kỳ giao dịch lỗi | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function crossTrade(keypairA, keypairB, accIdxA, accIdxB, total, proxyA, proxyB) {
  const addressA = keypairA.getPublicKey().toSuiAddress();
  const addressB = keypairB.getPublicKey().toSuiAddress();
  const walletA = shortWallet(addressA);
  const walletB = shortWallet(addressB);
  const crossPrice = config.marketplace?.crossPrice || 100_000_000; // 0.1 SUI min
  const MAX_RETRY = 2;

  async function ensurePass(keypair, address, accIdx, wallet, proxy) {
    let passes = await getOwnedObjects(address, CONTRACTS.supporterPassType);
    if (passes && passes.length > 0) return passes[0].data?.objectId;

    log(accIdx, total, wallet, proxy, '🎫 Không có pass → mint mới cho cross trade...', 'info');
    const hasSUI = await ensureSUI(keypair, 1.5, accIdx, total, wallet, proxy, null);
    if (!hasSUI) {
      log(accIdx, total, wallet, proxy, '⏭️ Không đủ SUI để mint pass', 'warn');
      return null;
    }
    const mintResult = await mintPass(keypair, accIdx, total, proxy);
    if (!mintResult.success) return null;

    await randomDelay(2000, 3000);
    passes = await getOwnedObjects(address, CONTRACTS.supporterPassType);
    return passes?.[0]?.data?.objectId || null;
  }

  try {
    log(accIdxA, total, walletA, proxyA, `🔄 Giao dịch chéo: ${walletA} ↔ ${walletB}`, 'info');

    // === A → B: A list, B buy ===
    let abDone = false;
    for (let attempt = 1; attempt <= MAX_RETRY && !abDone; attempt++) {
      const passIdA = await ensurePass(keypairA, addressA, accIdxA, walletA, proxyA);
      if (!passIdA) {
        log(accIdxA, total, walletA, proxyA, '⏭️ A không thể có pass → bỏ qua A→B', 'warn');
        break;
      }

      const listA = await listForSale(keypairA, passIdA, crossPrice, accIdxA, total, proxyA);
      if (!listA.success) break;

      await randomDelay(2000, 4000);

      let saleIdA = listA.saleListingId;
      if (!saleIdA) {
        const found = await findOwnSaleListing(addressA, null);
        saleIdA = found?.id;
      }
      if (!saleIdA) {
        log(accIdxB, total, walletB, proxyB, '⚠️ Không tìm thấy listing của A', 'warn');
        break;
      }

      const buyB = await buyAndTake(keypairB, saleIdA, crossPrice, accIdxB, total, proxyB);
      if (buyB.success) {
        abDone = true;
      } else if (attempt < MAX_RETRY) {
        log(accIdxA, total, walletA, proxyA, `⚠️ Mua bị snipe/lỗi → retry ${attempt + 1}/${MAX_RETRY}...`, 'warn');
        await randomDelay(2000, 3000);
      }
    }

    await randomDelay(3000, 5000);

    // === B → A: B list, A buy ===
    let baDone = false;
    for (let attempt = 1; attempt <= MAX_RETRY && !baDone; attempt++) {
      const passIdB = await ensurePass(keypairB, addressB, accIdxB, walletB, proxyB);
      if (!passIdB) {
        log(accIdxB, total, walletB, proxyB, '⏭️ B không thể có pass → bỏ qua B→A', 'warn');
        break;
      }

      const listB = await listForSale(keypairB, passIdB, crossPrice, accIdxB, total, proxyB);
      if (!listB.success) break;

      await randomDelay(2000, 4000);

      let saleIdB = listB.saleListingId;
      if (!saleIdB) {
        const found = await findOwnSaleListing(addressB, null);
        saleIdB = found?.id;
      }
      if (!saleIdB) {
        log(accIdxA, total, walletA, proxyA, '⚠️ Không tìm thấy listing của B', 'warn');
        break;
      }

      const buyA = await buyAndTake(keypairA, saleIdB, crossPrice, accIdxA, total, proxyA);
      if (buyA.success) {
        baDone = true;
      } else if (attempt < MAX_RETRY) {
        log(accIdxB, total, walletB, proxyB, `⚠️ Mua bị snipe/lỗi → retry ${attempt + 1}/${MAX_RETRY}...`, 'warn');
        await randomDelay(2000, 3000);
      }
    }

    const bothOK = abDone && baDone;
    const anyOK = abDone || baDone;
    if (bothOK) {
      log(accIdxA, total, walletA, proxyA, `✅ Giao dịch chéo hoàn tất: ${walletA} ↔ ${walletB} | A: +40đ, B: +40đ`, 'success');
    } else if (anyOK) {
      log(accIdxA, total, walletA, proxyA, `⚠️ Giao dịch chéo 1 chiều: ${abDone ? 'A→B' : 'B→A'} OK | ${walletA} ↔ ${walletB}`, 'warn');
    } else {
      log(accIdxA, total, walletA, proxyA, `❌ Giao dịch chéo thất bại: ${walletA} ↔ ${walletB}`, 'error');
    }
    return { success: anyOK };
  } catch (err) {
    log(accIdxA, total, walletA, proxyA, `❌ Giao dịch chéo lỗi | ${friendlyError(err.message)}`, 'error');
    return { success: false, error: err.message };
  }
}

export async function tradePass(keypair, accIdx, total, proxy, prefetchedPasses) {
  return tradeCycle(keypair, accIdx, total, proxy);
}

export default {
  depositSUI, claimRewards, mintPass, borrowSUI, repayLoan, loanCycle,
  listForSale, buyAndTake, delistPass, tradeCycle, tradePass, crossTrade,
  ensureSUI, buyPassFromMarketplace
};
