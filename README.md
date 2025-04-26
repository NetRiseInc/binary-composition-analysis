# NetRise: Binary Composition Analysis

This action automates the process of uploading software artifacts to NetRise's Turbine for composition analysis.

## Usage

### GitHub Action

```bash
- uses: netrise/artifact-submitter@v1
  with:

    # Authentication Info
    client-id: ""
    client-secret: ""
    organization-id: ""
    token-url: ""
    audience: ""
    endpoint: ""
    
    # Asset Info
    artifact-path: ""
    name: ""
    manufacturer: ""   (optional)
    model: ""          (optional)
    version: ""        (optional)
```

### Self-Hosted

If you are using this in a self-hosted environment, provide the following environment variables before running the script `action.py`:

```bash
# Authentication Info
CLIENT_ID=""
CLIENT_SECRET=""
ORGANIZATION_ID=""
TOKEN_URL=""
AUDIENCE=""
ENDPOINT=""

# Asset Info
ARTIFACT_PATH=""
NAME=""
MANUFACTURER=""   (optional)
MODEL=""          (optional)
VERSION=""        (optional)
```

You can also provide a `config.yaml` file in the working directory of the script to provide authentication info. If you do this, you can omit the authentication environment variables. But please don't put this file in your repository, as it contains sensitive information.

## Documentation

### Input

#### Authentication

The Authentication inputs are required as they provide necessary authentication information to NetRise's servers. You can find this information in your provided NetRise API configuration file (config.yaml). It is recommended to use GitHub's [secret](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) system to hold this data so as not to keep sensitive information in plain text in your repository.

#### Asset

The asset inputs configure how your software artifacts are sent to NetRise. Only two of these are required.

`artifact-path` (required): This is the path to your software artifact that will be submitted to Turbine for analysis.

`name` (required): This is the name of your software artifact. This can be whatever you want, it will be the primary label of the asset when submitted to Turbine.

`manufacturer` (optional): The manufacturer of your software artifact.

`model` (optional): The model of your software artifact.

`version` (optional): The current version of your software artifact. This field is optional, though it is very recommended.

### Output

#### GitHub

After running, the action provides the following outputs:

```bash
asset-id - The final submitted asset ID
upload-id - The ID for the upload job
uploaded - (True/False) Whether or not the asset was successfully uploaded
```

#### Self-Hosted

If in a self-hosted environment, the action provides the following environment variables after running:

```bash
ASSET_ID - The final submitted asset ID
UPLOAD_ID - The ID for the upload job
UPLOADED - (True/False) Whether or not the asset was successfully uploaded
```

### Errors

#### BadInputException

This exception occurs when a required input is not provided. Check the Usage section above to find which required input you are not providing. All inputs except those marked (optional) are required.

#### AuthException

An exception has occurred while initially authenticating. This is likely due to incorrect authentication credentials, so double-check your auth info and ensure they match those in your given NetRise configuration file. This could also occur due to a network issue (e.g., failing to connect to NetRise's authentication servers in the first place).

#### SubmitAssetException

An exception occured when trying to submit your software artifact to Turbine. This is most likely a network issue: either failing to get an upload URL from NetRise's servers, or failing to upload the artifact to that URL. It is also possible this is an authentication issue, so double-check your authentication information.

#### ProcessingException

This exception occurs only when your asset fails to process. This means your software artifact was successfully submitted to Turbine, however the platform failed to process it. Please contact support for help figuring out what the issue with your software artifact is.

#### TimeoutError

This exception occurs when a network request takes too long to process. Please check your network condition.

## Support

You may contact us at <support@netrise.com> for any further questions.
