from unittest.mock import MagicMock, mock_open, patch

from auth import query_asset_upload_with_retry, submit_asset


def test_query_asset_upload_with_retry_success_after_n():
    client = MagicMock()
    responses = [
        ("up-1", False, ""),
        ("up-1", False, ""),
        ("up-1", True, "asset-9"),
    ]

    with (
        patch("auth.query_asset_upload", side_effect=responses) as query,
        patch("time.sleep") as sleep,
    ):
        result = query_asset_upload_with_retry(
            client, "up-1", max_retries=5, retry_delay_seconds=0.5
        )

    assert result == ("up-1", True, "asset-9")
    assert query.call_count == 3
    assert sleep.call_count == 2
    sleep.assert_called_with(0.5)


def test_query_asset_upload_with_retry_exhausts():
    client = MagicMock()

    with (
        patch("auth.query_asset_upload", return_value=("up-1", False, "")) as query,
        patch("time.sleep") as sleep,
    ):
        result = query_asset_upload_with_retry(
            client, "up-1", max_retries=3, retry_delay_seconds=1.0
        )

    assert result == ("up-1", False, "")
    assert query.call_count == 3
    assert sleep.call_count == 2


def test_submit_asset_streams_file():
    client = MagicMock()
    submit = MagicMock()
    submit.upload_url = "https://upload.example/put"
    submit.upload_id = "upload-42"
    client.graphql.return_value.__enter__.return_value.mutation_asset_submit.return_value = (
        MagicMock(asset=MagicMock(submit=submit))
    )

    file_handle = MagicMock()
    http_response = MagicMock()
    http_client = MagicMock()
    http_client.put.return_value = http_response
    http_client_cm = MagicMock()
    http_client_cm.__enter__.return_value = http_client

    with (
        patch("auth.SubmitAssetInput") as submit_input_cls,
        patch("auth.httpx.Client", return_value=http_client_cm),
        patch("builtins.open", mock_open(read_data=b"payload")) as opened,
    ):
        # Ensure open returns our file handle for streaming assertion
        opened.return_value = file_handle
        file_handle.__enter__.return_value = file_handle

        upload_id = submit_asset(
            client,
            "/tmp/artifact.bin",
            "name",
            manufacturer="Acme",
            model="M1",
            version="1.0",
        )

    assert upload_id == "upload-42"
    submit_input_cls.assert_called_once()
    http_client.put.assert_called_once()
    put_kwargs = http_client.put.call_args
    assert put_kwargs.args[0] == "https://upload.example/put"
    assert put_kwargs.kwargs["content"] is file_handle
    assert put_kwargs.kwargs["headers"] == {"Content-Type": "application/octet-stream"}
    assert put_kwargs.kwargs["timeout"] == 300.0
    http_response.raise_for_status.assert_called_once()
