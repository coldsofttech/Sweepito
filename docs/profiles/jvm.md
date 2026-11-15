# jvm

[Back to all profiles](../profiles.md)

Java and JVM: Maven, Gradle, Kotlin, Spring Boot

**Detected by:** `build.sbt`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `jvm.kotlin` | `/.kotlin/` | `build.gradle`, `build.gradle.kts` | safe | Kotlin compiler session data |
| `jvm.maven-target` | `/target/` | `pom.xml` | configurable | Maven build output |
| `jvm.gradle-project` | `/.gradle/` | `settings.gradle`, `settings.gradle.kts`, `build.gradle`, `build.gradle.kts` | configurable | Project-level Gradle cache (not ~/.gradle) |
| `jvm.gradle-build` | `/build/` | `build.gradle`, `build.gradle.kts` | configurable | Gradle build output |
| `jvm.idea-out` | `/out/` | `*.iml` | configurable | IntelliJ default output directory |
| `jvm.sbt-target` | `/project/target/`, `/project/project/` | `build.sbt` | configurable | SBT meta-build output |
| `jvm.scala-tools` | `/.bloop/`, `/.metals/` | `build.sbt`, `build.sc`, `pom.xml`, `build.gradle`, `build.gradle.kts` | safe | Bloop and Metals build and language-server caches |

## Configuration

```toml
[clean]
enable  = ["jvm.maven-target", "jvm.gradle-build"]
exclude = ["legacy-module/"]
```

Command-line equivalent:

```bash
sweepito clean -p jvm --enable jvm.maven-target --enable jvm.gradle-build
```

Notes:

- `jvm.maven-target` needs `pom.xml`; `jvm.gradle-build` and `jvm.kotlin` need `build.gradle` or `build.gradle.kts`; `jvm.idea-out` needs an `*.iml` file.
- `jvm.gradle-project` removes the project-level `.gradle/` only, never `~/.gradle`.
- Spring Boot output lives in the Maven or Gradle build directories above.
