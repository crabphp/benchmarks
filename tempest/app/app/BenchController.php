<?php

declare(strict_types=1);

namespace App;

use Tempest\Database\Database;
use Tempest\Database\Query;
use Tempest\Http\GenericResponse;
use Tempest\Http\Request;
use Tempest\Http\Responses\Ok;
use Tempest\Http\Status;
use Tempest\Router\Get;
use Tempest\Router\Post;
use Tempest\Validation\Validator;

#[\Tempest\Router\WithoutMiddleware(
    \Tempest\Http\Session\ManageSessionMiddleware::class,
    \Tempest\Router\SetCookieHeadersMiddleware::class,
    \Tempest\Router\PreventCrossSiteRequestsMiddleware::class,
)]
final readonly class BenchController
{
    #[Get('/hello')]
    public function hello(): Ok
    {
        return new Ok(['message' => 'Hello, world']);
    }

    #[Get('/users/{id}')]
    public function user(int $id, Database $database): GenericResponse
    {
        $row = $database->fetchFirst(new Query('SELECT * FROM users WHERE id = ?', [$id]));
        return new GenericResponse($row === null ? Status::NOT_FOUND : Status::OK, $row ?? ['error' => 'Not found']);
    }

    #[Post('/users')]
    public function create(Request $request, Validator $validator): GenericResponse
    {
        $data = $request->body;
        $errors = $validator->validateValuesForClass(UserInput::class, $data);
        if ($errors !== [] || !is_int($data['age'] ?? null)) {
            return new GenericResponse(Status::UNPROCESSABLE_CONTENT, ['error' => 'Invalid input']);
        }
        return new GenericResponse(Status::CREATED, array_intersect_key($data, array_flip(['name', 'email', 'age'])));
    }

    #[Get('/__bench')]
    public function metadata(): Ok
    {
        $data = require '/bench/metadata.php';
        $data['debug'] = \Tempest\Core\Environment::guessFromEnvironment() !== \Tempest\Core\Environment::PRODUCTION;
        $data['workers'] = 2;
        $data['worker_mode'] = true;
        return new Ok($data);
    }
}
