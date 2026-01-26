const fs = require('fs');
const path = require('path');
const readline = require('readline');

const BOLD = '\x1b[1m';
const DIM = '\x1b[2m';
const ITALIC = '\x1b[3m';
const UNDERLINE = '\x1b[4m';

const BLACK = '\x1b[30m';
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const MAGENTA = '\x1b[35m';
const CYAN = '\x1b[36m';
const WHITE = '\x1b[37m';

const BG_BLACK = '\x1b[40m';
const BG_RED = '\x1b[41m';
const BG_GREEN = '\x1b[42m';
const BG_YELLOW = '\x1b[43m';
const BG_BLUE = '\x1b[44m';
const BG_MAGENTA = '\x1b[45m';
const BG_CYAN = '\x1b[46m';
const BG_WHITE = '\x1b[47m';

const RESET = '\x1b[0m';

const NOVALINK_PROFILE_URL = "https://prod-api.novalinkapp.com/api/v1/profile";
const NEURA_BASE_URL = "https://neura-knights-api-prod.anomalygames.ai";

function safeText(value) {
    let text = String(value);
    text = text.replace(/-/g, " ");
    text = text.replace(/\[/g, " ");
    text = text.replace(/\]/g, " ");
    text = text.replace(/#/g, " ");
    return text;
}

function logStep(step, message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${CYAN}${BOLD}[STEP]${RESET} ${WHITE}${step}${RESET} ${DIM}${message}${RESET}`);
}

function logInfo(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${BLUE}${BOLD}[INFO]${RESET} ${WHITE}${message}${RESET}`);
}

function logSuccess(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${GREEN}${BOLD}[SUCCESS]${RESET} ${GREEN}${message}${RESET}`);
}

function logWarn(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${YELLOW}${BOLD}[WARN]${RESET} ${YELLOW}${message}${RESET}`);
}

function logError(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${RED}${BOLD}[ERROR]${RESET} ${RED}${message}${RESET}`);
}

function logBattle(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${MAGENTA}${BOLD}[BATTLE]${RESET} ${MAGENTA}${message}${RESET}`);
}

function logReward(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${YELLOW}${BOLD}[REWARD]${RESET} ${YELLOW}${message}${RESET}`);
}

function logCard(message) {
    const timestamp = new Date().toLocaleTimeString('en-GB');
    console.log(`${DIM}[${timestamp}]${RESET} ${CYAN}${BOLD}[CARD]${RESET} ${CYAN}${message}${RESET}`);
}

function clearScreen() {
    process.stdout.write('\x1b[2J\x1b[H');
}

function printLine(char = '=', length = 50, color = CYAN) {
    console.log(`${color}${char.repeat(length)}${RESET}`);
}

function printDoubleLine(length = 50) {
    console.log(`${CYAN}${BOLD}${'='.repeat(length)}${RESET}`);
}

function centerText(text, width = 50) {
    const padding = Math.max(0, Math.floor((width - text.length) / 2));
    return ' '.repeat(padding) + text;
}

function banner() {
    clearScreen();
    console.log();
    printDoubleLine(50);
    console.log(`${CYAN}${BOLD}${centerText(' NEURA KNIGHT AUTO BOT', 50)}${RESET}`);
    console.log(`${MAGENTA}${BOLD}${centerText('CREATED BY KAZUHA VIP ONLY', 50)}${RESET}`);
    printDoubleLine(50);
    console.log();
}

function showMenu() {
    printLine('-', 50, DIM);
    console.log(`${CYAN}${BOLD}  MAIN MENU${RESET}`);
    printLine('-', 50, DIM);
    console.log();
    console.log(`  ${GREEN}${BOLD}[1]${RESET} ${WHITE}Complete Quests${RESET}`);
    console.log(`  ${BLUE}${BOLD}[2]${RESET} ${WHITE}Start Battle${RESET}`);
    console.log(`  ${MAGENTA}${BOLD}[3]${RESET} ${WHITE}Auto All${RESET}`);
    console.log(`  ${RED}${BOLD}[4]${RESET} ${WHITE}Exit${RESET}`);
    console.log();
    printLine('-', 50, DIM);
}

function setTitle() {
    process.stdout.write("\x1b]2;Neura Knight Bot by KAZUHA\x1b\\");
}

function getDataFilePath() {
    return path.join(__dirname, "data.txt");
}

function loadAccessTokens() {
    const filePath = getDataFilePath();
    if (!fs.existsSync(filePath)) {
        logError("Data file data.txt is missing in current directory");
        process.exit(1);
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n').map(line => line.trim()).filter(line => line);
    if (lines.length === 0) {
        logError("Data file data.txt does not contain any token value");
        process.exit(1);
    }
    const tokens = [];
    for (const raw of lines) {
        let token;
        if (raw.toLowerCase().startsWith("bearer ")) {
            token = raw;
        } else {
            token = "Bearer " + raw;
        }
        tokens.push(token);
    }
    logSuccess(`Loaded ${tokens.length} account(s) from data.txt`);
    return tokens;
}

async function performRequest(method, url, headers = {}, jsonBody = null) {
    const options = {
        method: method,
        headers: headers
    };
    if (jsonBody) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(jsonBody);
    }
    try {
        const response = await fetch(url, options);
        let data;
        try {
            data = await response.json();
        } catch (e) {
            logError("Response is not valid JSON format");
            throw e;
        }
        return { response, data };
    } catch (e) {
        logError("Network operation failed during HTTP request");
        throw e;
    }
}

async function fetchProfile(novalinkAuthHeader) {
    logStep("1/6", "Fetching user profile...");
    const headers = { "Authorization": novalinkAuthHeader };
    const { response, data } = await performRequest("GET", NOVALINK_PROFILE_URL, headers);
    if (response.status !== 200) {
        logError("Profile request returned unsuccessful status code");
        throw new Error("Profile status code error");
    }
    if (!data.success) {
        logError("Profile response indicates unsuccessful operation");
        throw new Error("Profile success flag error");
    }
    const profile = data.data || {};
    const novaId = profile.novaLinkUserId;
    const gameToken = profile.authToken;
    if (!novaId || !gameToken) {
        logError("Profile response is missing nova user data or game token");
        throw new Error("Profile payload error");
    }
    logSuccess(`Profile loaded for user: ${safeText(novaId)}`);
    return { novaId, gameToken };
}

async function fetchCards(novaId) {
    logStep("2/6", "Fetching card inventory...");
    const url = `${NEURA_BASE_URL}/api/inventory/cards?novalink_user_id=${novaId}`;
    const { response, data } = await performRequest("GET", url);
    if (response.status !== 200 || !data.success) {
        logWarn("Card inventory request failed");
        return [];
    }
    const cards = data.data || [];
    logSuccess(`Found ${cards.length} cards in inventory`);
    return cards;
}

function buildCardMap(cards) {
    const cardMap = {};
    for (const entry of cards) {
        const cardId = entry.card_id;
        if (!cardId) continue;
        cardMap[cardId] = {
            card_id: cardId,
            name: entry.card_name || cardId,
            slot: entry.slot || "",
            hero_class: entry.class || "",
            energy_cost: entry.energy_cost || "0",
            frequency: entry.frequency || "",
            effects: entry.card_effects || []
        };
    }
    return cardMap;
}

function computeEffectValue(cardEntry) {
    let total = 0;
    const effects = cardEntry.effects || [];
    for (const effect of effects) {
        const value = effect.effect_value;
        if (value === undefined || value === null) continue;
        try {
            total += parseInt(value);
        } catch (e) {
            continue;
        }
    }
    return total;
}

function chooseBestCardsForSlots(cardMap, heroClass) {
    logStep("3/6", "Evaluating best cards for each slot...");
    const bestBySlot = {};
    for (const card of Object.values(cardMap)) {
        if (card.hero_class !== heroClass) continue;
        const slotRaw = card.slot || "";
        if (!slotRaw) continue;
        const effectValue = computeEffectValue(card);
        if (effectValue <= 0) continue;
        const existing = bestBySlot[slotRaw];
        if (!existing || effectValue > existing.effect_value) {
            bestBySlot[slotRaw] = {
                card: card,
                effect_value: effectValue
            };
        }
    }
    for (const [slotRaw, info] of Object.entries(bestBySlot)) {
        logCard(`Best for ${safeText(slotRaw)}: ${safeText(info.card.name)} (Effect: ${info.effect_value})`);
    }
    if (Object.keys(bestBySlot).length === 0) {
        logWarn("No suitable cards found for Hero class");
    }
    return bestBySlot;
}

async function equipCards(gameAuthToken, heroClass, bestBySlot) {
    if (Object.keys(bestBySlot).length === 0) {
        logWarn("No cards to equip");
        return;
    }
    logStep("4/6", "Equipping best cards...");
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    for (const [slotRaw, info] of Object.entries(bestBySlot)) {
        const card = info.card;
        const cardId = card.card_id;
        const cardName = safeText(card.name);
        const slotLabel = safeText(slotRaw);
        const payload = {
            card_id: cardId,
            hero_class: heroClass,
            slot: slotRaw
        };
        const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/user/hero/equip-card`, headers, payload);
        if (response.status === 200 && data.success) {
            logSuccess(`Equipped ${cardName} to ${slotLabel}`);
        } else {
            logWarn(`Failed to equip ${cardName} to ${slotLabel}`);
        }
    }
}

async function fetchPackages(novaId) {
    logStep("5/6", "Checking package inventory...");
    const url = `${NEURA_BASE_URL}/api/inventory/packages?novalink_user_id=${novaId}`;
    const { response, data } = await performRequest("GET", url);
    if (response.status !== 200 || !data.success) {
        logWarn("Package inventory request failed");
        return [];
    }
    const packages = data.data || [];
    logSuccess(`Found ${packages.length} package type(s)`);
    return packages;
}

async function openAllPackages(novaId, packages) {
    if (packages.length === 0) {
        logWarn("No packages available to open");
        return;
    }
    logStep("6/6", "Opening all packages...");
    let totalOpened = 0;
    for (const pack of packages) {
        const packageType = pack.type;
        const collection = pack.collection;
        let countInt = parseInt(pack.count) || 0;
        const nameLabel = safeText(pack.name || "Unknown package");
        if (countInt <= 0) {
            continue;
        }
        for (let i = 0; i < countInt; i++) {
            const payload = {
                novalink_user_id: novaId,
                package_type: packageType,
                package_collection: collection
            };
            const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/package/open`, {}, payload);
            if (response.status === 200 && data.success) {
                const cardInfo = (data.data || {}).card || {};
                const cardName = safeText(cardInfo.card_name || "Unknown card");
                const rarityLabel = safeText(cardInfo.rarity || "Unknown");
                logReward(`Opened ${nameLabel} -> Got ${cardName} (${rarityLabel})`);
                totalOpened++;
            } else {
                logWarn(`Failed to open ${nameLabel}`);
            }
        }
    }
    logSuccess(`Opened ${totalOpened} package(s) total`);
}

async function fetchQuests(gameAuthToken) {
    logInfo("Fetching quest list...");
    const headers = { "Authorization": gameAuthToken };
    const { response, data } = await performRequest("GET", `${NEURA_BASE_URL}/api/quests`, headers);
    if (response.status !== 200 || !data.success) {
        logWarn("Quest listing request failed");
        return [];
    }
    const quests = data.data || [];
    logSuccess(`Found ${quests.length} quest(s)`);
    return quests;
}

async function claimAllQuests(gameAuthToken, quests) {
    if (quests.length === 0) {
        logWarn("No quests to claim");
        return;
    }
    logInfo("Claiming all quest rewards...");
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    let successCount = 0;
    for (const quest of quests) {
        const qid = quest.id;
        const reward = quest.reward;
        const rewardType = safeText(quest.reward_type || "Unknown");
        const payload = { quest_id: qid };
        const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/quests`, headers, payload);
        if (response.status === 200 && data.success) {
            logReward(`Claimed: ${reward} ${rewardType}`);
            successCount++;
        }
    }
    logSuccess(`Claimed ${successCount} quest reward(s)`);
}

function parseEnergyCost(cardEntry) {
    const raw = String(cardEntry.energy_cost || "0");
    try {
        const value = parseInt(raw);
        if (value < 0) return 0;
        return value;
    } catch (e) {
        return 0;
    }
}

function parseFrequencyLimit(cardEntry) {
    const raw = String(cardEntry.frequency || "").toLowerCase();
    if (raw.includes("single")) return 1;
    if (raw.includes("twice")) return 2;
    if (raw.includes("repeatable")) return 99;
    return 1;
}

async function startBattle(gameAuthToken) {
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    const locations = [
        "Forest",
        "Training Grounds",
        "Bridge",
        "Caves",
        "Ghost Town",
        "Mountain",
        "Castle"
    ];
    for (const loc of locations) {
        logBattle(`Attempting to start battle at ${loc}...`);
        const payload = { location: loc };
        const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/game/battle/start`, headers, payload);
        if (response.status === 200 && data.success) {
            const battleState = data.data || {};
            const monsterType = safeText(battleState.monster_type || "Unknown");
            logSuccess(`Battle started at ${loc} vs ${monsterType}`);
            const availableCards = [];
            const weapon = battleState.weapon_card_id;
            const hat = battleState.hat_card_id;
            const chest = battleState.chest_card_id;
            const offHand = battleState.off_hand_card_id;
            const necklace = battleState.necklace_card_id;
            for (const cid of [weapon, hat, chest, offHand, necklace]) {
                if (cid) availableCards.push(cid);
            }
            return { battleState, availableCards, allUnavailable: false };
        } else {
            logWarn(`Location ${loc} unavailable`);
        }
    }
    logError("All battle locations unavailable");
    return { battleState: null, availableCards: [], allUnavailable: true };
}

async function playCard(gameAuthToken, cardId) {
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    const payload = { card_id: cardId };
    const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/game/battle/play`, headers, payload);
    if (response.status !== 200 || !data.success) {
        return { battleState: null, availableCards: [] };
    }
    const body = data.data || {};
    const battleState = body.battleState || {};
    const availableCards = body.availableCards || [];
    return { battleState, availableCards };
}

async function endTurn(gameAuthToken) {
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/game/battle/end-turn`, headers);
    if (response.status !== 200 || !data.success) {
        return { battleState: null, availableCards: [] };
    }
    const body = data.data || {};
    const battleState = body.battleState || {};
    const availableCards = body.availableCards || [];
    return { battleState, availableCards };
}

function chooseCardToPlay(availableCards, cardMap, heroEnergy, usageMap, cardStats) {
    let bestCardId = null;
    let bestScore = -1.0;
    for (const cid of availableCards) {
        const cardEntry = cardMap[cid];
        if (!cardEntry) continue;
        const energyCost = parseEnergyCost(cardEntry);
        if (energyCost > heroEnergy) continue;
        const limit = parseFrequencyLimit(cardEntry);
        const used = usageMap[cid] || 0;
        if (used >= limit) continue;
        const effectValue = computeEffectValue(cardEntry);
        if (effectValue <= 0) continue;
        let score = effectValue;
        const nameLow = (cardEntry.name || "").toLowerCase();
        const slotLow = (cardEntry.slot || "").toLowerCase();
        if (slotLow.includes("weapon") || nameLow.includes("sword") || nameLow.includes("gun") || nameLow.includes("sidearm")) {
            score += effectValue;
        }
        const effects = cardEntry.effects || [];
        for (const eff of effects) {
            const effText = String(eff).toLowerCase();
            if (effText.includes("monster") || effText.includes("enemy") || effText.includes("damage") || effText.includes("attack")) {
                score += effectValue;
                break;
            }
        }
        const stats = cardStats[cid] || {};
        const damagePlays = stats.damage_plays || 0;
        if (damagePlays > 0) {
            score += effectValue * (1 + damagePlays);
        }
        if (score > bestScore) {
            bestScore = score;
            bestCardId = cid;
        }
    }
    return bestCardId;
}

async function runBattleLoop(gameAuthToken, cardMap, initialState, initialCards) {
    if (!initialState) {
        logWarn("Battle loop skipped - no initial state");
        return false;
    }
    let currentState = { ...initialState };
    let heroHp = currentState.hero_hp || 0;
    let monsterHp = currentState.monster_hp || 0;
    let roundValue = currentState.current_round || 1;
    
    console.log();
    printLine('-', 40, MAGENTA);
    logBattle(`Hero HP: ${heroHp} | Monster HP: ${monsterHp}`);
    printLine('-', 40, MAGENTA);
    
    let cardsInHand = [...initialCards];
    let usageMap = {};
    let cardStats = {};
    const maxTurns = 50;
    let turnCounter = 0;
    let noDamageRounds = 0;
    
    while (turnCounter < maxTurns) {
        if (monsterHp <= 0) {
            console.log();
            printLine('*', 40, GREEN);
            logSuccess(`VICTORY! Hero HP remaining: ${heroHp}`);
            printLine('*', 40, GREEN);
            return true;
        }
        if (heroHp <= 0) {
            console.log();
            printLine('*', 40, RED);
            logError("DEFEAT! Hero has fallen");
            printLine('*', 40, RED);
            return false;
        }
        
        const roundStartMonsterHp = monsterHp;
        let heroEnergy = currentState.hero_energy || 0;
        let selectedCardId = null;
        
        if (cardsInHand.length > 0 && heroEnergy > 0) {
            selectedCardId = chooseCardToPlay(cardsInHand, cardMap, heroEnergy, usageMap, cardStats);
        }
        
        if (selectedCardId) {
            const cardEntry = cardMap[selectedCardId] || {};
            const cardName = safeText(cardEntry.name || "Unknown");
            const effectValue = computeEffectValue(cardEntry);
            const prevMonsterHp = monsterHp;
            
            logBattle(`Playing: ${cardName} (Effect: ${effectValue})`);
            
            let result = await playCard(gameAuthToken, selectedCardId);
            if (!result.battleState) {
                logWarn("Play action failed - ending battle");
                return false;
            }
            
            currentState = { ...result.battleState };
            heroHp = currentState.hero_hp || heroHp;
            monsterHp = currentState.monster_hp || monsterHp;
            heroEnergy = currentState.hero_energy || heroEnergy;
            
            const damage = Math.max(0, prevMonsterHp - monsterHp);
            if (damage > 0) {
                logBattle(`Dealt ${damage} damage! Monster HP: ${monsterHp}`);
            }
            
            usageMap[selectedCardId] = (usageMap[selectedCardId] || 0) + 1;
            cardsInHand = [...result.availableCards];
            
            let stats = cardStats[selectedCardId] || { damage_plays: 0, total_plays: 0 };
            stats.total_plays = (stats.total_plays || 0) + 1;
            if (damage > 0) {
                stats.damage_plays = (stats.damage_plays || 0) + 1;
            }
            cardStats[selectedCardId] = stats;
            
            if (monsterHp <= 0) {
                console.log();
                printLine('*', 40, GREEN);
                logSuccess(`VICTORY! Hero HP remaining: ${heroHp}`);
                printLine('*', 40, GREEN);
                return true;
            }
        } else {
            logBattle("No playable cards this round");
        }
        
        logBattle("Ending turn...");
        
        let result = await endTurn(gameAuthToken);
        if (!result.battleState) {
            result = await endTurn(gameAuthToken);
            if (!result.battleState) {
                logWarn("End turn failed after retry");
                return false;
            }
        }
        
        currentState = { ...result.battleState };
        heroHp = currentState.hero_hp || heroHp;
        monsterHp = currentState.monster_hp || monsterHp;
        roundValue = currentState.current_round || roundValue;
        
        logBattle(`Round ${roundValue} | Hero: ${heroHp} HP | Monster: ${monsterHp} HP`);
        
        cardsInHand = [...result.availableCards];
        usageMap = {};
        
        if (monsterHp < roundStartMonsterHp) {
            noDamageRounds = 0;
        } else {
            noDamageRounds++;
            if (noDamageRounds >= 5) {
                logWarn("No damage dealt for 5 rounds - aborting");
                return false;
            }
        }
        turnCounter++;
    }
    logWarn("Maximum turn limit reached");
    return false;
}

async function claimAllRankRewards(gameAuthToken) {
    logInfo("Claiming rank rewards...");
    const headers = { "Authorization": gameAuthToken, "Content-Type": "application/json" };
    const rankOrder = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Knight"];
    const romanMap = { 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V" };
    let successCount = 0;
    let stopAll = false;
    
    for (const rankName of rankOrder) {
        if (stopAll) break;
        let rankHadSuccess = false;
        for (let level = 1; level <= 5; level++) {
            if (stopAll) break;
            const rankKey = `${rankName}_${level}`;
            const romanLevel = romanMap[level] || String(level);
            for (const isPremium of [false, true]) {
                const trackLabel = isPremium ? "Premium" : "Basic";
                const payload = {
                    rank: rankKey,
                    isPremium: isPremium
                };
                const { response, data } = await performRequest("POST", `${NEURA_BASE_URL}/api/user/rewards/claim`, headers, payload);
                if (response.status === 200 && data.success) {
                    const rewardData = (data.data || {}).reward || {};
                    const rewardType = safeText(rewardData.type || "Unknown");
                    const rewardValue = rewardData.value || "?";
                    logReward(`${rankName} ${romanLevel} ${trackLabel}: ${rewardValue} ${rewardType}`);
                    successCount++;
                    rankHadSuccess = true;
                } else {
                    if (rankHadSuccess) {
                        stopAll = true;
                        break;
                    }
                }
            }
        }
    }
    logSuccess(`Claimed ${successCount} rank reward(s)`);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function sleepUntilReset() {
    const nowUtc = new Date();
    const todayMidnightUtc = new Date(Date.UTC(nowUtc.getUTCFullYear(), nowUtc.getUTCMonth(), nowUtc.getUTCDate()));
    const nextMidnightUtc = new Date(todayMidnightUtc.getTime() + 24 * 60 * 60 * 1000);
    
    logWarn("All locations locked - waiting for daily reset...");
    
    while (true) {
        const nowUtcLoop = new Date();
        const remaining = (nextMidnightUtc.getTime() - nowUtcLoop.getTime()) / 1000;
        if (remaining <= 0) {
            logSuccess("Daily reset reached!");
            break;
        }
        const hours = Math.floor(remaining / 3600);
        const minutes = Math.floor((remaining % 3600) / 60);
        const seconds = Math.floor(remaining % 60);
        logInfo(`Next reset in: ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
        await sleep(60000);
    }
}

async function completeQuestsMode(tokens) {
    console.log();
    printDoubleLine(50);
    console.log(`${GREEN}${BOLD}${centerText('QUEST COMPLETION MODE', 50)}${RESET}`);
    printDoubleLine(50);
    console.log();
    
    for (let i = 0; i < tokens.length; i++) {
        console.log();
        printLine('-', 40, CYAN);
        logInfo(`Processing Account ${i + 1}/${tokens.length}`);
        printLine('-', 40, CYAN);
        
        try {
            const { novaId, gameToken } = await fetchProfile(tokens[i]);
            const quests = await fetchQuests(gameToken);
            await claimAllQuests(gameToken, quests);
            await claimAllRankRewards(gameToken);
            logSuccess(`Account ${i + 1} quest completion finished`);
        } catch (e) {
            logError(`Account ${i + 1} failed: ${e.message}`);
        }
    }
    
    console.log();
    printDoubleLine(50);
    logSuccess("All accounts processed");
    printDoubleLine(50);
}

async function startBattleMode(tokens) {
    console.log();
    printDoubleLine(50);
    console.log(`${MAGENTA}${BOLD}${centerText('BATTLE MODE', 50)}${RESET}`);
    printDoubleLine(50);
    console.log();
    
    for (let i = 0; i < tokens.length; i++) {
        console.log();
        printLine('-', 40, MAGENTA);
        logInfo(`Processing Account ${i + 1}/${tokens.length}`);
        printLine('-', 40, MAGENTA);
        
        try {
            const { novaId, gameToken } = await fetchProfile(tokens[i]);
            let cards = await fetchCards(novaId);
            let cardMap = buildCardMap(cards);
            let bestBySlot = chooseBestCardsForSlots(cardMap, "Hero");
            await equipCards(gameToken, "Hero", bestBySlot);
            
            const { battleState, availableCards, allUnavailable } = await startBattle(gameToken);
            
            if (allUnavailable) {
                logWarn("All locations unavailable for this account");
                continue;
            }
            
            await runBattleLoop(gameToken, cardMap, battleState, availableCards);
            logSuccess(`Account ${i + 1} battle sequence finished`);
        } catch (e) {
            logError(`Account ${i + 1} failed: ${e.message}`);
        }
    }
    
    console.log();
    printDoubleLine(50);
    logSuccess("All accounts processed");
    printDoubleLine(50);
}

async function autoAllMode(tokens) {
    console.log();
    printDoubleLine(50);
    console.log(`${CYAN}${BOLD}${centerText('FULL AUTO MODE', 50)}${RESET}`);
    printDoubleLine(50);
    console.log();
    
    while (true) {
        for (let i = 0; i < tokens.length; i++) {
            console.log();
            printLine('=', 50, CYAN);
            logInfo(`Processing Account ${i + 1}/${tokens.length}`);
            printLine('=', 50, CYAN);
            console.log();
            
            try {
                const { novaId, gameToken } = await fetchProfile(tokens[i]);
                
                let cards = await fetchCards(novaId);
                let cardMap = buildCardMap(cards);
                let bestBySlot = chooseBestCardsForSlots(cardMap, "Hero");
                await equipCards(gameToken, "Hero", bestBySlot);
                
                const packages = await fetchPackages(novaId);
                await openAllPackages(novaId, packages);
                
                cards = await fetchCards(novaId);
                cardMap = buildCardMap(cards);
                bestBySlot = chooseBestCardsForSlots(cardMap, "Hero");
                await equipCards(gameToken, "Hero", bestBySlot);
                
                const quests = await fetchQuests(gameToken);
                await claimAllQuests(gameToken, quests);
                await claimAllRankRewards(gameToken);
                
                console.log();
                logInfo("Starting battle sequence...");
                
                const { battleState, availableCards, allUnavailable } = await startBattle(gameToken);
                
                if (allUnavailable) {
                    await sleepUntilReset();
                    continue;
                }
                
                await runBattleLoop(gameToken, cardMap, battleState, availableCards);
                
                console.log();
                logSuccess(`Account ${i + 1} cycle completed`);
                
            } catch (e) {
                logError(`Account ${i + 1} error: ${e.message}`);
                await sleep(3000);
            }
        }
        
        console.log();
        logInfo("Cycle complete - starting next cycle in 3 seconds...");
        await sleep(3000);
    }
}

function createReadlineInterface() {
    return readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
}

async function askQuestion(rl, question) {
    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            resolve(answer.trim());
        });
    });
}

async function main() {
    setTitle();
    banner();
    
    const rl = createReadlineInterface();
    let tokens = null;
    
    try {
        tokens = loadAccessTokens();
    } catch (e) {
        logError("Failed to load tokens");
        rl.close();
        return;
    }
    
    let running = true;
    
    while (running) {
        showMenu();
        const choice = await askQuestion(rl, `  ${CYAN}${BOLD}Select option [1-4]:${RESET} `);
        
        switch (choice) {
            case '1':
                console.log();
                logInfo("Starting Quest Completion Mode...");
                await completeQuestsMode(tokens);
                console.log();
                await askQuestion(rl, `  ${DIM}Press Enter to continue...${RESET}`);
                banner();
                break;
                
            case '2':
                console.log();
                logInfo("Starting Battle Mode...");
                await startBattleMode(tokens);
                console.log();
                await askQuestion(rl, `  ${DIM}Press Enter to continue...${RESET}`);
                banner();
                break;
                
            case '3':
                console.log();
                logInfo("Starting Full Auto Mode (Press Ctrl+C to stop)...");
                rl.close();
                await autoAllMode(tokens);
                return;
                
            case '4':
                console.log();
                printLine('-', 50, RED);
                logInfo("Exiting bot... Goodbye!");
                printLine('-', 50, RED);
                running = false;
                break;
                
            default:
                console.log();
                logError("Invalid option! Please select 1, 2, 3, or 4");
                await sleep(1000);
                banner();
        }
    }
    
    rl.close();
}

main().catch((e) => {
    logError(`Fatal error: ${e.message}`);
    console.error(e);
    process.exit(1);
});