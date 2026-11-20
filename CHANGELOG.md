# Changelog

## 1.0.10

- Minor fix to test release automation

## 1.0.9

- Fix floating major-tag updates in `make release`: peel annotated release tags to the commit and write a lightweight unsigned `vN` tag (avoids nested tags and gitsign/sigstore hangs).

## 1.0.8

- Fix composite action outputs so `upload-id`, `uploaded`, and `asset-id` are available to callers.
- Run action code from `github.action_path` instead of re-checking out `main` (tags now pin the shipped Python).
- Pass `artifact-path` relative to the job workspace (or absolute); remove the `../` path hack.
- Pin `netrise-turbine-sdk==0.1.28` and `httpx` via `requirements.txt`.
- Stream artifact uploads instead of loading the whole file into memory.
- Self-hosted mode writes `netrise-outputs.env` (process env mutation never reached the parent shell).
- Add maintainer CI (ruff + pytest) and `make release` via the GitHub CLI (`gh`).


## 1.0.0

Initial Release
