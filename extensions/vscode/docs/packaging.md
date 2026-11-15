# Packaging and publishing

The extension ships as a single `.vsix` file. It is published to the Visual Studio Marketplace
and attached to each GitHub release. Run the commands below from
`extensions/vscode/`.

## What is in the package

The `.vsix` holds only what the extension needs at run time:

| File                                                   | Purpose                                                                            |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `dist/extension.js`                                    | The extension, bundled with its dependencies                                       |
| `dist/sweepito-hook.js`                                | The script an installed Git hook runs when the `sweepito` command is not available |
| `media/`                                               | The icon and the activity bar icon                                                 |
| `package.json`, `README.md`, `CHANGELOG.md`, `LICENSE` | The listing, shown on the Marketplace page                                         |

Everything else is left out by `.vscodeignore`, which excludes all files and then lists the ones
above. Because the code is bundled, the package ships without `node_modules`, and it is built
without installing dependencies. The bundled profiles come from the Python package
(`python/src/sweepito/profiles/`); they are converted to JSON when the extension is built.

## Build it yourself

```bash
npm ci
npm run package        # writes sweepito-<version>.vsix
```

`npm run package` runs the production build first (minified, no source maps), then packs the
file. To check what went in, run `npx vsce ls`. To try the result in VS Code:

```bash
code --install-extension sweepito-0.1.0.vsix
```

Remove it from the Extensions view, or with `code --uninstall-extension coldsofttech.sweepito`.

The extension needs VS Code 1.90 or later, and Git. It needs neither Python nor the `sweepito`
command line tool.

## Publishing

Publishing is done by the release workflow, not from a developer machine.

- **GitHub release.** Always. The `.vsix` is attached to the release for the tag.
- **Visual Studio Marketplace.** Under the `coldsofttech` publisher, through trusted
  publishing: the Marketplace trusts the `release.yml` workflow, so no token is stored.

The publish job runs in the `vscode` GitHub environment, so a reviewer has to approve the release
before anything is published. The extension is not published to Open VSX yet.

## CI and releases

- `.github/workflows/ci.yml` lints, tests, builds and packages the extension on pull requests
  that touch `extensions/`, the bundled profiles or the config template. The `.vsix` is uploaded
  as a build artifact for a week.
- `.github/workflows/release.yml` runs on a `vscode-vX.Y.Z` tag. It checks that the tag matches
  `version` in `package.json` and that `ci` passed on the tagged commit, then builds the `.vsix`
  and publishes as above. See [development.md](../../../docs/development.md#releasing)
  for the release steps.
