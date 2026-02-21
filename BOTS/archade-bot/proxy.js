// proxy.js - Proxy Management
const fs = require('fs');
const { log } = require('./utils');

let proxies = [];

/**
 * Load all proxies from proxy.txt
 * Format: One proxy per line
 * Supported formats:
 * - http://ip:port
 * - http://user:pass@ip:port
 * - https://ip:port
 * - socks5://ip:port
 */
function loadProxies() {
    try {
        if (!fs.existsSync('proxy.txt')) {
            log('warn', 'proxy.txt not found. Running without proxies.');
            proxies = [];
            return proxies;
        }

        const content = fs.readFileSync('proxy.txt', 'utf-8');
        proxies = content
            .split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#')); // Filter empty lines and comments

        if (proxies.length === 0) {
            log('warn', 'proxy.txt is empty. Running without proxies.');
        } else {
            log('info', `Loaded ${proxies.length} proxy(ies) from proxy.txt`);
        }

        return proxies;
    } catch (err) {
        log('error', `Failed to load proxies: ${err.message}`);
        proxies = [];
        return proxies;
    }
}

/**
 * Get proxy for specific account index
 * If no proxy exists for that index, returns null
 */
function getProxy(accountIndex) {
    if (accountIndex < 0 || accountIndex >= proxies.length) {
        return null;
    }
    return proxies[accountIndex];
}

/**
 * Parse proxy URL into axios-compatible config
 */
function parseProxyConfig(proxyUrl) {
    if (!proxyUrl) return null;

    try {
        const url = new URL(proxyUrl);

        const config = {
            protocol: url.protocol.replace(':', ''),
            host: url.hostname,
            port: parseInt(url.port) || (url.protocol === 'https:' ? 443 : 80)
        };

        // Add auth if present
        if (url.username && url.password) {
            config.auth = {
                username: url.username,
                password: url.password
            };
        }

        return config;
    } catch (err) {
        log('error', `Invalid proxy URL: ${proxyUrl}`);
        return null;
    }
}

/**
 * Get total number of proxies loaded
 */
function getProxyCount() {
    return proxies.length;
}

module.exports = {
    loadProxies,
    getProxy,
    parseProxyConfig,
    getProxyCount
};
