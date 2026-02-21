// api.js - API Client
const axios = require('axios');
const config = require('./config');
const FormData = require('form-data');
const fs = require('fs');
const { log } = require('./utils');
const { parseProxyConfig } = require('./proxy');

let apiClient = null;

/**
 * Initialize or update API client with optional proxy
 */
function createApiClient(proxyUrl = null) {
    const clientConfig = {
        baseURL: config.API_BASE_URL,
        headers: {
            ...config.HEADERS,
            'Authorization': `Bearer ${config.DEFAULT_AUTH_TOKEN}`
        }
    };

    // Add proxy configuration if provided
    if (proxyUrl) {
        const proxyConfig = parseProxyConfig(proxyUrl);
        if (proxyConfig) {
            clientConfig.proxy = proxyConfig;
            log('info', `API Client using proxy: ${proxyConfig.host}:${proxyConfig.port}`);
        }
    }

    apiClient = axios.create(clientConfig);
    return apiClient;
}

/**
 * Get or create API client
 */
function getApiClient() {
    if (!apiClient) {
        createApiClient();
    }
    return apiClient;
}

/**
 * Set proxy for API client
 */
function setProxy(proxyUrl) {
    createApiClient(proxyUrl);
}

// Initialize default client
createApiClient();

async function downloadRandomImage(targetPath) {
    try {
        const url = 'https://picsum.photos/500'; // Random image source
        const writer = fs.createWriteStream(targetPath);

        const response = await axios({
            url,
            method: 'GET',
            responseType: 'stream'
        });

        response.data.pipe(writer);

        return new Promise((resolve, reject) => {
            writer.on('finish', resolve);
            writer.on('error', reject);
        });
    } catch (error) {
        log('error', `Image Download Failed: ${error.message}`);
        throw error;
    }
}

async function getStats(mint) {
    try {
        const response = await getApiClient().get(`/trading/stats?mint=${mint}&fresh=true`);
        return response.data;
    } catch (error) {
        log('error', `Get Stats Failed: ${error.message}`);
        return null;
    }
}

async function prepareTrade(mint, user, amountSol, mode, slippage = 1) {
    try {
        const payload = { mint, user, amountSol, mode, slippage };
        const response = await getApiClient().post('/trade/prepare', payload);
        return response.data;
    } catch (error) {
        log('error', `Prepare Trade Failed: ${error.message}`);
        return null;
    }
}

async function recordTrade(tradeData) {
    try {
        const response = await getApiClient().post('/trade/record', tradeData);
        return response.data;
    } catch (error) {
        // 403 means we aren't authorized to record, but the trade happened on chain.
        log('warn', `Record Trade API Skipped: ${error.message} (On-chain tx successful)`);
        return null;
    }
}

async function uploadImage(imagePath) {
    try {
        const form = new FormData();
        form.append('file', fs.createReadStream(imagePath));

        const response = await getApiClient().post('/pinata/upload', form, {
            headers: {
                ...form.getHeaders()
            }
        });
        return response.data;
    } catch (error) {
        log('error', `Upload Image Failed: ${error.message}`);
        return null;
    }
}

async function uploadMetadata(name, symbol, description, imageUrl) {
    try {
        const payload = {
            name,
            symbol,
            description,
            image: imageUrl,
            properties: {
                files: [{ uri: imageUrl, type: "image/jpeg" }],
                category: "image"
            }
        };
        const response = await getApiClient().post('/pinata/json', payload);
        return response.data;
    } catch (error) {
        log('error', `Upload Metadata Failed: ${error.message}`);
        return null;
    }
}

async function createGroup(groupPayload) {
    try {
        const response = await getApiClient().post('/messages/group/create', groupPayload);
        return response.data;
    } catch (error) {
        log('error', `Create Group Failed: ${error.message}`);
        return null;
    }
}

async function createToken(tokenPayload) {
    try {
        const response = await getApiClient().post('/token/create', tokenPayload);
        return response.data;
    } catch (error) {
        log('error', `Create Token Failed: ${error.message}`);
        return null;
    }
}

async function follow(targetWallet) {
    try {
        const response = await getApiClient().post('/follow', { following: targetWallet });
        return response.data;
    } catch (error) {
        log('error', `Follow Failed: ${error.message}`);
        return null;
    }
}

async function likePost(postId) {
    try {
        const response = await getApiClient().post('/posts/like', { post_id: postId });
        return response.data;
    } catch (error) {
        log('warn', `Like Failed: ${error.message}`);
        return null;
    }
}

async function commentOnPost(postId, comment) {
    try {
        const response = await getApiClient().post('/comments', {
            post_id: postId,
            content: comment
        });
        return response.data;
    } catch (error) {
        log('warn', `Comment Failed: ${error.message}`);
        return null;
    }
}

module.exports = {
    setProxy,
    getStats,
    prepareTrade,
    recordTrade,
    uploadImage,
    uploadMetadata,
    createGroup,
    createToken,
    follow,
    likePost,
    commentOnPost,
    downloadRandomImage
};
