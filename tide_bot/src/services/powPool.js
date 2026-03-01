import { Worker } from 'worker_threads';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const WORKER_PATH = path.resolve(__dirname, 'powWorker.js');

let _jobIdCounter = 0;

class PoWPool {
  constructor(size) {
    this.size = size;
    this.workers = [];
    this.available = [];
    this.queue = [];
    this.pendingJobs = new Map();
    this._initPromise = null;
  }

  async init() {
    if (this._initPromise) return this._initPromise;

    this._initPromise = (async () => {
      const promises = [];
      for (let i = 0; i < this.size; i++) {
        promises.push(this._createWorker(i));
      }
      
      const results = await Promise.allSettled(promises);
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      
      if (successCount === 0) {
        throw new Error('Không thể tạo bất kỳ PoW worker nào');
      }
    })();

    return this._initPromise;
  }

  _createWorker(id) {
    return new Promise((resolve, reject) => {
      const worker = new Worker(WORKER_PATH);
      const timeout = setTimeout(() => {
        reject(new Error(`Worker ${id} init timeout`));
      }, 10000);

      const initHandler = (msg) => {
        if (msg.type === 'ready') {
          clearTimeout(timeout);
          worker.removeListener('message', initHandler);
          
          const workerInfo = { worker, id, busy: false };
          this.workers.push(workerInfo);
          this.available.push(id);
          
          worker.on('message', (m) => this._onWorkerMessage(id, m));
          worker.on('error', (err) => this._onWorkerError(id, err));
          worker.on('exit', (code) => this._onWorkerExit(id, code));
          
          resolve(workerInfo);
        } else if (msg.type === 'init-error') {
          clearTimeout(timeout);
          worker.terminate();
          reject(new Error(`Worker ${id}: ${msg.error}`));
        }
      };

      worker.on('message', initHandler);
      worker.on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      });
    });
  }

  _onWorkerMessage(workerId, msg) {
    if (msg.type === 'result' || msg.type === 'error') {
      const job = this.pendingJobs.get(msg.jobId);
      if (job) {
        if (job.timer) clearTimeout(job.timer);
        this.pendingJobs.delete(msg.jobId);
        
        if (msg.type === 'result') {
          job.resolve({ hash: msg.hash, nonce: msg.nonce });
        } else {
          job.reject(new Error(msg.error));
        }
      }

      const workerInfo = this.workers.find(w => w.id === workerId);
      if (workerInfo) workerInfo.busy = false;
      this.available.push(workerId);

      this._processQueue();
    }
  }

  _onWorkerError(workerId, err) {
    console.error(`[PoW Pool] Worker ${workerId} lỗi: ${err.message}`);
    this._cleanupWorker(workerId, new Error(`Worker crashed: ${err.message}`));
  }

  _onWorkerExit(workerId, code) {
    if (code !== 0) {
      this._cleanupWorker(workerId, new Error(`Worker exit code ${code}`));
    }
  }

  _cleanupWorker(workerId, error) {
    for (const [jobId, job] of this.pendingJobs) {
      if (job.workerId === workerId) {
        if (job.timer) clearTimeout(job.timer);
        this.pendingJobs.delete(jobId);
        job.reject(error);
      }
    }

    this.available = this.available.filter(id => id !== workerId);

    const idx = this.workers.findIndex(w => w.id === workerId);
    if (idx >= 0) {
      this.workers.splice(idx, 1);
    }

    const newId = this.workers.length > 0 
      ? Math.max(...this.workers.map(w => w.id)) + 1 
      : 0;
    this._createWorker(newId).then(() => {
      this._processQueue();
    }).catch(() => { });
  }

  _processQueue() {
    while (this.queue.length > 0 && this.available.length > 0) {
      const job = this.queue.shift();
      this._dispatch(job);
    }
  }

  _dispatch(job) {
    const workerId = this.available.shift();
    const workerInfo = this.workers.find(w => w.id === workerId);
    
    if (!workerInfo) {
      this.queue.unshift(job);
      return;
    }

    workerInfo.busy = true;
    job.workerId = workerId;
    this.pendingJobs.set(job.jobId, job);

    workerInfo.worker.postMessage({
      type: 'solve',
      jobId: job.jobId,
      ts: Number(job.ts),
      difficulty: job.difficulty,
      challengeStr: job.challengeStr
    });
  }

  async solve(ts, difficulty, challengeStr, timeoutMs = 25000) {
    await this.init();

    const jobId = ++_jobIdCounter;

    return new Promise((resolve, reject) => {
      const job = { jobId, ts, difficulty, challengeStr, resolve, reject, workerId: null, timer: null };

      if (timeoutMs > 0) {
        job.timer = setTimeout(() => {
          const pending = this.pendingJobs.get(jobId);
          if (pending) {
            this.pendingJobs.delete(jobId);
            pending.reject(new Error('PoW timeout'));
            if (pending.workerId != null) {
              const wi = this.workers.find(w => w.id === pending.workerId);
              if (wi) {
                wi.worker.terminate();
              }
            }
          } else {
            const qIdx = this.queue.findIndex(q => q.jobId === jobId);
            if (qIdx >= 0) {
              this.queue.splice(qIdx, 1);
              reject(new Error('PoW timeout (queued)'));
            }
          }
        }, timeoutMs);
      }

      if (this.available.length > 0) {
        this._dispatch(job);
      } else {
        this.queue.push(job);
      }
    });
  }

  destroy() {
    for (const { worker } of this.workers) {
      worker.terminate();
    }
    this.workers = [];
    this.available = [];
    this.queue = [];
    this.pendingJobs.clear();
  }

  get poolSize() {
    return this.workers.length;
  }
}

import config from '../core/config.js';

const cpuCount = os.cpus().length;
const poolSize = config.powThreads || Math.max(2, Math.min(cpuCount, 8));
const pool = new PoWPool(poolSize);

export async function solvePoWParallel(ts, difficulty, challengeStr) {
  return pool.solve(ts, difficulty, challengeStr);
}

export function getPoolSize() {
  return poolSize;
}

export function destroyPool() {
  pool.destroy();
}

export default { solvePoWParallel, getPoolSize, destroyPool };
