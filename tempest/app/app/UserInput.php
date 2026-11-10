<?php

declare(strict_types=1);

namespace App;

use Tempest\Validation\Rules\HasLength;
use Tempest\Validation\Rules\IsEmail;
use Tempest\Validation\Rules\IsBetween;

final class UserInput
{
    #[HasLength(min: 1, max: 100)]
    public string $name;
    #[IsEmail]
    public string $email;
    #[IsBetween(min: 18, max: 120)]
    public int $age;
}
