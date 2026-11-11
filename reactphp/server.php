<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';
require '/bench/async.php';

use FastRoute\Dispatcher;
use FastRoute\RouteCollector;
use Psr\Http\Message\ServerRequestInterface;
use React\EventLoop\Loop;
use React\Http\HttpServer;
use React\Http\Message\Response;
use React\MySQL\Factory;
use React\MySQL\QueryResult;
use React\Socket\SocketServer;

benchWorkers(static function (): void {
    $factory = new Factory();
    $connections = [];
    for ($i = 0; $i < 10; ++$i) {
        $connections[] = $factory->createLazyConnection('bench:bench@mysql:23306/benchmark?charset=utf8mb4&idle=600&timeout=10');
    }
    $next = 0;
    $router = FastRoute\simpleDispatcher(static function (RouteCollector $routes): void {
        $routes->addRoute('GET', '/hello', 'hello');
        $routes->addRoute('GET', '/users/{id:\d+}', 'user');
        $routes->addRoute('POST', '/users', 'validate');
        $routes->addRoute('GET', '/__bench', 'metadata');
    });
    $json = static fn (array $data, int $status = 200): Response => new Response(
        $status, ['content-type' => 'application/json'], json_encode($data, JSON_THROW_ON_ERROR),
    );
    $server = new HttpServer(static function (ServerRequestInterface $request) use ($router, $json, $connections, &$next) {
        $route = $router->dispatch($request->getMethod(), $request->getUri()->getPath());
        if ($route[0] !== Dispatcher::FOUND) {
            return $json(['error' => 'Not found'], 404);
        }
        switch ($route[1]) {
            case 'hello':
                return $json(['message' => 'Hello, world']);
            case 'user':
                // Each native async connection queues queries; round-robin bounds the pool to ten.
                $connection = $connections[$next++ % count($connections)];
                return $connection->query('SELECT id, name, email, age FROM users WHERE id = ?', [(int) $route[2]['id']])
                    ->then(static function (QueryResult $result) use ($json): Response {
                        $row = benchUser($result->resultRows[0] ?? null);
                        return $row === null ? $json(['error' => 'Not found'], 404) : $json($row);
                    });
            case 'validate':
                $data = benchValidate((string) $request->getBody());
                return $data === null ? $json(['error' => 'Invalid input'], 422) : $json($data, 201);
            case 'metadata':
                return $json(array_replace(require '/bench/metadata.php', [
                    'workers' => 2, 'pool_per_worker' => 10, 'persistent' => true,
                    'event' => phpversion('event'), 'loop' => Loop::get()::class,
                    'database_driver' => 'react/mysql', 'validation' => 'explicit PHP checks',
                ]));
        }
    });
    $server->on('error', static function (Throwable $error): void {
        fwrite(STDERR, (string) $error . PHP_EOL);
    });
    $socket = new SocketServer('0.0.0.0:8080', ['tcp' => ['so_reuseport' => true, 'tcp_nodelay' => true]]);
    $server->listen($socket);
    foreach ([SIGINT, SIGTERM] as $signal) {
        Loop::addSignal($signal, static function () use ($socket, $connections): void {
            $socket->close();
            foreach ($connections as $connection) {
                $connection->close();
            }
            Loop::stop();
        });
    }
    Loop::run();
});
