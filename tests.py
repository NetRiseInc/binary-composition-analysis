from auth import create_client
from action import create_config, submit, wait_for_processing, OUTPUT, error, str_error, BadInputException
import os
import base64


def test_config():
    print("Testing config creation...")
    try:
        config = create_config()
    except BadInputException:
        str_error(
            "Failed to create config",
            "Please either provide the required environment variables/github inputs or supply a config.yaml file in the current working directory.",
        )
        exit(1)
    print("Config test successful")
    return config


def test_client(config):
    print("Testing client creation...")
    client = create_client(config)
    print("Client test successful")
    return client


def test_submit(client):
    print("Testing asset submission with mock data...")

    # create random fake firmware file
    data = base64.b64encode(os.urandom(1000)).decode("utf-8")
    with open(".fake-firmware.bin", "w") as ff:
        ff.write(data)

    upload_id, asset_id, uploaded = submit(
        client,
        ".fake-firmware.bin",
        "GitHub Action Test",
        "NetRise",
        "NR-1000",
        "1.2.3",
    )
    os.remove(".fake-firmware.bin")

    print("Asset submission test successful")
    return (upload_id, asset_id, uploaded)


def test_wait_for_processing(client, asset_id):
    print("Testing wait_for_processing...")
    wait_for_processing(client, asset_id)
    print("wait_for_processing test successful")


def test_all():
    print("Running tests...")

    try:
        config = test_config()
        client = test_client(config)
        OUTPUT.upload_id, OUTPUT.asset_id, OUTPUT.uploaded = test_submit(client)
        test_wait_for_processing(client, OUTPUT.asset_id)
        OUTPUT.write()

        print("All tests successful. Final outputs:")
        print(f"asset-id: {OUTPUT.asset_id}")
        print(f"upload-id: {OUTPUT.upload_id}")
        print(f"uploaded: {OUTPUT.uploaded}")

    except Exception as e:
        error(e)


if __name__ == "__main__":
    test_all()
