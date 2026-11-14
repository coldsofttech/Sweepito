# ruby

[Back to all profiles](../profiles.md)

Ruby: Bundler, Rails, Sinatra

**Detected by:** `Gemfile`, `config/application.rb`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `ruby.yard` | `/.yardoc/` | `Gemfile` | safe | YARD documentation cache |
| `ruby.coverage` | `/coverage/` | `Gemfile` | safe | SimpleCov reports |
| `rails.tmp-cache` | `/tmp/cache/` | `config/application.rb` | configurable | Rails Bootsnap and asset caches |
| `rails.tmp` | `/tmp/pids/`, `/tmp/sockets/` | `config/application.rb` | configurable | Stale PID files and sockets |
| `rails.logs` | `/log/*.log` | `config/application.rb` | configurable | Rails logs |
| `ruby.vendor-bundle` | `/vendor/bundle/` | `Gemfile` | high-impact | Bundled gems (requires reinstall) |

## Configuration

```toml
[clean]
enable = ["rails.tmp-cache", "rails.logs"]
```

Command-line equivalent:

```bash
sweepito clean -p ruby --enable rails.tmp-cache
```

Notes:

- Rails rules need `config/application.rb`.
- `rails.tmp` removes stale PID files and sockets that can block server start.
- `vendor/bundle/` is `high-impact` and needs `bundle install` afterwards.
