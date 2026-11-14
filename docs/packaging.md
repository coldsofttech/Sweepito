# Packaging and installers

Sweepito ships as a Python package on PyPI and as native installers for each operating system.
The installers bundle the Python runtime, so they need no Python on the machine.

| OS | File | Installs to | On `PATH` |
| --- | --- | --- | --- |
| Windows | `sweepito-<version>.setup.exe` | `%LOCALAPPDATA%\Programs\coldsofttech\Sweepito` (this user) or `Program Files` (all users) | optional, on by default |
| Windows | `sweepito-<version>-windows-x64.zip` | wherever you unzip it | no (portable) |
| Debian, Ubuntu | `sweepito_<version>_<arch>.deb` | `/usr/lib/sweepito` | `/usr/bin/sweepito` |
| Fedora, RHEL, openSUSE | `sweepito-<version>.<arch>.rpm` | `/usr/lib/sweepito` | `/usr/bin/sweepito` |
| macOS | `sweepito-<version>-macos-<arch>.pkg` | `/usr/local/lib/sweepito` | `/usr/local/bin/sweepito` |
| macOS | `sweepito-<version>-macos-<arch>.tar.gz` | wherever you extract it | no (portable) |

`<arch>` is `x86_64`/`amd64` or `arm64`. Download the files from the
[GitHub releases](https://github.com/coldsofttech/Sweepito/releases); `SHA256SUMS.txt` lists their
checksums.

## Install and remove

**Windows.** Run the setup, or silently:

```powershell
sweepito-0.1.0.setup.exe /S /currentuser          # this user, no administrator needed
sweepito-0.1.0.setup.exe /S /allusers             # all users (UAC prompt)
sweepito-0.1.0.setup.exe /S /NOPATH /D=C:\Tools\Sweepito
```

Remove it in Settings > Apps, or run `uninstall.exe /S` from the install folder.

**Linux.**

```bash
sudo apt-get install ./sweepito_0.1.0_amd64.deb    # remove: sudo apt-get remove sweepito
sudo dnf install ./sweepito-0.1.0.x86_64.rpm       # remove: sudo dnf remove sweepito
```

**macOS.** Open the `.pkg`, or:

```bash
sudo installer -pkg sweepito-0.1.0-macos-arm64.pkg -target /
sudo /usr/local/lib/sweepito/uninstall.sh          # remove
```

Every installer removes only the files it installed. Settings and your projects are never touched.

## Build them yourself

An installer is built on the OS it is for (PyInstaller does not cross-compile), from the project's
metadata: names and version from `pyproject.toml` and `sweepito.__version__`.

```bash
uv sync --group installer
uv run python scripts/build_installer.py --smoke   # writes dist/installer/
```

`--smoke` starts the frozen program and checks that it reports its version and loads the bundled
profiles. Extra tools, pinned in `installer/tools.toml`:

- Windows: [NSIS](https://nsis.sourceforge.io/) (`makensis` on `PATH`)
- Linux: [nfpm](https://nfpm.goreleaser.com/) (`nfpm` on `PATH`, or set `NFPM`); `--formats deb` or
  `--formats rpm` builds one
- macOS: `pkgbuild` and `productbuild`, which come with Xcode's command line tools

| Path | Purpose |
| --- | --- |
| `installer/pyinstaller/cli.spec` | PyInstaller one-folder build, shared by every OS |
| `installer/windows/` | NSIS setup (`cli.nsi`, `common.nsh`) and the `PATH` helper (`path.ps1`) |
| `installer/linux/nfpm.yaml` | deb and rpm layout |
| `installer/macos/` | pkg distribution template and `uninstall.sh` |
| `installer/tools.toml` | versions of NSIS and nfpm |

## Signing

Installers are unsigned by default, so Windows SmartScreen and macOS Gatekeeper warn on first run.

- **Windows, any signing tool:** set `SIGN_COMMAND` to a command that signs one file, with `{file}` where its path
  goes. The executable and the setup are signed. In CI, store it as the repository variable
  `SIGN_COMMAND`.
- **Windows releases (SignPath):** `release.yml` can sign the setup with
  [SignPath](https://signpath.org/) (free certificates for open-source projects). It is off until you
  set it up once:
  1. Apply to the SignPath Foundation for the project and, once approved, create a project with the
     slug `sweepito`, a signing policy `release-signing` and the artifact configuration in
     `installer/signpath/artifact-configuration.xml` (slug `windows-setup`). Link the GitHub
     repository as the trusted build system.
  2. In the repository, add the secret `SIGNPATH_API_TOKEN` and the variable
     `SIGNPATH_ORGANIZATION_ID`. Only if your slugs differ, also set `SIGNPATH_PROJECT_SLUG`,
     `SIGNPATH_SIGNING_POLICY_SLUG` and `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG`.

  The release then signs `sweepito-<version>.setup.exe`; the signature is checked against this
  workflow run. The portable zip and the `sweepito.exe` inside the setup stay unsigned. SignPath's
  free tier covers Windows only, so the Linux and macOS files are not signed this way.
- **macOS:** set `MACOS_CODESIGN_IDENTITY` (Developer ID Application) and
  `MACOS_INSTALLER_IDENTITY` (Developer ID Installer). Notarize the signed `.pkg` afterwards with
  `xcrun notarytool submit --wait` and `xcrun stapler staple`.

## CI and releases

- `.github/workflows/installers.yml` builds every installer on pull requests that touch
  `installer/`, `src/` or the build script, and installs, runs and uninstalls each one.
- `.github/workflows/release.yml` builds them on a version tag and attaches them, with
  `SHA256SUMS.txt`, to the GitHub release. A failing installer stops the release before PyPI.
