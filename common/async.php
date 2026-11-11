<?php

declare(strict_types=1);

/** Two application workers; no sockets, loops or database connections exist before fork. */
function benchWorkers(Closure $worker): never
{
    $children = [];
    for ($i = 0; $i < 2; ++$i) {
        $pid = pcntl_fork();
        if ($pid === -1) {
            foreach ($children as $child) {
                posix_kill($child, SIGTERM);
            }
            throw new RuntimeException('Could not fork benchmark worker.');
        }
        if ($pid === 0) {
            $worker();
            exit(0);
        }
        $children[$pid] = $pid;
    }
    $stopping = false;
    pcntl_async_signals(true);
    $stop = static function () use (&$stopping, &$children): void {
        $stopping = true;
        foreach ($children as $child) {
            posix_kill($child, SIGTERM);
        }
    };
    // Interrupt wait() so PHP can dispatch the handler before children have exited.
    pcntl_signal(SIGTERM, $stop, false);
    pcntl_signal(SIGINT, $stop, false);
    $failed = false;
    while ($children !== []) {
        $pid = pcntl_wait($status);
        if ($pid > 0) {
            unset($children[$pid]);
            if (!$stopping) {
                // A missing worker invalidates the two-worker comparison; fail the whole app.
                $failed = true;
                $stop();
            }
        }
    }
    exit($failed ? 1 : 0);
}

/** Explicit validation for HTTP libraries, which do not ship application validators. */
function benchValidate(string $body): ?array
{
    try {
        $data = json_decode($body, true, 512, JSON_THROW_ON_ERROR);
    } catch (JsonException) {
        return null;
    }
    if (!is_array($data)
        || !is_string($data['name'] ?? null)
        || mb_strlen($data['name']) < 1 || mb_strlen($data['name']) > 100
        || !is_string($data['email'] ?? null)
        || !filter_var($data['email'], FILTER_VALIDATE_EMAIL)
        || !is_int($data['age'] ?? null) || $data['age'] < 18 || $data['age'] > 120
    ) {
        return null;
    }
    return array_intersect_key($data, array_flip(['name', 'email', 'age']));
}

function benchUser(?array $row): ?array
{
    if ($row === null) {
        return null;
    }
    return ['id' => (int) $row['id'], 'name' => $row['name'], 'email' => $row['email'], 'age' => (int) $row['age']];
}
