#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

DOCUMENTATION = r"""
---
module: database_instance
short_description: Create a Magalu Cloud DBaaS database instance
version_added: 1.0.0
description:
  - Sends one request to the Magalu Cloud DBaaS API to create a database instance.
  - The API creates the instance asynchronously. The module returns as soon as the API accepts the request and does not wait
    for the instance to become ready.
  - This module is B(not idempotent). Every run outside check mode creates a new instance, even when an instance with the
    same O(name) already exists.
author:
  - Dennis Urtubia (@dennisurtubia)
options:
  api_key:
    description:
      - Magalu Cloud API key, sent in the C(x-api-key) header.
      - The key needs permission to create database resources.
      - If not set, the value of the E(MAGALU_CLOUD_API_KEY) environment variable is used. This variable name is a convention
        of this collection, not of Magalu Cloud.
    type: str
    required: true
  region:
    description:
      - Magalu Cloud region where the instance is created. It selects the API endpoint
        C(https://api.magalu.cloud/<region>/database).
    type: str
    required: true
    choices: [br-se1, br-ne1]
  name:
    description:
      - Name of the instance. The API accepts at most 100 characters.
    type: str
    required: true
  engine_id:
    description:
      - ID (UUID) of the database engine. The DBaaS API lists the available engines at C(GET /v2/engines).
    type: str
    required: true
  instance_type_id:
    description:
      - ID (UUID) of the instance type, which sets vCPU and RAM. The DBaaS API lists the available types at
        C(GET /v2/instance-types).
    type: str
    required: true
  user:
    description:
      - Name of the database administrator user. The API accepts at most 25 characters.
    type: str
    required: true
  password:
    description:
      - Password of the database administrator user. The API accepts at most 50 characters.
    type: str
    required: true
  volume:
    description:
      - Storage volume of the instance.
    type: dict
    required: true
    suboptions:
      size:
        description:
          - Volume size in GiB. The API accepts values from 10 to 50000.
        type: int
        required: true
      type:
        description:
          - Volume type. The API documents C(CLOUD_NVME15K), C(CLOUD_NVME20K), C(CLOUD_NVME30K), C(CLOUD_NVME40K), and
            C(CLOUD_NVME50K).
          - The API documents C(CLOUD_NVME30K), C(CLOUD_NVME40K), and C(CLOUD_NVME50K) as preview types that require tenant
            permission.
          - If not set, the API default (C(CLOUD_NVME15K)) applies.
        type: str
  deletion_protected:
    description:
      - Whether the instance is protected against deletion.
      - If not set, the API default (V(false)) applies.
    type: bool
  security_groups:
    description:
      - IDs (UUIDs) of security groups from the Magalu Cloud Network API that control access to the instance.
    type: list
    elements: str
  parameter_group_id:
    description:
      - ID (UUID) of the parameter group to apply to the instance.
    type: str
  backup_retention_days:
    description:
      - Number of days each automated backup is kept.
      - If not set, the API default (V(7)) applies.
    type: int
  backup_start_at:
    description:
      - Time of day, in UTC and C(HH:MM:SS) format, from which the automated backup process may start.
      - If not set, the API default (V(04:00:00)) applies.
    type: str
  availability_zone:
    description:
      - Availability zone of the instance. The API documents C(br-se1-a), C(br-se1-b), C(br-se1-c), C(br-ne1-a), and
        C(br-ne1-b).
    type: str
  timeout:
    description:
      - Number of seconds to wait for the API to respond to the create request.
    type: int
    default: 30
notes:
  - Supports check mode. In check mode the module sends no request and reports a change, because every real run creates an
    instance.
  - The module sends at most one request per run and never retries it. If the connection fails or times out, the instance may
    still have been created. Check the Magalu Cloud console or the API before running the task again.
  - The module does not check whether an instance with the same name already exists. The DBaaS API documents no idempotency
    mechanism and no name uniqueness.
  - The DBaaS API reference lists the northeast server as C(br-ne-1), while the Magalu Cloud API authentication guide uses
    C(br-ne1). The module follows the authentication guide.
seealso:
  - name: DBaaS API reference
    description: Official Magalu Cloud DBaaS API documentation, including the create instance operation.
    link: https://docs.magalu.cloud/api/database
  - name: Magalu Cloud API authentication
    description: How to authenticate to Magalu Cloud APIs with an API key.
    link: https://docs.magalu.cloud/docs/devops-tools/apis/auth
"""

EXAMPLES = r"""
# This module is not idempotent: every run creates a new instance.
# Run it once and keep the returned ID instead of running it on every play.
- name: Create a database instance
  dennisurtubia.magalu_cloud.database_instance:
    region: br-se1
    name: my-db-instance
    engine_id: b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0
    instance_type_id: b67afca2-5b6f-43dd-b5de-7627dae240c8
    user: admin
    password: "{{ db_admin_password }}"
    volume:
      size: 30
  register: db_instance

- name: Show the ID of the new instance
  ansible.builtin.debug:
    msg: "{{ db_instance.instance.id }}"
  when: db_instance is changed and not ansible_check_mode

- name: Create a database instance with every optional setting
  dennisurtubia.magalu_cloud.database_instance:
    api_key: "{{ magalu_cloud_api_key }}"
    region: br-ne1
    name: my-db-instance
    engine_id: b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0
    instance_type_id: b67afca2-5b6f-43dd-b5de-7627dae240c8
    user: admin
    password: "{{ db_admin_password }}"
    volume:
      size: 50
      type: CLOUD_NVME20K
    deletion_protected: true
    security_groups:
      - 497f6eca-6276-4993-bfeb-53cbbbba6f08
    parameter_group_id: 60517f0f-1194-4a4f-8234-33197a1e7381
    backup_retention_days: 14
    backup_start_at: "03:00:00"
    availability_zone: br-ne1-a
"""

RETURN = r"""
instance:
  description: The instance the API accepted for creation.
  returned: success, except in check mode
  type: dict
  contains:
    id:
      description: ID (UUID) of the new instance.
      returned: always
      type: str
      sample: 497f6eca-6276-4993-bfeb-53cbbbba6f08
status:
  description: HTTP status code of the API response.
  returned: when the API responds with an error or an unexpected status
  type: int
  sample: 422
error:
  description: Error returned by the API.
  returned: when the API responds with an error and a JSON body
  type: dict
  contains:
    slug:
      description: Short error identifier.
      returned: always
      type: str
      sample: unprocessable_entity
    message:
      description: Error message.
      returned: always
      type: str
      sample: Unprocessable entity
    details:
      description: Additional error details.
      returned: when provided by the API
      type: dict
body:
  description: Raw response body, when the API responds with an error that is not JSON.
  returned: when the API responds with an error and a body that is not JSON
  type: str
"""

import json

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import fetch_url

# Contract: POST /v2/instances in the DBaaS API spec 2.33.3, https://docs.magalu.cloud/redocusaurus/dbaas-openapi.yaml
# Authentication with the x-api-key header: https://docs.magalu.cloud/docs/devops-tools/apis/auth
API_URL = "https://api.magalu.cloud/{region}/database/v2/instances"

# Options sent to the API as fields of the request body, under the same names.
BODY_OPTIONS = (
    "name",
    "engine_id",
    "instance_type_id",
    "user",
    "password",
    "volume",
    "deletion_protected",
    "security_groups",
    "parameter_group_id",
    "backup_retention_days",
    "backup_start_at",
    "availability_zone",
)

MAY_HAVE_BEEN_CREATED = (
    "An instance may have been created. Check the Magalu Cloud console or the API before running this task again."
)


class DatabaseInstance:
    """Creates a DBaaS instance with a single request to the Magalu Cloud API."""

    def __init__(self, module):
        self.module = module

    @classmethod
    def define_module(cls):
        return AnsibleModule(
            argument_spec=dict(
                api_key=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["MAGALU_CLOUD_API_KEY"])),
                region=dict(type="str", required=True, choices=["br-se1", "br-ne1"]),
                name=dict(type="str", required=True),
                engine_id=dict(type="str", required=True),
                instance_type_id=dict(type="str", required=True),
                user=dict(type="str", required=True),
                password=dict(type="str", required=True, no_log=True),
                volume=dict(
                    type="dict",
                    required=True,
                    options=dict(
                        size=dict(type="int", required=True),
                        type=dict(type="str"),
                    ),
                ),
                deletion_protected=dict(type="bool"),
                security_groups=dict(type="list", elements="str"),
                parameter_group_id=dict(type="str"),
                backup_retention_days=dict(type="int"),
                backup_start_at=dict(type="str"),
                availability_zone=dict(type="str"),
                timeout=dict(type="int", default=30),
            ),
            supports_check_mode=True,
        )

    def create(self):
        if self.module.check_mode:
            return dict(changed=True)
        response, info = self._request(self._build_body())
        return self._handle_response(response, info)

    def _build_body(self):
        params = self.module.params
        # Unset options are left out so the API applies its own defaults.
        body = {key: params[key] for key in BODY_OPTIONS if params[key] is not None}
        body["volume"] = {key: value for key, value in params["volume"].items() if value is not None}
        return body

    def _request(self, body):
        return fetch_url(
            self.module,
            API_URL.format(region=self.module.params["region"]),
            data=json.dumps(body),
            headers={
                "x-api-key": self.module.params["api_key"],
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
            timeout=self.module.params["timeout"],
            # Keep the API key off any redirected request.
            unredirected_headers=["x-api-key"],
        )

    def _handle_response(self, response, info):
        status = info["status"]

        # No HTTP response: the request may still have reached the API, so it is never re-sent.
        if status == -1:
            self.module.fail_json(
                msg="Failed to create database instance: {0}. {1}".format(info.get("msg"), MAY_HAVE_BEEN_CREATED),
                changed=False,
            )

        if status >= 400:
            self._fail_with_api_error(status, to_text(info.get("body") or b"", errors="surrogate_or_replace"))

        if status != 202:
            self.module.fail_json(
                msg="Unexpected HTTP status {0} from the DBaaS API. {1}".format(status, MAY_HAVE_BEEN_CREATED),
                changed=False,
                status=status,
            )

        instance = self._parse_json(to_text(response.read(), errors="surrogate_or_replace"))
        if not isinstance(instance, dict) or not instance.get("id"):
            self.module.fail_json(
                msg="The API accepted the creation request but its response has no instance ID. {0}".format(MAY_HAVE_BEEN_CREATED),
                changed=True,
            )

        return dict(changed=True, instance=dict(id=instance["id"]))

    def _fail_with_api_error(self, status, raw):
        error = self._parse_json(raw)
        if isinstance(error, dict):
            message = error.get("message")
            detail = ": {0}".format(message) if message else ""
            self.module.fail_json(
                msg="Failed to create database instance: HTTP {0}{1}".format(status, detail),
                changed=False,
                status=status,
                error=error,
            )
        self.module.fail_json(msg="Failed to create database instance: HTTP {0}".format(status), changed=False, status=status, body=raw)

    @staticmethod
    def _parse_json(raw):
        try:
            return json.loads(raw)
        except ValueError:
            return None


def main():
    module = DatabaseInstance.define_module()
    result = DatabaseInstance(module).create()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
