# swift

[Back to all profiles](../profiles.md)

Swift Package Manager and Xcode

**Detected by:** `Package.swift`, `*.xcodeproj/project.pbxproj`, `Podfile`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `swift.build` | `/.build/` | `Package.swift` | configurable | SwiftPM build output |
| `swift.swiftpm` | `/.swiftpm/` | `Package.swift` | configurable | SwiftPM and Xcode package state |
| `xcode.xcuserdata` | `xcuserdata/` | `*.xcodeproj/project.pbxproj` | configurable | Per-user Xcode state |
| `xcode.pods` | `/Pods/` | `Podfile` | high-impact | CocoaPods dependencies (requires pod install) |

## Configuration

```toml
[clean]
enable = ["swift.build", "xcode.xcuserdata"]
```

Command-line equivalent:

```bash
sweepito clean -p swift --enable swift.build
```

Notes:

- Xcode projects are detected through `*.xcodeproj/project.pbxproj`.
- `~/Library/Developer/Xcode/DerivedData` is global and out of scope.
- `Pods/` is `high-impact` and needs `pod install` afterwards.
