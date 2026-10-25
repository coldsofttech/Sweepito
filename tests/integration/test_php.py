"""Integration tests for the php profile."""

from tests.integration.support import Case, ProfileSuite

CASE = Case(
    id="php",
    profile="php",
    markers={"artisan": "", "composer.json": "{}", "symfony.lock": "{}"},
    targets={
        "laravel.cache": [
            "storage/framework/cache/",
            "storage/framework/views/",
            "bootstrap/cache/packages.php",
        ],
        "laravel.logs": ["storage/logs/"],
        "php.phpunit": [".phpunit.cache/", ".phpunit.result.cache"],
        "php.tool-caches": [".php-cs-fixer.cache", ".phpstan.cache"],
        "php.vendor": ["vendor/"],
        "symfony.cache": ["var/cache/"],
        "symfony.logs": ["var/log/"],
    },
    blocked_without={
        "laravel.cache": ["artisan"],
        "laravel.logs": ["artisan"],
        "php.vendor": ["composer.json"],
        "symfony.cache": ["symfony.lock"],
        "symfony.logs": ["symfony.lock"],
    },
)

CASES = [CASE]


class TestPhp(ProfileSuite):
    case = CASE
