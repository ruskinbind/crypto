// utils.js
const gradient = require('gradient-string');
const chalk = require('chalk');
const readline = require('readline-sync');

const kazuhaTheme = gradient(['#FF0080', '#7928CA', '#FF0080']); // Pink/Purple vibe

function printBanner() {
    console.clear();
    console.log(kazuhaTheme("\n╔════════════════════════════════════════╗"));
    console.log(kazuhaTheme("║   ARCHADE BOT - CREATED BY KAZUHA VIP   ║"));
    console.log(kazuhaTheme("╚════════════════════════════════════════╝\n"));
}

function printMenu() {
    console.log(chalk.hex('#FF0080')("1. BUY TRADE"));
    console.log(chalk.hex('#7928CA')("2. SELL TRADE"));
    console.log(chalk.hex('#FF0080')("3. CREATE A TOKEN"));
    console.log(chalk.hex('#7928CA')("4. TASKS"));
    console.log(chalk.hex('#FF6B35')("5. SWITCH ACCOUNT"));
    console.log(chalk.hex('#FF0080')("6. EXIT"));
}

function log(type, message) {
    const timestamp = new Date().toLocaleTimeString();
    switch (type) {
        case 'info':
            console.log(chalk.cyan(`[${timestamp}] INFO: ${message}`));
            break;
        case 'success':
            console.log(chalk.green(`[${timestamp}] SUCCESS: ${message}`));
            break;
        case 'error':
            console.log(chalk.red(`[${timestamp}] ERROR: ${message}`));
            break;
        case 'warn':
            console.log(chalk.yellow(`[${timestamp}] WARN: ${message}`));
            break;
        default:
            console.log(message);
    }
}

function ask(question) {
    return readline.question(chalk.white(question + ": "));
}

module.exports = {
    printBanner,
    printMenu,
    log,
    ask,
    gradient: kazuhaTheme
};

