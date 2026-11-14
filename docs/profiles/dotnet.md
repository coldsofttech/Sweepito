# dotnet

[Back to all profiles](../profiles.md)

.NET: C#, F#, ASP.NET Core

**Detected by:** `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `dotnet.testresults` | `TestResults/` | `*.csproj`, `*.fsproj`, `*.vbproj`, `*.sln` | safe | Test run output |
| `dotnet.bin-obj` | `/bin/`, `/obj/` | `*.csproj`, `*.fsproj`, `*.vbproj` | configurable | Build and intermediate output |
| `dotnet.artifacts` | `/artifacts/` | `Directory.Build.props`, `*.sln` | configurable | Centralised build artifacts |
| `dotnet.vs` | `/.vs/` | `*.sln` | configurable | Visual Studio per-user state |
| `dotnet.publish` | `/publish/` | `*.csproj`, `*.fsproj` | configurable | dotnet publish output |

## Configuration

```toml
[clean]
enable  = ["dotnet.bin-obj", "dotnet.publish"]
disable = ["dotnet.vs"]   # leave Visual Studio per-user state alone
```

Command-line equivalent:

```bash
sweepito clean -p dotnet --enable dotnet.bin-obj
```

Notes:

- `bin/` and `obj/` are only matched beside a `*.csproj`, `*.fsproj` or `*.vbproj`, because those names are generic.
- `dotnet.testresults` (`TestResults/`) is `safe` and matches at any depth.
- NuGet's global package cache is out of scope.
