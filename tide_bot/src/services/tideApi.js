import axios from 'axios';
import { HttpsProxyAgent } from 'https-proxy-agent';
import { SocksProxyAgent } from 'socks-proxy-agent';
import config from '../core/config.js';
import { getFingerprintHeaders } from './deviceFingerprint.js';
import { assignProxy, loadProxies } from '../utils/fileLoader.js';

const BASE_URL = config.api.tideBaseUrl || 'https://tide.am/api';

let _proxiesCache = null;
function getProxies() {
  if (!_proxiesCache) _proxiesCache = loadProxies();
  return _proxiesCache;
}

function createProxyAgent(proxyObj) {
  if (!proxyObj || !proxyObj.url) return null;
  const proto = proxyObj.protocol || 'http';
  if (proto.startsWith('socks')) return new SocksProxyAgent(proxyObj.url);
  return new HttpsProxyAgent(proxyObj.url);
}

function createClient(walletAddress, proxyObj) {
  const headers = getFingerprintHeaders(walletAddress);
  const refCode = config.referral?.enabled && config.referral?.code
    ? config.referral.code
    : null;

  if (!proxyObj && config.proxy?.enabled) {
    const proxies = getProxies();
    if (proxies.length > 0) {
      proxyObj = proxies[Math.floor(Math.random() * proxies.length)];
    }
  }

  const agent = createProxyAgent(proxyObj);
  const proxyOpts = agent ? { httpAgent: agent, httpsAgent: agent } : {};

  return axios.create({
    baseURL: BASE_URL,
    timeout: 15000,
    ...proxyOpts,
    headers: {
      ...headers,
      'Accept': 'application/json',
      'Origin': 'https://tide.am',
      'Referer': refCode
        ? `https://tide.am/r/${refCode}`
        : 'https://tide.am/',
      ...(refCode ? { 'Cookie': `ref=${refCode}` } : {})
    }
  });
}

export async function getListings(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/listings');
  return res.data;
}

export async function getActiveListing(walletAddress, proxyObj) {
  const data = await getListings(walletAddress, proxyObj);
  const listings = data?.data?.listings || [];
  const active = listings.find(l => l.state !== 'FINALIZED' && l.state !== 'RELEASED');
  if (active) return active;
  return listings[0] || null;
}

export async function getPasses(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get(`/passes?owner=${walletAddress}`);
  return res.data;
}

export async function getMarketplace(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/marketplace');
  return res.data;
}

export async function getLoans(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get(`/loans?borrower=${walletAddress}`);
  return res.data;
}

export async function getPrice(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/price');
  return res.data;
}

export async function getUserPoints(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get(`/points/user/${walletAddress}`);
  return res.data;
}

export async function getLeaderboard(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/points/leaderboard');
  return res.data;
}

export async function getPointsHistory(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get(`/points/history/${walletAddress}`);
  return res.data;
}

export async function getProtocolStats(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/protocol/stats');
  return res.data;
}

export async function getFaithProtocol(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/protocol/faith-protocol');
  return res.data;
}

export async function getTreasury(walletAddress, proxyObj) {
  const client = createClient(walletAddress, proxyObj);
  const res = await client.get('/treasury/faith-protocol');
  return res.data;
}

export async function applyReferral(walletAddress, proxyObj) {
  const refCode = config.referral?.code;
  if (!refCode) throw new Error('No referral code configured');
  const client = createClient(walletAddress, proxyObj);
  const res = await client.post('/points/referral', {
    referralCode: refCode,
    newUserAddress: walletAddress
  });
  return res.data;
}

export async function getCheapestListings(walletAddress, maxPrice = 5_000_000_000, limit = 200, proxyObj) {
  try {
    const data = await getMarketplace(walletAddress, proxyObj);
    const listings = data?.data?.listings || [];
    return listings
      .filter(l => {
        const price = Number(l.price || l.priceMist || 0);
        return price > 0 && price <= maxPrice && l.seller !== walletAddress;
      })
      .sort((a, b) => Number(a.price || a.priceMist || 0) - Number(b.price || b.priceMist || 0))
      .slice(0, limit);
  } catch {
    return [];
  }
}

export function resetProxyCache() {
  _proxiesCache = null;
}

export default {
  getListings, getActiveListing, getPasses, getMarketplace, getLoans, getPrice,
  getUserPoints, getLeaderboard, getPointsHistory,
  getProtocolStats, getFaithProtocol, getTreasury, applyReferral, getCheapestListings, resetProxyCache
};
