# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

"""Shared HTTP access to the Magalu Cloud DBaaS API."""

from __future__ import annotations

import json
from urllib.parse import urlencode

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import fetch_url

# Contract: DBaaS API spec 2.33.3, https://docs.magalu.cloud/redocusaurus/dbaas-openapi.yaml
# Authentication with the x-api-key header: https://docs.magalu.cloud/docs/devops-tools/apis/auth
API_URL = "https://api.magalu.cloud/{region}/database/v2{path}"


def argument_spec():
    """Options shared by every DBaaS module, documented in the dennisurtubia.magalu_cloud.database doc fragment."""
    return dict(
        api_key=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["MAGALU_CLOUD_API_KEY"])),
        region=dict(type="str", required=True, choices=["br-se1", "br-ne1"]),
        timeout=dict(type="int", default=30),
    )


def request(module, path, method="GET", query=None, body=None):
    """Send one request to the DBaaS API and return the (response, info) pair of fetch_url."""
    url = API_URL.format(region=module.params["region"], path=path)
    if query:
        url = "{0}?{1}".format(url, urlencode(query))
    headers = {"x-api-key": module.params["api_key"], "Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body)
    return fetch_url(
        module,
        url,
        data=data,
        headers=headers,
        method=method,
        timeout=module.params["timeout"],
        # Keep the API key off any redirected request.
        unredirected_headers=["x-api-key"],
    )


def parse_json(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def fail_with_api_error(module, action, info):
    """Fail the module with the error the API returned for an HTTP status of 400 or above."""
    status = info["status"]
    raw = to_text(info.get("body") or b"", errors="surrogate_or_replace")
    error = parse_json(raw)
    if isinstance(error, dict):
        message = error.get("message")
        detail = ": {0}".format(message) if message else ""
        module.fail_json(msg="Failed to {0}: HTTP {1}{2}".format(action, status, detail), changed=False, status=status, error=error)
    module.fail_json(msg="Failed to {0}: HTTP {1}".format(action, status), changed=False, status=status, body=raw)
