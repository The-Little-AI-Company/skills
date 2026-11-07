# Surfaces

Read this in step 6. The README is one surface among several, and a README is often read off GitHub. Test each surface the project publishes to, because rules differ.

Repository settings are the owner's to change. Give them the exact values and commands. Sources were read on 2026-11-06.

## Audit first

These commands read only:

```text
gh repo view owner/repo --json description,homepageUrl,usesCustomOpenGraphImage,latestRelease
gh api repos/owner/repo/topics --jq .names
```

`repo-audit` reports these as MET-001 to MET-004.

## Description

- One plain sentence on what the project does. It repeats the README's purpose sentence.
- [Standard Readme](https://github.com/RichardLitt/standard-readme/blob/main/spec.md) keeps it under 120 characters and matches it to the package manager description.
- The Terraform Registry uses it as the module's short description.
- Having one is opinion for private scratch repositories.

```text
gh repo edit owner/repo --description "Turn build logs into charts."
```

## Topics

- [GitHub's rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics): at most 20 topics. Each is lowercase with hyphens, 50 characters at most.
- Having at least one is opinion.
- Cover the language, the problem and the type, such as `cli`, `logging` and `go`. Prefer topics that peers already use, and check by opening the topic page. This is opinion.

```text
gh repo edit owner/repo --add-topic cli --add-topic logging
gh repo edit owner/repo --remove-topic misc
```

## Website

Set a homepage when a site or docs site exists. Leave it empty otherwise.

```text
gh repo edit owner/repo --homepage "https://example.com"
```

## Social preview

- [GitHub's rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview): PNG, JPG or GIF under 1 MB, at least 640 by 320, best at 1280 by 640. If unsure about transparency, use a solid background.
- This shows wherever the link is shared. Keep text large enough to read at thumbnail size, and keep it inside the center. This is opinion.
- [socialify](https://github.com/wei/socialify) generates these images. A custom one built from the product usually looks better. This is opinion.
- `gh repo edit` has no flag for this. The owner uploads the image in the browser, under Settings, General, Social preview.
- Having a custom image is opinion. Do not generate one that makes a claim the README does not support.

Confirm after upload:

```text
gh repo view owner/repo --json usesCustomOpenGraphImage --jq .usesCustomOpenGraphImage
```

## Releases

- A release shows in the sidebar and gives users a stable thing to install. Publish one when the project has versions.
- Write notes for users, not as a commit list.
- Attach binaries for `cli`, `desktop` and `game` types, and link the download from the README. Downloads per platform are a type rule in [presets.md](presets.md).
- Link to `releases/latest` from the README instead of naming a version.

```text
gh release create v1.2.0 --title "v1.2.0" --generate-notes
gh release edit v1.2.0 --notes-file notes.md
```

Publishing a release is an outward action. It waits for the owner.

## Pinned repositories

Up to six repositories and gists, combined, set in the browser. See [profile.md](profile.md#pinned-repositories).

## npm

- [npm](https://docs.npmjs.com/about-package-readme-files) refreshes the README only on publish. A README fix on GitHub does not reach the package page until the next version.
- Handling of relative images and `<picture>` on npm was not verified. Render the package page after publishing, or use absolute URLs pinned to a tag.

```text
npm publish --dry-run
npm publish
```

The dry run shows what the package will include. Use the project's own package manager and release flow if it has one.

## PyPI

[The packaging guide](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/):

- `Description` holds the README contents. `Description-Content-Type` must match, and takes `text/plain`, `text/x-rst` or `text/markdown`.
- In `setup.py`, these are `long_description` and `long_description_content_type`. The first takes the contents, not a path.
- Invalid reStructuredText makes PyPI show raw source. Sphinx directives and roles are not allowed.
- `twine` 1.12.0 or later validates rendering.

```text
python -m build
twine check dist/*
```

Handling of relative images and `<picture>` on PyPI was not verified. Use absolute URLs pinned to a tag until checked.

## VS Code Marketplace

[The publishing guide](https://code.visualstudio.com/api/working-with-extensions/publishing-extension):

- Image URLs in `README.md` and `CHANGELOG.md` must resolve to `https`.
- Images cannot be SVG unless they come from a [trusted badge provider](https://code.visualstudio.com/api/references/extension-manifest#approved-badges). `vsce` refuses to publish user-provided SVGs.
- The `icon` in `package.json` is a PNG of at least 128 by 128 pixels, and cannot be SVG.
- If `repository` points to a public GitHub repository, `vsce` rewrites relative links, using `main` by default.
- `--githubBranch` picks another branch. `--baseContentUrl` and `--baseImagesUrl` set the bases directly.

```text
vsce package
vsce package --githubBranch release
vsce publish
```

`vsce package` builds a `.vsix` without publishing, which is the safe test. [prettier-vscode](https://github.com/prettier/prettier-vscode) has zero non-badge images, which sidesteps the SVG rule.

## Terraform Registry

[Rules for public modules](https://developer.hashicorp.com/terraform/registry/modules/publish). Private modules need not follow them.

- A public GitHub repository named `terraform-<PROVIDER>-<NAME>`. `<NAME>` may contain hyphens.
- A single-sentence repository description, used as the short description.
- The standard module structure, so the Registry can parse it.
- Semantic version tags, with an optional `v` prefix. At least one must exist before publishing.
- The Registry shows generated documentation, the README, examples, inputs, outputs, dependencies and version history.

README requirements beyond display were not found in that page. Keep inputs and outputs generated by [terraform-docs](https://terraform-docs.io/), between `BEGIN_TF_DOCS` markers. The first command below was not run during the research.

```text
terraform-docs markdown table --output-file README.md --output-mode inject .
gh release create v1.0.0 --generate-notes
```

## Hugging Face

[Model cards](https://huggingface.co/docs/hub/model-cards):

- `README.md` renders as the model card, with YAML metadata at the top.
- Theme images use `#hf-dark-mode-only` and `#hf-light-mode-only`, so GitHub's `<picture>` may not carry over.
- Cover intended use, limits, data and metrics.

Push `README.md` to the model repository on the Hub. Keep a separate card if the GitHub README must stay free of YAML metadata. Check the card on the Hub after pushing.

## GitHub Marketplace for Actions

To list an Action, keep a single `action.yml` at the repository root. [GitHub's page](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace) did not cover README or branding requirements, so those are unverified.

## App stores

Store badge artwork rules for Apple and Google were not read. Check the current brand rules before adding a store badge.

## Not verified

- npm and PyPI handling of relative images and `<picture>`.
- Mermaid on npm, PyPI, the Marketplace and the Registry.
- Marketplace README or branding requirements for Actions.
- Terraform Registry README requirements beyond display.
- Store badge artwork rules.

When a surface is unverified, publish a test version or check a real package page, and record what you saw in the pull request.
