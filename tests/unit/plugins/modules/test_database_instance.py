# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from ansible.module_utils.testing import patch_module_args
from ansible_collections.dennisurtubia.magalu_cloud.plugins.modules import database_instance

API_KEY = "test-api-key-0a1b2c3d"
PASSWORD = "test-password-4e5f6a7b"
INSTANCE_ID = "497f6eca-6276-4993-bfeb-53cbbbba6f08"

REQUIRED_ARGS = {
    "api_key": API_KEY,
    "region": "br-se1",
    "name": "my-db-instance",
    "engine_id": "b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0",
    "instance_type_id": "b67afca2-5b6f-43dd-b5de-7627dae240c8",
    "user": "admin",
    "password": PASSWORD,
    "volume": {"size": 30},
}

REQUIRED_BODY = {
    "name": "my-db-instance",
    "engine_id": "b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0",
    "instance_type_id": "b67afca2-5b6f-43dd-b5de-7627dae240c8",
    "user": "admin",
    "password": PASSWORD,
    "volume": {"size": 30},
}

# Error examples from the DBaaS API spec (components.responses).
API_ERRORS = {
    400: {"slug": "bad_request", "message": "Bad request"},
    401: {"slug": "unauthorized", "message": "Access unauthorized"},
    403: {"slug": "forbidden", "message": "Access Forbidden"},
    422: {"slug": "unprocessable_entity", "message": "Unprocessable entity"},
    500: {"slug": "internal_server_error", "message": "Internal server error"},
}


@pytest.fixture
def fetch_url(mocker):
    return mocker.patch.object(database_instance, "fetch_url")


def http_response(status, body):
    """Build the (response, info) pair that fetch_url returns."""
    if status >= 400:
        return None, {"status": status, "msg": "HTTP Error {0}".format(status), "body": body}
    response = MagicMock()
    response.read.return_value = body
    return response, {"status": status, "msg": "OK"}


def run_module(capsys, args):
    with patch_module_args(args):
        with pytest.raises(SystemExit):
            database_instance.main()
    output = capsys.readouterr().out
    assert API_KEY not in output
    assert PASSWORD not in output
    return json.loads(output)


def test_create_returns_instance_id(capsys, fetch_url):
    fetch_url.return_value = http_response(202, json.dumps({"id": INSTANCE_ID}).encode())

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["changed"] is True
    assert result["instance"] == {"id": INSTANCE_ID}
    assert "failed" not in result
    fetch_url.assert_called_once()
    args, kwargs = fetch_url.call_args
    assert args[1] == "https://api.magalu.cloud/br-se1/database/v2/instances"
    assert kwargs["method"] == "POST"
    assert kwargs["headers"] == {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    assert kwargs["unredirected_headers"] == ["x-api-key"]
    assert kwargs["timeout"] == 30
    assert json.loads(kwargs["data"]) == REQUIRED_BODY


def test_region_selects_endpoint(capsys, fetch_url):
    fetch_url.return_value = http_response(202, json.dumps({"id": INSTANCE_ID}).encode())

    run_module(capsys, dict(REQUIRED_ARGS, region="br-ne1"))

    assert fetch_url.call_args[0][1] == "https://api.magalu.cloud/br-ne1/database/v2/instances"


def test_all_options_are_sent(capsys, fetch_url):
    fetch_url.return_value = http_response(202, json.dumps({"id": INSTANCE_ID}).encode())
    optional = {
        "volume": {"size": 50, "type": "CLOUD_NVME20K"},
        "deletion_protected": True,
        "security_groups": ["497f6eca-6276-4993-bfeb-53cbbbba6f08"],
        "parameter_group_id": "60517f0f-1194-4a4f-8234-33197a1e7381",
        "backup_retention_days": 14,
        "backup_start_at": "03:00:00",
        "availability_zone": "br-se1-a",
    }

    run_module(capsys, dict(REQUIRED_ARGS, timeout=60, **optional))

    kwargs = fetch_url.call_args[1]
    assert json.loads(kwargs["data"]) == dict(REQUIRED_BODY, **optional)
    assert kwargs["timeout"] == 60


def test_check_mode_sends_no_request(capsys, fetch_url):
    result = run_module(capsys, dict(REQUIRED_ARGS, _ansible_check_mode=True))

    assert result["changed"] is True
    assert "instance" not in result
    fetch_url.assert_not_called()


@pytest.mark.parametrize("status", sorted(API_ERRORS))
def test_api_error_is_reported(capsys, fetch_url, status):
    fetch_url.return_value = http_response(status, json.dumps(API_ERRORS[status]).encode())

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is False
    assert result["status"] == status
    assert result["error"] == API_ERRORS[status]
    assert result["msg"] == "Failed to create database instance: HTTP {0}: {1}".format(status, API_ERRORS[status]["message"])
    fetch_url.assert_called_once()


def test_api_error_without_json_body(capsys, fetch_url):
    fetch_url.return_value = http_response(502, b"<html>Bad Gateway</html>")

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["status"] == 502
    assert result["body"] == "<html>Bad Gateway</html>"
    assert "error" not in result
    assert result["msg"] == "Failed to create database instance: HTTP 502"


def test_secrets_echoed_by_the_api_are_masked(capsys, fetch_url):
    error = {"slug": "unprocessable_entity", "message": "Unprocessable entity", "details": {"password": PASSWORD, "key": API_KEY}}
    fetch_url.return_value = http_response(422, json.dumps(error).encode())

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["error"]["slug"] == "unprocessable_entity"


def test_connection_failure_is_not_retried(capsys, fetch_url):
    fetch_url.return_value = (None, {"status": -1, "msg": "Connection failure: timed out"})

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is False
    assert "Connection failure: timed out" in result["msg"]
    assert "may have been created" in result["msg"]
    fetch_url.assert_called_once()


@pytest.mark.parametrize("body", [b"not json", b"{}", b'{"id": ""}', b'["unexpected"]'])
def test_accepted_without_instance_id(capsys, fetch_url, body):
    fetch_url.return_value = http_response(202, body)

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is True
    assert "no instance ID" in result["msg"]
    assert "may have been created" in result["msg"]
    assert "instance" not in result


@pytest.mark.parametrize("status", [200, 201, 204])
def test_undocumented_success_status(capsys, fetch_url, status):
    fetch_url.return_value = http_response(status, json.dumps({"id": INSTANCE_ID}).encode())

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is False
    assert result["status"] == status
    assert "may have been created" in result["msg"]
    assert "instance" not in result


@pytest.mark.parametrize("missing", ["name", "engine_id", "instance_type_id", "user", "password", "volume"])
def test_missing_required_option(capsys, fetch_url, missing):
    args = {key: value for key, value in REQUIRED_ARGS.items() if key != missing}

    result = run_module(capsys, args)

    assert result["failed"] is True
    assert missing in result["msg"]
    fetch_url.assert_not_called()


def test_missing_volume_size(capsys, fetch_url):
    result = run_module(capsys, dict(REQUIRED_ARGS, volume={"type": "CLOUD_NVME15K"}))

    assert result["failed"] is True
    assert "size" in result["msg"]
    fetch_url.assert_not_called()


def test_invalid_region(capsys, fetch_url):
    result = run_module(capsys, dict(REQUIRED_ARGS, region="br-ne-1"))

    assert result["failed"] is True
    assert "region" in result["msg"]
    fetch_url.assert_not_called()


def test_api_key_from_environment(capsys, fetch_url, monkeypatch):
    monkeypatch.setenv("MAGALU_CLOUD_API_KEY", API_KEY)
    fetch_url.return_value = http_response(202, json.dumps({"id": INSTANCE_ID}).encode())
    args = {key: value for key, value in REQUIRED_ARGS.items() if key != "api_key"}

    result = run_module(capsys, args)

    assert result["changed"] is True
    assert fetch_url.call_args[1]["headers"]["x-api-key"] == API_KEY


def test_missing_api_key(capsys, fetch_url, monkeypatch):
    monkeypatch.delenv("MAGALU_CLOUD_API_KEY", raising=False)
    args = {key: value for key, value in REQUIRED_ARGS.items() if key != "api_key"}

    result = run_module(capsys, args)

    assert result["failed"] is True
    assert "api_key" in result["msg"]
    fetch_url.assert_not_called()
