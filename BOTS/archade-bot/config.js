// config.js
// Constants and Configuration

module.exports = {
    // API Endpoints
    RPC_URL: "https://solana-devnet.g.alchemy.com/v2/tnXWZRfORKaKRWc_OcRWq",
    API_BASE_URL: "https://archade.io/api",

    // Auth
    // Extracted from logs - User should update if expired
    DEFAULT_AUTH_TOKEN: "124e1b32-12f9-484b-b311-8e0742205dbf",

    // Default Token for testing (KAZUHA)
    DEFAULT_MINT: "EjaiRtBzm5ekm72sr2HWAQSqb64SYJ5iTkMMYM5R8sWg",

    // Target wallet for tasks (follow, like, comment)
    TARGET_WALLET: "32EmHth7X4iXTNkve3TiTKBURqPtJFJCR5KR13ReG9QV",

    // Target post ID for likes and comments
    TARGET_POST_ID: "ae9e755b-1f38-434b-adaa-d9de556230be",

    // Headers
    HEADERS: {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36 Edg/144.0.0.0",
        "Origin": "https://archade.io",
        "Referer": "https://archade.io/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
};
