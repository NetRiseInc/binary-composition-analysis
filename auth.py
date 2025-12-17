import os
from netrise_turbine_sdk import TurbineClient, TurbineClientConfig
from netrise_turbine_sdk_graphql.input_types import SubmitAssetInput, AssetUploadInput
import httpx


class DetailedException(Exception):
    def __init__(self, message, detail=None):
        self.message = message
        self.detail = detail

    def __str__(self):
        return self.message


class AuthException(DetailedException):
    pass


class SubmitAssetException(DetailedException):
    pass


def create_sdk_config() -> TurbineClientConfig:
    """Create TurbineClientConfig from environment variables."""
    token_url = os.getenv("TOKEN_URL")
    if not token_url:
        raise AuthException(
            "TOKEN_URL is required",
            "The TOKEN_URL environment variable must be set.",
        )
    
    # Extract domain: "https://domain.auth0.com/oauth/token" -> "https://domain.auth0.com"
    auth0_domain = token_url.rsplit("/oauth/token", 1)[0].rstrip("/")
    
    endpoint = os.getenv("ENDPOINT")
    if not endpoint:
        raise AuthException(
            "ENDPOINT is required",
            "The ENDPOINT environment variable must be set.",
        )
    
    return TurbineClientConfig(
        endpoint=endpoint,
        auth0_domain=auth0_domain,
        auth0_client_id=os.getenv("CLIENT_ID"),
        auth0_client_secret=os.getenv("CLIENT_SECRET"),
        auth0_audience=os.getenv("AUDIENCE"),
        auth0_organization_id=os.getenv("ORGANIZATION_ID"),
    )


def create_client(config: TurbineClientConfig) -> TurbineClient:
    """Create and return a TurbineClient instance."""
    try:
        print("Authenticating...")
        client = TurbineClient(config)
        print("Successfully authenticated")
        return client
    except Exception as e:
        raise AuthException(
            f"Failed to authenticate: {e} ({type(e).__name__})",
            "An issue has occurred with authentication. Double-check your configuration inputs.",
        )


def submit_asset(
    client: TurbineClient,
    artifact_path: str,
    name: str,
    manufacturer: str = None,
    model: str = None,
    version: str = None,
) -> str:
    """Submit an asset and return the upload_id.
    
    Args:
        client: TurbineClient instance
        artifact_path: Path to the artifact file
        name: Asset name
        manufacturer: Optional manufacturer
        model: Optional model
        version: Optional version
    
    Returns:
        upload_id: The upload ID for this submission
    """
    print("Submitting asset...")
    
    try:
        # Create SubmitAssetInput with optional fields
        submit_input = SubmitAssetInput(
            name=name,
            manufacturer=manufacturer or None,
            model=model or None,
            version=version or None,
        )
        
        # Call mutation to get upload URL
        # Use just the filename, not the full path
        import os as os_module
        file_name = os_module.path.basename(artifact_path)
        with client.graphql() as gql_client:
            response = gql_client.mutation_asset_submit(
                asset_submit_file_name=file_name,
                asset_submit_args=submit_input,
            )
            
            upload_url = response.asset.submit.upload_url
            upload_id = response.asset.submit.upload_id
        
        # Upload file to the upload URL with proper headers and timeout
        with open(artifact_path, "rb") as f:
            file_content = f.read()
            with httpx.Client() as http_client:
                upload_response = http_client.put(
                    upload_url,
                    content=file_content,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=300.0,
                )
                upload_response.raise_for_status()
        
        print("Successfully submitted asset")
        return upload_id
        
    except Exception as e:
        raise SubmitAssetException(
            f"Failed to submit asset: {e} ({type(e).__name__})",
            "An exception occurred trying to submit the asset to Turbine. This could be due to a network issue or authentication problem.",
        )


def query_asset_upload(client: TurbineClient, upload_id: str) -> tuple[str, bool, str]:
    """Query asset upload status and return upload_id, uploaded status, and asset_id.
    
    Args:
        client: TurbineClient instance
        upload_id: The upload ID to query
    
    Returns:
        tuple: (upload_id, uploaded, asset_id)
    """
    try:
        with client.graphql() as gql_client:
            response = gql_client.query_asset_upload(
                asset_upload_args=AssetUploadInput(upload_id=upload_id)
            )
        
        # Note: asset_upload can be null if the uploadId is unknown / expired
        upload = response.asset_upload
        if not upload:
            return (upload_id, False, "")
        
        return (
            upload.upload_id or upload_id,
            upload.uploaded or False,
            upload.asset_id or "",
        )
    except Exception as e:
        raise SubmitAssetException(
            f"Failed to query asset upload: {e} ({type(e).__name__})",
            "An exception occurred trying to query the asset upload status.",
        )


def query_asset_upload_with_retry(
    client: TurbineClient,
    upload_id: str,
    max_retries: int = 10,
    retry_delay_seconds: float = 2.0,
) -> tuple[str, bool, str]:
    """Query asset upload status with retry logic until asset_id is available or max retries reached.
    
    Args:
        client: TurbineClient instance
        upload_id: The upload ID to query
        max_retries: Maximum number of retry attempts (default: 10, minimum: 1)
        retry_delay_seconds: Delay between retries in seconds (default: 2.0, minimum: 0.5)
    
    Returns:
        tuple: (upload_id, uploaded, asset_id)
    """
    import time
    
    # Ensure valid retry parameters
    max_retries = max(1, max_retries)
    retry_delay_seconds = max(0.5, retry_delay_seconds)
    
    for attempt in range(1, max_retries + 1):
        upload_id_result, uploaded, asset_id = query_asset_upload(client, upload_id)
        
        # If we got an asset_id, we're done
        if asset_id:
            if attempt > 1:
                print(f"Asset ID retrieved after {attempt} attempt(s)")
            return (upload_id_result, uploaded, asset_id)
        
        # If this is not the last attempt, wait and retry
        if attempt < max_retries:
            print(f"Attempt {attempt}/{max_retries}: Asset ID not yet available. Retrying in {retry_delay_seconds}s...")
            time.sleep(retry_delay_seconds)
        else:
            print(f"Attempt {attempt}/{max_retries}: Asset ID still not available after {max_retries} attempts.")
            print("This is normal - the asset may still be processing. The upload_id can be used to query status later.")
    
    # Return the last result even if asset_id is empty
    return (upload_id_result, uploaded, asset_id)
