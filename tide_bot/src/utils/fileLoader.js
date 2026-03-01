import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import config from '../core/config.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '../..');

export function loadAccounts(filePath = 'accounts.txt') {
  const fullPath = path.join(ROOT_DIR, filePath);

  if (!fs.existsSync(fullPath)) {
    const sample = [
      '# Mỗi dòng 1 private key (hex) hoặc seed phrase',
      '# Ví dụ private key:',
      '# 0xabc123def456...',
      '# Ví dụ seed phrase:',
      '# word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
      ''
    ].join('\n');
    fs.writeFileSync(fullPath, sample, 'utf-8');
    return [];
  }

  const lines = fs.readFileSync(fullPath, 'utf-8')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#'));

  const accounts = [];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];

    if (raw.includes(' ') && raw.split(/\s+/).length >= 12) {
      accounts.push({
        index: accounts.length + 1,
        raw: raw,
        type: 'seedphrase'
      });
    }
    else if (/^(0x)?[a-fA-F0-9]{64}$/.test(raw) || /^(suiprivkey)[a-zA-Z0-9]+$/i.test(raw)) {
      accounts.push({
        index: accounts.length + 1,
        raw: raw,
        type: 'privatekey'
      });
    }
    else if (raw.length > 10) {
      accounts.push({
        index: accounts.length + 1,
        raw: raw,
        type: 'privatekey'
      });
    }
  }

  return accounts;
}

export function loadProxies(filePath = 'proxy.txt') {
  const fullPath = path.join(ROOT_DIR, filePath);

  if (!fs.existsSync(fullPath)) {
    const sample = [
      '# Mỗi dòng 1 proxy, hỗ trợ các format:',
      '# host:port',
      '# host:port:user:pass',
      '# http://user:pass@host:port',
      '# socks5://user:pass@host:port',
      ''
    ].join('\n');
    fs.writeFileSync(fullPath, sample, 'utf-8');
    return [];
  }

  const lines = fs.readFileSync(fullPath, 'utf-8')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#'));

  return lines.map(raw => parseProxy(raw)).filter(Boolean);
}

function parseProxy(raw) {
  try {
    const urlMatch = raw.match(/^(https?|socks[45]?):\/\/(?:([^:]+):([^@]+)@)?([^:]+):(\d+)$/i);
    if (urlMatch) {
      return {
        raw,
        protocol: urlMatch[1].toLowerCase(),
        host: urlMatch[4],
        port: parseInt(urlMatch[5]),
        username: urlMatch[2] || null,
        password: urlMatch[3] || null,
        url: raw
      };
    }

    const parts = raw.split(':');
    const defaultProto = config.proxy?.protocol || 'http';
    if (parts.length === 4 && !raw.includes('//')) {
      return {
        raw,
        protocol: defaultProto,
        host: parts[0],
        port: parseInt(parts[1]),
        username: parts[2],
        password: parts[3],
        url: `${defaultProto}://${parts[2]}:${parts[3]}@${parts[0]}:${parts[1]}`
      };
    }

    if (parts.length === 2) {
      return {
        raw,
        protocol: defaultProto,
        host: parts[0],
        port: parseInt(parts[1]),
        username: null,
        password: null,
        url: `${defaultProto}://${parts[0]}:${parts[1]}`
      };
    }

    return null;
  } catch {
    return null;
  }
}

export function assignProxy(accountIndex, proxies) {
  if (!proxies || proxies.length === 0) return null;
  if (config.proxy?.randomProxy) {
    return proxies[Math.floor(Math.random() * proxies.length)];
  }
  return proxies[(accountIndex - 1) % proxies.length];
}

export default { loadAccounts, loadProxies, assignProxy };
