import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Account, Ed25519PrivateKey, Network } from '@aptos-labs/ts-sdk';
import { ShelbyNodeClient } from '@shelby-protocol/sdk/node';
import chalk from 'chalk';
import readlineSync from 'readline-sync';
import { HttpsProxyAgent } from 'https-proxy-agent';

// Suppress Aptos SDK Warnings
const originalWarn = console.warn;
console.warn = (...args) => {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('[Aptos SDK]')) return;
    originalWarn.apply(console, args);
};

// Fix for __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const DEFAULT_API_KEY = "AG-MR5SFEFY8BSVMEMVG9YETVQBZJJ2QYEPF";
const IMAGE_URL = "https://picsum.photos/1920/1080";
const FAUCET_URL = "https://faucet.shelbynet.shelby.xyz/fund";
const EXPIRATION_SECONDS = 30 * 24 * 60 * 60;

// Helper to delay execution
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Display Header
function displayHeader() {
    console.clear();
    console.log(chalk.bold.cyan("=================================================="));
    console.log(chalk.bold.cyan("                 SHELBY TESTNET BOT"));
    console.log(chalk.bold.cyan("              CREATED BY KAZUHA VIP ONLY"));
    console.log(chalk.bold.cyan("=================================================="));
    console.log();
}

// Get Proxies
function getProxies() {
    const proxyFile = path.join(__dirname, 'proxy.txt');
    if (!fs.existsSync(proxyFile)) return [];
    return fs.readFileSync(proxyFile, 'utf8')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));
}

// Get Axios Config with Proxy
function getAxiosConfig(proxy) {
    const config = { headers: { 'Content-Type': 'application/json' } };
    if (proxy) {
        config.httpsAgent = new HttpsProxyAgent(proxy);
        config.proxy = false; // Disable default axios proxy handling to use agent
    }
    return config;
}

// Faucet Claim Function
async function claimFaucet(address, proxy) {
    try {
        console.log(chalk.bold.white(`> Claiming Faucet for: ${chalk.cyan(address)}`));
        if (proxy) console.log(chalk.gray(`  Using Proxy: ${proxy}`));

        const payload = {
            address: address,
            amount: 1000000000
        };

        const response = await axios.post(FAUCET_URL, payload, getAxiosConfig(proxy));

        if (response.data && response.data.txn_hashes) {
            const txHash = response.data.txn_hashes[0];
            const explorerUrl = `https://explorer.aptoslabs.com/txn/${txHash}?network=shelbynet`;
            console.log(chalk.bold.green(`  + Faucet Claimed Successfully!`));
            console.log(chalk.bold.blue(`  > Explorer: ${explorerUrl}`));
        } else {
            console.log(chalk.bold.red(`  - Faucet Claim Failed (No Hash)`));
        }

    } catch (error) {
        console.log(chalk.bold.red(`  - Error: ${error.message}`));
    }
}

// Download Image Function
async function downloadImage(proxy) {
    try {
        const config = getAxiosConfig(proxy);
        config.responseType = 'arraybuffer';
        config.url = IMAGE_URL;
        config.method = 'GET';

        const response = await axios(config);
        return Buffer.from(response.data);
    } catch (error) {
        console.log(chalk.bold.red(`  - Error downloading image: ${error.message}`));
        return null;
    }
}

// Upload Blob Function
async function uploadData(signer, proxy) {
    try {
        const address = signer.accountAddress.toString();

        const client = new ShelbyNodeClient({
            network: Network.SHELBYNET,
            apiKey: process.env.SHELBY_API_KEY || DEFAULT_API_KEY,
        });

        console.log(chalk.bold.white(`> Downloading random image...`));
        const imageBuffer = await downloadImage(proxy);
        if (!imageBuffer) return;

        const timestamp = Date.now();
        const randomSuffix = Math.floor(Math.random() * 1000);
        const blobName = `image_${timestamp}_${randomSuffix}.png`;
        const expirationMicros = BigInt(Date.now() * 1000) + (BigInt(EXPIRATION_SECONDS) * 1000000n);

        console.log(chalk.bold.white(`> Uploading to Shelby (Name: ${blobName})...`));

        const upload = await client.upload({
            blobData: imageBuffer,
            signer: signer,
            blobName: blobName,
            expirationMicros: expirationMicros,
        });

        console.log(chalk.bold.green(`  + Uploaded Successfully!`));
        const explorerUrl = `https://explorer.aptoslabs.com/account/${address}?network=shelbynet`;
        console.log(chalk.bold.blue(`  > Explorer: ${explorerUrl}`));

    } catch (error) {
        if (error.message.includes("E_BLOB_ALREADY_EXISTS")) {
            console.log(chalk.yellow(`  * Blob already exists (Skipping)`));
        } else {
            console.log(chalk.bold.red(`  - Upload Error: ${error.message}`));
        }
    }
}

// Processing Loop
async function processAccounts(action) {
    const pvFile = path.join(__dirname, 'pv.txt');
    if (!fs.existsSync(pvFile)) {
        console.log(chalk.red("Error: pv.txt not found!"));
        return;
    }

    const privateKeys = fs.readFileSync(pvFile, 'utf8')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#') && !line.startsWith('PUT_YOUR'));

    if (privateKeys.length === 0) {
        console.log(chalk.red("Error: No private keys found in pv.txt"));
        return;
    }

    const proxies = getProxies();

    let loopCount = 1;
    if (action === 'upload') {
        const input = readlineSync.question(chalk.bold.white("How many times to upload per account? "));
        loopCount = parseInt(input) || 1;
    }

    console.log(chalk.bold.yellow(`Loading ${privateKeys.length} accounts...`));

    for (let i = 0; i < privateKeys.length; i++) {
        let pk = privateKeys[i];
        if (pk.startsWith('0x')) pk = pk.slice(2);

        const signer = Account.fromPrivateKey({ privateKey: new Ed25519PrivateKey(pk) });
        const address = signer.accountAddress.toString();
        const proxy = proxies.length > 0 ? proxies[i % proxies.length] : null;

        console.log(chalk.bold.magenta(`\n[Account ${i + 1}/${privateKeys.length}] ${address}`));

        if (action === 'faucet') {
            await claimFaucet(address, proxy);
        } else if (action === 'upload') {
            for (let j = 0; j < loopCount; j++) {
                console.log(chalk.gray(`\n  [Run ${j + 1}/${loopCount}]`));
                await uploadData(signer, proxy);
                await sleep(2000);
            }
        }
    }
}

// Main Menu
async function main() {
    while (true) {
        displayHeader();
        console.log(chalk.bold.yellow("1. Claim Faucet"));
        console.log(chalk.bold.yellow("2. Upload Data"));
        console.log(chalk.bold.red("3. Exit"));
        console.log();

        const input = readlineSync.question(chalk.bold.white('Select Option [1-3]: '));
        const choice = parseInt(input);

        if (choice === 1) {
            await processAccounts('faucet');
        } else if (choice === 2) {
            await processAccounts('upload');
        } else if (choice === 3) {
            console.log(chalk.gray("Exiting..."));
            process.exit(0);
        } else {
            console.log(chalk.red("Invalid option!"));
        }

        readlineSync.question(chalk.gray("\nPress Enter to return to menu..."));
    }
}

main();
