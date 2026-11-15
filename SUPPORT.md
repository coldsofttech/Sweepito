# Support

## Getting help

- **Usage questions:** start with the [README](README.md), the [CLI reference](python/docs/cli.md)
  and the [configuration guide](docs/configuration.md). Run `sweepito <command> --help`
  for every option, and `sweepito doctor` to check your environment.
- **Which rule removed (or kept) something:** run `sweepito scan --verbose` and
  `sweepito rules --explain <rule-id>`; the [profiles and rules](docs/profiles.md) pages list
  every built-in rule.
- **Bugs:** [open an issue](https://github.com/coldsofttech/Sweepito/issues/new/choose) with
  the bug report form. Include the output of `sweepito --version` and `sweepito doctor`, your
  operating system, and the smallest repository layout that reproduces the problem.
- **Missing technology or rule:** use the *new technology or rule* issue form.
- **Feature ideas:** use the feature request form.

## Security issues

Do not report these in a public issue. Anything that makes Sweepito delete files it should
not is a vulnerability; follow [SECURITY.md](SECURITY.md).

## Supported versions

Only the latest released version receives fixes.

## Contributing

Want to fix something yourself? See [CONTRIBUTING.md](CONTRIBUTING.md).
