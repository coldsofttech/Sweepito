# elixir

[Back to all profiles](../profiles.md)

Elixir: Mix and Phoenix

**Detected by:** `mix.exs`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `elixir.ls` | `/.elixir_ls/` | `mix.exs` | safe | ElixirLS cache |
| `elixir.crash` | `erl_crash.dump` | `mix.exs` | safe | Erlang crash dumps |
| `elixir.cover` | `/cover/` | `mix.exs` | safe | Coverage reports |
| `elixir.build` | `/_build/` | `mix.exs` | configurable | Mix build output |
| `phoenix.static` | `/priv/static/` | `mix.exs` | configurable | Phoenix compiled assets (tracked files are protected) |
| `elixir.deps` | `/deps/` | `mix.exs` | high-impact | Mix dependencies |

## Configuration

```toml
[clean]
enable = ["elixir.build", "phoenix.static"]
```

Command-line equivalent:

```bash
sweepito clean -p elixir --enable elixir.build
```

Notes:

- `phoenix.static` removes `priv/static/` only when it is git-ignored and untracked, so committed static assets are safe.
- `deps/` is `high-impact` and needs `mix deps.get` afterwards.
