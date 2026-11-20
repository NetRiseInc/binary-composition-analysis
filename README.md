# NetRise Binary Composition Analysis

GitHub Action that uploads a software artifact to the [NetRise Turbine](https://netrise.io) platform and returns upload identifiers you can use in later steps.

It authenticates, uploads the file, then polls briefly for an asset ID. It does **not** wait for full binary analysis to finish.

Pin a release tag when you use it (`@v1` or `@v1.0.8`). That tag is the code that runs.

## Quick start

Store auth values in [GitHub secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions), then add:

```yaml
- name: Upload to NetRise
  id: netrise
  uses: NetRiseInc/binary-composition-analysis@v1
  with:
    client-id: ${{ secrets.NETRISE_CLIENT_ID }}
    client-secret: ${{ secrets.NETRISE_CLIENT_SECRET }}
    organization-id: ${{ secrets.NETRISE_ORGANIZATION_ID }}
    domain: ${{ secrets.NETRISE_DOMAIN }}
    audience: ${{ secrets.NETRISE_AUDIENCE }}
    endpoint: ${{ secrets.NETRISE_ENDPOINT }}
    artifact-path: dist/my-package.whl
    name: my-package
    version: 1.2.3

- name: Use upload results
  run: |
    echo "upload-id=${{ steps.netrise.outputs.upload-id }}"
    echo "uploaded=${{ steps.netrise.outputs.uploaded }}"
    echo "asset-id=${{ steps.netrise.outputs.asset-id }}"
```

`artifact-path` is relative to the job workspace (or an absolute path). Build or download the artifact in an earlier step so the file exists before this action runs.

## Inputs

### Authentication (all required)

| Input | What to put |
| --- | --- |
| `client-id` | Auth0 client ID |
| `client-secret` | Auth0 client secret |
| `organization-id` | NetRise organization ID |
| `domain` | Auth0 **domain** only, e.g. `https://authn.turbine.netrise.io` — not a full `/oauth/token` URL |
| `audience` | Auth0 audience |
| `endpoint` | Turbine API endpoint |

These match the fields in the NetRise API config you were given.

### Asset

| Input | Required | Notes |
| --- | --- | --- |
| `artifact-path` | yes | File to upload. Relative to `GITHUB_WORKSPACE`, or absolute. |
| `name` | yes | Label for the asset in Turbine. |
| `version` | no | Strongly recommended. |
| `manufacturer` | no | Optional metadata. |
| `model` | no | Optional metadata. |

## Outputs

| Output | Meaning |
| --- | --- |
| `upload-id` | Upload job ID. Keep this if you need to query status later. |
| `uploaded` | `true` or `false` — whether the file upload finished. |
| `asset-id` | Turbine asset ID. May be empty if provisioning is still in progress after the short poll. |

Example conditional:

```yaml
- if: ${{ steps.netrise.outputs.uploaded == 'true' }}
  run: echo "Asset ${{ steps.netrise.outputs.asset-id }}"
```

## Self-hosted

Same script the Action runs. From a checkout of this repo:

```bash
pip install -r requirements.txt

export CLIENT_ID=...
export CLIENT_SECRET=...
export ORGANIZATION_ID=...
export DOMAIN=https://authn.turbine.netrise.io
export AUDIENCE=...
export ENDPOINT=...

export ARTIFACT_PATH=./firmware.bin   # relative to cwd, or absolute
export NAME=my-firmware
export VERSION=1.2.3                  # optional: MANUFACTURER, MODEL

python action.py

set -a; source netrise-outputs.env; set +a
echo "$UPLOAD_ID $UPLOADED $ASSET_ID"
```

Optional: put auth fields in a local `config.yaml` (`KEY: value` lines) instead of exporting them. Do not commit that file.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `BadInputException` | Missing required input, or `artifact-path` does not exist at run time. |
| `AuthException` | Wrong credentials, or `domain` is a token URL instead of the Auth0 domain. |
| `SubmitAssetException` | Upload URL / PUT / status query failed (network or auth). |
| Empty `asset-id`, job still green | Normal after the short poll; use `upload-id` to check later. Analysis is not finished yet. |

## Support

<support@netrise.com>

## Maintainers

```bash
make install   # once
make check     # lint + format check + tests (same gates as CI)
```

Release and floating `@v1` tag steps: [RELEASE.md](RELEASE.md).
