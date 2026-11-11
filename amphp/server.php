<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';
require '/bench/async.php';

use Amp\Http\Server\DefaultErrorHandler;
use Amp\Http\Server\Driver\SocketClientFactory;
use Amp\Http\Server\Request;
use Amp\Http\Server\RequestHandler\ClosureRequestHandler;
use Amp\Http\Server\Response;
use Amp\Http\Server\Router;
use Amp\Http\Server\SocketHttpServer;
use Amp\Mysql\MysqlConfig;
use Amp\Mysql\MysqlConnectionPool;
use Amp\Socket\BindContext;
use Amp\Socket\ResourceServerSocketFactory;
use Psr\Log\NullLogger;
use Revolt\EventLoop;
use function Amp\trapSignal;

benchWorkers(static function (): void {
    $logger = new NullLogger();
    // Match the upstream benchmark example: TCP_NODELAY and no compression middleware.
    $server = new SocketHttpServer($logger, new ResourceServerSocketFactory(), new SocketClientFactory($logger));
    $server->expose('0.0.0.0:8080', (new BindContext())->withReusePort()->withTcpNoDelay());
    $errorHandler = new DefaultErrorHandler();
    $router = new Router($server, $logger, $errorHandler);
    $db = new MysqlConnectionPool(new MysqlConfig(
        host: 'mysql', port: 23306, user: 'bench', password: 'bench', database: 'benchmark', charset: 'utf8mb4',
    ), maxConnections: 10, idleTimeout: 600);
    $json = static fn (array $data, int $status = 200): Response => new Response(
        $status, ['content-type' => 'application/json'], json_encode($data, JSON_THROW_ON_ERROR),
    );
    $router->addRoute('GET', '/hello', new ClosureRequestHandler(static fn (): Response => $json(['message' => 'Hello, world'])));
    $router->addRoute('GET', '/users/{id:\d+}', new ClosureRequestHandler(static function (Request $request) use ($db, $json): Response {
        $id = (int) $request->getAttribute(Router::class)['id'];
        $row = benchUser($db->execute('SELECT id, name, email, age FROM users WHERE id = ?', [$id])->fetchRow());
        return $row === null ? $json(['error' => 'Not found'], 404) : $json($row);
    }));
    $router->addRoute('POST', '/users', new ClosureRequestHandler(static function (Request $request) use ($json): Response {
        $data = benchValidate($request->getBody()->buffer());
        return $data === null ? $json(['error' => 'Invalid input'], 422) : $json($data, 201);
    }));
    $router->addRoute('GET', '/__bench', new ClosureRequestHandler(static fn (): Response => $json(array_replace(
        require '/bench/metadata.php', [
            'workers' => 2, 'pool_per_worker' => 10, 'persistent' => true,
            'event' => phpversion('event'), 'loop' => EventLoop::getDriver()::class,
            'database_driver' => 'amphp/mysql', 'validation' => 'explicit PHP checks',
        ],
    ))));
    $server->start($router, $errorHandler);
    trapSignal([SIGINT, SIGTERM]);
    $server->stop();
    $db->close();
});
