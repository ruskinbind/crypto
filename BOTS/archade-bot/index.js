// index.js - Main Entry Point
const { printBanner, printMenu, log, ask } = require('./utils');
const api = require('./api');
const solana = require('./solana');
const config = require('./config');
const proxy = require('./proxy');
const chalk = require('chalk');
const { Keypair } = require('@solana/web3.js');

/**
 * Display account selection menu and set up proxy
 */
function selectAccount() {
    const walletCount = solana.getWalletCount();
    const currentIndex = solana.getCurrentWalletIndex();

    console.log(chalk.hex('#FF6B35')('\n╔════════════════════════════════════════════════════════════╗'));
    console.log(chalk.hex('#FF6B35')('║              🔐 ACCOUNT SELECTION                          ║'));
    console.log(chalk.hex('#FF6B35')('╚════════════════════════════════════════════════════════════╝\n'));

    // Display all accounts
    for (let i = 0; i < walletCount; i++) {
        const wallet = solana.loadWallet(i);
        const address = wallet.publicKey.toString();
        const shortAddress = `${address.slice(0, 6)}...${address.slice(-4)}`;
        const proxyInfo = proxy.getProxy(i);
        const proxyDisplay = proxyInfo ? chalk.green(`✓ Proxy`) : chalk.gray('No Proxy');
        const current = i === currentIndex ? chalk.yellow(' [CURRENT]') : '';

        console.log(chalk.cyan(`${i + 1}. ${shortAddress} - ${proxyDisplay}${current}`));
    }

    console.log(chalk.gray(`\nTotal Accounts: ${walletCount}`));
    const choice = ask('\nSelect Account (number)');
    const accountIndex = parseInt(choice) - 1;

    if (accountIndex >= 0 && accountIndex < walletCount) {
        solana.setCurrentWallet(accountIndex);

        // Set proxy if available
        const proxyUrl = proxy.getProxy(accountIndex);
        if (proxyUrl) {
            api.setProxy(proxyUrl);
            log('success', `Using proxy for this account`);
        } else {
            api.setProxy(null);
            log('info', `No proxy configured for this account`);
        }

        const wallet = solana.loadWallet(accountIndex);
        console.log(chalk.green(`\n✅ Selected Account: ${wallet.publicKey.toString()}`));
    } else {
        log('error', 'Invalid account selection');
        selectAccount(); // Retry
    }
}

async function handleBuy() {
    console.log(chalk.yellow("\n--- BUY MODE ---"));
    const mint = config.DEFAULT_MINT;
    const amount = ask("Enter SOL Amount to Buy");
    const times = parseInt(ask("How many times to buy?"));

    const amountFloat = parseFloat(amount);
    const amountLamports = Math.floor(amountFloat * 1_000_000_000);
    const userWallet = solana.getWalletAddress();

    log('info', `Wallet: ${userWallet}`);
    log('info', `Will execute ${times} buy transaction(s)...`);

    for (let i = 1; i <= times; i++) {
        console.log(chalk.cyan(`\n[${i}/${times}] Executing buy...`));

        const prep = await api.prepareTrade(mint, userWallet, amountFloat, 'buy');

        if (prep && prep.success && prep.tx) {
            log('info', `Trade Prepared. Signing...`);
            try {
                const { signature, slot } = await solana.sendTransaction(prep.tx, prep.isVersioned);

                const tokenAmountRaw = Math.floor((prep.expectedOut || 0) * 1_000_000);

                try {
                    const recordPayload = {
                        mint,
                        wallet: userWallet,
                        is_buy: true,
                        sol_amount: amountLamports,
                        token_amount: tokenAmountRaw,
                        signature
                    };
                    await api.recordTrade(recordPayload);
                    log('info', 'Trade Recorded on Archade.');
                } catch (recErr) {
                    // Silent fail
                }

                log('success', `Buy Complete! [${i}/${times}]`);
                console.log(chalk.magenta(`Block Number: ${slot}`));
                console.log(chalk.cyan(`Explorer: https://solscan.io/tx/${signature}?cluster=devnet`));

            } catch (err) {
                log('error', `Buy Failed: ${err.message}`);
            }
        } else {
            log('error', `Could not prepare trade. Request failed.`);
        }

        // Small delay between transactions
        if (i < times) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    console.log(chalk.green(`\n✅ Completed ${times} buy transaction(s)!`));
}

async function handleSell() {
    console.log(chalk.yellow("\n--- SELL MODE ---"));
    const mint = config.DEFAULT_MINT;
    const amount = ask("Enter Token Amount to Sell");
    const times = parseInt(ask("How many times to sell?"));

    const userWallet = solana.getWalletAddress();
    const amountInt = parseInt(amount);

    log('info', `Will execute ${times} sell transaction(s)...`);

    for (let i = 1; i <= times; i++) {
        console.log(chalk.cyan(`\n[${i}/${times}] Executing sell...`));

        const prep = await api.prepareTrade(mint, userWallet, amountInt, 'sell');
        if (prep && prep.success && prep.tx) {
            log('info', `Trade Prepared. Signing...`);
            try {
                const { signature, slot } = await solana.sendTransaction(prep.tx, prep.isVersioned);

                try {
                    const recordPayload = {
                        mint,
                        wallet: userWallet,
                        is_buy: false,
                        sol_amount: 0,
                        token_amount: amountInt,
                        signature
                    };
                    await api.recordTrade(recordPayload);
                } catch (recErr) {
                    // Silent fail
                }

                log('success', `Sell Complete! [${i}/${times}]`);
                console.log(chalk.magenta(`Block Number: ${slot}`));
                console.log(chalk.cyan(`Explorer: https://solscan.io/tx/${signature}?cluster=devnet`));
            } catch (err) {
                log('error', `Sell Failed: ${err.message}`);
            }
        } else {
            log('error', `Could not prepare trade.`);
        }

        // Small delay between transactions
        if (i < times) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    console.log(chalk.green(`\n✅ Completed ${times} sell transaction(s)!`));
}

async function handleCreate() {
    console.log(chalk.hex('#7928CA')("\n--- CREATE TOKEN MODE ---"));
    const baseName = ask("Token Name");
    const baseSymbol = ask("Token Symbol");
    const desc = ask("Description");
    const times = parseInt(ask("How many tokens to create?"));

    const userWallet = solana.getWalletAddress();

    log('info', `Will create ${times} token(s)...`);

    for (let i = 1; i <= times; i++) {
        console.log(chalk.cyan(`\n[${i}/${times}] Creating token...`));

        // Add number suffix if creating multiple
        const name = times > 1 ? `${baseName} #${i}` : baseName;
        const symbol = times > 1 ? `${baseSymbol}${i}` : baseSymbol;
        const imagePath = `./temp_token_${i}.jpg`;

        // 1. Download Random Image (Auto)
        log('info', 'Downloading Random Image...');
        try {
            await api.downloadRandomImage(imagePath);
            log('success', 'Image Downloaded!');
        } catch (err) {
            log('error', 'Could not download random image.');
            continue;
        }

        // 2. Upload Image
        log('info', 'Uploading Image...');
        const imgRes = await api.uploadImage(imagePath);
        if (!imgRes || !imgRes.success) {
            log('error', 'Image Upload Failed');
            continue;
        }
        const imageUrl = imgRes.url;
        log('success', `Image Uploaded: ${imageUrl}`);

        // 3. Upload Metadata
        log('info', 'Uploading Metadata...');
        const metaRes = await api.uploadMetadata(name, symbol, desc, imageUrl);
        if (!metaRes || !metaRes.success) {
            log('error', 'Metadata Upload Failed');
            continue;
        }
        const metadataUrl = metaRes.url;
        log('success', `Metadata Uploaded: ${metadataUrl}`);

        // Generate Mint
        const mintKeypair = Keypair.generate();
        const mintAddress = mintKeypair.publicKey.toString();
        log('info', `Generated Mint Address: ${mintAddress}`);

        // 4. Create Public Group (Community)
        log('info', 'Creating Public Group...');
        const publicGroupPayload = {
            name: `$${symbol} Community`,
            participants: [],
            avatar: imageUrl,
            isTokenGroup: true,
            tokenMint: mintAddress,
            groupType: "public"
        };
        const publicGroupRes = await api.createGroup(publicGroupPayload);
        const publicGroupId = publicGroupRes?.conversation?.id || null;

        // 5. Create Holders Group
        log('info', 'Creating Holders Group...');
        const holdersGroupPayload = {
            name: `$${symbol} Holders`,
            participants: [],
            avatar: imageUrl,
            isTokenGroup: true,
            tokenMint: mintAddress,
            groupType: "holders",
            minHolding: 10000
        };
        const holdersGroupRes = await api.createGroup(holdersGroupPayload);
        const holdersGroupId = holdersGroupRes?.conversation?.id || null;

        if (!publicGroupId || !holdersGroupId) {
            log('warn', 'Group Creation had issues');
        } else {
            log('success', 'Groups Created!');
        }

        // 6. Create Token on Archade
        log('info', 'Creating Token on Archade...');
        const tokenPayload = {
            mint: mintAddress,
            name: name,
            symbol: symbol,
            description: desc,
            image_url: imageUrl,
            banner_url: imageUrl,
            creator_wallet: userWallet,
            virtual_sol_reserves: "30000000000",
            virtual_token_reserves: "0",
            real_sol_reserves: "0",
            real_token_reserves: "800000000000000",
            current_price_sol: 3.75e-8,
            current_price_usd: 0.000004875,
            fdv_usd: 4875,
            market_cap_usd: 0,
            public_group_id: publicGroupId,
            holders_group_id: holdersGroupId,
            holders_min_amount: 10000
        };

        const tokenRes = await api.createToken(tokenPayload);
        if (tokenRes && tokenRes.success) {
            log('success', `Token Created Successfully! [${i}/${times}]`);
            console.log(chalk.magenta(`Mint Address: ${mintAddress}`));
            console.log(chalk.cyan(`View on Archade: https://archade.io/coin/${mintAddress}`));
        } else {
            log('error', 'Token Creation Failed');
        }

        // Small delay between token creations
        if (i < times) {
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    console.log(chalk.green(`\n✅ Created ${times} token(s)!`));
}

async function handleCompleteTask() {
    console.log(chalk.hex('#FF0080')("\n--- TASKS ---"));
    const targetWallet = config.TARGET_WALLET;
    const targetPostId = config.TARGET_POST_ID;

    // Task 1: Follow
    log('info', `Following ${targetWallet}...`);
    const followRes = await api.follow(targetWallet);
    if (followRes && followRes.success) {
        log('success', `✓ Followed!`);
    } else {
        log('warn', 'Follow skipped (may already be following)');
    }

    // Task 2: Random Likes (2-5 likes on the same post)
    const likeCount = Math.floor(Math.random() * 4) + 2; // 2-5
    log('info', `Sending ${likeCount} likes to post...`);
    let successfulLikes = 0;
    for (let i = 0; i < likeCount; i++) {
        const likeRes = await api.likePost(targetPostId);
        if (likeRes && likeRes.success) {
            successfulLikes++;
        }
        await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
    }
    log('success', `✓ Sent ${successfulLikes} likes!`);

    // Task 3: Random Comments (1-3 comments)
    const commentCount = Math.floor(Math.random() * 3) + 1; // 1-3
    const randomComments = [
        "Great project! 🚀",
        "To the moon! 🌙",
        "Love this token! 💎",
        "Amazing work! 🔥",
        "LFG! 💪",
        "This is fire! 🔥🔥",
        "Bullish! 📈",
        "NICE",
        "Awesome! 👏",
        "Keep it up! 💯"
    ];

    log('info', `Posting ${commentCount} comments...`);
    let successfulComments = 0;
    for (let i = 0; i < commentCount; i++) {
        const randomComment = randomComments[Math.floor(Math.random() * randomComments.length)];
        const commentRes = await api.commentOnPost(targetPostId, randomComment);
        if (commentRes && commentRes.success) {
            successfulComments++;
        }
        await new Promise(resolve => setTimeout(resolve, 800)); // Delay between comments
    }
    log('success', `✓ Posted ${successfulComments} comments!`);

    console.log(chalk.cyan("\n✅ All tasks completed successfully!"));
}

async function main() {
    // Initialize wallets and proxies
    solana.loadAllWallets();
    proxy.loadProxies();

    printBanner();

    // Initial account selection
    if (solana.getWalletCount() > 1) {
        selectAccount();
    } else {
        log('info', 'Single account mode');
        const wallet = solana.loadWallet(0);
        console.log(chalk.green(`\n✅ Using Account: ${wallet.publicKey.toString()}`));

        // Set proxy if available
        const proxyUrl = proxy.getProxy(0);
        if (proxyUrl) {
            api.setProxy(proxyUrl);
            log('success', 'Proxy configured');
        }
    }

    while (true) {
        printBanner();

        // Show current account info
        const currentWallet = solana.loadWallet();
        const address = currentWallet.publicKey.toString();
        const shortAddress = `${address.slice(0, 6)}...${address.slice(-4)}`;
        console.log(chalk.gray(`Current Account: ${shortAddress}\n`));

        printMenu();
        const choice = ask("Select Option");

        switch (choice) {
            case '1':
                await handleBuy();
                break;
            case '2':
                await handleSell();
                break;
            case '3':
                await handleCreate();
                break;
            case '4':
                await handleCompleteTask();
                break;
            case '5':
                selectAccount();
                continue; // Skip the "Press Enter" prompt
            case '6':
                console.log(chalk.gray("Exiting... Bye Kazuha!"));
                process.exit(0);
                break;
            default:
                console.log(chalk.red("Invalid Option"));
        }
        console.log("\n");
        ask("Press Enter to continue");
    }
}

main().catch(console.error);
