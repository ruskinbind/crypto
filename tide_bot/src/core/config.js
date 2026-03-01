import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '../..');
const CONFIG_PATH = path.join(ROOT_DIR, 'config.json');

const DEFAULT_CONFIG = {
  threads: 5,

  // Delay ngẫu nhiên giữa các action (ms)
  delay: { min: 3000, max: 7000 },

  // Cấu hình API
  api: {
    tideBaseUrl: 'https://tide.am/api',
    suiRpc: 'https://fullnode.testnet.sui.io/',
    faucetUrl: 'https://faucet.testnet.sui.io'
  },

  // Bật/tắt từng tính năng
  features: {
    faucet: true,        // Claim SUI testnet faucet
    deposit: true,       // Deposit SUI vào Tide
    mintPass: true,      // Mint supporter pass
    claimRewards: true,  // Claim rewards
    borrow: true,        // Borrow SUI
    tradePass: true,     // Mua/bán pass trên marketplace
    dailyLoop: true      // Lặp lại hàng ngày
  },

  // Cấu hình proxy
  proxy: {
    enabled: false,
    protocol: 'socks5'     // 'http' | 'https' | 'socks5' | 'socks4' - dùng khi proxy.txt không có prefix
  },

  // Cấu hình captcha (cho faucet)
  captcha: {
    service: 'capsolver',     // '2captcha' | 'capmonster' | 'capsolver'
    apiKey2Captcha: '',
    apiKeyCapslover: '',
    apiKeyCapmonster: ''
  },

  // Cấu hình faucet
  faucet: {
    maxClaims: 5,            // Số lần claim tối đa mỗi phiên (SUI cho ~5 lần/ngày)
    delayBetween: 5000       // Delay giữa mỗi lần claim (ms)
  },

  // Cấu hình deposit
  deposit: {
    amountSUI: 1            // Số SUI deposit vào Tide (tối thiểu 1 SUI)
  },

  // Cấu hình marketplace (buy+sell loop)
  marketplace: {
    maxBuyPrice: 5000000000,  // Giá tối đa mua pass (in MIST, 5 SUI)
    sellPrice: 3000000000,    // Giá bán pass (in MIST, 3 SUI)
    repeatCount: 3            // Số lần lặp buy→sell mỗi chu kỳ
  },

  // Cấu hình loan (borrow+repay loop)
  loan: {
    borrowAmount: 0.5,        // Số SUI vay mỗi lần (MIST)
    repeatCount: 3            // Số lần lặp borrow→repay mỗi chu kỳ
  },

  // Cấu hình referral
  referral: {
    enabled: true,
    code: 'TIDE-249BF61FYYCX'
  },

  // Cấu hình rescue SUI (chuyển SUI giữa các ví khi faucet fail)
  rescue: {
    enabled: true,           // Bật/tắt rescue
    minBalance: 1.0,         // Ví có balance < minBalance sẽ được rescue
    reserveBalance: 1.0,     // Giữ lại ít nhất X SUI trong ví donor
    maxTransfer: 5.0,        // Tối đa chuyển X SUI mỗi lần
    runBefore: true          // Chạy rescue bulk scan trước mỗi chu kỳ farming
  },

  // Cấu hình gom SUI (thu hồi tất cả SUI về 1 ví)
  collect: {
    targetIndex: 0,          // Ví đích (index trong accounts.txt, 0 = ví đầu tiên)
    targetAddress: '',       // Hoặc chỉ định địa chỉ ví đích (ưu tiên hơn targetIndex)
    minKeep: 0.01            // Giữ lại tối thiểu X SUI trong mỗi ví nguồn
  },

  // Cấu hình schedule (24/7 farming)
  schedule: {
    intervalHours: 6        // Lặp lại mỗi X giờ (6h = 4 chu kỳ/ngày)
  }
};

export const CONTRACTS = {
  corePackage: '0xbf119a288b73ea42990f87a978c376d168b35439ce06c28d16fc8f5cfe2ebbae',
  marketplacePackage: '0x53eedd7e88c454de73d0edea1aaeba07218cd5108fde2f07d3a987a140c10d80',
  loansPackage: '0xbec1ffea9715d7a5d909e170b7c4f42f149ea8f8398f7c3c143c7f384a99a5ce',

  tideConfig: '0x4ec2294cf9991e99b510eb4ac7f9f205da82738eaf3a95d46ad64e902740adba',
  listing: '0xac9da36f4a5a1b82ba01ae7853c8a57c0cb24ec747b1516e65fab81596901178',
  marketplace: '0xad829858b1c8d879a21db90c9b85834a2d39f9161e6439d390b6fd3acab3828e',
  loanVault: '0xe2a43b983c01016c16fc9c46bc2d836bb8d84b6f2a921b1af68b051b5502565e',
  treasuryVault: '0xd560280699a4eb863f9f000bbd63cab2d7e04c2ae5ddc6896df68369a7c32d59',

  registry: '0xa165153b9e4c5f29d906e44adca26ed1b0bba575da611595c594b9730a108df7',
  depositPool: '0x9d7208daba050739ed6c7c92534559015ce1a20dfb737ea455f1ed6e845dba2e',

  supporterPassType: '0xbf119a288b73ea42990f87a978c376d168b35439ce06c28d16fc8f5cfe2ebbae::supporter_pass::SupporterPass',
  loanReceiptType: '0xbec1ffea9715d7a5d909e170b7c4f42f149ea8f8398f7c3c143c7f384a99a5ce::loan_vault::LoanReceipt',
  saleListingType: '0x53eedd7e88c454de73d0edea1aaeba07218cd5108fde2f07d3a987a140c10d80::marketplace::SaleListing',
  suiCoinType: '0x2::coin::Coin<0x2::sui::SUI>',
  clock: '0x6'
};

export const FAUCET_CONFIG = {
  challengeUrl: 'https://faucet.testnet.sui.io/v2/request_challenge',
  gasUrl: 'https://faucet.testnet.sui.io/v2/faucet_web_gas',
  turnsiteSiteKey: '0x4AAAAAAA11HKyGNZq_dUKj',

};

function deepMerge(target, source) {
  const result = { ...target };
  for (const key of Object.keys(source)) {
    if (
      source[key] &&
      typeof source[key] === 'object' &&
      !Array.isArray(source[key]) &&
      target[key] &&
      typeof target[key] === 'object' &&
      !Array.isArray(target[key])
    ) {
      result[key] = deepMerge(target[key], source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
}

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(DEFAULT_CONFIG, null, 2), 'utf-8');
    console.log(`⚙️ Đã tạo config.json mặc định tại: ${CONFIG_PATH}`);
    return { ...DEFAULT_CONFIG };
  }

  try {
    const raw = fs.readFileSync(CONFIG_PATH, 'utf-8');
    const userConfig = JSON.parse(raw);

    const merged = deepMerge(DEFAULT_CONFIG, userConfig);

    fs.writeFileSync(CONFIG_PATH, JSON.stringify(merged, null, 2), 'utf-8');

    return merged;
  } catch (err) {
    console.error(`❌ Lỗi đọc config.json: ${err.message}. Sử dụng config mặc định.`);
    return { ...DEFAULT_CONFIG };
  }
}

const config = loadConfig();
export default config;
