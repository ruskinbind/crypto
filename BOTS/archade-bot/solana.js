// solana.js
const { Connection, Keypair, VersionedTransaction, Transaction, sendAndConfirmTransaction } = require('@solana/web3.js');
const bs58 = require('bs58');
const fs = require('fs');
const config = require('./config');
const { log } = require('./utils');

const connection = new Connection(config.RPC_URL, 'confirmed');

let wallets = [];
let currentWalletIndex = 0;

/**
 * Load all wallets from pv.txt
 * Format: One Base58 private key per line
 */
function loadAllWallets() {
    try {
        if (!fs.existsSync('pv.txt')) {
            log('error', 'pv.txt not found. Please create it and add your private keys.');
            process.exit(1);
        }

        const content = fs.readFileSync('pv.txt', 'utf-8');
        const privateKeys = content
            .split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#')); // Filter empty lines and comments

        if (privateKeys.length === 0) {
            log('error', 'pv.txt is empty. Please add at least one Private Key (Base58).');
            process.exit(1);
        }

        wallets = privateKeys.map((key, index) => {
            try {
                const secretKey = bs58.decode(key);
                return Keypair.fromSecretKey(secretKey);
            } catch (err) {
                log('error', `Invalid private key at line ${index + 1}: ${err.message}`);
                return null;
            }
        }).filter(wallet => wallet !== null);

        if (wallets.length === 0) {
            log('error', 'No valid private keys found in pv.txt');
            process.exit(1);
        }

        log('info', `Loaded ${wallets.length} wallet(s) from pv.txt`);
        return wallets;
    } catch (err) {
        log('error', `Failed to load wallets: ${err.message}`);
        process.exit(1);
    }
}

/**
 * Get wallet by index
 */
function loadWallet(index = null) {
    if (wallets.length === 0) {
        loadAllWallets();
    }

    const walletIndex = index !== null ? index : currentWalletIndex;

    if (walletIndex < 0 || walletIndex >= wallets.length) {
        log('error', `Invalid wallet index: ${walletIndex}`);
        return wallets[0];
    }

    return wallets[walletIndex];
}

/**
 * Set current wallet index
 */
function setCurrentWallet(index) {
    if (index < 0 || index >= wallets.length) {
        log('error', `Invalid wallet index: ${index}`);
        return false;
    }
    currentWalletIndex = index;
    log('info', `Switched to wallet ${index + 1}/${wallets.length}`);
    return true;
}

/**
 * Get total number of wallets
 */
function getWalletCount() {
    if (wallets.length === 0) {
        loadAllWallets();
    }
    return wallets.length;
}

/**
 * Get current wallet index
 */
function getCurrentWalletIndex() {
    return currentWalletIndex;
}

async function sendTransaction(txBase64, isVersioned = false) {
    const wallet = loadWallet();
    const txBuffer = Buffer.from(txBase64, 'base64');

    try {
        let signature;
        if (isVersioned) {
            const transaction = VersionedTransaction.deserialize(txBuffer);
            transaction.sign([wallet]);
            signature = await connection.sendTransaction(transaction);
        } else {
            const transaction = Transaction.from(txBuffer);
            transaction.sign(wallet);
            signature = await connection.sendRawTransaction(transaction.serialize());
        }

        log('info', `Transaction Sent. Signature: ${signature}`);

        const confirmation = await connection.confirmTransaction(signature, 'confirmed');
        if (confirmation.value.err) {
            throw new Error(`Transaction failed: ${JSON.stringify(confirmation.value.err)}`);
        }

        const slot = confirmation.context.slot;
        log('success', `Transaction Confirmed! Block: ${slot}`);
        return { signature, slot };
    } catch (err) {
        log('error', `Transaction Error: ${err.message}`);
        throw err;
    }
}

function getWalletAddress() {
    const wallet = loadWallet();
    return wallet.publicKey.toString();
}

// Add SPL Token imports
const { createMint, getOrCreateAssociatedTokenAccount, mintTo } = require('@solana/spl-token');

async function createSPLToken(mintKeypair) {
    const wallet = loadWallet();
    log('info', `Deploying Token (Mint: ${mintKeypair.publicKey.toString()})...`);

    try {
        // Create Mint on-chain
        const mint = await createMint(
            connection,
            wallet,               // Payer
            wallet.publicKey,     // Mint Authority
            wallet.publicKey,     // Freeze Authority
            6,                    // Decimals
            mintKeypair           // Keypair
        );

        log('success', `Token Minted On-Chain! Block Hash: ${mint.toString()}`);
        return mint.toString();
    } catch (err) {
        log('error', `Token Deployment Failed: ${err.message}`);
        throw err;
    }
}

module.exports = {
    loadWallet,
    loadAllWallets,
    setCurrentWallet,
    getWalletCount,
    getCurrentWalletIndex,
    sendTransaction,
    getWalletAddress,
    createSPLToken,
    connection
};
