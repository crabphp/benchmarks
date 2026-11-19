// Two Next.js standalone server processes sharing port 8080 through node:cluster.
// A worker that exits outside shutdown stops the whole app, matching the PHP adapters.
const cluster = require('node:cluster');
const WORKERS = 2;
if (cluster.isPrimary) {
  let stopping = false;
  let failed = false;
  const stop = () => {
    stopping = true;
    for (const worker of Object.values(cluster.workers)) worker.process.kill('SIGTERM');
  };
  process.on('SIGTERM', stop);
  process.on('SIGINT', stop);
  cluster.on('exit', () => {
    if (!stopping) { failed = true; stop(); }
    if (Object.keys(cluster.workers).length === 0) process.exit(failed ? 1 : 0);
  });
  for (let i = 0; i < WORKERS; i++) cluster.fork({ BENCH_WORKERS: String(WORKERS) });
} else {
  require('./server.js');
}
