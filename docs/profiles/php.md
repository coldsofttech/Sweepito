# php

[Back to all profiles](../profiles.md)

PHP: Composer, Laravel, Symfony

**Detected by:** `composer.json`, `artisan`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `php.phpunit` | `.phpunit.cache/`, `.phpunit.result.cache` | `composer.json`, `artisan` | safe | PHPUnit caches |
| `php.tool-caches` | `.php-cs-fixer.cache`, `.phpstan.cache` | `composer.json`, `artisan` | safe | Code style and static analysis caches |
| `laravel.cache` | `/storage/framework/cache/`, `/storage/framework/views/`, `/bootstrap/cache/*.php` | `artisan` | configurable | Laravel framework caches (never storage/app) |
| `laravel.logs` | `/storage/logs/` | `artisan` | configurable | Laravel logs |
| `symfony.cache` | `/var/cache/` | `symfony.lock` | configurable | Symfony cache |
| `symfony.logs` | `/var/log/` | `symfony.lock` | configurable | Symfony logs |
| `php.vendor` | `/vendor/` | `composer.json` | high-impact | Composer dependencies |

## Configuration

```toml
[clean]
enable = ["laravel.cache", "symfony.cache"]
```

Command-line equivalent:

```bash
sweepito clean -p php --enable laravel.cache
```

Notes:

- Laravel rules need `artisan`; Symfony rules need `symfony.lock`.
- `storage/app` (uploads) is never targeted.
- `laravel.logs` and `symfony.logs` are opt-in because logs may be needed.
- `vendor/` (`php.vendor`) is `high-impact`.
