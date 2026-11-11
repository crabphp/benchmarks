<?php

declare(strict_types=1);

require dirname(__DIR__) . '/common/async.php';

$valid = ['name' => 'Ada Example', 'email' => 'ada@example.test', 'age' => 36];
foreach ([$valid, array_replace($valid, ['name' => ' ', 'age' => 18]), array_replace($valid, ['name' => str_repeat('x', 100), 'age' => 120])] as $data) {
    if (benchValidate(json_encode($data, JSON_THROW_ON_ERROR)) !== $data) {
        throw new RuntimeException('Rejected valid boundary: ' . json_encode($data));
    }
}
foreach ([[], array_replace($valid, ['name' => '']), array_replace($valid, ['name' => str_repeat('x', 101)]),
    array_replace($valid, ['email' => 'bad']), array_replace($valid, ['name' => 7]),
    ...array_map(static fn ($age) => array_replace($valid, ['age' => $age]), [17, 121, '36', 36.0, true, null]),
] as $data) {
    if (benchValidate(json_encode($data, JSON_THROW_ON_ERROR | JSON_PRESERVE_ZERO_FRACTION)) !== null) {
        throw new RuntimeException('Accepted invalid input: ' . json_encode($data));
    }
}
foreach (['{bad', 'null', '1', '"text"', 'true'] as $body) {
    if (benchValidate($body) !== null) {
        throw new RuntimeException('Accepted malformed input: ' . $body);
    }
}
if (benchUser(null) !== null || benchUser(['id' => '1', 'name' => 'A', 'email' => 'a@example.test', 'age' => '18']) !== ['id' => 1, 'name' => 'A', 'email' => 'a@example.test', 'age' => 18]) {
    throw new RuntimeException('Database value normalization failed.');
}
echo "Async input validation and database normalization passed.\n";
