import os
from auth import create_sdk_config, create_client, submit_asset, query_asset_upload, DetailedException


class BadInputException(DetailedException):
    pass


class Output:
    def __init__(self):
        self.upload_id = ""
        self.uploaded = False
        self.asset_id = ""

    def write(self):
        if is_github_action():
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                print(f"upload-id={self.upload_id}", file=f)
                print(f"uploaded={self.uploaded}", file=f)
                print(f"asset-id={self.asset_id}", file=f)
        else:
            os.environ["UPLOAD_ID"] = self.upload_id
            os.environ["UPLOADED"] = str(self.uploaded)
            os.environ["ASSET_ID"] = self.asset_id


OUTPUT = Output()


def error(exception):
    OUTPUT.write()
    str_error(type(exception).__name__, str(exception))
    if isinstance(exception, DetailedException) and exception.detail:
        print(exception.detail)
    print()
    print("Check the README documentation for info about this exception.")
    print("For further support, contact support@netrise.com")
    exit(1)


def str_error(title, message):
    if is_github_action():
        print(f"::error title={title}::{message}")
    else:
        print(f"ERROR: {title}")
        if message:
            print(message)


def get_input(env: str, required: bool):
    upper = env.upper().replace("-", "_")
    lower = env.lower().replace("_", "-")
    if is_github_action():
        input = lower
    else:
        input = upper
    value = os.getenv(upper, None)

    if value is None and required:
        raise BadInputException(f"Input '{input}' is required.")
    return value


def is_github_action():
    return os.getenv("GITHUB_ACTIONS", False)


def create_config():
    # first, check if a config.yaml exists and pull info from that
    try:
        with open("config.yaml", "r") as cf:
            for line in cf:
                name, value = line.split(":", 1)
                name = name.upper().strip()
                value = value.strip().replace('"', "")
                os.environ[name] = value
            print("Using authentication info from config.yaml")
    except Exception as e:
        pass

    # create the SDK config
    try:
        config = create_sdk_config()
    except Exception as e:
        raise BadInputException(
            f"Failed to create config: {e}",
            "Please either provide the required environment variables/github inputs or supply a config.yaml file in the current working directory.",
        )

    return config


def main():
    try:
        # create the config
        config = create_config()

        # collect asset inputs
        artifact_path = get_input("ARTIFACT_PATH", True)
        name = get_input("NAME", True)
        manufacturer = get_input("MANUFACTURER", False)
        model = get_input("MODEL", False)
        version = get_input("VERSION", False)
    except BadInputException as e:
        error(e)

    # log OK and collected asset info
    print("Inputs OK!")
    print(f"'{artifact_path.split('/')[-1]}' will be submitted as '{name}'")
    if manufacturer:
        print(f"Manufacturer: '{manufacturer}'")
    if model:
        print(f"Model: '{model}'")
    if version:
        print(f"Version: '{version}'")

    # create SDK client
    try:
        client = create_client(config)
    except Exception as e:
        error(e)
    print("Created client")

    # submit asset and get upload_id
    try:
        OUTPUT.upload_id = submit_asset(
            client, artifact_path, name, manufacturer, model, version
        )
    except Exception as e:
        error(e)

    print(f"Upload complete. Upload ID: {OUTPUT.upload_id}")
    
    # query asset upload to get uploaded status and asset_id
    print("Querying asset upload status...")
    try:
        OUTPUT.upload_id, OUTPUT.uploaded, OUTPUT.asset_id = query_asset_upload(
            client, OUTPUT.upload_id
        )
        print(f"Upload status - Upload ID: {OUTPUT.upload_id}, Uploaded: {OUTPUT.uploaded}, Asset ID: {OUTPUT.asset_id}")
    except Exception as e:
        error(e)


if __name__ == "__main__":
    main()
    OUTPUT.write()
