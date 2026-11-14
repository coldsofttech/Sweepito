# terraform

[Back to all profiles](../profiles.md)

Terraform and Terragrunt (state files and lock files are never cleaned)

**Detected by:** `*.tf`, `terragrunt.hcl`

## Rules

| Rule ID | Targets | Requires | Risk | Description |
|---|---|---|---|---|
| `terraform.crash-log` | `crash.log`, `crash.*.log` | `*.tf` | safe | Terraform crash logs |
| `terraform.plans` | `*.tfplan`, `tfplan` | `*.tf` | configurable | Saved plans (a plan may be awaiting apply) |
| `terraform.dir` | `/.terraform/` | `*.tf` | configurable | Provider plugins (terraform init required again) |
| `terragrunt.cache` | `/.terragrunt-cache/` | `terragrunt.hcl` | configurable | Terragrunt module cache |

## Configuration

```toml
[clean]
enable = ["terraform.dir", "terragrunt.cache"]
```

Command-line equivalent:

```bash
sweepito clean -p terraform --enable terraform.dir
```

Notes:

- State files (`*.tfstate`, `*.tfstate.backup`) and `.terraform.lock.hcl` are never targeted by any rule.
- `terraform.dir` removes provider plugins, so `terraform init` must run again.
- `terraform.plans` is opt-in because a saved plan may be awaiting apply.
