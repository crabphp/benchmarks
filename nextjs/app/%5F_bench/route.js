import { readFileSync } from 'node:fs';
import { pool } from '../../lib/db.js';

export const dynamic = 'force-dynamic';

export function GET() {
  const next = JSON.parse(readFileSync('/srv/app/node_modules/next/package.json', 'utf8')).version;
  const mysql2 = JSON.parse(readFileSync('/srv/app/node_modules/mysql2/package.json', 'utf8')).version;
  pool();
  return Response.json({
    node: process.versions.node, v8: process.versions.v8, next, mysql2,
    node_env: process.env.NODE_ENV, debug: false, pid: process.pid,
    workers: Number(process.env.BENCH_WORKERS), pool_per_worker: 10, persistent: true,
    server: 'next standalone server.js under node:cluster',
    database_driver: 'mysql2/promise pool', validation: 'explicit JavaScript checks',
    memory: process.memoryUsage(),
  });
}
