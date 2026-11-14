# docker

[Back to all profiles](../profiles.md)

Docker, Compose, Dev Containers, BuildKit and Skaffold (daemon images, volumes and caches are never touched)

**Detected by:** `Dockerfile`, `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, `.devcontainer/devcontainer.json`, `.devcontainer.json`, `skaffold.yaml`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `docker.buildx-cache` | `/.buildx-cache/`, `/.buildx-cache-new/` | `Dockerfile` | configurable | Local BuildKit cache export (next build is slower) |

## Configuration

```toml
[clean]
enable = ["docker.buildx-cache"]
```

Command-line equivalent:

```bash
sweepito clean -p docker --enable docker.buildx-cache
```

Notes:

- Sweepito never runs Docker commands and never touches daemon storage, images, named volumes or global build caches.
- Compose, Dev Containers and Skaffold write no fixed project-local generated folder, so they have markers but no rules. Bind-mounted data folders are never targeted.
- `docker.buildx-cache` matches the conventional `.buildx-cache/` and `.buildx-cache-new/` destinations of `--cache-to type=local,dest=...`; for any other destination add a custom rule.
