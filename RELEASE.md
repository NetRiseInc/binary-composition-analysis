# Releasing

This is a composite GitHub Action. Consumers pin a ref such as `@v1` or `@v1.0.8`. The Python, `action.yml`, and `requirements.txt` shipped at that ref are what run.

Releases are cut locally with `git` + the [GitHub CLI](https://cli.github.com/) (`gh`).

## Cut a release

1. Land your changes on `main` and **push** them (`CI` green on `main`).
2. Ensure [CHANGELOG.md](CHANGELOG.md) has a section for the version you will ship (e.g. `## 1.1.0` for tag `v1.1.0`).
3. On a clean checkout of `main` that matches `origin/main`:

```bash
make release
```

The script will:

1. Confirm you are on `main`, clean, and in sync with `origin/main`
2. Detect the current release tag
3. Suggest the next version — **minor (default)** or **major** (patch is also offered)
4. Ask for **y/n** confirmation
5. Ask whether to update the floating major tag (`@v1`, `@v2`, …) — default yes
6. Run `make check` (skip with `SKIP_CHECK=1`)
7. Create the annotated tag, push it, and run `gh release create` from the CHANGELOG section

Requires `gh` authenticated to this repo (`gh auth status`).

### Non-interactive

```bash
VERSION=v1.0.8 make release
VERSION=v1.0.8 UPDATE_MAJOR=1 make release
```

## Checklist

- [ ] Changes are on `origin/main` and CI is green
- [ ] Input and output names unchanged (or documented as a breaking change / major bump)
- [ ] `requirements.txt` pins reviewed
- [ ] CHANGELOG section matches the tag you will confirm
- [ ] Ran `make release` (and accepted updating the floating major tag when `@vN` should move)
