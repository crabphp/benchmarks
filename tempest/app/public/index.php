<?php

declare(strict_types=1);

require dirname(__DIR__) . '/vendor/autoload.php';
$app = \Tempest\Router\WorkerModeApplication::boot(dirname(__DIR__));
$handler = static function () use ($app): void {
    try {
        $app->run();
    } catch (\Throwable $error) {
        // Exceptions must be handled within the worker request so the worker can serve the next one.
        \Tempest\Container\get(\Tempest\Core\ExceptionHandler::class)->handle($error);
    }
};
$running = true;
while ($running) {
    $running = frankenphp_handle_request($handler);
}
