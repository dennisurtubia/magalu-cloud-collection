# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from unittest.mock import MagicMock
from urllib.parse import parse_qsl, urlsplit

import pytest

from ansible.module_utils.testing import patch_module_args
from ansible_collections.dennisurtubia.magalu_cloud.plugins.module_utils import database
from ansible_collections.dennisurtubia.magalu_cloud.plugins.modules import database_instance_info

API_KEY = "test-api-key-0a1b2c3d"
INSTANCE_ID = "497f6eca-6276-4993-bfeb-53cbbbba6f08"
LIST_URL = "https://api.magalu.cloud/br-se1/database/v2/instances"
GET_URL = "{0}/{1}".format(LIST_URL, INSTANCE_ID)

REQUIRED_ARGS = {"api_key": API_KEY, "region": "br-se1"}

# Response example of GET /v2/instances/{instance_id} from the DBaaS API spec.
INSTANCE = {
    "id": INSTANCE_ID,
    "name": "my-db-instance",
    "engine_id": "b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0",
    "parameter_group_id": "60517f0f-1194-4a4f-8234-33197a1e7381",
    "port_id": "2b97437e-648a-4484-9174-d069ca9706be",
    "apply_parameters_pending": True,
    "deletion_protected": True,
    "instance_type_id": "b67afca2-5b6f-43dd-b5de-7627dae240c8",
    "volume": {"size": 30, "type": "CLOUD_HDD", "encrypted": True},
    "addresses": [{"access": "PRIVATE", "type": "IPv4", "address": "172.53.10.82"}],
    "status": "ACTIVE",
    "availability_zone": "br-ne1-a",
    "generation": "G10",
    "backup_retention_days": 7,
    "backup_start_at": "04:00:00",
    "created_at": "2019-08-24T14:15:22Z",
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
    return mocker.patch.object(database, "fetch_url")


def http_response(status, body):
    """Build the (response, info) pair that fetch_url returns."""
    if isinstance(body, (dict, list)):
        body = json.dumps(body).encode()
    if status >= 400:
        return None, {"status": status, "msg": "HTTP Error {0}".format(status), "body": body}
    response = MagicMock()
    response.read.return_value = body
    return response, {"status": status, "msg": "OK"}


def instance(number):
    return dict(INSTANCE, id="00000000-0000-0000-0000-{0:012d}".format(number), name="db-{0}".format(number))


def list_page(results, total, offset=0):
    page = {"offset": offset, "limit": 25, "count": len(results), "total": total, "max_limit": 25}
    return http_response(200, {"meta": {"filters": [], "page": page}, "results": results})


def run_module(capsys, args):
    with patch_module_args(args):
        with pytest.raises(SystemExit):
            database_instance_info.main()
    output = capsys.readouterr().out
    assert API_KEY not in output
    return json.loads(output)


def requested(call):
    """Split the URL of a fetch_url call into its base and its query parameters."""
    url = urlsplit(call[0][1])
    return "{0}://{1}{2}".format(url.scheme, url.netloc, url.path), dict(parse_qsl(url.query))


def test_list_returns_instances(capsys, fetch_url):
    fetch_url.return_value = list_page([INSTANCE], total=1)

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["changed"] is False
    assert result["instances"] == [INSTANCE]
    assert "failed" not in result
    fetch_url.assert_called_once()
    assert requested(fetch_url.call_args) == (LIST_URL, {"_limit": "25", "_offset": "0"})
    kwargs = fetch_url.call_args[1]
    assert kwargs["method"] == "GET"
    assert kwargs["data"] is None
    assert kwargs["headers"] == {"x-api-key": API_KEY, "Accept": "application/json"}
    assert kwargs["unredirected_headers"] == ["x-api-key"]
    assert kwargs["timeout"] == 30


def test_list_reads_every_page(capsys, fetch_url):
    first = [instance(number) for number in range(25)]
    second = [instance(number) for number in range(25, 30)]
    fetch_url.side_effect = [list_page(first, total=30), list_page(second, total=30, offset=25)]

    result = run_module(capsys, dict(REQUIRED_ARGS, timeout=60))

    assert result["instances"] == first + second
    assert fetch_url.call_count == 2
    assert [requested(call)[1]["_offset"] for call in fetch_url.call_args_list] == ["0", "25"]
    assert all(call[1]["timeout"] == 60 for call in fetch_url.call_args_list)


def test_list_without_instances(capsys, fetch_url):
    fetch_url.return_value = list_page([], total=0)

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["changed"] is False
    assert result["instances"] == []
    fetch_url.assert_called_once()


def test_list_stops_at_an_empty_page(capsys, fetch_url):
    first = [instance(number) for number in range(25)]
    fetch_url.side_effect = [list_page(first, total=30), list_page([], total=30, offset=25)]

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["instances"] == first
    assert fetch_url.call_count == 2


def test_filters_are_sent_as_query_parameters(capsys, fetch_url):
    fetch_url.return_value = list_page([], total=0)
    filters = {
        "status": "ACTIVE",
        "engine_id": "b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0",
        "parameter_group_id": "60517f0f-1194-4a4f-8234-33197a1e7381",
        "deletion_protected": False,
    }

    run_module(capsys, dict(REQUIRED_ARGS, **filters))

    assert requested(fetch_url.call_args)[1] == dict(filters, deletion_protected="false", _limit="25", _offset="0")


def test_filters_are_kept_on_every_page(capsys, fetch_url):
    first = [instance(number) for number in range(25)]
    fetch_url.side_effect = [list_page(first, total=26), list_page([instance(25)], total=26, offset=25)]

    run_module(capsys, dict(REQUIRED_ARGS, deletion_protected=True, include_replicas=True))

    queries = [requested(call)[1] for call in fetch_url.call_args_list]
    assert queries == [
        {"deletion_protected": "true", "_expand": "replicas", "_limit": "25", "_offset": "0"},
        {"deletion_protected": "true", "_expand": "replicas", "_limit": "25", "_offset": "25"},
    ]


def test_list_includes_replicas(capsys, fetch_url):
    fetch_url.return_value = list_page([], total=0)

    run_module(capsys, dict(REQUIRED_ARGS, include_replicas=True))

    assert requested(fetch_url.call_args)[1] == {"_expand": "replicas", "_limit": "25", "_offset": "0"}


def test_get_returns_instance(capsys, fetch_url):
    fetch_url.return_value = http_response(200, INSTANCE)

    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID))

    assert result["changed"] is False
    assert result["instances"] == [INSTANCE]
    fetch_url.assert_called_once()
    assert requested(fetch_url.call_args) == (GET_URL, {})
    kwargs = fetch_url.call_args[1]
    assert kwargs["method"] == "GET"
    assert kwargs["headers"] == {"x-api-key": API_KEY, "Accept": "application/json"}
    assert kwargs["unredirected_headers"] == ["x-api-key"]


def test_get_includes_replicas(capsys, fetch_url):
    replica = {"id": "6c3b4d8e-1f2a-4b5c-9d0e-7f8a9b0c1d2e", "source_id": INSTANCE_ID, "status": "ACTIVE"}
    fetch_url.return_value = http_response(200, dict(INSTANCE, replicas=[replica]))

    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID, include_replicas=True))

    assert result["instances"][0]["replicas"] == [replica]
    assert requested(fetch_url.call_args) == (GET_URL, {"_expand": "replicas"})


def test_get_quotes_the_id(capsys, fetch_url):
    fetch_url.return_value = http_response(404, {"slug": "not_found", "message": "Not Found"})

    run_module(capsys, dict(REQUIRED_ARGS, id="../engines?x=1"))

    assert fetch_url.call_args[0][1] == LIST_URL + "/..%2Fengines%3Fx%3D1"


def test_get_missing_instance_returns_empty_list(capsys, fetch_url):
    fetch_url.return_value = http_response(404, {"slug": "not_found", "message": "Not Found"})

    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID))

    assert result["changed"] is False
    assert result["instances"] == []
    assert "failed" not in result


def test_list_not_found_is_an_error(capsys, fetch_url):
    fetch_url.return_value = http_response(404, {"slug": "not_found", "message": "Not Found"})

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["status"] == 404
    assert result["msg"] == "Failed to list database instances: HTTP 404: Not Found"


@pytest.mark.parametrize("option, value", [("status", "ACTIVE"), ("engine_id", INSTANCE_ID), ("parameter_group_id", INSTANCE_ID), ("deletion_protected", True)])
def test_id_excludes_filters(capsys, fetch_url, option, value):
    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID, **{option: value}))

    assert result["failed"] is True
    assert "mutually exclusive" in result["msg"]
    assert option in result["msg"]
    fetch_url.assert_not_called()


@pytest.mark.parametrize("status", sorted(API_ERRORS))
def test_list_api_error_is_reported(capsys, fetch_url, status):
    fetch_url.return_value = http_response(status, API_ERRORS[status])

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is False
    assert result["status"] == status
    assert result["error"] == API_ERRORS[status]
    assert result["msg"] == "Failed to list database instances: HTTP {0}: {1}".format(status, API_ERRORS[status]["message"])
    assert "instances" not in result
    fetch_url.assert_called_once()


@pytest.mark.parametrize("status", sorted(API_ERRORS))
def test_get_api_error_is_reported(capsys, fetch_url, status):
    fetch_url.return_value = http_response(status, API_ERRORS[status])

    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID))

    assert result["failed"] is True
    assert result["changed"] is False
    assert result["status"] == status
    assert result["error"] == API_ERRORS[status]
    assert result["msg"] == "Failed to get database instance: HTTP {0}: {1}".format(status, API_ERRORS[status]["message"])
    assert "instances" not in result


def test_api_error_on_a_later_page(capsys, fetch_url):
    first = [instance(number) for number in range(25)]
    fetch_url.side_effect = [list_page(first, total=30), http_response(500, API_ERRORS[500])]

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["status"] == 500
    assert "instances" not in result


def test_api_error_without_json_body(capsys, fetch_url):
    fetch_url.return_value = http_response(502, b"<html>Bad Gateway</html>")

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["status"] == 502
    assert result["body"] == "<html>Bad Gateway</html>"
    assert "error" not in result
    assert result["msg"] == "Failed to list database instances: HTTP 502"


def test_api_key_echoed_by_the_api_is_masked(capsys, fetch_url):
    error = {"slug": "unauthorized", "message": "Access unauthorized", "details": {"key": API_KEY}}
    fetch_url.return_value = http_response(401, error)

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["error"]["slug"] == "unauthorized"


@pytest.mark.parametrize("args", [REQUIRED_ARGS, dict(REQUIRED_ARGS, id=INSTANCE_ID)])
def test_connection_failure_is_not_retried(capsys, fetch_url, args):
    fetch_url.return_value = (None, {"status": -1, "msg": "Connection failure: timed out"})

    result = run_module(capsys, args)

    assert result["failed"] is True
    assert result["changed"] is False
    assert "Connection failure: timed out" in result["msg"]
    fetch_url.assert_called_once()


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b'["unexpected"]',
        b"{}",
        b'{"meta": {"page": {"total": 1}}}',
        b'{"meta": {"page": {"total": 1}}, "results": {}}',
        b'{"meta": {"page": {"total": 1}}, "results": ["unexpected"]}',
        b'{"results": []}',
        b'{"meta": {}, "results": []}',
        b'{"meta": {"page": {"total": "1"}}, "results": []}',
        b'{"meta": {"page": {"total": null}}, "results": []}',
    ],
)
def test_malformed_list_response(capsys, fetch_url, body):
    fetch_url.return_value = http_response(200, body)

    result = run_module(capsys, REQUIRED_ARGS)

    assert result["failed"] is True
    assert result["changed"] is False
    assert "malformed" in result["msg"]
    assert "instances" not in result


@pytest.mark.parametrize("body", [b"not json", b"{}", b'{"id": ""}', b'["unexpected"]'])
def test_malformed_get_response(capsys, fetch_url, body):
    fetch_url.return_value = http_response(200, body)

    result = run_module(capsys, dict(REQUIRED_ARGS, id=INSTANCE_ID))

    assert result["failed"] is True
    assert result["changed"] is False
    assert "no instance ID" in result["msg"]
    assert "instances" not in result


@pytest.mark.parametrize("args", [REQUIRED_ARGS, dict(REQUIRED_ARGS, id=INSTANCE_ID)])
@pytest.mark.parametrize("status", [201, 202, 204])
def test_undocumented_success_status(capsys, fetch_url, args, status):
    fetch_url.return_value = http_response(status, INSTANCE)

    result = run_module(capsys, args)

    assert result["failed"] is True
    assert result["changed"] is False
    assert result["status"] == status
    assert "instances" not in result


def test_region_selects_endpoint(capsys, fetch_url):
    fetch_url.return_value = list_page([], total=0)

    run_module(capsys, dict(REQUIRED_ARGS, region="br-ne1"))

    assert requested(fetch_url.call_args)[0] == "https://api.magalu.cloud/br-ne1/database/v2/instances"


def test_invalid_region(capsys, fetch_url):
    result = run_module(capsys, dict(REQUIRED_ARGS, region="br-ne-1"))

    assert result["failed"] is True
    assert "region" in result["msg"]
    fetch_url.assert_not_called()


def test_check_mode_reads_instances(capsys, fetch_url):
    fetch_url.return_value = list_page([INSTANCE], total=1)

    result = run_module(capsys, dict(REQUIRED_ARGS, _ansible_check_mode=True))

    assert result["changed"] is False
    assert result["instances"] == [INSTANCE]
    fetch_url.assert_called_once()


def test_api_key_from_environment(capsys, fetch_url, monkeypatch):
    monkeypatch.setenv("MAGALU_CLOUD_API_KEY", API_KEY)
    fetch_url.return_value = list_page([], total=0)

    result = run_module(capsys, {"region": "br-se1"})

    assert result["instances"] == []
    assert fetch_url.call_args[1]["headers"]["x-api-key"] == API_KEY


def test_missing_api_key(capsys, fetch_url, monkeypatch):
    monkeypatch.delenv("MAGALU_CLOUD_API_KEY", raising=False)

    result = run_module(capsys, {"region": "br-se1"})

    assert result["failed"] is True
    assert "api_key" in result["msg"]
    fetch_url.assert_not_called()
