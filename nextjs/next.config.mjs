/** Production standalone server; no response caching or static generation for benchmark routes. */
export default {
  output: 'standalone',
  poweredByHeader: false,
  compress: false,
  serverExternalPackages: ['mysql2'],
};
