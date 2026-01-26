const fs = require('fs');
const axios = require('axios');
const { ethers } = require('ethers');
const readline = require('readline');
const { HttpsProxyAgent } = require('https-proxy-agent');

// ============================================
// CONFIGURATION
// ============================================
const CONFIG = {
    RPC_URL: 'https://testnet.riselabs.xyz',
    CHAIN_ID: 11155931,
    QUOTE_API: 'https://sugar-sdk-production.up.railway.app/quote',
    ROUTER_CONTRACT: '0x93f504193778ebe3cC7986D85E02502B46e616D7',
    SWAP_ROUTER: '0xA33BE72Bf5f5fA7B98c104cFB56cE83072d872dE',
    VOTING_ESCROW: '0xabF09819bE66582bE528659053ECc4ed42c9846d',
    BRIBE_VOTING_REWARD: '0xD1a194205205126f3DCb5988270212e42E7eEb7e',
    GAUGE_CONTRACT: '0x7ba79373295d83C9c58Fd9bB4034c54e4BD14239',
    WETH_ADDRESS: '0x4200000000000000000000000000000000000006',
    TOKEN_ADDRESS: '0x8A93d247134d91e0de6f96547cB0204e5BE8e5D8',
    IRS_TOKEN: '0x1467fD9f96982b0Cb3C130483C93Ff8C6677e7cb',
    USDT_TOKEN: '0x40918Ba7f132E0aCba2CE4de4c4baF9BD2D7D849',
    LP_TOKEN: '0x651D399C50BCbD64C7381455d62820789dd8C90B',
    SWAP_TOKEN: '0x1467fD9f96982b0Cb3C130483C93Ff8C6677e7cb',
    SWAP_AMOUNT: '10000000000000',
    LIQUIDITY_AMOUNT_ETH: '1000000000000',
    LIQUIDITY_AMOUNT_TOKEN: '6028',
    VOTE_LIQUIDITY_IRS: '100000000000000',
    VOTE_LIQUIDITY_USDT: '10005',
    LOCK_AMOUNT: '100000000000000',
    LOCK_DURATION: '31449600',
    INCENTIVE_AMOUNT: '100000000000000',
    SLIPPAGE: '0.5',
    PRIVATE_KEY_FILE: 'pv.txt',
    PROXY_FILE: 'proxy.txt',
    STEP_DELAY: 3000,
    EXPLORER_URL: 'https://explorer.testnet.riselabs.xyz',
    MAX_APPROVAL: '115792089237316195423570985008687907853269984665640564039457584007913129639935',
    RPC_TIMEOUT: 120000
};

// ============================================
// COLORED LOGGING SYSTEM
// ============================================
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    white: '\x1b[37m'
};

function log(message, type = 'INFO') {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    
    const colorMap = {
        INFO: colors.cyan,
        SUCCESS: colors.green,
        ERROR: colors.red,
        WARNING: colors.yellow,
        MENU: colors.magenta,
        TASK: colors.blue
    };
    
    const color = colorMap[type] || colors.white;
    console.log(`${colors.bright}${color}[${timestamp}] [${type}]${colors.reset} ${message}`);
}

function printLine(char = '=', color = 'cyan') {
    const line = char.repeat(70);
    const colorCode = colors[color] || colors.cyan;
    console.log(`${colors.bright}${colorCode}${line}${colors.reset}`);
}

function printHeader(title, color = 'cyan') {
    const colorCode = colors[color] || colors.cyan;
    printLine('=', color);
    console.log(`${colors.bright}${colorCode}${title.toUpperCase()}${colors.reset}`);
    printLine('=', color);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function readPrivateKey() {
    try {
        const privateKey = fs.readFileSync(CONFIG.PRIVATE_KEY_FILE, 'utf8').trim();
        if (!privateKey) {
            throw new Error('Private key file is empty');
        }
        log('Private key loaded successfully', 'SUCCESS');
        return privateKey;
    } catch (error) {
        log(`Failed to read private key: ${error.message}`, 'ERROR');
        process.exit(1);
    }
}

function readProxy() {
    try {
        if (!fs.existsSync(CONFIG.PROXY_FILE)) {
            log('No proxy file found, using direct connection', 'WARNING');
            return null;
        }
        const proxy = fs.readFileSync(CONFIG.PROXY_FILE, 'utf8').trim();
        if (!proxy) {
            log('Proxy file is empty, using direct connection', 'WARNING');
            return null;
        }
        log('Proxy loaded successfully', 'SUCCESS');
        return proxy;
    } catch (error) {
        log(`Failed to read proxy: ${error.message}`, 'WARNING');
        return null;
    }
}

function parseProxy(proxyString) {
    if (!proxyString) return null;
    
    try {
        if (proxyString.includes('@')) {
            return proxyString;
        } else if (proxyString.includes('://')) {
            return proxyString;
        } else {
            return `http://${proxyString}`;
        }
    } catch (error) {
        log(`Invalid proxy format: ${error.message}`, 'ERROR');
        return null;
    }
}

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================
// MENU INTERFACE
// ============================================
function displayMenu() {
    console.clear();
    printLine('=', 'magenta');
    console.log(`${colors.bright}${colors.magenta}           RISE TESTNET AUTO BOT V5.0${colors.reset}`);
    console.log(`${colors.bright}${colors.white}           CREATED BY KAZUHA | VIP ONLY${colors.reset}`);
    printLine('=', 'magenta');
    console.log('');
    console.log(`${colors.bright}${colors.cyan}  1.${colors.reset} Swap Tokens`);
    console.log(`${colors.bright}${colors.cyan}  2.${colors.reset} Add Liquidity (WETH/USDC)`);
    console.log(`${colors.bright}${colors.cyan}  3.${colors.reset} Add Liquidity (IRS/USDT)`);
    console.log(`${colors.bright}${colors.cyan}  4.${colors.reset} Create Vote Lock`);
    console.log(`${colors.bright}${colors.cyan}  5.${colors.reset} Add Incentive/Bribe`);
    console.log(`${colors.bright}${colors.yellow}  6.${colors.reset} AUTO MODE (All Tasks)`);
    console.log(`${colors.bright}${colors.red}  7.${colors.reset} Exit`);
    console.log('');
    printLine('=', 'magenta');
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function askQuestion(query) {
    return new Promise(resolve => rl.question(`${colors.bright}${colors.cyan}${query}${colors.reset}`, resolve));
}

// ============================================
// BLOCKCHAIN INTERACTION
// ============================================
class LiquidityBot {
    constructor() {
        this.privateKey = readPrivateKey();
        this.proxyUrl = parseProxy(readProxy());
        
        if (this.proxyUrl) {
            const fetchReq = new ethers.FetchRequest(CONFIG.RPC_URL);
            fetchReq.timeout = CONFIG.RPC_TIMEOUT;
            fetchReq.getUrlFunc = ethers.FetchRequest.createGetUrlFunc({
                agent: new HttpsProxyAgent(this.proxyUrl)
            });
            this.provider = new ethers.JsonRpcProvider(fetchReq, CONFIG.CHAIN_ID);
            log(`Using proxy: ${this.proxyUrl}`, 'SUCCESS');
        } else {
            const fetchReq = new ethers.FetchRequest(CONFIG.RPC_URL);
            fetchReq.timeout = CONFIG.RPC_TIMEOUT;
            this.provider = new ethers.JsonRpcProvider(fetchReq, CONFIG.CHAIN_ID);
            log('Using direct connection', 'INFO');
        }
        
        this.wallet = new ethers.Wallet(this.privateKey, this.provider);
        
        this.swapRouter = new ethers.Contract(
            CONFIG.SWAP_ROUTER,
            ['function execute(bytes commands, bytes[] inputs) payable'],
            this.wallet
        );
        
        this.liquidityRouter = new ethers.Contract(
            CONFIG.ROUTER_CONTRACT,
            [
                'function addLiquidity(address tokenA, address tokenB, bool stable, uint256 amountADesired, uint256 amountBDesired, uint256 amountAMin, uint256 amountBMin, address to, uint256 deadline) returns (uint256, uint256, uint256)'
            ],
            this.wallet
        );

        this.votingEscrow = new ethers.Contract(
            CONFIG.VOTING_ESCROW,
            [
                'function createLock(uint256 _value, uint256 _lockDuration) returns (uint256)'
            ],
            this.wallet
        );

        this.bribeReward = new ethers.Contract(
            CONFIG.BRIBE_VOTING_REWARD,
            [
                'function notifyRewardAmount(address token, uint256 amount)'
            ],
            this.wallet
        );

        this.gaugeContract = new ethers.Contract(
            CONFIG.GAUGE_CONTRACT,
            [
                'function deposit(uint256 _amount)',
                'function balanceOf(address account) view returns (uint256)'
            ],
            this.wallet
        );
        
        this.wethContract = new ethers.Contract(
            CONFIG.WETH_ADDRESS,
            [
                'function approve(address spender, uint256 amount) returns (bool)',
                'function allowance(address owner, address spender) view returns (uint256)',
                'function balanceOf(address owner) view returns (uint256)',
                'function deposit() payable',
                'function withdraw(uint256 amount)',
                'function transfer(address to, uint256 amount) returns (bool)'
            ],
            this.wallet
        );
        
        this.tokenContract = new ethers.Contract(
            CONFIG.TOKEN_ADDRESS,
            [
                'function approve(address spender, uint256 amount) returns (bool)',
                'function allowance(address owner, address spender) view returns (uint256)',
                'function balanceOf(address owner) view returns (uint256)',
                'function transfer(address to, uint256 amount) returns (bool)'
            ],
            this.wallet
        );

        this.irsContract = new ethers.Contract(
            CONFIG.IRS_TOKEN,
            [
                'function approve(address spender, uint256 amount) returns (bool)',
                'function allowance(address owner, address spender) view returns (uint256)',
                'function balanceOf(address owner) view returns (uint256)',
                'function transfer(address to, uint256 amount) returns (bool)'
            ],
            this.wallet
        );

        this.usdtContract = new ethers.Contract(
            CONFIG.USDT_TOKEN,
            [
                'function approve(address spender, uint256 amount) returns (bool)',
                'function allowance(address owner, address spender) view returns (uint256)',
                'function balanceOf(address owner) view returns (uint256)',
                'function transfer(address to, uint256 amount) returns (bool)'
            ],
            this.wallet
        );

        this.lpTokenContract = new ethers.Contract(
            CONFIG.LP_TOKEN,
            [
                'function approve(address spender, uint256 amount) returns (bool)',
                'function allowance(address owner, address spender) view returns (uint256)',
                'function balanceOf(address owner) view returns (uint256)'
            ],
            this.wallet
        );
    }

    async checkBalance() {
        try {
            const balance = await this.provider.getBalance(this.wallet.address);
            const wethBalance = await this.wethContract.balanceOf(this.wallet.address);
            const tokenBalance = await this.tokenContract.balanceOf(this.wallet.address);
            const irsBalance = await this.irsContract.balanceOf(this.wallet.address);
            const usdtBalance = await this.usdtContract.balanceOf(this.wallet.address);
            const lpBalance = await this.lpTokenContract.balanceOf(this.wallet.address);
            const gaugeBalance = await this.gaugeContract.balanceOf(this.wallet.address);
            
            printHeader('WALLET BALANCES', 'green');
            log(`Wallet Address: ${this.wallet.address}`, 'INFO');
            log(`ETH Balance: ${ethers.formatEther(balance)} ETH`, 'SUCCESS');
            log(`WETH Balance: ${ethers.formatEther(wethBalance)} WETH`, 'SUCCESS');
            log(`USDC Balance: ${tokenBalance.toString()}`, 'SUCCESS');
            log(`IRS Balance: ${ethers.formatEther(irsBalance)} IRS`, 'SUCCESS');
            log(`USDT Balance: ${usdtBalance.toString()}`, 'SUCCESS');
            log(`LP Token Balance: ${ethers.formatEther(lpBalance)} LP`, 'SUCCESS');
            log(`Staked in Gauge: ${ethers.formatEther(gaugeBalance)} LP`, 'SUCCESS');
            printLine('-', 'green');
            
            return balance;
        } catch (error) {
            log(`Failed to check balance: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async getSwapQuote() {
        try {
            log('Fetching swap quote...', 'TASK');
            
            const axiosConfig = {
                timeout: CONFIG.RPC_TIMEOUT
            };
            
            if (this.proxyUrl) {
                axiosConfig.httpsAgent = new HttpsProxyAgent(this.proxyUrl);
            }
            
            const response = await axios.get(CONFIG.QUOTE_API, {
                params: {
                    token_from: 'ETH',
                    token_to: CONFIG.SWAP_TOKEN,
                    amount: CONFIG.SWAP_AMOUNT,
                    slippage: CONFIG.SLIPPAGE
                },
                headers: {
                    'accept': '*/*',
                    'origin': 'https://www.icarus.finance',
                    'referer': 'https://www.icarus.finance/'
                },
                ...axiosConfig
            });

            log('Quote received successfully', 'SUCCESS');
            await delay(CONFIG.STEP_DELAY);
            return response.data;
        } catch (error) {
            log(`Failed to get quote: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async executeSwap(quoteData) {
        try {
            printHeader('EXECUTING SWAP TRANSACTION', 'yellow');
            
            const commands = quoteData.encoded_commands;
            const inputs = quoteData.pretty_encoded_inputs;

            log(`Amount In: ${ethers.formatEther(quoteData.amount_in)} ETH`, 'INFO');
            log(`Expected Out: ${ethers.formatUnits(quoteData.amount_out, 18)} IRS`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            const tx = await this.swapRouter.execute(
                commands,
                inputs,
                {
                    value: quoteData.amount_in,
                    gasLimit: 300000
                }
            );

            log(`Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('SWAP SUCCESSFUL', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                printLine('-', 'green');
                return receipt;
            } else {
                throw new Error('Transaction failed');
            }
        } catch (error) {
            log(`Swap failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async wrapETH(amount) {
        try {
            log('Wrapping ETH to WETH...', 'TASK');
            log(`Amount to wrap: ${ethers.formatEther(amount)} ETH`, 'INFO');
            await delay(CONFIG.STEP_DELAY);
            
            const tx = await this.wethContract.deposit({
                value: amount,
                gasLimit: 100000
            });
            
            log(`Wrap Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for wrap confirmation...', 'TASK');
            
            const receipt = await tx.wait();
            
            if (receipt.status === 1) {
                log('ETH wrapped to WETH successfully', 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                await delay(CONFIG.STEP_DELAY);
                return receipt;
            } else {
                throw new Error('WETH wrap failed');
            }
        } catch (error) {
            log(`Failed to wrap ETH: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async approveToken(tokenContract, spender, amount, tokenName) {
        try {
            log(`Checking ${tokenName} allowance...`, 'TASK');
            await delay(CONFIG.STEP_DELAY);
            
            const allowance = await tokenContract.allowance(this.wallet.address, spender);
            
            if (BigInt(allowance) < BigInt(amount)) {
                log(`Approving ${tokenName}...`, 'WARNING');
                await delay(CONFIG.STEP_DELAY);
                
                const tx = await tokenContract.approve(spender, CONFIG.MAX_APPROVAL, {
                    gasLimit: 100000
                });
                
                log(`Approval Hash: ${tx.hash}`, 'INFO');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
                log('Waiting for approval confirmation...', 'TASK');
                
                const receipt = await tx.wait();
                
                if (receipt.status === 1) {
                    log(`${tokenName} approved successfully`, 'SUCCESS');
                    log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                    log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                    await delay(CONFIG.STEP_DELAY);
                } else {
                    throw new Error(`${tokenName} approval failed`);
                }
            } else {
                log(`${tokenName} already approved`, 'SUCCESS');
                await delay(CONFIG.STEP_DELAY);
            }
        } catch (error) {
            log(`Failed to approve ${tokenName}: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async depositToGauge(lpAmount) {
        try {
            printHeader('DEPOSITING LP TO GAUGE (STAKING)', 'yellow');
            log(`LP Amount to stake: ${ethers.formatEther(lpAmount)}`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            // Step 1: Approve LP token for Gauge
            log('Step 1/2: Approving LP token for Gauge...', 'TASK');
            await this.approveToken(
                this.lpTokenContract,
                CONFIG.GAUGE_CONTRACT,
                lpAmount,
                'LP Token'
            );

            // Step 2: Deposit to Gauge
            log('Step 2/2: Depositing to Gauge...', 'WARNING');
            await delay(CONFIG.STEP_DELAY);

            const tx = await this.gaugeContract.deposit(lpAmount, {
                gasLimit: 200000
            });

            log(`Deposit Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for deposit confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('LP STAKED SUCCESSFULLY', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                printLine('-', 'green');
                return receipt;
            } else {
                throw new Error('Deposit failed');
            }
        } catch (error) {
            log(`Deposit to Gauge failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async addLiquidityWETH() {
        try {
            printHeader('ADDING LIQUIDITY (WETH/USDC)', 'yellow');
            await delay(CONFIG.STEP_DELAY);

            const amountWETH = CONFIG.LIQUIDITY_AMOUNT_ETH;
            const amountUSDC = CONFIG.LIQUIDITY_AMOUNT_TOKEN;
            const amountWETHMin = (BigInt(amountWETH) * 95n) / 100n;
            const amountUSDCMin = (BigInt(amountUSDC) * 95n) / 100n;
            const deadline = Math.floor(Date.now() / 1000) + 1200;

            const wethBalance = await this.wethContract.balanceOf(this.wallet.address);
            const usdcBalance = await this.tokenContract.balanceOf(this.wallet.address);
            
            log(`Current WETH Balance: ${ethers.formatEther(wethBalance)}`, 'INFO');
            log(`Current USDC Balance: ${usdcBalance.toString()}`, 'INFO');
            log(`Required WETH: ${ethers.formatEther(amountWETH)}`, 'INFO');
            log(`Required USDC: ${amountUSDC}`, 'INFO');
            
            // Step 1: Wrap ETH if needed
            if (BigInt(wethBalance) < BigInt(amountWETH)) {
                const neededWETH = BigInt(amountWETH) - BigInt(wethBalance);
                log(`Need to wrap ${ethers.formatEther(neededWETH)} ETH to WETH`, 'WARNING');
                log('Step 1/5: Wrapping ETH to WETH...', 'TASK');
                await this.wrapETH(neededWETH.toString());
                
                const newWethBalance = await this.wethContract.balanceOf(this.wallet.address);
                log(`New WETH Balance: ${ethers.formatEther(newWethBalance)}`, 'SUCCESS');
            } else {
                log('Step 1/5: Sufficient WETH balance', 'SUCCESS');
            }

            // Step 2: Check USDC
            if (BigInt(usdcBalance) < BigInt(amountUSDC)) {
                log(`Insufficient USDC balance! Need ${amountUSDC}, have ${usdcBalance}`, 'ERROR');
                throw new Error('Insufficient USDC balance');
            } else {
                log('Step 2/5: USDC balance check passed', 'SUCCESS');
            }

            // Step 3: Approve WETH
            log('Step 3/5: Approving WETH...', 'TASK');
            await this.approveToken(
                this.wethContract,
                CONFIG.ROUTER_CONTRACT,
                amountWETH,
                'WETH'
            );

            // Step 4: Approve USDC
            log('Step 4/5: Approving USDC...', 'TASK');
            await this.approveToken(
                this.tokenContract,
                CONFIG.ROUTER_CONTRACT,
                amountUSDC,
                'USDC'
            );

            // Step 5: Add liquidity
            log('Step 5/5: Adding liquidity to pool...', 'WARNING');
            log(`WETH Amount: ${ethers.formatEther(amountWETH)}`, 'INFO');
            log(`USDC Amount: ${amountUSDC}`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            const lpBalanceBefore = await this.lpTokenContract.balanceOf(this.wallet.address);

            const tx = await this.liquidityRouter.addLiquidity(
                CONFIG.WETH_ADDRESS,
                CONFIG.TOKEN_ADDRESS,
                false,
                amountWETH,
                amountUSDC,
                amountWETHMin.toString(),
                amountUSDCMin.toString(),
                this.wallet.address,
                deadline,
                {
                    gasLimit: 250000
                }
            );

            log(`Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('LIQUIDITY ADDED SUCCESSFULLY', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                
                const lpBalanceAfter = await this.lpTokenContract.balanceOf(this.wallet.address);
                const lpReceived = BigInt(lpBalanceAfter) - BigInt(lpBalanceBefore);
                
                log(`LP Tokens Received: ${ethers.formatEther(lpReceived)} LP`, 'SUCCESS');
                printLine('-', 'green');

                // AUTO STAKE LP TOKENS
                if (lpReceived > 0n) {
                    log('Starting automatic LP staking...', 'WARNING');
                    await delay(CONFIG.STEP_DELAY);
                    await this.depositToGauge(lpReceived.toString());
                }
                
                return receipt;
            } else {
                throw new Error('Transaction failed');
            }
        } catch (error) {
            log(`Add liquidity failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async addLiquidityIRS() {
        try {
            printHeader('ADDING LIQUIDITY (IRS/USDT)', 'yellow');
            await delay(CONFIG.STEP_DELAY);

            const amountIRS = CONFIG.VOTE_LIQUIDITY_IRS;
            const amountUSDT = CONFIG.VOTE_LIQUIDITY_USDT;
            const amountIRSMin = (BigInt(amountIRS) * 95n) / 100n;
            const amountUSDTMin = (BigInt(amountUSDT) * 95n) / 100n;
            const deadline = Math.floor(Date.now() / 1000) + 1200;

            const irsBalance = await this.irsContract.balanceOf(this.wallet.address);
            const usdtBalance = await this.usdtContract.balanceOf(this.wallet.address);
            
            log(`Current IRS Balance: ${ethers.formatEther(irsBalance)}`, 'INFO');
            log(`Current USDT Balance: ${usdtBalance.toString()}`, 'INFO');
            log(`Required IRS: ${ethers.formatEther(amountIRS)}`, 'INFO');
            log(`Required USDT: ${amountUSDT}`, 'INFO');

            if (BigInt(irsBalance) < BigInt(amountIRS)) {
                log(`Insufficient IRS balance!`, 'ERROR');
                throw new Error('Insufficient IRS balance');
            }

            if (BigInt(usdtBalance) < BigInt(amountUSDT)) {
                log(`Insufficient USDT balance!`, 'ERROR');
                throw new Error('Insufficient USDT balance');
            }

            log('Step 1/3: Approving IRS...', 'TASK');
            await this.approveToken(
                this.irsContract,
                CONFIG.ROUTER_CONTRACT,
                amountIRS,
                'IRS'
            );

            log('Step 2/3: Approving USDT...', 'TASK');
            await this.approveToken(
                this.usdtContract,
                CONFIG.ROUTER_CONTRACT,
                amountUSDT,
                'USDT'
            );

            log('Step 3/3: Adding liquidity to pool...', 'WARNING');
            log(`IRS Amount: ${ethers.formatEther(amountIRS)}`, 'INFO');
            log(`USDT Amount: ${amountUSDT}`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            const tx = await this.liquidityRouter.addLiquidity(
                CONFIG.IRS_TOKEN,
                CONFIG.USDT_TOKEN,
                true,
                amountIRS,
                amountUSDT,
                amountIRSMin.toString(),
                amountUSDTMin.toString(),
                this.wallet.address,
                deadline,
                {
                    gasLimit: 250000
                }
            );

            log(`Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('LIQUIDITY ADDED SUCCESSFULLY', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                printLine('-', 'green');
                return receipt;
            } else {
                throw new Error('Transaction failed');
            }
        } catch (error) {
            log(`Add liquidity failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async createVoteLock() {
        try {
            printHeader('CREATING VOTE LOCK', 'yellow');
            await delay(CONFIG.STEP_DELAY);

            const lockAmount = CONFIG.LOCK_AMOUNT;
            const lockDuration = CONFIG.LOCK_DURATION;

            const irsBalance = await this.irsContract.balanceOf(this.wallet.address);
            log(`Current IRS Balance: ${ethers.formatEther(irsBalance)}`, 'INFO');
            log(`Required IRS: ${ethers.formatEther(lockAmount)}`, 'INFO');

            if (BigInt(irsBalance) < BigInt(lockAmount)) {
                log(`Insufficient IRS balance!`, 'ERROR');
                throw new Error('Insufficient IRS balance');
            }

            log('Step 1/2: Approving IRS for Voting Escrow...', 'TASK');
            await this.approveToken(
                this.irsContract,
                CONFIG.VOTING_ESCROW,
                lockAmount,
                'IRS'
            );

            log('Step 2/2: Creating lock...', 'WARNING');
            log(`Lock Amount: ${ethers.formatEther(lockAmount)} IRS`, 'INFO');
            log(`Lock Duration: ${lockDuration} seconds (1 year)`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            const tx = await this.votingEscrow.createLock(
                lockAmount,
                lockDuration,
                {
                    gasLimit: 500000
                }
            );

            log(`Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('VOTE LOCK CREATED SUCCESSFULLY', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                
                try {
                    const transferLog = receipt.logs.find(log => 
                        log.topics[0] === '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
                    );
                    if (transferLog && transferLog.topics.length >= 4) {
                        const tokenId = BigInt(transferLog.topics[3]).toString();
                        log(`veNFT Token ID: ${tokenId}`, 'SUCCESS');
                    }
                } catch (e) {
                    // Ignore
                }
                
                printLine('-', 'green');
                return receipt;
            } else {
                throw new Error('Transaction failed');
            }
        } catch (error) {
            log(`Create vote lock failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async addIncentive() {
        try {
            printHeader('ADDING INCENTIVE/BRIBE', 'yellow');
            await delay(CONFIG.STEP_DELAY);

            const incentiveAmount = CONFIG.INCENTIVE_AMOUNT;

            const irsBalance = await this.irsContract.balanceOf(this.wallet.address);
            log(`Current IRS Balance: ${ethers.formatEther(irsBalance)}`, 'INFO');
            log(`Required IRS: ${ethers.formatEther(incentiveAmount)}`, 'INFO');

            if (BigInt(irsBalance) < BigInt(incentiveAmount)) {
                log(`Insufficient IRS balance!`, 'ERROR');
                throw new Error('Insufficient IRS balance');
            }

            log('Step 1/2: Approving IRS for Bribe Reward...', 'TASK');
            await this.approveToken(
                this.irsContract,
                CONFIG.BRIBE_VOTING_REWARD,
                incentiveAmount,
                'IRS'
            );

            log('Step 2/2: Notifying reward amount...', 'WARNING');
            log(`Incentive Amount: ${ethers.formatEther(incentiveAmount)} IRS`, 'INFO');
            await delay(CONFIG.STEP_DELAY);

            const tx = await this.bribeReward.notifyRewardAmount(
                CONFIG.IRS_TOKEN,
                incentiveAmount,
                {
                    gasLimit: 150000
                }
            );

            log(`Transaction Hash: ${tx.hash}`, 'INFO');
            log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${tx.hash}`, 'INFO');
            log('Waiting for confirmation...', 'TASK');

            const receipt = await tx.wait();

            if (receipt.status === 1) {
                printHeader('INCENTIVE ADDED SUCCESSFULLY', 'green');
                log(`Hash: ${receipt.hash}`, 'SUCCESS');
                log(`Gas Used: ${receipt.gasUsed.toString()}`, 'SUCCESS');
                log(`Block: ${receipt.blockNumber}`, 'SUCCESS');
                log(`Explorer: ${CONFIG.EXPLORER_URL}/tx/${receipt.hash}`, 'SUCCESS');
                printLine('-', 'green');
                return receipt;
            } else {
                throw new Error('Transaction failed');
            }
        } catch (error) {
            log(`Add incentive failed: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async performSwap() {
        try {
            console.clear();
            printHeader('SWAP MODE', 'cyan');
            await delay(CONFIG.STEP_DELAY);
            await this.checkBalance();
            const quote = await this.getSwapQuote();
            await this.executeSwap(quote);
        } catch (error) {
            log(`Swap operation failed: ${error.message}`, 'ERROR');
        }
    }

    async performAddLiquidityWETH() {
        try {
            console.clear();
            printHeader('ADD LIQUIDITY MODE (WETH/USDC)', 'cyan');
            await delay(CONFIG.STEP_DELAY);
            await this.checkBalance();
            await this.addLiquidityWETH();
        } catch (error) {
            log(`Liquidity operation failed: ${error.message}`, 'ERROR');
        }
    }

    async performAddLiquidityIRS() {
        try {
            console.clear();
            printHeader('ADD LIQUIDITY MODE (IRS/USDT)', 'cyan');
            await delay(CONFIG.STEP_DELAY);
            await this.checkBalance();
            await this.addLiquidityIRS();
        } catch (error) {
            log(`Liquidity operation failed: ${error.message}`, 'ERROR');
        }
    }

    async performCreateVoteLock() {
        try {
            console.clear();
            printHeader('CREATE VOTE LOCK MODE', 'cyan');
            await delay(CONFIG.STEP_DELAY);
            await this.checkBalance();
            await this.createVoteLock();
        } catch (error) {
            log(`Vote lock operation failed: ${error.message}`, 'ERROR');
        }
    }

    async performAddIncentive() {
        try {
            console.clear();
            printHeader('ADD INCENTIVE MODE', 'cyan');
            await delay(CONFIG.STEP_DELAY);
            await this.checkBalance();
            await this.addIncentive();
        } catch (error) {
            log(`Incentive operation failed: ${error.message}`, 'ERROR');
        }
    }

    async performAutoMode() {
        try {
            console.clear();
            printHeader('AUTO MODE - EXECUTING ALL TASKS', 'magenta');
            await delay(CONFIG.STEP_DELAY);

            // Task 1
            printLine('-', 'cyan');
            log('[TASK 1/5] Checking Balances...', 'TASK');
            printLine('-', 'cyan');
            await this.checkBalance();
            await delay(CONFIG.STEP_DELAY * 2);

            // Task 2
            printLine('-', 'cyan');
            log('[TASK 2/5] Performing Swap...', 'TASK');
            printLine('-', 'cyan');
            try {
                const quote = await this.getSwapQuote();
                await this.executeSwap(quote);
            } catch (error) {
                log(`Swap task failed: ${error.message}`, 'ERROR');
            }
            await delay(CONFIG.STEP_DELAY * 2);

            // Task 3
            printLine('-', 'cyan');
            log('[TASK 3/5] Adding Liquidity (WETH/USDC) + Auto Staking...', 'TASK');
            printLine('-', 'cyan');
            try {
                await this.addLiquidityWETH();
            } catch (error) {
                log(`WETH/USDC liquidity task failed: ${error.message}`, 'ERROR');
            }
            await delay(CONFIG.STEP_DELAY * 2);

            // Task 4
            printLine('-', 'cyan');
            log('[TASK 4/5] Adding Liquidity (IRS/USDT)...', 'TASK');
            printLine('-', 'cyan');
            try {
                await this.addLiquidityIRS();
            } catch (error) {
                log(`IRS/USDT liquidity task failed: ${error.message}`, 'ERROR');
            }
            await delay(CONFIG.STEP_DELAY * 2);

            // Task 5
            printLine('-', 'cyan');
            log('[TASK 5/5] Creating Vote Lock...', 'TASK');
            printLine('-', 'cyan');
            try {
                await this.createVoteLock();
            } catch (error) {
                log(`Vote lock task failed: ${error.message}`, 'ERROR');
            }
            await delay(CONFIG.STEP_DELAY * 2);

            printHeader('AUTO MODE COMPLETED', 'green');

        } catch (error) {
            log(`Auto mode failed: ${error.message}`, 'ERROR');
        }
    }
}

// ============================================
// MAIN MENU LOGIC
// ============================================
async function mainMenu() {
    const bot = new LiquidityBot();
    let running = true;

    while (running) {
        displayMenu();
        const choice = await askQuestion('\nEnter your choice (1-7): ');

        switch (choice.trim()) {
            case '1':
                await bot.performSwap();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '2':
                await bot.performAddLiquidityWETH();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '3':
                await bot.performAddLiquidityIRS();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '4':
                await bot.performCreateVoteLock();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '5':
                await bot.performAddIncentive();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '6':
                await bot.performAutoMode();
                await askQuestion('\nPress Enter to continue...');
                break;

            case '7':
                console.clear();
                printHeader('GOODBYE', 'green');
                log('Thanks for using RISE Testnet Bot!', 'SUCCESS');
                log('Created by Kazuha with love', 'SUCCESS');
                printLine('=', 'green');
                running = false;
                rl.close();
                process.exit(0);
                break;

            default:
                log('Invalid choice! Please select 1-7', 'ERROR');
                await askQuestion('\nPress Enter to continue...');
        }
    }
}

// ============================================
// START APPLICATION
// ============================================
async function main() {
    try {
        console.clear();
        printLine('=', 'cyan');
        console.log(`${colors.bright}${colors.cyan}           RISE TESTNET AUTO BOT V5.0${colors.reset}`);
        console.log(`${colors.bright}${colors.white}           CREATED BY KAZUHA | VIP ONLY${colors.reset}`);
        printLine('=', 'cyan');
        console.log('');
        log(`Network: RISE Testnet`, 'INFO');
        log(`Chain ID: ${CONFIG.CHAIN_ID}`, 'INFO');
        log(`Explorer: ${CONFIG.EXPLORER_URL}`, 'INFO');
        console.log('');
        printLine('=', 'cyan');
        
        await delay(3000);
        await mainMenu();
    } catch (error) {
        log(`Fatal error: ${error.message}`, 'ERROR');
        process.exit(1);
    }
}

process.on('SIGINT', () => {
    console.clear();
    log('Bot terminated by user', 'WARNING');
    process.exit(0);
});

process.on('unhandledRejection', (error) => {
    log(`Unhandled error: ${error.message}`, 'ERROR');
});

main();