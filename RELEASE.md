# Releasing

This is a composite GitHub Action. Consumers pin a ref such as `@v1` or `@v1.0.8`. The Python, `action.yml`, and `requirements.txt` shipped at that ref are what run.

## Cut a patch/minor release (v1 line)

1. Land your changes on `main` (CI green).
2. Update [CHANGELOG.md](CHANGELOG.md) with the new version section (if not already done).
3. Create and push an annotated tag:

```bash
VERSION=v1.0.8
git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"
```

4. Pushing the `v*` tag triggers [.github/workflows/release.yml](.github/workflows/release.yml), which creates a GitHub Release from the matching CHANGELOG section.

5. Move the floating major tag so `@v1` picks up the fix (manual on purpose):

```bash
VERSION=v1.0.8
git tag -f v1 "$VERSION"
git push origin v1 --force
```

Only force-push the major tag (`v1`), never rewrite published patch tags like `v1.0.8`.

## Checklist

- [ ] Input and output names unchanged (or documented as a breaking change / major bump)
- [ ] `requirements.txt` pins reviewed
- [ ] CHANGELOG section matches the tag version (`1.0.8` for tag `v1.0.8`)
- [ ] CI passed on the commit you tagged
- [ ] Floating `v1` updated after the GitHub Release looks correct
