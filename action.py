import os
import time
from auth import Config, create_client, submit, wait_for_processing, DetailedException


class BadInputException(DetailedException):
    pass


class ProcessingException(DetailedException):
    pass


class Output:
    def __init__(self):
        self.asset_id = ""
        self.upload_id = ""
        self.uploaded = False

    def write(self):
        if is_github_action():
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                print(f"asset-id={self.asset_id}", file=f)
                print(f"upload-id={self.upload_id}", file=f)
                print(f"uploaded={self.uploaded}", file=f)
        else:
            os.environ["ASSET_ID"] = self.asset_id
            os.environ["UPLOAD_ID"] = self.upload_id
            os.environ["UPLOADED"] = str(self.uploaded)


OUTPUT = Output()


def error(exception):
    OUTPUT.write()
    str_error(type(exception).__name__, str(exception))
    if exception is DetailedException and exception.detail:
        print(exception.detail)
    if isinstance(exception, TimeoutError):
        print("A timeout has repeatedly occured. Please check your network conditions.")
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


def retry(retries, function, *args, **kwargs):
    """Retries a function `retries` times with exponential backoff"""

    tries = 0
    while True:
        try:
            return function(*args, **kwargs)
        except Exception as e:
            if tries == retries:
                raise e

            if is_github_action():
                print(
                    f"::warning title={type(e).__name__}::Retrying... ({tries+1}/{retries} retries)"
                )
            else:
                print(
                    f"ERROR: {type(e).__name__}: Retrying... ({tries+1}/{retries} retries)"
                )
            t = 2 * 2**tries
            time.sleep(t)
            tries += 1


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

    # create the config
    config = Config(
        get_input("TOKEN_URL", True),
        get_input("CLIENT_SECRET", True),
        get_input("AUDIENCE", True),
        get_input("CLIENT_ID", True),
        get_input("ORGANIZATION_ID", True),
        get_input("ENDPOINT", True),
    )

    return config


def main():
    try:
        # create the config file
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

    # create gql client
    try:
        client = retry(5, create_client, config)
    except Exception as e:
        error(e)
    print("Created client")

    # submit and assign outputs
    try:
        OUTPUT.upload_id, OUTPUT.asset_id, OUTPUT.uploaded = retry(
            5, submit, client, artifact_path, name, manufacturer, model, version
        )
    except Exception as e:
        error(e)

    # wait for the asset to finish processing and print the result
    print("Waiting for asset to finish processing...")

    try:
        processed_successfully = retry(5, wait_for_processing, client, OUTPUT.asset_id)
        if processed_successfully:
            print("Asset successfully processed")
        else:
            raise ProcessingException(
                "Asset failed to process",
                "The asset was successfully submitted, however it failed to finish processing.",
            )
    except Exception as e:
        print("The asset was successfully submitted, however an error occurred while waiting for it to finish processing.")
        error(e)


if __name__ == "__main__":
    main()
    OUTPUT.write()
