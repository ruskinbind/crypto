import chalk from 'chalk';
import dayjs from 'dayjs';

const PROJECT_NAME = 'Tide';

export function shortWallet(addr) {
  if (!addr || addr.length < 10) return addr || '-';
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function normalizeAddress(addr) {
  if (!addr) return addr;
  let hex = String(addr).toLowerCase().trim();
  if (hex.startsWith('0x')) hex = hex.slice(2);
  if (hex.length === 64) return '0x' + hex;
  if (hex.length < 64) return '0x' + hex.padStart(64, '0');
  return '0x' + hex;
}

function formatTime() {
  return dayjs().format('HH:mm:ss');
}

export function friendlyError(msg) {
  if (!msg) return 'Lỗi không xác định';
  const s = String(msg);

  if (s.includes('InsufficientGas') || s.includes('InsufficientCoinBalance'))
    return 'Không đủ SUI để trả phí gas. Cần nhận faucet.';
  if (s.includes('INSUFFICIENT_BALANCE'))
    return 'Số dư không đủ để thực hiện giao dịch.';
  if (s.includes('ObjectNotFound'))
    return 'Object không tồn tại trên chain (sai ID hoặc chưa tạo).';
  if (s.includes('MoveAbort'))
    return `Lỗi Move contract: ${s.slice(0, 150)}`;
  if (s.includes('ECONNREFUSED') || s.includes('ECONNRESET'))
    return 'Không kết nối được server. Kiểm tra mạng/proxy.';
  if (s.includes('ETIMEDOUT') || s.includes('timeout'))
    return 'Kết nối timeout. Mạng chậm hoặc server không phản hồi.';
  if (s.includes('429') || s.includes('Too Many Requests'))
    return 'Bị giới hạn tần suất. Chờ vài giờ rồi thử lại.';
  if (s.includes('500') || s.includes('Internal Server Error'))
    return 'Server lỗi nội bộ. Thử lại sau.';
  if (s.includes('captcha') || s.includes('Turnstile'))
    return 'Lỗi giải captcha. Kiểm tra API key và service.';
  if (s.includes('faucet'))
    return 'Lỗi faucet. Có thể đã nhận rồi hoặc bị giới hạn.';
  if (s.includes('TransactionExpired'))
    return 'Giao dịch hết hạn. Thử lại sau.';
  if (s.includes('quorum'))
    return 'Không đủ validator xác nhận. Mạng testnet đang chậm.';

  if (s.length > 200) {
    const errorPart = s.match(/failed with an error:\s*(.{1,150})/);
    if (errorPart) return errorPart[1].trim();
    return s.slice(0, 150) + '...';
  }

  return s;
}

const badges = {
  'FAUCET':    (t) => chalk.bgHex('#0288D1').white.bold(` ${t} `),      // Ocean blue
  'CAPTCHA':   (t) => chalk.bgHex('#7B1FA2').white.bold(` ${t} `),      // Purple
  'POW':       (t) => chalk.bgHex('#5C6BC0').white.bold(` ${t} `),      // Indigo

  'DEPOSIT':   (t) => chalk.bgHex('#0277BD').white.bold(` ${t} `),      // Deep ocean blue
  'WITHDRAW':  (t) => chalk.bgHex('#C2185B').white.bold(` ${t} `),      // Cherry pink
  'MINT':      (t) => chalk.bgHex('#8E24AA').white.bold(` ${t} `),      // Violet
  'CLAIM':     (t) => chalk.bgHex('#00897B').white.bold(` ${t} `),      // Teal
  'BORROW':    (t) => chalk.bgHex('#E91E63').white.bold(` ${t} `),      // Bright pink
  'REPAY':     (t) => chalk.bgHex('#F06292').white.bold(` ${t} `),      // Sakura pink
  'TRADE':     (t) => chalk.bgHex('#039BE5').white.bold(` ${t} `),      // Light ocean blue

  'LIST':      (t) => chalk.bgHex('#0097A7').white.bold(` ${t} `),      // Cyan ocean
  'BUY':       (t) => chalk.bgHex('#00ACC1').white.bold(` ${t} `),      // Aqua blue
  'DELIST':    (t) => chalk.bgHex('#D81B60').white.bold(` ${t} `),      // Rose

  'OK':        (t) => chalk.bgHex('#00897B').white.bold(` ${t} `),      // Teal
  'FAIL':      (t) => chalk.bgHex('#C62828').white.bold(` ${t} `),      // Red
  'SKIP':      (t) => chalk.bgHex('#455A64').hex('#F48FB1').bold(` ${t} `), // Gray bg pink text

  'BALANCE':   (t) => chalk.bgHex('#37474F').hex('#F8BBD0').bold(` ${t} `), // Dark bg light pink
  'POINTS':    (t) => chalk.bgHex('#37474F').hex('#B39DDB').bold(` ${t} `), // Dark bg lavender
  'PASS':      (t) => chalk.bgHex('#0097A7').white.bold(` ${t} `),      // Cyan ocean
  'LOAN':      (t) => chalk.bgHex('#E91E63').white.bold(` ${t} `),      // Bright pink
  'SUMMARY':   (t) => chalk.bgHex('#37474F').hex('#80DEEA').bold(` ${t} `), // Dark bg cyan text
  'RESCUE':    (t) => chalk.bgHex('#FF6F00').white.bold(` ${t} `),          // Amber/orange
  'POOL':      (t) => chalk.bgHex('#283593').hex('#90CAF9').bold(` ${t} `),  // Deep indigo bg
  'COLLECT':   (t) => chalk.bgHex('#1B5E20').hex('#A5D6A7').bold(` ${t} `),  // Dark green bg
  'REFERRAL':  (t) => chalk.bgHex('#7B1FA2').hex('#F3E5F5').bold(` ${t} `), // Purple bg
  'SUILEARN':  (t) => chalk.bgHex('#00796B').hex('#E0F2F1').bold(` ${t} `), // Teal bg mint text
};

function highlightMessage(message) {
  let msg = message;

  msg = msg.replace(/([0-9]+\.?[0-9]*)\s*SUI/g, (_, amt) =>
    chalk.hex('#4FC3F7').bold(amt) + chalk.hex('#80DEEA')(' SUI')
  );

  msg = msg.replace(/([0-9]+)\s*MIST/g, (_, amt) =>
    chalk.hex('#F48FB1').bold(amt) + chalk.hex('#F8BBD0')(' MIST')
  );

  msg = msg.replace(/TX: ([A-Za-z0-9+/=]{20,})/g, (_, hash) =>
    'TX: ' + chalk.hex('#80DEEA').bold(hash) + chalk.hex('#4DD0E1')(' (suiscan.xyz/testnet/tx/' + hash.slice(0,8) + '...)')
  );

  msg = msg.replace(/ID: (0x[a-f0-9]{6,}\.{0,3})/gi, (_, id) =>
    'ID: ' + chalk.hex('#CE93D8')(id)
  );

  msg = msg.replace(/(\d+)\s*points?/gi, (_, pts) =>
    chalk.hex('#F48FB1').bold(pts) + chalk.hex('#F8BBD0')(' points')
  );

  msg = msg.replace(/giá:\s*([0-9]+\.?[0-9]*)/gi, (_, p) =>
    'giá: ' + chalk.hex('#B39DDB').bold(p)
  );

  msg = msg.replace(/Fingerprint: (.+)/g, (_, fp) =>
    chalk.hex('#B0BEC5')('Fingerprint: ') + chalk.hex('#78909C')(fp)
  );

  msg = msg.replace(/(\d+)\s*(giây|phút|giờ)/g, (_, n, unit) =>
    chalk.hex('#FFD54F').bold(n) + ' ' + chalk.hex('#90CAF9')(unit)
  );

  msg = msg.replace(/Pass #(\d+)/g, (_, num) =>
    chalk.hex('#CE93D8').bold('Pass #' + num)
  );

  return msg;
}

function applyBadges(message) {
  let msg = message;

  // === SUILEARN FAUCET (must come before generic faucet badges) ===
  msg = msg.replace(/🚰\s*\[SuiLearn\]\s*Claiming faucet/g, () =>
    badges['SUILEARN']('🚰 SUILEARN') + ' Claiming...'
  );
  msg = msg.replace(/✅\s*\[SuiLearn\]\s*Claim OK/g, () =>
    badges['SUILEARN']('🚰 SUILEARN') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/⚠️\s*\[SuiLearn\]\s*(.+)/g, (_, detail) =>
    badges['SUILEARN']('🚰 SUILEARN') + ' ' + chalk.bgHex('#E65100').white.bold(' ⚠ LIMIT ') + ' ' + detail
  );
  msg = msg.replace(/❌\s*\[SuiLearn\]\s*(.+)/g, (_, detail) =>
    badges['SUILEARN']('🚰 SUILEARN') + ' ' + badges['FAIL']('LỖI ✗') + ' ' + detail
  );
  msg = msg.replace(/🎉\s*Cả 2 faucet OK/g, () =>
    badges['SUILEARN']('🚰 SUILEARN') + ' + ' + badges['FAUCET']('OFFICIAL') + ' ' + badges['OK']('COMBO ✓')
  );
  msg = msg.replace(/❌\s*Faucet Official thất bại/g, () =>
    badges['FAUCET']('🚰 OFFICIAL') + ' ' + badges['FAIL']('LỖI ✗')
  );

  // === OFFICIAL FAUCET ===
  msg = msg.replace(/🚰\s*Đang claim faucet/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' Đang claim...'
  );
  msg = msg.replace(/🚰\s*Bắt đầu nhận faucet/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' Bắt đầu nhận...'
  );
  msg = msg.replace(/✅\s*Claim faucet thành công/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Claim faucet thất bại/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['FAIL']('LỖI ✗')
  );
  msg = msg.replace(/❌\s*Faucet thất bại/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['FAIL']('LỖI ✗')
  );
  msg = msg.replace(/❌\s*Faucet (\d+)\/(\d+) thất bại/g, (_, i, max) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['FAIL'](`${i}/${max} LỖI`)
  );
  msg = msg.replace(/✅\s*Faucet (\d+)\/(\d+) OK/g, (_, i, max) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['OK'](`${i}/${max} OK ✓`)
  );
  msg = msg.replace(/✅\s*\[(.+?)\]\s*\+/g, (_, src) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['OK'](`${src} ✓`) + ' +'
  );
  msg = msg.replace(/⏹️\s*Bị giới hạn tần suất/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex('#E65100').white.bold(' ⏹ GIỚI HẠN ')
  );
  msg = msg.replace(/📊\s*Kết quả faucet:/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['SUMMARY']('📊 KẾT QUẢ') + ':'
  );

  msg = msg.replace(/🔑\s*Đang giải (Turnstile|captcha)/g, () =>
    badges['CAPTCHA']('🔑 CAPTCHA') + ' Đang giải...'
  );
  msg = msg.replace(/✅\s*(Captcha|Turnstile) OK/g, () =>
    badges['CAPTCHA']('🔑 CAPTCHA') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/⛏️\s*Đang giải PoW/g, () =>
    badges['POW']('⛏️ POW') + ' Đang giải...'
  );
  msg = msg.replace(/✅\s*PoW OK/g, () =>
    badges['POW']('⛏️ POW') + ' ' + badges['OK']('OK ✓')
  );

  msg = msg.replace(/⏳ PoW timeout \((\d+)\/(\d+)\)/g, (_, i, max) =>
    badges['POW']('⛏️ POW') + ' ' + chalk.bgHex('#E65100').white.bold(` ⏳ TIMEOUT ${i}/${max} `) + ' → lấy challenge mới...'
  );

  msg = msg.replace(/⏹️\s*Challenge hết hạn (\d+) lần liên tục/g, (_, n) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex('#BF360C').white.bold(` ⏹ EXPIRED ×${n} `) + ' → faucet đang quá tải, dừng'
  );

  msg = msg.replace(/⚠️\s*Challenge hết hạn \((\d+)\/3\)/g, (_, n) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex('#E65100').white.bold(` ⚠ EXPIRED ${n}/3 `) + ' → đợi thêm rồi thử lại...'
  );

  msg = msg.replace(/⏹️\s*(\d+) lỗi mạng\/proxy liên tiếp/g, (_, n) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex('#BF360C').white.bold(` ⏹ MẠNG ×${n} `) + ' → dừng faucet'
  );

  msg = msg.replace(/⏹️\s*(\d+) lỗi liên tiếp → dừng faucet/g, (_, n) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex('#BF360C').white.bold(` ⏹ LỖI ×${n} `) + ' → dừng faucet'
  );

  msg = msg.replace(/⏹️\s*Lỗi captcha → dừng faucet/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['FAIL']('CAPTCHA LỖI') + ' → dừng faucet'
  );

  msg = msg.replace(/❌\s*Faucet (\d+)\/(\d+) lỗi \((.+?)\)/g, (_, i, max, errType) => {
    const errColors = {
      'expired': '#E65100', 'ratelimit': '#F57F17', 'network': '#4527A0',
      'proxy': '#1565C0', 'captcha': '#6A1B9A', 'unknown': '#455A64'
    };
    const color = errColors[errType] || '#455A64';
    return badges['FAUCET']('🚰 FAUCET') + ' ' + chalk.bgHex(color).white.bold(` ${i}/${max} ${errType.toUpperCase()} `);
  });

  // === RESCUE ===
  msg = msg.replace(/🆘\s*Rescue: cần thêm/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' Cần thêm'
  );
  msg = msg.replace(/🔍\s*Rescue: tìm thấy/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + chalk.hex('#81C784')('🔍 Tìm thấy')
  );
  msg = msg.replace(/🔄\s*Rescue:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' 🔄'
  );
  msg = msg.replace(/✅\s*Rescue OK:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Rescue thất bại:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['FAIL']('LỖI ✗')
  );
  msg = msg.replace(/❌\s*Rescue: không tìm thấy ví/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['SKIP']('KHÔNG CÓ DONOR')
  );
  msg = msg.replace(/❌\s*Rescue: (.+?) ví có surplus nhưng/g, (_, n) =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['SKIP'](`${n} ví - THIẾU`)
  );
  msg = msg.replace(/⏭️\s*Rescue: không tìm được donor/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['SKIP']('BỎ QUA')
  );
  msg = msg.replace(/💰\s*Balance sau rescue:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['BALANCE']('💰 SỐ DƯ') + ':'
  );

  // === COLLECT (GOM SUI) ===
  msg = msg.replace(/📦\s*Gom SUI:/g, () =>
    badges['COLLECT']('📦 GOM SUI')
  );
  msg = msg.replace(/💸\s*Chuyển .+? SUI → ví chính/g, (m) =>
    badges['COLLECT']('📦 GOM') + ' ' + m.replace('💸 ', '')
  );
  msg = msg.replace(/✅\s*Gom OK:/g, () =>
    badges['COLLECT']('📦 GOM') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/⏭️\s*Bỏ qua gom - (.+)/g, (_, reason) =>
    badges['COLLECT']('📦 GOM') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/❌\s*Gom thất bại:/g, () =>
    badges['COLLECT']('📦 GOM') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/📥\s*Deposit (.+?) SUI/g, (_, amt) =>
    badges['DEPOSIT']('📥 NẠP') + ' ' + chalk.hex('#4FC3F7').bold(amt) + ' SUI'
  );
  msg = msg.replace(/✅\s*Deposit thành công/g, () =>
    badges['DEPOSIT']('📥 NẠP') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Deposit thất bại/g, () =>
    badges['DEPOSIT']('📥 NẠP') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🎫\s*Đang mint pass/g, () =>
    badges['MINT']('🎫 MINT') + ' Đang mint pass...'
  );
  msg = msg.replace(/✅\s*Mint pass thành công/g, () =>
    badges['MINT']('🎫 MINT') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Mint pass thất bại/g, () =>
    badges['MINT']('🎫 MINT') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🎁\s*Đang claim rewards/g, () =>
    badges['CLAIM']('🎁 NHẬN') + ' Đang claim rewards...'
  );
  msg = msg.replace(/✅\s*Claim rewards thành công/g, () =>
    badges['CLAIM']('🎁 NHẬN') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Claim rewards thất bại/g, () =>
    badges['CLAIM']('🎁 NHẬN') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🏦\s*Đang borrow/g, () =>
    badges['BORROW']('🏦 VAY') + ' Đang borrow...'
  );
  msg = msg.replace(/✅\s*Borrow thành công/g, () =>
    badges['BORROW']('🏦 VAY') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Borrow thất bại/g, () =>
    badges['BORROW']('🏦 VAY') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/💳\s*Đang trả nợ loan/g, () =>
    badges['REPAY']('💳 TRẢ NỢ') + ' Đang trả nợ...'
  );
  msg = msg.replace(/✅\s*Repay loan thành công/g, () =>
    badges['REPAY']('💳 TRẢ NỢ') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/❌\s*Repay loan thất bại/g, () =>
    badges['REPAY']('💳 TRẢ NỢ') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/📋\s*Đăng bán pass/g, () =>
    badges['LIST']('📋 ĐĂNG BÁN') + ' Đang đăng bán...'
  );
  msg = msg.replace(/✅\s*Đăng bán pass thành công/g, () =>
    badges['LIST']('📋 ĐĂNG BÁN') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/🛒\s*Mua pass từ sàn/g, () =>
    badges['BUY']('🛒 MUA') + ' Đang mua...'
  );
  msg = msg.replace(/✅\s*Mua pass thành công/g, () =>
    badges['BUY']('🛒 MUA') + ' ' + badges['OK']('OK ✓')
  );
  msg = msg.replace(/🗑️\s*Gỡ bán pass/g, () =>
    badges['DELIST']('🗑️ GỠ BÁN') + ' Đang gỡ bán...'
  );
  msg = msg.replace(/✅\s*Gỡ bán thành công/g, () =>
    badges['DELIST']('🗑️ GỠ BÁN') + ' ' + badges['OK']('OK ✓')
  );

  msg = msg.replace(/💰\s*Số dư:/g, () =>
    badges['BALANCE']('💰 SỐ DƯ') + ':'
  );
  msg = msg.replace(/✅\s*Số dư sau faucet:/g, () =>
    badges['BALANCE']('💰 SỐ DƯ') + ' sau faucet:'
  );
  msg = msg.replace(/🔄\s*Faucet lần (\d+)\/(\d+)/g, (_, i, max) =>
    badges['FAUCET']('🚰 FAUCET') + ' lần ' + chalk.hex('#FFD54F').bold(i) + '/' + chalk.hex('#90CAF9')(max)
  );
  msg = msg.replace(/⭐\s*Điểm:/g, () =>
    badges['POINTS']('⭐ ĐIỂM') + ':'
  );

  msg = msg.replace(/🎫\s*Đang có (\d+) passes?/g, (_, count) =>
    badges['PASS']('🎫 THẺ') + ' Đang có ' + chalk.hex('#FFD54F').bold(count)
  );

  msg = msg.replace(/📊\s*Loan:/g, () =>
    badges['LOAN']('📊 VAY') + ':'
  );

  msg = msg.replace(/🔄\s*Bắt đầu chu kỳ giao dịch/g, () =>
    badges['TRADE']('🔄 G.DỊCH') + ' Bắt đầu...'
  );

  msg = msg.replace(/🔄\s*G.dịch lần (\d+)\/(\d+)/g, (_, i, max) =>
    badges['TRADE']('🔄 G.DỊCH') + ' lần ' + chalk.hex('#FFD54F').bold(i) + '/' + chalk.hex('#90CAF9')(max)
  );
  msg = msg.replace(/📊\s*Chu kỳ giao dịch:/g, () =>
    badges['TRADE']('🔄 G.DỊCH') + ' ' + badges['SUMMARY']('📊 KẾT QUẢ') + ':'
  );
  msg = msg.replace(/✅\s*Hoàn tất chu kỳ giao dịch/g, () =>
    badges['TRADE']('🔄 G.DỊCH') + ' ' + badges['OK']('HOÀN TẤT ✓')
  );
  msg = msg.replace(/❌\s*Chu kỳ giao dịch lỗi/g, () =>
    badges['TRADE']('🔄 G.DỊCH') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🔄\s*Bắt đầu chu kỳ vay/g, () =>
    badges['LOAN']('💳 VAY') + ' Bắt đầu...'
  );
  msg = msg.replace(/📊\s*Chu kỳ vay:/g, () =>
    badges['LOAN']('💳 VAY') + ' ' + badges['SUMMARY']('📊 KẾT QUẢ') + ':'
  );
  msg = msg.replace(/❌\s*Chu kỳ vay lỗi/g, () =>
    badges['LOAN']('💳 VAY') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🚀\s*Bắt đầu farming/g, () =>
    chalk.bgHex('#E91E63').white.bold(' 🌸 BẮT ĐẦU FARM ')
  );
  msg = msg.replace(/🎉\s*Hoàn tất chu kỳ farming/g, () =>
    chalk.bgHex('#00897B').white.bold(' ✔ FARMING HOÀN TẤT ')
  );

  msg = msg.replace(/⏭️\s*Listing #(\d+) đã FINALIZED/g, (_, num) =>
    badges['SKIP']('⏭️ BỎ QUA') + ' Listing #' + chalk.hex('#F48FB1').bold(num) + ' đã ' + chalk.hex('#4FC3F7').bold('FINALIZED')
  );

  msg = msg.replace(/⏭️\s*Borrow đang tạm dừng/g, () =>
    badges['BORROW']('🏦 VAY') + ' ' + badges['SKIP']('TẠM DỪNG') + ' LoanVault tạm dừng'
  );

  msg = msg.replace(/⏭️\s*Bỏ qua claim - (.+)/g, (_, reason) =>
    badges['CLAIM']('🎁 NHẬN') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/⏭️\s*Bỏ qua borrow - (.+)/g, (_, reason) =>
    badges['BORROW']('🏦 VAY') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/⏭️\s*Bỏ qua repay - (.+)/g, (_, reason) =>
    badges['REPAY']('💳 TRẢ NỢ') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/⏭️\s*Bỏ qua trade - (.+)/g, (_, reason) =>
    badges['TRADE']('🔄 G.DỊCH') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/⏭️\s*Hết SUI, dừng trade cycle/g, () =>
    badges['TRADE']('🔄 G.DỊCH') + ' ' + badges['SKIP']('HẾT SUI') + ' dừng trade cycle'
  );
  msg = msg.replace(/⏭️\s*Bỏ qua deposit - (.+)/g, (_, reason) =>
    badges['DEPOSIT']('📥 NẠP') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );
  msg = msg.replace(/⏭️\s*Bỏ qua mint - (.+)/g, (_, reason) =>
    badges['MINT']('🎫 MINT') + ' ' + badges['SKIP']('BỎ QUA') + ' ' + reason
  );

  msg = msg.replace(/⏭️\s*Bỏ qua (.+)/g, (_, reason) =>
    badges['SKIP']('⏭️ BỎ QUA') + ' ' + reason
  );

  msg = msg.replace(/🚰\s*Thiếu SUI \((.+?)\) → tự động faucet/g, (_, info) =>
    badges['FAUCET']('🚰 FAUCET') + ' Thiếu SUI (' + chalk.hex('#F48FB1').bold(info) + ') → tự động faucet'
  );
  msg = msg.replace(/✅\s*Đã faucet đủ: (.+?) SUI/g, (_, amt) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['OK']('ĐỦ ✓') + ' ' + chalk.hex('#4FC3F7').bold(amt) + ' SUI'
  );
  msg = msg.replace(/⚠️\s*Faucet xong nhưng vẫn thiếu/g, () =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['SKIP']('VẪN THIẾU')
  );
  msg = msg.replace(/⏭️\s*Thiếu SUI \((.+?)\) nhưng chưa có captcha key/g, (_, info) =>
    badges['FAUCET']('🚰 FAUCET') + ' ' + badges['SKIP']('BỎ QUA') + ' Thiếu SUI (' + chalk.hex('#F48FB1').bold(info) + ')'
  );
  msg = msg.replace(/⏭️\s*Không đủ SUI để mua pass/g, () =>
    badges['BUY']('🛒 MUA') + ' ' + badges['SKIP']('THIẾU SUI')
  );

  msg = msg.replace(/🛒\s*Tìm pass rẻ nhất trên sàn/g, () =>
    badges['BUY']('🛒 MUA') + ' Tìm pass rẻ nhất...'
  );
  msg = msg.replace(/🛒\s*Chưa có thẻ → tìm mua từ sàn/g, () =>
    badges['BUY']('🛒 MUA') + ' Chưa có thẻ → tìm mua từ sàn'
  );
  msg = msg.replace(/⏭️\s*Không tìm thấy pass nào trên sàn/g, () =>
    badges['BUY']('🛒 MUA') + ' ' + badges['SKIP']('KHÔNG CÓ') + ' Hết pass trên sàn'
  );
  msg = msg.replace(/❌\s*Không mua được pass nào/g, () =>
    badges['BUY']('🛒 MUA') + ' ' + badges['FAIL']('LỖI ✗') + ' Tất cả listing không hợp lệ'
  );
  msg = msg.replace(/❌\s*Mua pass từ sàn lỗi/g, () =>
    badges['BUY']('🛒 MUA') + ' ' + badges['FAIL']('LỖI ✗')
  );

  msg = msg.replace(/🔗\s*Referral OK: (.+)/g, (_, text) =>
    badges['REFERRAL']('🔗 G.THIỆU') + ' ' + badges['OK']('OK ✓') + ' ' + text
  );

  msg = msg.replace(/📊\s*Tổng kết:/g, () =>
    badges['SUMMARY']('📊 TỔNG KẾT') + ':'
  );

  return msg;
}

function applySystemBadges(message) {
  let msg = message;

  msg = msg.replace(/⚙️\s*Đã tải cấu hình/g, () =>
    chalk.bgHex('#37474F').hex('#90CAF9').bold(' ⚙️ CẤU HÌNH ') + ' Đã tải'
  );
  msg = msg.replace(/🔧\s*Tính năng: (.+)/g, (_, features) =>
    chalk.bgHex('#37474F').hex('#CE93D8').bold(' 🔧 TÍNH NĂNG ') + ' ' + features
  );
  msg = msg.replace(/👥\s*Đã tải (\d+) tài khoản/g, (_, count) =>
    chalk.bgHex('#37474F').hex('#81C784').bold(' 👥 TÀI KHOẢN ') + ' ' + chalk.hex('#FFD54F').bold(count)
  );
  msg = msg.replace(/🌐\s*Đã tải (\d+) proxy/g, (_, count) =>
    chalk.bgHex('#37474F').hex('#81C784').bold(' 🌐 PROXY ') + ' ' + chalk.hex('#FFD54F').bold(count)
  );
  msg = msg.replace(/🔄\s*Bắt đầu chu kỳ farming #(\d+)/g, (_, cycle) =>
    chalk.bgHex('#1A237E').white.bold(` 🔄 FARMING #${cycle} `)
  );
  msg = msg.replace(/✅\s*Hoàn tất chu kỳ #(\d+)/g, (_, cycle) =>
    chalk.bgHex('#1B5E20').white.bold(` ✅ CHU KỲ #${cycle} HOÀN TẤT `)
  );
  msg = msg.replace(/⏳\s*Nghỉ (.+?) trước chu kỳ tiếp/g, (_, time) =>
    chalk.bgHex('#37474F').hex('#90CAF9').bold(' ⏳ NGHỈ ') + ' ' + time
  );
  msg = msg.replace(/⏳\s*Chờ (.+) trước batch tiếp/g, (_, time) =>
    chalk.bgHex('#37474F').hex('#90CAF9').bold(' ⏳ CHỜ ') + ' ' + time
  );
  msg = msg.replace(/🔧\s*Đang xử lý batch/g, () =>
    chalk.bgHex('#37474F').hex('#90CAF9').bold(' 🔧 ĐỢT ')
  );
  msg = msg.replace(/❌\s*THIẾU API KEY/g, () =>
    badges['FAIL']('❌ API KEY') + ' THIẾU'
  );
  msg = msg.replace(/❌\s*Không tìm thấy tài khoản/g, () =>
    badges['FAIL']('❌ LỖI') + ' Không tìm thấy tài khoản'
  );
  msg = msg.replace(/🔗\s*Referral: (.+)/g, (_, code) =>
    badges['REFERRAL']('🔗 G.THIỆU') + ' ' + chalk.hex('#F48FB1').bold(code)
  );
  msg = msg.replace(/💧\s*Bắt đầu chế độ FAUCET/g, () =>
    chalk.bgHex('#0288D1').white.bold(' 💧 CHẾ ĐỘ FAUCET ')
  );
  msg = msg.replace(/💧\s*Chế độ: CHỈ FAUCET/g, () =>
    chalk.bgHex('#0288D1').white.bold(' 💧 CHỈ FAUCET ')
  );
  msg = msg.replace(/✅\s*Hoàn tất faucet tất cả tài khoản/g, () =>
    chalk.bgHex('#00897B').white.bold(' ✅ FAUCET HOÀN TẤT ')
  );

  msg = msg.replace(/🆘\s*Rescue: đang scan tất cả ví/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' Đang scan tất cả ví...'
  );
  msg = msg.replace(/📊\s*Rescue scan:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['SUMMARY']('📊 SCAN') + ':'
  );
  msg = msg.replace(/💎\s*Top ví giàu:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' 💎 Top ví giàu:'
  );
  msg = msg.replace(/✅\s*Rescue: tất cả ví đều có đủ SUI/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['OK']('ĐỦ SUI ✓') + ' Tất cả ví OK'
  );
  msg = msg.replace(/❌\s*Rescue: không có ví nào đủ giàu/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['FAIL']('LỖI') + ' Không có ví donor đủ giàu'
  );
  msg = msg.replace(/✅\s*Rescue hoàn tất:/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['OK']('HOÀN TẤT ✓') + ':'
  );
  msg = msg.replace(/⚠️\s*Rescue: không chuyển được cho ví nào/g, () =>
    badges['RESCUE']('🆘 CỨU HỘ') + ' ' + badges['SKIP']('KHÔNG CHUYỂN ĐƯỢC')
  );
  msg = msg.replace(/⛏️\s*PoW Pool:/g, () =>
    badges['POOL']('⛏️ PoW POOL') + ':'
  );

  // === COLLECT (GOM SUI) system ===
  msg = msg.replace(/📦\s*Bắt đầu gom SUI/g, () =>
    badges['COLLECT']('📦 GOM SUI') + ' Bắt đầu gom...'
  );
  msg = msg.replace(/📊\s*Gom scan:/g, () =>
    badges['COLLECT']('📦 GOM SUI') + ' ' + badges['SUMMARY']('📊 SCAN') + ':'
  );
  msg = msg.replace(/✅\s*Gom SUI hoàn tất:/g, () =>
    badges['COLLECT']('📦 GOM SUI') + ' ' + badges['OK']('HOÀN TẤT ✓') + ':'
  );
  msg = msg.replace(/⚠️\s*Gom SUI: không có ví nào để gom/g, () =>
    badges['COLLECT']('📦 GOM SUI') + ' ' + badges['SKIP']('KHÔNG CÓ VÍ')
  );
  msg = msg.replace(/🎯\s*Ví đích gom:/g, () =>
    badges['COLLECT']('📦 GOM SUI') + ' 🎯 Ví đích:'
  );

  return msg;
}

export function log(accIdx, total, wallet, proxy, message, level = 'info') {
  const time = chalk.gray(`[${formatTime()}]`);
  const proj = chalk.bgHex('#E91E63').white.bold(` ${PROJECT_NAME} `);
  const acc = chalk.bgHex('#0277BD').hex('#E0F7FA').bold(` ${accIdx}/${total} `);
  const wal = chalk.hex('#F48FB1')(`[${shortWallet(wallet)}]`);
  const proxyShort = proxy ? proxy.split(':').slice(0, 2).join(':') : 'ko proxy';
  const prx = chalk.hex('#4DD0E1')(`[${proxyShort}]`);

  let msg = applyBadges(message);
  msg = highlightMessage(msg);

  let levelIndicator = '';
  switch (level) {
    case 'success':
      levelIndicator = chalk.bgHex('#00897B').white.bold(' ✓ ');
      break;
    case 'warn':
      levelIndicator = chalk.bgHex('#F06292').white.bold(' ⚠ ');
      break;
    case 'error':
      levelIndicator = chalk.bgHex('#C62828').white.bold(' ✗ ');
      break;
    default:
      levelIndicator = chalk.bgHex('#37474F').hex('#B2EBF2')(' ▸ ');
  }

  console.log(`${time} ${proj} ${acc} ${wal}${prx} ${levelIndicator} ${msg}`);
}

export function logSystem(message, level = 'info') {
  const time = chalk.gray(`[${formatTime()}]`);
  const proj = chalk.bgHex('#E91E63').white.bold(` ${PROJECT_NAME} `);
  const tag = chalk.bgHex('#0277BD').white.bold(' HỆ THỐNG ');

  let msg = applySystemBadges(message);
  msg = highlightMessage(msg);

  let levelIndicator = '';
  switch (level) {
    case 'success':
      levelIndicator = chalk.bgHex('#00897B').white.bold(' ✓ ');
      break;
    case 'warn':
      levelIndicator = chalk.bgHex('#F06292').white.bold(' ⚠ ');
      break;
    case 'error':
      levelIndicator = chalk.bgHex('#C62828').white.bold(' ✗ ');
      break;
    default:
      levelIndicator = chalk.bgHex('#37474F').hex('#B2EBF2')(' ▸ ');
  }

  console.log(`${time} ${proj} ${tag} ${levelIndicator} ${msg}`);
}

export function printBanner() {
  const sakura = chalk.hex('#F48FB1');
  const ocean = chalk.hex('#4FC3F7');
  const dim = chalk.hex('#546E7A');

  console.log('');
  console.log('  ' + sakura('✿ ') + ocean('━'.repeat(50)) + sakura(' ✿'));
  console.log('       ' + chalk.bgHex('#E91E63').white.bold('  🌸  TIDE PROTOCOL AUTO BOT  🌸  '));
  console.log('  ' + dim('─'.repeat(55)));
  console.log('    ' + sakura('❀') + chalk.hex('#F8BBD0')(' Mạng:      ') + chalk.hex('#80DEEA').bold('SUI Testnet'));
  console.log('    ' + sakura('❀') + chalk.hex('#F8BBD0')(' Chức năng: ') + badges['FAUCET']('FAUCET') + ' ' + badges['DEPOSIT']('DEPOSIT') + ' ' + badges['MINT']('MINT') + ' ' + badges['CLAIM']('CLAIM'));
  console.log('    ' + sakura('❀') + chalk.hex('#F8BBD0')(' Thêm:      ') + badges['BORROW']('BORROW') + ' ' + badges['REPAY']('REPAY') + ' ' + badges['TRADE']('TRADE') + ' ' + badges['LOAN']('LOAN') + ' ' + badges['LIST']('LIST') + ' ' + badges['BUY']('BUY'));
  console.log('    ' + sakura('❀') + chalk.hex('#F8BBD0')(' Cứu hộ:    ') + badges['RESCUE']('RESCUE') + ' ' + badges['COLLECT']('COLLECT') + ' ' + badges['POOL']('PoW POOL'));
  console.log('    ' + sakura('❀') + chalk.hex('#F8BBD0')(' Giao thức: ') + chalk.hex('#B39DDB')('tide.am'));
  console.log('  ' + sakura('✿ ') + ocean('━'.repeat(50)) + sakura(' ✿'));
  console.log('');
}

export function randomDelay(min, max) {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default { log, logSystem, printBanner, shortWallet, normalizeAddress, randomDelay, friendlyError };
