# ocaml

[Back to all profiles](../profiles.md)

OCaml: dune

**Detected by:** `dune-project`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `ocaml.build` | `/_build/` | `dune-project` | safe | dune build output |

## Configuration

```toml
[clean]
enable = ["ocaml.build"]
```

Command-line equivalent:

```bash
sweepito clean -p ocaml --enable ocaml.build
```

Notes:

- `_build/` is only matched beside `dune-project`.
