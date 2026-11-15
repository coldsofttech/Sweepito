# cpp

[Back to all profiles](../profiles.md)

C and C++: CMake, Make, Ninja, Meson

**Detected by:** `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `cpp.clangd` | `.cache/clangd/` | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | safe | clangd index |
| `cpp.cmake-build` | `cmake-build-*/` | `CMakeLists.txt` | configurable | CLion build directories |
| `cpp.build` | `/build/` | `CMakeLists.txt`, `meson.build`, `build.ninja` | configurable | Out-of-source build directory |
| `cpp.cmake-in-source` | `/CMakeCache.txt`, `/CMakeFiles/` | `CMakeLists.txt` | configurable | In-source CMake build leftovers |
| `cpp.objects` | `*.o`, `*.obj`, `*.a` | `CMakeLists.txt`, `Makefile`, `build.ninja`, `meson.build` | configurable | Object files and static libraries |
| `cpp.ninja` | `/.ninja_log`, `/.ninja_deps` | `build.ninja` | configurable | Ninja logs |
| `cpp.compile-commands` | `/compile_commands.json` | `CMakeLists.txt`, `meson.build`, `build.ninja`, `Makefile` | configurable | Generated compilation database (clangd needs it; regenerate with CMake, Bear or similar) |

## Configuration

```toml
[clean]
enable  = ["cpp.build", "cpp.cmake-build"]
exclude = ["third_party/"]

# Extra build directories named build-debug, build-release, ...
[[rule]]
id = "custom.cpp-build-dirs"
paths = ["/build-*/"]
requires = ["CMakeLists.txt"]
```

Command-line equivalent:

```bash
sweepito clean -p cpp --enable cpp.build --enable cpp.cmake-build
```

Notes:

- `cpp.build` needs `CMakeLists.txt`, `meson.build` or `build.ninja` beside it.
- `cpp.objects` (`*.o`, `*.obj`, `*.a`) is pattern based, so it only removes files that git ignores.
- A Makefile alone activates the profile but does not satisfy `cpp.build`.
