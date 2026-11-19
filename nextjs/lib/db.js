import mysql from 'mysql2/promise';

// One pool per worker process, created on first use and kept for the process lifetime.
const globalPool = globalThis;
export function pool() {
  globalPool.benchPool ??= mysql.createPool({
    host: process.env.DB_HOST ?? 'mysql',
    port: Number(process.env.DB_PORT ?? 23306),
    user: process.env.DB_USERNAME ?? 'bench',
    password: process.env.DB_PASSWORD ?? 'bench',
    database: process.env.DB_DATABASE ?? 'benchmark',
    charset: 'utf8mb4',
    connectionLimit: 10,
    maxIdle: 10,
    idleTimeout: 600_000,
    enableKeepAlive: true,
  });
  return globalPool.benchPool;
}
