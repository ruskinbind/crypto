import { ethers } from 'ethers';
import fetch from 'node-fetch';
import fs from 'fs';
import readline from 'readline';
import { HttpsProxyAgent } from 'https-proxy-agent';

// ============================================
// CONFIGURATION
// ============================================

const WRAP_PERCENT = 1; // 1% of balance

const NETWORKS = {
    SEPOLIA: {
        name: 'Sepolia',
        rpcUrl: 'https://sepolia.drpc.org',
        chainId: 11155111,
        explorer: 'https://sepolia.etherscan.io',
        faucetUrl: 'https://faucet.fluton.io',
        tokens: {
            USDC: '0x24827f35B1a04c66009adBb207D0415250Fd16da',
            USDT: '0xEDb85a5c17135B82966B686cCC9C28F42078f3E0',
            DAI: '0x6a978e705f6c3104992cb72714E5eDa41a96E928',
            UNI: '0x6a9380b81a176d68fE1b53f5B0FE283E7d83Db00',
            XFL: '0xE559bAfec0da476cd245Dd173f26e7b4b197Ca8b',
            AAVE: '0xBd0d0C12f9F13AEC9931ff4BC5A6c7f203aD3AaB'
        },
        wrappers: {
            eUSDC: '0xE4Ba3Eb60283A4955DD6Fb1BD1241d9AA8F6e9B3',
            eUSDT: '0x265283BB4C3b3f67Dd644609CaA99b4Cc825baE2',
            eDAI: '0xA80Fab3bDa70C9FB67f0Ee3d023C022F70a0Cd87',
            eUNI: '0x3C267B5D56B9eDc3e4CC49649528d43e7Edbd121',
            eXFL: '0x353550e34A09A7030F48DA00f7745547fadE6AFc',
            eAAVE: '0xd3D6B9dd47092Ffc217c7F1FD26AccD855562986'
        }
    },
    BASE_SEPOLIA: {
        name: 'Base Sepolia',
        rpcUrl: 'https://sepolia.base.org',
        chainId: 84532,
        explorer: 'https://sepolia.basescan.org',
        faucetUrl: null,
        tokens: {
            USDC: '0x86db0a9184bE890FC254948E414A982258cd1528',
            USDT: '0x2a1a79Ae4e6Af8a37566fAf91Fd818B1574d61D7',
            DAI: '0xEfaD718634B87C59fdc9eAb27F0AF0543c939dA5',
            UNI: '0xF8c2D4B68F93f3E332B30FD32a59d5C5e6358A83',
            XFL: '0xF620BCdCE0219cC11fa9ac89Ce6C807d810f0FB2',
            AAVE: '0xE25f846f653e4A14B9A175B6a9b6a061698D41a4'
        },
        wrappers: {
            eUSDC: '0xA7074187981A9Bea5DE4205e6B79FBD01F89B1B6',
            eUSDT: '0xb17ECAF7eDd1E4a1d568e755d6E54205731b50E1',
            eDAI: '0x4269a03167c961425733F5dd8408fD6A9b61B49C',
            eUNI: '0x189dC7eAAE2dEe0579652AEa4422e86CB3d8FDd8',
            eXFL: '0x02875082E053BAF0A3563E27cB26D846F1994199',
            eAAVE: '0x638C1654b1ea3B65677f1B295e763778a49A1532'
        }
    },
    ARBITRUM_SEPOLIA: {
        name: 'Arbitrum Sepolia',
        rpcUrl: 'https://sepolia-rollup.arbitrum.io/rpc',
        chainId: 421614,
        explorer: 'https://sepolia.arbiscan.io',
        faucetUrl: null,
        tokens: {
            USDC: '0xEc63750335f33117f3f7a43d96aa75235460df57',
            USDT: '0xf539C016a7b527621056893Cb05e061509B7cE40',
            DAI: '0xFEF1Cc0D465C561a77F76EF8cF6f562F09D460C8',
            UNI: '0xF41561BF42418B69791f026a97CF9e4F8BC95703',
            XFL: '0xF620BCdCE0219cC11fa9ac89Ce6C807d810f0FB2',
            AAVE: '0xE25f846f653e4A14B9A175B6a9b6a061698D41a4'
        },
        wrappers: {
            eUSDC: '0x61255666E2D40F969902565EA3Ba9FaB8b32cD9A',
            eUSDT: '0xbaFcb71F4FCDa9fE3bf63daB1B40eC9A4AC2de60',
            eDAI: '0x2E09526C5fb096Fe4972513dc520256e3274b5dA',
            eUNI: '0xe7A73D4d6Cd7C69d7DA6CF96061c5Fac910a8E22',
            eXFL: '0x02875082E053BAF0A3563E27cB26D846F1994199',
            eAAVE: '0x638C1654b1ea3B65677f1B295e763778a49A1532'
        }
    }
};

// ABIs
const TOKEN_ABI = [
    'function decimals() view returns (uint8)',
    'function balanceOf(address) view returns (uint256)',
    'function allowance(address,address) view returns (uint256)',
    'function approve(address,uint256) external returns (bool)',
    'function symbol() view returns (string)'
];

const WRAP_ABI = ['function wrap(address to, uint256 amount) external'];

// HTTP Headers for faucet
const HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://testnet.fluton.io',
    'Referer': 'https://testnet.fluton.io/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
};

// ============================================
// GLOBAL VARIABLES
// ============================================

let PRIVATE_KEYS = [];
let PROXIES = [];

// ============================================
// UTILITY FUNCTIONS
// ============================================

function loadPrivateKeys() {
    try {
        if (!fs.existsSync('pv.txt')) {
            console.log('\x1b[31m[ERROR] pv.txt file not found!\x1b[0m');
            console.log('\x1b[33m[INFO] Create pv.txt file and add your private keys (one per line)\x1b[0m');
            process.exit(1);
        }
        
        const content = fs.readFileSync('pv.txt', 'utf8').trim();
        if (!content) {
            console.log('\x1b[31m[ERROR] pv.txt is empty!\x1b[0m');
            process.exit(1);
        }
        
        const keys = content.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'))
            .map(key => {
                key = key.startsWith('0x') ? key : `0x${key}`;
                if (!/^0x[a-fA-F0-9]{64}$/.test(key)) {
                    console.log('\x1b[31m[ERROR] Invalid private key format found!\x1b[0m');
                    process.exit(1);
                }
                return key;
            });
        
        if (keys.length === 0) {
            console.log('\x1b[31m[ERROR] No valid private keys found!\x1b[0m');
            process.exit(1);
        }
        
        return keys;
    } catch (err) {
        console.log('\x1b[31m[ERROR] Failed to read pv.txt:\x1b[0m', err.message);
        process.exit(1);
    }
}

function loadProxies() {
    try {
        if (!fs.existsSync('proxy.txt')) {
            console.log('\x1b[33m[INFO] proxy.txt not found - using direct connection\x1b[0m');
            return [];
        }
        
        const content = fs.readFileSync('proxy.txt', 'utf8').trim();
        if (!content) {
            console.log('\x1b[33m[INFO] proxy.txt is empty - using direct connection\x1b[0m');
            return [];
        }
        
        const proxies = content.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));
        
        if (proxies.length === 0) {
            console.log('\x1b[33m[INFO] No valid proxies found - using direct connection\x1b[0m');
            return [];
        }
        
        console.log(`\x1b[32m[INFO] Loaded ${proxies.length} proxies\x1b[0m`);
        return proxies;
    } catch (err) {
        console.log('\x1b[33m[WARNING] Failed to read proxy.txt - using direct connection\x1b[0m');
        return [];
    }
}

function getProxyForIndex(index) {
    if (PROXIES.length === 0) return null;
    return PROXIES[index % PROXIES.length];
}

function formatProxy(proxy) {
    if (!proxy) return null;
    
    if (proxy.startsWith('http://') || proxy.startsWith('https://')) {
        return proxy;
    }
    
    const parts = proxy.split(':');
    if (parts.length === 2) {
        return `http://${parts[0]}:${parts[1]}`;
    } else if (parts.length === 4) {
        return `http://${parts[2]}:${parts[3]}@${parts[0]}:${parts[1]}`;
    }
    
    return `http://${proxy}`;
}

function createFetchWithProxy(proxy) {
    if (!proxy) {
        return fetch;
    }
    
    const formattedProxy = formatProxy(proxy);
    const agent = new HttpsProxyAgent(formattedProxy);
    
    return (url, options = {}) => {
        return fetch(url, { ...options, agent });
    };
}

function clearScreen() {
    console.clear();
}

function displayBanner() {
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('\x1b[1m\x1b[33m              FLUTON TESTNET BOT\x1b[0m');
    console.log('\x1b[1m\x1b[32m           Created by Kazuha VIP ONLY \x1b[0m');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('');
}

function displayAccountsInfo() {
    console.log('\x1b[1m\x1b[36m[ACCOUNTS LOADED]\x1b[0m');
    console.log(`\x1b[32m   Total Accounts: ${PRIVATE_KEYS.length}\x1b[0m`);
    console.log(`\x1b[32m   Proxies: ${PROXIES.length > 0 ? PROXIES.length : 'Direct Connection'}\x1b[0m`);
    console.log('');
}

function displayMainMenu() {
    console.log('\x1b[1m\x1b[36m[MAIN MENU]\x1b[0m');
    console.log('');
    console.log('\x1b[36m' + '-'.repeat(60) + '\x1b[0m');
    console.log('\x1b[33m  [1]\x1b[0m Claim Faucet (Sepolia Only)');
    console.log('\x1b[33m  [2]\x1b[0m Shield Token');
    console.log('\x1b[33m  [3]\x1b[0m Exit');
    console.log('');
    console.log('\x1b[36m' + '-'.repeat(60) + '\x1b[0m');
}

function displayNetworkMenu() {
    console.log('\x1b[1m\x1b[36m[SELECT NETWORK]\x1b[0m');
    console.log('');
    console.log('\x1b[33m  [1]\x1b[0m Sepolia');
    console.log('\x1b[33m  [2]\x1b[0m Base Sepolia');
    console.log('\x1b[33m  [3]\x1b[0m Arbitrum Sepolia');
    console.log('');
    console.log('\x1b[36m' + '-'.repeat(60) + '\x1b[0m');
}

function displayTokenMenu() {
    console.log('\x1b[1m\x1b[36m[SELECT TOKEN TO SHIELD]\x1b[0m');
    console.log('');
    console.log('\x1b[33m  [1]\x1b[0m USDC');
    console.log('\x1b[33m  [2]\x1b[0m USDT');
    console.log('\x1b[33m  [3]\x1b[0m DAI');
    console.log('\x1b[33m  [4]\x1b[0m UNI');
    console.log('\x1b[33m  [5]\x1b[0m XFL');
    console.log('\x1b[33m  [6]\x1b[0m AAVE');
    console.log('\x1b[33m  [7]\x1b[0m All Tokens');
    console.log('');
    console.log('\x1b[36m' + '-'.repeat(60) + '\x1b[0m');
}

function logInfo(msg) {
    console.log('\x1b[36m[INFO]\x1b[0m ' + msg);
}

function logSuccess(msg) {
    console.log('\x1b[32m[SUCCESS]\x1b[0m ' + msg);
}

function logError(msg) {
    console.log('\x1b[31m[ERROR]\x1b[0m ' + msg);
}

function logWarning(msg) {
    console.log('\x1b[33m[WARNING]\x1b[0m ' + msg);
}

function logProcess(msg) {
    console.log('\x1b[35m[PROCESS]\x1b[0m ' + msg);
}

function logAccount(index, total, address) {
    console.log('');
    console.log('\x1b[36m' + '═'.repeat(60) + '\x1b[0m');
    console.log(`\x1b[1m\x1b[33m[ACCOUNT ${index}/${total}]\x1b[0m`);
    console.log(`\x1b[32m   Address: ${address}\x1b[0m`);
    console.log('\x1b[36m' + '═'.repeat(60) + '\x1b[0m');
}

function logTx(explorer, txHash, blockNumber) {
    console.log('');
    console.log('\x1b[32m   ✓ Transaction Hash:\x1b[0m ' + txHash);
    console.log('\x1b[32m   ✓ Block Number:\x1b[0m ' + blockNumber);
    console.log('\x1b[32m   ✓ Explorer URL:\x1b[0m ' + explorer + '/tx/' + txHash);
    console.log('');
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function shortenAddress(address) {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
}

// ============================================
// CLI INPUT
// ============================================

function createReadlineInterface() {
    return readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
}

async function askQuestion(rl, question) {
    return new Promise(resolve => {
        rl.question(question, answer => {
            resolve(answer.trim());
        });
    });
}

async function waitForEnter(rl) {
    await askQuestion(rl, '\n\x1b[36mPress ENTER to continue...\x1b[0m');
}

// ============================================
// FAUCET FUNCTIONS
// ============================================

async function canRequestFunds(address, faucetUrl, fetchFn) {
    const url = `${faucetUrl}/can-request-funds?address=${encodeURIComponent(address)}`;
    try {
        const res = await fetchFn(url, { headers: HEADERS });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (!data.canRequest) {
            const nextClaimMs = data.nextClaim;
            const nowMs = Date.now();
            const waitMs = nextClaimMs - nowMs;

            if (waitMs > 0) {
                const waitSec = Math.ceil(waitMs / 1000);
                const hours = Math.floor(waitSec / 3600);
                const mins = Math.floor((waitSec % 3600) / 60);
                const secs = waitSec % 60;
                return { canRequest: false, cooldown: `${hours}h ${mins}m ${secs}s` };
            }
        }
        return { canRequest: true, cooldown: null };
    } catch (err) {
        return { canRequest: false, cooldown: null, error: err.message };
    }
}

async function claimFaucetForAccount(address, proxy, accountIndex, totalAccounts) {
    const network = NETWORKS.SEPOLIA;
    const fetchFn = createFetchWithProxy(proxy);
    
    logProcess(`[${accountIndex}/${totalAccounts}] Checking faucet for ${shortenAddress(address)}...`);
    
    if (proxy) {
        logInfo(`Using proxy: ${proxy.substring(0, 30)}...`);
    }

    const checkResult = await canRequestFunds(address, network.faucetUrl, fetchFn);
    
    if (checkResult.error) {
        logError(`Failed to check cooldown: ${checkResult.error}`);
        return { success: false, address, reason: 'check_failed' };
    }
    
    if (!checkResult.canRequest) {
        logWarning(`Cooldown active: ${checkResult.cooldown}`);
        return { success: false, address, reason: 'cooldown', cooldown: checkResult.cooldown };
    }

    logProcess('Claiming faucet...');
    const url = `${network.faucetUrl}/request-funds`;
    const body = JSON.stringify({ address });

    try {
        const res = await fetchFn(url, {
            method: 'POST',
            headers: HEADERS,
            body,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.success) {
            logSuccess(`Faucet claimed for ${shortenAddress(address)}!`);
            for (const hash of data.hashes || []) {
                console.log('\x1b[32m   ✓ TX:\x1b[0m ' + network.explorer + '/tx/' + hash);
            }
            return { success: true, address, hashes: data.hashes };
        } else {
            logError('Claim failed: ' + JSON.stringify(data));
            return { success: false, address, reason: 'claim_failed' };
        }
    } catch (err) {
        logError('Faucet error: ' + err.message);
        return { success: false, address, reason: 'error', error: err.message };
    }
}

async function claimFaucetAllAccounts() {
    console.log('');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('\x1b[1m\x1b[33m           FAUCET CLAIM - ALL ACCOUNTS\x1b[0m');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('');
    
    logInfo(`Total Accounts: ${PRIVATE_KEYS.length}`);
    logInfo(`Network: Sepolia`);
    console.log('');
    
    const results = [];
    
    for (let i = 0; i < PRIVATE_KEYS.length; i++) {
        const wallet = new ethers.Wallet(PRIVATE_KEYS[i]);
        const proxy = getProxyForIndex(i);
        
        console.log('\x1b[36m' + '-'.repeat(60) + '\x1b[0m');
        
        const result = await claimFaucetForAccount(wallet.address, proxy, i + 1, PRIVATE_KEYS.length);
        results.push(result);
        
        // Delay between accounts
        if (i < PRIVATE_KEYS.length - 1) {
            logInfo('Waiting 3 seconds before next account...');
            await delay(3000);
        }
    }
    
    // Summary
    console.log('');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('\x1b[1m\x1b[33m                    SUMMARY\x1b[0m');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    
    const successful = results.filter(r => r.success);
    const cooldown = results.filter(r => r.reason === 'cooldown');
    const failed = results.filter(r => !r.success && r.reason !== 'cooldown');
    
    console.log('');
    logSuccess(`Claimed: ${successful.length}/${PRIVATE_KEYS.length}`);
    if (cooldown.length > 0) {
        logWarning(`Cooldown: ${cooldown.length} accounts`);
    }
    if (failed.length > 0) {
        logError(`Failed: ${failed.length} accounts`);
    }
    
    console.log('');
    console.log('\x1b[1m\x1b[36m[DETAILS]\x1b[0m');
    results.forEach((r, i) => {
        const status = r.success ? '\x1b[32m✓ CLAIMED\x1b[0m' : 
                       r.reason === 'cooldown' ? `\x1b[33m⏳ COOLDOWN (${r.cooldown})\x1b[0m` : 
                       '\x1b[31m✗ FAILED\x1b[0m';
        console.log(`   [${i + 1}] ${shortenAddress(r.address)} - ${status}`);
    });
}

// ============================================
// SHIELD (WRAP) FUNCTIONS
// ============================================

async function shieldToken(wallet, network, tokenSymbol, iterations, accountIndex, totalAccounts) {
    const tokenAddress = network.tokens[tokenSymbol];
    const wrapperSymbol = `e${tokenSymbol}`;
    const wrapperAddress = network.wrappers[wrapperSymbol];

    if (!tokenAddress || !wrapperAddress) {
        logError(`Token ${tokenSymbol} not found on ${network.name}`);
        return false;
    }

    logProcess(`Shielding ${tokenSymbol} -> ${wrapperSymbol}`);

    const tokenContract = new ethers.Contract(tokenAddress, TOKEN_ABI, wallet);
    const wrapContract = new ethers.Contract(wrapperAddress, WRAP_ABI, wallet);

    let successCount = 0;

    for (let i = 1; i <= iterations; i++) {
        logProcess(`[Iteration ${i}/${iterations}] Processing ${tokenSymbol}...`);

        try {
            let decimals;
            try {
                decimals = Number(await tokenContract.decimals());
            } catch (err) {
                logError(`Cannot read decimals for ${tokenSymbol}: ${err.message}`);
                continue;
            }

            let balance;
            try {
                balance = await tokenContract.balanceOf(wallet.address);
            } catch (err) {
                logError(`Cannot read balance for ${tokenSymbol}: ${err.message}`);
                continue;
            }

            if (balance === 0n) {
                logWarning(`Skipping ${tokenSymbol}: zero balance`);
                return false;
            }

            const amountInWei = (balance * BigInt(WRAP_PERCENT)) / 100n;

            if (amountInWei === 0n) {
                logWarning(`Skipping ${tokenSymbol}: amount too small`);
                return false;
            }

            const humanBalance = ethers.formatUnits(balance, decimals);
            const humanAmount = ethers.formatUnits(amountInWei, decimals);

            logInfo(`Balance: ${humanBalance} ${tokenSymbol}`);
            logInfo(`Shielding: ${humanAmount} ${tokenSymbol} (${WRAP_PERCENT}%)`);

            let currentAllowance;
            try {
                currentAllowance = await tokenContract.allowance(wallet.address, wrapperAddress);
            } catch (err) {
                logError(`Cannot check allowance: ${err.message}`);
                continue;
            }

            if (currentAllowance < amountInWei) {
                logProcess('Approving tokens...');
                try {
                    const approveTx = await tokenContract.approve(wrapperAddress, ethers.MaxUint256, {
                        gasLimit: 100000
                    });
                    const approveReceipt = await approveTx.wait();
                    logSuccess('Approved');
                    logTx(network.explorer, approveReceipt.hash, approveReceipt.blockNumber);
                    await delay(2000);
                } catch (err) {
                    logError(`Approval failed: ${err.message}`);
                    continue;
                }
            }

            logProcess('Shielding tokens...');
            try {
                const wrapTx = await wrapContract.wrap(wallet.address, amountInWei, {
                    gasLimit: 500000
                });
                const wrapReceipt = await wrapTx.wait();
                
                if (wrapReceipt.status === 1) {
                    logSuccess(`Shielded ${tokenSymbol} -> ${wrapperSymbol}`);
                    logTx(network.explorer, wrapReceipt.hash, wrapReceipt.blockNumber);
                    successCount++;
                } else {
                    logError(`Transaction failed for ${tokenSymbol}`);
                }
            } catch (err) {
                logError(`Shield failed: ${err.message}`);
                continue;
            }

            if (i < iterations) {
                logInfo('Waiting 3 seconds...');
                await delay(3000);
            }

        } catch (err) {
            logError(`Failed to shield ${tokenSymbol}: ${err.message}`);
        }
    }

    return successCount > 0;
}

async function shieldAllTokens(wallet, network, iterations, accountIndex, totalAccounts) {
    const tokenList = ['USDC', 'USDT', 'DAI', 'UNI', 'XFL', 'AAVE'];
    
    let totalSuccess = 0;

    for (const tokenSymbol of tokenList) {
        console.log('\x1b[35m' + '─'.repeat(40) + '\x1b[0m');
        const result = await shieldToken(wallet, network, tokenSymbol, iterations, accountIndex, totalAccounts);
        if (result) totalSuccess++;
        
        await delay(2000);
    }

    return totalSuccess;
}

async function shieldForAllAccounts(network, selectedToken, iterations) {
    console.log('');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('\x1b[1m\x1b[33m           SHIELD TOKEN - ALL ACCOUNTS\x1b[0m');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('');
    
    logInfo(`Network: ${network.name}`);
    logInfo(`Token: ${selectedToken}`);
    logInfo(`Iterations: ${iterations}`);
    logInfo(`Total Accounts: ${PRIVATE_KEYS.length}`);
    console.log('');
    
    const results = [];
    
    for (let i = 0; i < PRIVATE_KEYS.length; i++) {
        const provider = new ethers.JsonRpcProvider(network.rpcUrl);
        const wallet = new ethers.Wallet(PRIVATE_KEYS[i], provider);
        
        logAccount(i + 1, PRIVATE_KEYS.length, wallet.address);
        
        // Show ETH balance
        try {
            const ethBalance = await provider.getBalance(wallet.address);
            logInfo(`ETH Balance: ${ethers.formatEther(ethBalance)} ETH`);
        } catch (err) {
            logWarning('Could not fetch ETH balance');
        }
        console.log('');
        
        let result;
        if (selectedToken === 'ALL') {
            const successCount = await shieldAllTokens(wallet, network, iterations, i + 1, PRIVATE_KEYS.length);
            result = { success: successCount > 0, address: wallet.address, tokensShielded: successCount };
        } else {
            const success = await shieldToken(wallet, network, selectedToken, iterations, i + 1, PRIVATE_KEYS.length);
            result = { success, address: wallet.address, token: selectedToken };
        }
        
        results.push(result);
        
        // Delay between accounts
        if (i < PRIVATE_KEYS.length - 1) {
            logInfo('Waiting 5 seconds before next account...');
            await delay(5000);
        }
    }
    
    // Summary
    console.log('');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    console.log('\x1b[1m\x1b[33m                    SUMMARY\x1b[0m');
    console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
    
    const successful = results.filter(r => r.success);
    
    console.log('');
    logSuccess(`Successful: ${successful.length}/${PRIVATE_KEYS.length} accounts`);
    
    console.log('');
    console.log('\x1b[1m\x1b[36m[DETAILS]\x1b[0m');
    results.forEach((r, i) => {
        const status = r.success ? '\x1b[32m✓ SUCCESS\x1b[0m' : '\x1b[31m✗ FAILED/SKIPPED\x1b[0m';
        const extra = r.tokensShielded !== undefined ? ` (${r.tokensShielded} tokens)` : '';
        console.log(`   [${i + 1}] ${shortenAddress(r.address)} - ${status}${extra}`);
    });
}

// ============================================
// MAIN FUNCTION
// ============================================

async function main() {
    clearScreen();
    displayBanner();

    // Load private keys
    logProcess('Loading private keys from pv.txt...');
    PRIVATE_KEYS = loadPrivateKeys();
    logSuccess(`Loaded ${PRIVATE_KEYS.length} private key(s)`);

    // Load proxies
    logProcess('Loading proxies from proxy.txt...');
    PROXIES = loadProxies();

    console.log('');
    displayAccountsInfo();

    const rl = createReadlineInterface();

    let running = true;
    while (running) {
        displayMainMenu();

        const choice = await askQuestion(rl, '\x1b[1m\x1b[33mSelect option [1-3]: \x1b[0m');

        console.log('');

        switch (choice) {
            case '1': {
                // Claim Faucet - All Accounts (auto one by one)
                await claimFaucetAllAccounts();
                await waitForEnter(rl);
                clearScreen();
                displayBanner();
                displayAccountsInfo();
                break;
            }

            case '2': {
                // Shield Token - All Accounts (auto one by one)
                clearScreen();
                displayBanner();
                displayNetworkMenu();
                
                const networkChoice = await askQuestion(rl, '\x1b[1m\x1b[33mSelect network [1-3]: \x1b[0m');
                
                let selectedNetwork;
                switch (networkChoice) {
                    case '1':
                        selectedNetwork = NETWORKS.SEPOLIA;
                        break;
                    case '2':
                        selectedNetwork = NETWORKS.BASE_SEPOLIA;
                        break;
                    case '3':
                        selectedNetwork = NETWORKS.ARBITRUM_SEPOLIA;
                        break;
                    default:
                        logError('Invalid network selection!');
                        await waitForEnter(rl);
                        clearScreen();
                        displayBanner();
                        displayAccountsInfo();
                        continue;
                }

                console.log('');
                clearScreen();
                displayBanner();
                logInfo(`Selected Network: ${selectedNetwork.name}`);
                console.log('');
                displayTokenMenu();

                const tokenChoice = await askQuestion(rl, '\x1b[1m\x1b[33mSelect token [1-7]: \x1b[0m');
                
                let selectedToken;
                switch (tokenChoice) {
                    case '1':
                        selectedToken = 'USDC';
                        break;
                    case '2':
                        selectedToken = 'USDT';
                        break;
                    case '3':
                        selectedToken = 'DAI';
                        break;
                    case '4':
                        selectedToken = 'UNI';
                        break;
                    case '5':
                        selectedToken = 'XFL';
                        break;
                    case '6':
                        selectedToken = 'AAVE';
                        break;
                    case '7':
                        selectedToken = 'ALL';
                        break;
                    default:
                        logError('Invalid token selection!');
                        await waitForEnter(rl);
                        clearScreen();
                        displayBanner();
                        displayAccountsInfo();
                        continue;
                }

                console.log('');
                const iterationsInput = await askQuestion(rl, '\x1b[1m\x1b[33mHow many iterations per token? \x1b[0m');
                const iterations = parseInt(iterationsInput) || 1;

                await shieldForAllAccounts(selectedNetwork, selectedToken, iterations);

                await waitForEnter(rl);
                clearScreen();
                displayBanner();
                displayAccountsInfo();
                break;
            }

            case '3': {
                // Exit
                console.log('');
                console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
                console.log('\x1b[1m\x1b[33m      Thank you for using Fluton Bot!\x1b[0m');
                console.log('\x1b[1m\x1b[32m      Created by Kazuha\x1b[0m');
                console.log('\x1b[36m' + '='.repeat(60) + '\x1b[0m');
                running = false;
                break;
            }

            default:
                logError('Invalid option! Please select 1-3');
                await waitForEnter(rl);
                clearScreen();
                displayBanner();
                displayAccountsInfo();
        }
    }

    rl.close();
    process.exit(0);
}

// ============================================
// RUN
// ============================================

main().catch(err => {
    console.log('\x1b[31m[FATAL ERROR]\x1b[0m ' + err.message);
    process.exit(1);
});