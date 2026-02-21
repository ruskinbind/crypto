# ==================== CONFIGURATION ====================

# Network Config
RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002
EXPLORER_URL = "https://testnet.arcscan.app"

# Contract Addresses
ROUTER_CONTRACT = "0xE9f3e9a6c9304D384c38ad8DB5b4707580e8714C"
WUSDC_CONTRACT = "0x911b4000D3422F482F4062a913885f7b035382Df"
USDC_CONTRACT = "0x3600000000000000000000000000000000000000"

# Liquidity Constants
LIQUIDITY_ROUTER = "0xfeB8a2648b1C0112aaF69014Acc071a3e6491C14"
POOL_TOKEN = "0x97c0194480Adb526194835D2688A333BBE55d770"
USDC_A_TOKEN = "0xC0D12A7Cf565A004757c62cAF34Dd37467F57f0e"

# SwapArcDex Constants
ARCDEX_POOL = "0x2F4490e7c6F3DaC23ffEe6e71bFcb5d1CCd7d4eC"
SWAPARC_POOL_V2 = "0xd22e4fB80E21e8d2C91131eC2D6b0C000491934B"
SWAPARC_LP_TOKEN = "0x454f21b7738A446f79ea4ff00e71b9e8E9E6FEE9"
EURC_TOKEN = "0x89b50855aa3be2f677cd6303cec089b5f319d72a"
SWPRC_TOKEN = "0xbe7477bf91526fc9988c8f33e91b6db687119d45"

# NFT Contracts
NFT_CONTRACTS = {
    "KIKO": {
        "address": "0x84C76A7bc68eDE072B630F5c5d3531f874aaEf7C",
        "name": "KIKIO",
        "price": 1.5,
        "price_wei": "0x14d1120d7b160000"
    },
    "FLORA": {
        "address": "0x34c9BC2d07CD57aE7D026dE730380D47BCA7D9A5",
        "name": "FLORA",
        "price": 1.0,
        "price_wei": "0x0de0b6b3a7640000"
    },
    "CANVAS": {
        "address": "0x3636d635bA461ee9e14D2EEC3BA31Fcf4776ed41",
        "name": "CANVAS (FREE)",
        "price": 0,
        "price_wei": "0x0"
    }
}

# API Endpoints
QUOTE_API = "https://testnet.axpha.io/api/Aggregator/5042002/solver/quote"
PRICE_API = "https://api.diadata.org/v1/quotation/USDC"

# Arcade API Config
ARCADE_BASE_URL = "https://www.arcadeonarc.fun"
DYNAMIC_AUTH_URL = "https://app.dynamicauth.com/api/v0/sdk"
DYNAMIC_ENV_ID = "a3744fd0-3794-4b60-a36a-57dbdbda6855"

# Swap Tokens
SWAP_TOKENS = {
    "1": {"address": "0x89b50855aa3be2f677cd6303cec089b5f319d72a", "symbol": "EURC", "decimals": 6},
    "2": {"address": "0x808e4e5a6006296b274c02683d17047bea92e6ba", "symbol": "AD", "decimals": 18},
    "3": {"address": "0xe8bc5d6c5bd36b1984b54a5b593f61ae668acc27", "symbol": "Circle", "decimals": 18},
    "4": {"address": "0x52654c73dbc772c015effdc600794daf1475be4f", "symbol": "ARC", "decimals": 18},
    "5": {"address": "0x0248bac1a78a324a7e16387b6277b96b24c3b026", "symbol": "Panic", "decimals": 18},
    "6": {"address": "0x6415b825099d6b6d74eb7a9ff18a15f47699db13", "symbol": "HM", "decimals": 18}
}

# ArcDex Tokens
ARCDEX_TOKENS = {
    "USDC": {"address": USDC_CONTRACT, "index": 0, "decimals": 6},
    "EURC": {"address": EURC_TOKEN, "index": 1, "decimals": 6},
    "SWPRC": {"address": SWPRC_TOKEN, "index": 2, "decimals": 6}
}

# ABIs
WUSDC_ABI = [
    {"inputs": [], "name": "deposit", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]