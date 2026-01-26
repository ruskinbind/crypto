const fs = require('fs');
const readline = require('readline');
const { ethers } = require('ethers');
const dotenv = require('dotenv');
const axios = require('axios');
const { HttpsProxyAgent } = require('https-proxy-agent');

dotenv.config();

// Color codes for terminal with bold
const colors = {
    reset: "\x1b[0m",
    bright: "\x1b[1m",
    green: "\x1b[32m\x1b[1m",
    yellow: "\x1b[33m\x1b[1m",
    blue: "\x1b[34m\x1b[1m",
    magenta: "\x1b[35m\x1b[1m",
    cyan: "\x1b[36m\x1b[1m",
    white: "\x1b[37m\x1b[1m",
    red: "\x1b[31m\x1b[1m"
};

// Clear terminal
function clearTerminal() {
    console.clear();
}

// Display banner
function displayBanner() {
    console.log(`${colors.magenta}BLOCKSTREET BOT V3${colors.reset}`);
    console.log(`${colors.green}Created By Kazuha VIP only${colors.reset}\n`);
}

// Display menu
function displayMenu() {
    console.log(`${colors.white}--- MAIN MENU ---${colors.reset}`);
    console.log(`1. Auto Swap`);
    console.log(`2. Manual Swap`);
    console.log(`3. Supply`);
    console.log(`4. Withdrawal`);
    console.log(`5. Borrow`);
    console.log(`6. Repay`);
    console.log(`7. Auto All`);
    console.log(`8. Set Transaction Count`);
    console.log(`9. Exit`);
    console.log(`${colors.white}-----------------${colors.reset}`);
}

// Enhanced logger without emojis
const logger = {
    info: (wallet, msg) => {
        const walletDisplay = wallet || 'System';
        console.log(`${colors.cyan}[${walletDisplay}]${colors.reset} [INFO] ${msg}`);
    },
    success: (wallet, msg) => {
        const walletDisplay = wallet || 'System';
        console.log(`${colors.cyan}[${walletDisplay}]${colors.reset} ${colors.green}[SUCCESS] ${msg}${colors.reset}`);
    },
    error: (wallet, msg) => {
        const walletDisplay = wallet || 'System';
        console.log(`${colors.cyan}[${walletDisplay}]${colors.reset} ${colors.red}[ERROR] ${msg}${colors.reset}`);
    },
    warning: (wallet, msg) => {
        const walletDisplay = wallet || 'System';
        console.log(`${colors.cyan}[${walletDisplay}]${colors.reset} ${colors.yellow}[WARN] ${msg}${colors.reset}`);
    },
    process: (wallet, msg) => {
        const walletDisplay = wallet || 'System';
        console.log(`${colors.cyan}[${walletDisplay}]${colors.reset} ${colors.magenta}[PROCESS] ${msg}${colors.reset}`);
    }
};

// Storage for transaction count
let globalTransactionCount = 1;

// Function to read captcha key from key.txt
function getCaptchaKey() {
    try {
        if (!fs.existsSync('key.txt')) {
            logger.error(null, 'key.txt file not found! Please create it with your Captcha API key');
            return null;
        }
        const key = fs.readFileSync('key.txt', 'utf-8').trim();
        if (!key) {
            logger.error(null, 'key.txt is empty! Please add your Captcha API key');
            return null;
        }
        logger.success(null, 'Captcha API key loaded from key.txt');
        return key;
    } catch (error) {
        logger.error(null, `Error reading key.txt: ${error.message}`);
        return null;
    }
}

// Load wallets from pv.txt
function loadWalletsFromFile() {
    const wallets = [];
    try {
        if (!fs.existsSync('pv.txt')) {
            logger.error(null, 'pv.txt file not found! Please create it with format: privatekey:name');
            return wallets;
        }

        const content = fs.readFileSync('pv.txt', 'utf-8');
        const lines = content.split('\n').filter(line => line.trim());

        lines.forEach((line, index) => {
            try {
                const [privateKey, name] = line.trim().split(':');
                if (privateKey) {
                    const wallet = new ethers.Wallet(privateKey.trim());
                    wallets.push({
                        wallet: wallet,
                        name: name ? name.trim() : `Wallet${index + 1}`
                    });
                }
            } catch (error) {
                logger.warning(null, `Failed to load wallet from line ${index + 1}`);
            }
        });

        if (wallets.length > 0) {
            logger.success(null, `Loaded ${wallets.length} wallet(s) from pv.txt`);
        }
    } catch (error) {
        logger.error(null, `Error reading pv.txt: ${error.message}`);
    }
    return wallets;
}

const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
];

function randomUA() {
    return userAgents[Math.floor(Math.random() * userAgents.length)];
}

function parseProxy(proxyLine) {
    let proxy = proxyLine.trim();
    if (!proxy) return null;
    proxy = proxy.replace(/^https?:\/\//, '');
    const specialMatch = proxy.match(/^([^:]+):(\d+)@(.+):(.+)$/);
    if (specialMatch) {
        const [, host, port, user, pass] = specialMatch;
        return `http://${user}:${pass}@${host}:${port}`;
    }
    const parts = proxy.split(':');
    if (parts.length === 4 && !isNaN(parts[1])) {
        const [host, port, user, pass] = parts;
        return `http://${user}:${pass}@${host}:${port}`;
    }
    return `http://${proxy}`;
}

function readAndParseProxies(filePath) {
    if (!fs.existsSync(filePath)) return [];
    const lines = fs.readFileSync(filePath, 'utf-8').split('\n');
    return lines.map(line => parseProxy(line)).filter(Boolean);
}

const CUSTOM_SIGN_TEXT = `blockstreet.money wants you to sign in with your Ethereum account:
0x4CBB1421DF1CF362DC618d887056802d8adB7BC0

Welcome to Block Street

URI: https://blockstreet.money
Version: 1
Chain ID: 1
Nonce: Z9YFj5VY80yTwN3n
Issued At: 2025-10-27T09:49:38.537Z
Expiration Time: 2025-10-27T09:51:38.537Z`;

const SAMPLE_HEADERS = {
    timestamp: process.env.EXAMPLE_TIMESTAMP || '',
    signatureHeader: process.env.EXAMPLE_SIGNATURE || '',
    fingerprint: process.env.EXAMPLE_FINGERPRINT || '',
    abs: process.env.EXAMPLE_ABS || '',
    token: process.env.EXAMPLE_TOKEN || '',
    origin: 'https://blockstreet.money'
};

// Fixed captcha solving function
async function solveTurnstile(apikey, sitekey, pageurl) {
    logger.process(null, 'Solving Cloudflare Turnstile captcha...');
    if (!apikey) throw new Error('Captcha API key is missing from key.txt file.');

    const submitUrl = 'https://api.sctg.xyz/in.php';
    const submitData = new URLSearchParams({
        key: apikey,
        method: 'turnstile',
        sitekey: sitekey,
        pageurl: pageurl,
        json: 1
    });

    try {
        const submitRes = await axios.post(submitUrl, submitData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });

        if (submitRes.data.status !== 1) throw new Error(`Captcha submit failed: ${submitRes.data.request || submitRes.data.error_text}`);
        const requestId = submitRes.data.request;

        const resUrl = `https://api.sctg.xyz/res.php`;

        while (true) {
            await new Promise(resolve => setTimeout(resolve, 5000));
            const resRes = await axios.get(resUrl, {
                params: {
                    key: apikey,
                    action: 'get',
                    id: requestId,
                    json: 1
                }
            });

            if (resRes.data.status === 1) {
                logger.success(null, 'Captcha solved successfully!');
                return resRes.data.request;
            }
            if (resRes.data.request !== 'CAPCHA_NOT_READY') throw new Error(`Captcha solve failed: ${resRes.data.request}`);
            logger.process(null, 'Captcha not ready, waiting...');
        }
    } catch (error) {
        throw new Error(`Captcha solving process error: ${error.message}`);
    }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const question = (query) => new Promise(resolve => rl.question(query, resolve));
const closeRl = () => rl.close();

const getRandomAmount = (min, max) => Math.random() * (max - min) + min;
const randomDelay = async (min = 5000, max = 10000) => await sleep(getRandomAmount(min, max));

// Randomization Helpers
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

const shouldSkip = (probability = 0.2) => Math.random() < probability;

const countdown = async (seconds) => {
    let remaining = seconds;
    while (remaining > 0) {
        const h = Math.floor(remaining / 3600).toString().padStart(2, '0');
        const m = Math.floor((remaining % 3600) / 60).toString().padStart(2, '0');
        const s = Math.floor(remaining % 60).toString().padStart(2, '0');
        process.stdout.write(`${colors.cyan}[WAIT] Next run in: ${h}:${m}:${s} ...${colors.reset}\r`);
        remaining--;
        await sleep(1000);
    }
    console.log('\n');
};

class BlockStreetAPI {
    constructor(wallet, walletName, proxy = null) {
        this.wallet = wallet;
        this.walletName = walletName;
        this.sessionCookie = null;
        let agent = null;
        if (proxy) {
            try {
                agent = new HttpsProxyAgent(proxy);
            } catch (e) {
                logger.error(this.walletName, `Failed to create proxy agent: ${e.message}`);
            }
        }
        this.axios = axios.create({
            baseURL: 'https://api.blockstreet.money/api',
            httpsAgent: agent,
            headers: {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.9",
                "priority": "u=1, i",
                "sec-ch-ua": "\"Brave\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "sec-gpc": "1",
                "Referer": "https://blockstreet.money/",
                "Origin": SAMPLE_HEADERS.origin
            },
            validateStatus: () => true
        });
    }

    async #sendRequest(config, requiresAuth = true) {
        config.headers = { ...(config.headers || {}), 'User-Agent': randomUA() };
        config.headers['fingerprint'] = SAMPLE_HEADERS.fingerprint;
        config.headers['timestamp'] = String(Date.now());
        config.headers['Cookie'] = requiresAuth ? (this.sessionCookie || '') : 'gfsessionid=';
        config.headers['origin'] = SAMPLE_HEADERS.origin;
        if (SAMPLE_HEADERS.token) config.headers['token'] = SAMPLE_HEADERS.token;

        try {
            const response = await this.axios.request(config);
            const setCookie = response.headers['set-cookie'];
            if (setCookie && Array.isArray(setCookie)) {
                const sessionCookie = setCookie.find(c => c.startsWith('gfsessionid='));
                if (sessionCookie) this.sessionCookie = sessionCookie.split(';')[0];
            }
            if (response.data && (response.data.code === 0 || response.data.code === '0')) {
                return response.data.data;
            }
            if (response.status >= 200 && response.status < 300) {
                return response.data;
            }
            throw new Error(JSON.stringify(response.data || response.statusText || response.status));
        } catch (error) {
            throw new Error(error.response?.data?.message || error.message || String(error));
        }
    }

    async login(captchaToken) {
        try {
            const useCustom = true;
            let nonce = null;
            let messageToSign = null;
            let issuedAt = new Date().toISOString();
            let expirationTime = new Date(Date.now() + 2 * 60 * 1000).toISOString();

            if (useCustom) {
                messageToSign = CUSTOM_SIGN_TEXT;
                const match = CUSTOM_SIGN_TEXT.match(/Nonce:\s*([^\n\r]+)/i);
                nonce = match ? match[1].trim() : (Math.random().toString(36).slice(2, 10));
                const issuedAtMatch = CUSTOM_SIGN_TEXT.match(/Issued At:\s*([^\n\r]+)/i);
                const expirationMatch = CUSTOM_SIGN_TEXT.match(/Expiration Time:\s*([^\n\r]+)/i);
                if (issuedAtMatch) issuedAt = issuedAtMatch[1].trim();
                if (expirationMatch) expirationTime = expirationMatch[1].trim();
            } else {
                const signnonce = await this.#sendRequest({ url: '/account/signnonce', method: 'GET' }, false);
                nonce = (signnonce && signnonce.signnonce) ? signnonce.signnonce : (Math.random().toString(36).slice(2, 10));
                messageToSign = `blockstreet.money wants you to sign in with your Ethereum account:\n${this.wallet.address}\n\nWelcome to Block Street\n\nURI: https://blockstreet.money\nVersion: 1\nChain ID: 1\nNonce: ${nonce}\nIssued At: ${issuedAt}\nExpiration Time: ${expirationTime}`;
            }

            logger.process(this.walletName, 'Signing message...');
            const signatureHex = await this.wallet.signMessage(messageToSign);
            const useStaticSig = process.env.USE_STATIC_SIGNATURE === '1';
            const headerSignatureValue = useStaticSig ? SAMPLE_HEADERS.signatureHeader : signatureHex;

            const form = new URLSearchParams();
            form.append('address', this.wallet.address);
            form.append('nonce', nonce);
            form.append('signature', signatureHex);
            form.append('chainId', '1');
            form.append('issuedAt', issuedAt);
            form.append('expirationTime', expirationTime);
            form.append('invite_code', process.env.INVITE_CODE || '');

            const config = {
                url: '/account/signverify',
                method: 'POST',
                headers: {
                    ...this.axios.defaults.headers,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': randomUA(),
                    'timestamp': SAMPLE_HEADERS.timestamp,
                    'signature': headerSignatureValue,
                    'fingerprint': SAMPLE_HEADERS.fingerprint,
                    'abs': SAMPLE_HEADERS.abs,
                    'token': SAMPLE_HEADERS.token,
                    'origin': SAMPLE_HEADERS.origin,
                    'Cookie': this.sessionCookie || '',
                },
                data: form.toString(),
                httpsAgent: this.axios.defaults.httpsAgent,
            };

            logger.process(this.walletName, 'Sending signverify request...');
            const response = await axios({
                baseURL: this.axios.defaults.baseURL,
                ...config,
                validateStatus: () => true
            });

            if (response.headers['set-cookie']) {
                const sessionCookie = response.headers['set-cookie'].find(c => c.startsWith('gfsessionid='));
                if (sessionCookie) { this.sessionCookie = sessionCookie.split(';')[0]; }
            }

            if (response.data && (response.data.code === 0 || response.status === 200)) {
                logger.success(this.walletName, 'Login successful');
                return response.data.data || response.data;
            } else {
                const errMsg = response.data?.message || response.data?.msg || JSON.stringify(response.data) || `${response.status} ${response.statusText}`;
                throw new Error(`Sign verify failed: ${errMsg}`);
            }
        } catch (error) {
            throw new Error(`Login failed: ${error.message}`);
        }
    }

    getTokenList() { return this.#sendRequest({ url: '/swap/token_list', method: 'GET' }, false); }
    share() { return this.#sendRequest({ url: '/share', method: 'POST' }); }
    swap(f, t, fa, ta) { return this.#sendRequest({ url: '/swap', method: 'POST', data: { from_symbol: f, to_symbol: t, from_amount: String(fa), to_amount: String(ta) }, headers: { 'content-type': 'application/json' } }); }
    supply(s, a) { return this.#sendRequest({ url: '/supply', method: 'POST', data: { symbol: s, amount: String(a) }, headers: { 'content-type': 'application/json' } }); }
    withdraw(s, a) { return this.#sendRequest({ url: '/withdraw', method: 'POST', data: { symbol: s, amount: String(a) }, headers: { 'content-type': 'application/json' } }); }
    borrow(s, a) { return this.#sendRequest({ url: '/borrow', method: 'POST', data: { symbol: s, amount: String(a) }, headers: { 'content-type': 'application/json' } }); }
    repay(s, a) { return this.#sendRequest({ url: '/repay', method: 'POST', data: { symbol: s, amount: String(a) }, headers: { 'content-type': 'application/json' } }); }
    getEarnInfo() { return this.#sendRequest({ url: '/earn/info', method: 'GET' }); }
    getSupplies() { return this.#sendRequest({ url: '/my/supply', method: 'GET' }); }
}

const displayWalletInfo = async (api, walletName) => {
    try {
        const earnInfo = await api.getEarnInfo();

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Wallet: ${walletName}${colors.reset}`);
        if (earnInfo && earnInfo.balance) {
            console.log(`${colors.green}Balance: ${parseFloat(earnInfo.balance).toFixed(4)}${colors.reset}`);
        }
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}\n`);
    } catch (e) {
        logger.warning(walletName, `Could not fetch wallet info: ${e.message}`);
    }
};

const displayAndSelectToken = async (tokenList, promptMessage) => {
    console.log(`\n${colors.yellow}${promptMessage}${colors.reset}`);
    tokenList.forEach((token, index) => {
        console.log(`${colors.green}[${index + 1}]${colors.reset} ${colors.white}${token.symbol}${colors.reset}`);
    });
    const choiceIndex = parseInt(await question(`${colors.green}Select token: ${colors.reset}`), 10) - 1;
    return (choiceIndex >= 0 && choiceIndex < tokenList.length) ? tokenList[choiceIndex] : null;
};

const processAutoSwap = async (walletsList, proxies, tokenList, captchaToken) => {
    logger.info(null, `Starting Auto Swap for ${walletsList.length} wallet(s)`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            const supplies = await api.getSupplies();
            const ownedTokens = (supplies || []).filter(a => a && parseFloat(a.amount) > 0);

            if (!ownedTokens || ownedTokens.length === 0) {
                logger.warning(walletData.name, "No supplied assets found to swap");
                continue;
            }

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing swap ${i + 1}/${globalTransactionCount}`);
                try {
                    const fromTokenAsset = ownedTokens[Math.floor(Math.random() * ownedTokens.length)];
                    const fromToken = tokenList.find(t => t.symbol === fromTokenAsset.symbol);
                    if (!fromToken) continue;

                    let toToken;
                    do {
                        toToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                    } while (toToken.symbol === fromToken.symbol);

                    const fromAmount = getRandomAmount(0.001, 0.0015);
                    const toAmount = (fromAmount * parseFloat(fromToken.price)) / parseFloat(toToken.price || 1);

                    await api.swap(fromToken.symbol, toToken.symbol, fromAmount.toFixed(8), toAmount.toFixed(8));
                    logger.success(walletData.name, `Swapped ${fromAmount.toFixed(5)} ${fromToken.symbol} -> ${toAmount.toFixed(5)} ${toToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Swap failed: ${e.message}`);
                }
                await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processManualSwap = async (walletsList, proxies, tokenList, captchaToken) => {
    const fromToken = await displayAndSelectToken(tokenList, "Select token to swap FROM:");
    if (!fromToken) {
        logger.error(null, "Invalid 'from' token selection");
        return;
    }

    const toToken = await displayAndSelectToken(tokenList, "Select token to swap TO:");
    if (!toToken) {
        logger.error(null, "Invalid 'to' token selection");
        return;
    }

    if (fromToken.symbol === toToken.symbol) {
        logger.error(null, "Cannot swap to the same token");
        return;
    }

    const fromAmount = parseFloat(await question(`${colors.green}Amount of ${fromToken.symbol} to swap: ${colors.reset}`));
    if (isNaN(fromAmount) || fromAmount <= 0) {
        logger.error(null, "Invalid amount");
        return;
    }

    logger.info(null, `Starting Manual Swap for ${walletsList.length} wallet(s)`);
    logger.info(null, `Swap: ${fromAmount} ${fromToken.symbol} -> ${toToken.symbol}`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing swap ${i + 1}/${globalTransactionCount}`);
                try {
                    const toAmount = (fromAmount * parseFloat(fromToken.price)) / parseFloat(toToken.price || 1);
                    await api.swap(fromToken.symbol, toToken.symbol, fromAmount, toAmount.toFixed(8));
                    logger.success(walletData.name, `Swapped ${fromAmount} ${fromToken.symbol} -> ${toAmount.toFixed(5)} ${toToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Swap failed: ${e.message}`);
                }
                if (i < globalTransactionCount - 1) await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processSupply = async (walletsList, proxies, tokenList, captchaToken) => {
    const selectedToken = await displayAndSelectToken(tokenList, "Select a token to Supply:");
    if (!selectedToken) {
        logger.error(null, "Invalid token selection");
        return;
    }

    const amount = parseFloat(await question(`${colors.green}Amount of ${selectedToken.symbol} to supply: ${colors.reset}`));
    if (isNaN(amount) || amount <= 0) {
        logger.error(null, "Invalid amount");
        return;
    }

    logger.info(null, `Starting Supply for ${walletsList.length} wallet(s)`);
    logger.info(null, `Supply: ${amount} ${selectedToken.symbol}`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing supply ${i + 1}/${globalTransactionCount}`);
                try {
                    await api.supply(selectedToken.symbol, amount);
                    logger.success(walletData.name, `Supplied ${amount} ${selectedToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Supply failed: ${e.message}`);
                }
                if (i < globalTransactionCount - 1) await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processWithdraw = async (walletsList, proxies, tokenList, captchaToken) => {
    const selectedToken = await displayAndSelectToken(tokenList, "Select a token to Withdraw:");
    if (!selectedToken) {
        logger.error(null, "Invalid token selection");
        return;
    }

    const amount = parseFloat(await question(`${colors.green}Amount of ${selectedToken.symbol} to withdraw: ${colors.reset}`));
    if (isNaN(amount) || amount <= 0) {
        logger.error(null, "Invalid amount");
        return;
    }

    logger.info(null, `Starting Withdrawal for ${walletsList.length} wallet(s)`);
    logger.info(null, `Withdraw: ${amount} ${selectedToken.symbol}`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing withdrawal ${i + 1}/${globalTransactionCount}`);
                try {
                    await api.withdraw(selectedToken.symbol, amount);
                    logger.success(walletData.name, `Withdrew ${amount} ${selectedToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Withdrawal failed: ${e.message}`);
                }
                if (i < globalTransactionCount - 1) await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processBorrow = async (walletsList, proxies, tokenList, captchaToken) => {
    const selectedToken = await displayAndSelectToken(tokenList, "Select a token to Borrow:");
    if (!selectedToken) {
        logger.error(null, "Invalid token selection");
        return;
    }

    const amount = parseFloat(await question(`${colors.green}Amount of ${selectedToken.symbol} to borrow: ${colors.reset}`));
    if (isNaN(amount) || amount <= 0) {
        logger.error(null, "Invalid amount");
        return;
    }

    logger.info(null, `Starting Borrow for ${walletsList.length} wallet(s)`);
    logger.info(null, `Borrow: ${amount} ${selectedToken.symbol}`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing borrow ${i + 1}/${globalTransactionCount}`);
                try {
                    await api.borrow(selectedToken.symbol, amount);
                    logger.success(walletData.name, `Borrowed ${amount} ${selectedToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Borrow failed: ${e.message}`);
                }
                if (i < globalTransactionCount - 1) await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processRepay = async (walletsList, proxies, tokenList, captchaToken) => {
    const selectedToken = await displayAndSelectToken(tokenList, "Select a token to Repay:");
    if (!selectedToken) {
        logger.error(null, "Invalid token selection");
        return;
    }

    const amount = parseFloat(await question(`${colors.green}Amount of ${selectedToken.symbol} to repay: ${colors.reset}`));
    if (isNaN(amount) || amount <= 0) {
        logger.error(null, "Invalid amount");
        return;
    }

    logger.info(null, `Starting Repay for ${walletsList.length} wallet(s)`);
    logger.info(null, `Repay: ${amount} ${selectedToken.symbol}`);
    logger.info(null, `Transactions per wallet: ${globalTransactionCount}`);

    let proxyIndex = 0;
    for (const [index, walletData] of walletsList.entries()) {
        const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

        console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
        console.log(`${colors.yellow}Processing Wallet ${index + 1}/${walletsList.length}: ${walletData.name}${colors.reset}`);
        console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

        const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
        try {
            await api.login(captchaToken);
            await displayWalletInfo(api, walletData.name);

            for (let i = 0; i < globalTransactionCount; i++) {
                logger.process(walletData.name, `Executing repay ${i + 1}/${globalTransactionCount}`);
                try {
                    await api.repay(selectedToken.symbol, amount);
                    logger.success(walletData.name, `Repaid ${amount} ${selectedToken.symbol}`);
                } catch (e) {
                    logger.error(walletData.name, `Repay failed: ${e.message}`);
                }
                if (i < globalTransactionCount - 1) await randomDelay();
            }
        } catch (error) {
            logger.error(walletData.name, `Could not process wallet: ${error.message}`);
        }
        await sleep(3000);
    }
};

const processAutoAll = async (walletsList, proxies, tokenList, captchaToken) => {
    logger.info(null, `Starting Auto All for ${walletsList.length} wallet(s)`);
    logger.info(null, `This will run daily check-in and randomized operations`);

    while (true) {
        // Shuffle wallets for random order
        const shuffledWallets = shuffleArray([...walletsList]);
        logger.info(null, `Randomized wallet order for this cycle`);

        let proxyIndex = 0;
        for (const [index, walletData] of shuffledWallets.entries()) {
            const proxy = proxies.length > 0 ? proxies[proxyIndex++ % proxies.length] : null;

            console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
            console.log(`${colors.yellow}Processing Wallet ${index + 1}/${shuffledWallets.length}: ${walletData.name}${colors.reset}`);
            console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);

            const api = new BlockStreetAPI(walletData.wallet, walletData.name, proxy);
            try {
                await api.login(captchaToken);
                await displayWalletInfo(api, walletData.name);

                // Define all possible actions
                const actions = [
                    {
                        name: 'Daily Share',
                        fn: async () => {
                            logger.process(walletData.name, "Checking in (Daily Share)...");
                            try {
                                await api.share();
                                logger.success(walletData.name, "Daily share complete");
                            } catch (e) {
                                logger.warning(walletData.name, "Daily share failed or already done");
                            }
                        }
                    },
                    {
                        name: 'Random Swaps',
                        fn: async () => {
                            let supplies = [];
                            try { supplies = await api.getSupplies(); } catch (e) { }
                            const ownedTokens = (supplies || []).filter(a => a && parseFloat(a.amount) > 0);

                            if (ownedTokens.length > 0) {
                                // Randomize number of swaps between 1 and 5
                                const swapCount = Math.floor(getRandomAmount(1, 5));
                                logger.process(walletData.name, `Executing ${swapCount} random swaps...`);

                                for (let j = 0; j < swapCount; j++) {
                                    try {
                                        const fromTokenAsset = ownedTokens[Math.floor(Math.random() * ownedTokens.length)];
                                        const fromToken = tokenList.find(t => t.symbol === fromTokenAsset.symbol);
                                        if (!fromToken) continue;

                                        let toToken;
                                        do {
                                            toToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                                        } while (toToken.symbol === fromToken.symbol);

                                        const fromAmount = getRandomAmount(0.001, 0.0015);
                                        const toAmount = (fromAmount * parseFloat(fromToken.price)) / parseFloat(toToken.price || 1);

                                        await api.swap(fromToken.symbol, toToken.symbol, fromAmount.toFixed(8), toAmount.toFixed(8));
                                        logger.success(walletData.name, `Swap ${j + 1}/${swapCount}: ${fromAmount.toFixed(5)} ${fromToken.symbol} -> ${toAmount.toFixed(5)} ${toToken.symbol}`);
                                    } catch (e) {
                                        logger.error(walletData.name, `Swap failed: ${e.message}`);
                                    }
                                    await randomDelay(5000, 15000); // Random delay between swaps
                                }
                            } else {
                                logger.warning(walletData.name, "No assets to swap, skipping...");
                            }
                        }
                    },
                    {
                        name: 'Supply',
                        fn: async () => {
                            const count = Math.floor(getRandomAmount(1, 3));
                            logger.process(walletData.name, `Executing ${count} supplies...`);
                            for (let j = 0; j < count; j++) {
                                try {
                                    const randomToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                                    const amount = getRandomAmount(0.001, 0.0015);
                                    await api.supply(randomToken.symbol, amount.toFixed(8));
                                    logger.success(walletData.name, `Supplied ${amount.toFixed(5)} ${randomToken.symbol}`);
                                } catch (e) { logger.error(walletData.name, `Supply failed: ${e.message}`); }
                                await randomDelay(5000, 15000);
                            }
                        }
                    },
                    {
                        name: 'Withdraw',
                        fn: async () => {
                            const count = Math.floor(getRandomAmount(1, 3));
                            logger.process(walletData.name, `Executing ${count} withdrawals...`);
                            for (let j = 0; j < count; j++) {
                                try {
                                    const randomToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                                    const amount = getRandomAmount(0.001, 0.0015);
                                    await api.withdraw(randomToken.symbol, amount.toFixed(8));
                                    logger.success(walletData.name, `Withdrew ${amount.toFixed(5)} ${randomToken.symbol}`);
                                } catch (e) { logger.error(walletData.name, `Withdrawal failed: ${e.message}`); }
                                await randomDelay(5000, 15000);
                            }
                        }
                    },
                    {
                        name: 'Borrow',
                        fn: async () => {
                            const count = Math.floor(getRandomAmount(1, 3));
                            logger.process(walletData.name, `Executing ${count} borrows...`);
                            for (let j = 0; j < count; j++) {
                                try {
                                    const randomToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                                    const amount = getRandomAmount(0.001, 0.0015);
                                    await api.borrow(randomToken.symbol, amount.toFixed(8));
                                    logger.success(walletData.name, `Borrowed ${amount.toFixed(5)} ${randomToken.symbol}`);
                                } catch (e) { logger.error(walletData.name, `Borrow failed: ${e.message}`); }
                                await randomDelay(5000, 15000);
                            }
                        }
                    },
                    {
                        name: 'Repay',
                        fn: async () => {
                            const count = Math.floor(getRandomAmount(1, 3));
                            logger.process(walletData.name, `Executing ${count} repayments...`);
                            for (let j = 0; j < count; j++) {
                                try {
                                    const randomToken = tokenList[Math.floor(Math.random() * tokenList.length)];
                                    const amount = getRandomAmount(0.001, 0.0015);
                                    await api.repay(randomToken.symbol, amount.toFixed(8));
                                    logger.success(walletData.name, `Repaid ${amount.toFixed(5)} ${randomToken.symbol}`);
                                } catch (e) { logger.error(walletData.name, `Repay failed: ${e.message}`); }
                                await randomDelay(5000, 15000);
                            }
                        }
                    }
                ];

                // Shuffle actions
                const shuffledActions = shuffleArray(actions);

                for (const action of shuffledActions) {
                    // Random probability to skip this action (20% chance)
                    if (shouldSkip(0.2)) {
                        logger.warning(walletData.name, `Skipping ${action.name} action (Random choice)`);
                        continue;
                    }

                    await action.fn();
                    // Random delay between actions
                    const delay = getRandomAmount(10000, 30000);
                    logger.info(walletData.name, `Sleeping for ${(delay / 1000).toFixed(1)}s before next action...`);
                    await sleep(delay);
                }

                logger.success(walletData.name, "All scheduled operations completed for this wallet");

            } catch (error) {
                logger.error(walletData.name, `Could not process wallet: ${error.message}`);
            }

            // Random delay between wallets
            const walletWait = getRandomAmount(30000, 90000); // 30s to 90s
            logger.info(null, `Waiting ${(walletWait / 1000).toFixed(1)}s before next wallet...`);
            await sleep(walletWait);
        }

        logger.success(null, "Cycle completed for all wallets");
        logger.info(null, "Waiting 24 hours for next run...");
        await countdown(24 * 60 * 60);
    }
};

const setTransactionCount = async () => {
    console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
    console.log(`${colors.yellow}SET TRANSACTION COUNT${colors.reset}`);
    console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}`);
    console.log(`${colors.white}Current transaction count: ${colors.green}${globalTransactionCount}${colors.reset}`);

    const newCount = await question(`${colors.green}Enter new transaction count (1-100): ${colors.reset}`);
    const count = parseInt(newCount, 10);

    if (isNaN(count) || count < 1 || count > 100) {
        logger.error(null, "Invalid transaction count. Must be between 1 and 100");
        return;
    }

    globalTransactionCount = count;
    logger.success(null, `Transaction count updated to: ${globalTransactionCount}`);
};

const main = async () => {
    clearTerminal();
    displayBanner();

    // Load wallets from pv.txt only
    const walletsList = loadWalletsFromFile();

    if (walletsList.length === 0) {
        logger.error(null, 'No valid wallets found in pv.txt. Exiting.');
        logger.info(null, 'Please create pv.txt with format: privatekey:name');
        closeRl();
        return;
    }

    const proxies = readAndParseProxies('proxies.txt');
    if (proxies.length > 0) {
        logger.success(null, `${proxies.length} valid proxies loaded`);
    } else {
        logger.warning(null, "No proxies loaded. Running without proxy");
    }

    logger.success(null, `Total ${walletsList.length} wallet(s) loaded`);

    console.log(`\n${colors.cyan}------------------------------------------------------------${colors.reset}`);
    console.log(`${colors.yellow}LOADED WALLETS${colors.reset}`);
    console.log(`------------------------------------------------------------${colors.reset}`);
    walletsList.forEach((walletData, index) => {
        console.log(`${colors.green}[${index + 1}]${colors.reset} ${colors.white}${walletData.name}${colors.reset}`);
    });
    console.log(`${colors.cyan}------------------------------------------------------------${colors.reset}\n`);

    // Load captcha key from key.txt
    const captchaApiKey = getCaptchaKey();
    if (!captchaApiKey) {
        logger.error(null, 'Cannot proceed without Captcha API key');
        closeRl();
        return;
    }

    let sessionCaptchaToken;
    try {
        sessionCaptchaToken = await solveTurnstile(
            captchaApiKey,
            '0x4AAAAAABpfyUqunlqwRBYN',
            'https://blockstreet.money/dashboard'
        );
        if (!sessionCaptchaToken) throw new Error("Failed to solve the initial captcha");
    } catch (error) {
        logger.error(null, `Could not solve initial captcha: ${error.message}`);
        closeRl();
        return;
    }

    let tokenList = [];
    try {
        const firstApi = new BlockStreetAPI(walletsList[0].wallet, walletsList[0].name, proxies.length > 0 ? proxies[0] : null);
        await firstApi.login(sessionCaptchaToken);
        logger.success(null, "Initial login successful");

        logger.process(null, "Fetching token list...");
        tokenList = await firstApi.getTokenList();
        logger.success(null, `Token list fetched: ${tokenList.length} tokens available`);

        logger.process(null, "Checking-in (Daily Share)...");
        try {
            await firstApi.share();
            logger.success(null, "Daily share complete");
        } catch (e) {
            logger.warning(null, "Daily share failed or already done");
        }

        await displayWalletInfo(firstApi, walletsList[0].name);
    } catch (error) {
        logger.error(null, `Initial setup failed: ${error.message}`);
        closeRl();
        return;
    }

    while (true) {
        displayMenu();
        console.log(`${colors.white}Current Transaction Count: ${colors.green}${globalTransactionCount}${colors.reset}`);
        const choice = await question(`${colors.green}Select option (1-9): ${colors.reset}`);

        switch (choice) {
            case '1':
                await processAutoSwap(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '2':
                await processManualSwap(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '3':
                await processSupply(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '4':
                await processWithdraw(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;
            case '5':
                await processBorrow(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '6':
                await processRepay(walletsList, proxies, tokenList, sessionCaptchaToken);
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '7':
                await processAutoAll(walletsList, proxies, tokenList, sessionCaptchaToken);
                break;

            case '8':
                await setTransactionCount();
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;

            case '9':
                logger.info(null, 'Exiting BlockStreet Bot...');
                closeRl();
                return;

            default:
                logger.error(null, 'Invalid option selected. Please choose between 1-9');
                await question(`\n${colors.yellow}Press Enter to continue...${colors.reset}`);
                break;
        }
        clearTerminal();
        displayBanner();
    }
};

// Handle uncaught errors
process.on('uncaughtException', (error) => {
    logger.error(null, `Uncaught Exception: ${error.message}`);
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    logger.error(null, `Unhandled Rejection at: ${promise}, reason: ${reason}`);
});

// Start the application
main().catch(error => {
    logger.error(null, `Fatal error in main: ${error.message}`);
    closeRl();
});
