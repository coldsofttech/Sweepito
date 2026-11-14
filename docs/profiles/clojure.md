# clojure

[Back to all profiles](../profiles.md)

Clojure: Leiningen and tools.deps

**Detected by:** `project.clj`, `deps.edn`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `clojure.cpcache` | `/.cpcache/` | `deps.edn` | safe | tools.deps classpath cache |
| `clojure.target` | `/target/` | `project.clj`, `deps.edn` | safe | Leiningen and tools.build output |

## Configuration

```toml
[clean]
enable = ["clojure.target"]
```

Command-line equivalent:

```bash
sweepito clean -p clojure --enable clojure.target
```

Notes:

- `.cpcache/` needs `deps.edn`; `target/` needs `project.clj` or `deps.edn`.
- `~/.m2` and `~/.gitlibs` are global and out of scope.
