import { Ed25519Keypair } from '@mysten/sui/keypairs/ed25519';
import { SuiClient, getFullnodeUrl } from '@mysten/sui/client';
import { Transaction } from '@mysten/sui/transactions';
import { decodeSuiPrivateKey } from '@mysten/sui/cryptography';
import config from '../core/config.js';

let _client = null;
export function getClient() {
  if (!_client) {
    _client = new SuiClient({ url: config.api.suiRpc || getFullnodeUrl('testnet') });
  }
  return _client;
}

async function withRetry(fn, maxRetries = 3, baseDelay = 2000) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const msg = err.message || '';
      const isRetryable = msg.includes('429') || msg.includes('ECONNRESET') || msg.includes('ETIMEDOUT')
        || msg.includes('ECONNREFUSED') || msg.includes('socket hang up') || msg.includes('Too Many Requests')
        || msg.includes('quorum') || msg.includes('fetch failed');

      if (!isRetryable || attempt === maxRetries) throw err;

      const delay = baseDelay * attempt + Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

export function createKeypair(accountData) {
  const { raw, type } = accountData;

  if (type === 'seedphrase') {
    return Ed25519Keypair.deriveKeypair(raw.trim());
  }

  let keyStr = raw.trim();

  if (keyStr.startsWith('suiprivkey')) {
    const { secretKey } = decodeSuiPrivateKey(keyStr);
    return Ed25519Keypair.fromSecretKey(secretKey);
  }

  if (keyStr.startsWith('0x')) {
    keyStr = keyStr.slice(2);
  }

  const secretKey = Buffer.from(keyStr, 'hex');
  return Ed25519Keypair.fromSecretKey(secretKey);
}

export async function getBalance(address) {
  return withRetry(async () => {
    const client = getClient();
    const balance = await client.getBalance({
      owner: address,
      coinType: '0x2::sui::SUI'
    });
    return {
      totalBalance: BigInt(balance.totalBalance),
      balanceSUI: Number(balance.totalBalance) / 1e9
    };
  });
}

export async function getSuiCoins(address) {
  return withRetry(async () => {
    const client = getClient();
    const coins = await client.getCoins({
      owner: address,
      coinType: '0x2::sui::SUI'
    });
    return coins.data;
  });
}

export async function getOwnedObjects(address, structType) {
  return withRetry(async () => {
    const client = getClient();
    const objects = await client.getOwnedObjects({
      owner: address,
      filter: { StructType: structType },
      options: {
        showContent: true,
        showType: true
      }
    });
    return objects.data;
  });
}

export async function signAndExecute(keypair, tx) {
  return withRetry(async () => {
    const client = getClient();
    const result = await client.signAndExecuteTransaction({
      signer: keypair,
      transaction: tx,
      options: {
        showEffects: true,
        showObjectChanges: true
      }
    });
    return result;
  }, 2);
}

export async function waitForTransaction(digest) {
  return withRetry(async () => {
    const client = getClient();
    return await client.waitForTransaction({
      digest,
      options: {
        showEffects: true
      }
    });
  });
}

export default { getClient, createKeypair, getBalance, getSuiCoins, getOwnedObjects, signAndExecute, waitForTransaction };
