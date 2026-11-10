<?php

return new \Tempest\Database\Config\MysqlConfig(
    host: 'mysql', port: '23306', username: 'bench', password: 'bench', database: 'benchmark',
    persistent: true, parameters: ['charset' => 'utf8mb4'],
);
