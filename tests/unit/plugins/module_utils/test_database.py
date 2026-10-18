# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from ansible_collections.dennisurtubia.magalu_cloud.plugins.module_utils import database

PARAMS = {"api_key": "test-api-key-0a1b2c3d", "region": "br-se1", "timeout": 30}


@pytest.fixture
def module():
    return MagicMock(params=dict(PARAMS))


@pytest.fixture
def fetch_url(mocker):
    return mocker.patch.object(database, "fetch_url", return_value=(None, {"status": 200}))


def test_get_request_has_no_body(module, fetch_url):
    database.request(module, "/instances")

    fetch_url.assert_called_once_with(
        module,
        "https://api.magalu.cloud/br-se1/database/v2/instances",
        data=None,
        headers={"x-api-key": PARAMS["api_key"], "Accept": "application/json"},
        method="GET",
        timeout=30,
        unredirected_headers=["x-api-key"],
    )


def test_request_with_body_is_json(module, fetch_url):
    database.request(module, "/instances", method="POST", body={"name": "db"})

    kwargs = fetch_url.call_args[1]
    assert kwargs["method"] == "POST"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert json.loads(kwargs["data"]) == {"name": "db"}


def test_query_is_encoded(module, fetch_url):
    database.request(module, "/instances", query={"status": "ACTIVE", "volume.size": 10, "x": "a b&c"})

    assert fetch_url.call_args[0][1] == "https://api.magalu.cloud/br-se1/database/v2/instances?status=ACTIVE&volume.size=10&x=a+b%26c"


def test_empty_query_is_left_out(module, fetch_url):
    database.request(module, "/instances", query={})

    assert fetch_url.call_args[0][1] == "https://api.magalu.cloud/br-se1/database/v2/instances"


@pytest.mark.parametrize("raw, expected", [('{"id": "1"}', {"id": "1"}), ("[]", []), ("not json", None), ("", None)])
def test_parse_json(raw, expected):
    assert database.parse_json(raw) == expected
