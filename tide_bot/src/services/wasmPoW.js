import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const WASM_PATH = path.resolve(__dirname, '../../data/wasm_pow_bg.wasm');

let wasm = null;
let cachedUint8Mem = null;
let WASM_VECTOR_LEN = 0;

const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });

function getUint8Memory() {
  if (cachedUint8Mem === null || cachedUint8Mem.byteLength === 0) {
    cachedUint8Mem = new Uint8Array(wasm.memory.buffer);
  }
  return cachedUint8Mem;
}

function passStringToWasm(arg) {
  const buf = encoder.encode(arg);
  const ptr = wasm.__wbindgen_malloc(buf.length, 1) >>> 0;
  getUint8Memory().subarray(ptr, ptr + buf.length).set(buf);
  WASM_VECTOR_LEN = buf.length;
  return ptr;
}

function getStringFromWasm(ptr, len) {
  ptr = ptr >>> 0;
  return decoder.decode(getUint8Memory().subarray(ptr, ptr + len));
}

async function initWasm() {
  if (wasm) return;

  const wasmBuffer = fs.readFileSync(WASM_PATH);

  const imports = {
    wbg: {
      __wbindgen_throw(ptr, len) {
        throw new Error(getStringFromWasm(ptr, len));
      },
      __wbindgen_init_externref_table() {
        const table = wasm.__wbindgen_export_0;
        const base = table.grow(4);
        table.set(base + 0, undefined);
        table.set(base + 1, null);
        table.set(base + 2, true);
        table.set(base + 3, false);
      }
    }
  };

  const wasmModule = new WebAssembly.Module(wasmBuffer);
  const wasmInstance = new WebAssembly.Instance(wasmModule, imports);
  wasm = wasmInstance.exports;
  cachedUint8Mem = null;
  wasm.__wbindgen_start();
}

export async function solvePoWWasm(ts, difficulty, challengeStr) {
  await initWasm();

  const ptr = passStringToWasm(challengeStr);
  const len = WASM_VECTOR_LEN;
  const resultPtr = wasm.mine(BigInt(ts), difficulty, ptr, len);
  const nonce = wasm.powchallenge_nonce(resultPtr) >>> 0;
  const [hashPtr, hashLen] = wasm.powchallenge_hash(resultPtr);
  const hash = getStringFromWasm(hashPtr, hashLen);

  wasm.__wbindgen_free(hashPtr, hashLen, 1);
  wasm.__wbg_powchallenge_free(resultPtr, 0);

  return { hash, nonce };
}

export default { solvePoWWasm };
