#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

DOCUMENTATION = r"""
---
module: database_instance_info
short_description: Gather information about Magalu Cloud DBaaS database instances
version_added: 1.0.0
description:
  - Gathers information about Magalu Cloud DBaaS database instances in a region.
  - With O(id), returns the instance with that ID. Without O(id), lists every instance that matches the given filters,
    requesting all pages of results from the API.
  - This module is read-only and never changes any resource.
author:
  - Dennis Urtubia (@dennisurtubia)
extends_documentation_fragment:
  - dennisurtubia.magalu_cloud.database
options:
  id:
    description:
      - ID (UUID) of the instance to return.
      - Mutually exclusive with O(status), O(engine_id), O(parameter_group_id), and O(deletion_protected).
    type: str
  status:
    description:
      - Return only instances in this status.
      - The API documents C(CREATING), C(ERROR), C(STOPPED), C(REBOOT), C(PENDING), C(RESIZING), C(DELETED), C(ACTIVE),
        C(STARTING), C(STOPPING), C(BACKING_UP), C(DELETING), C(RESTORING), C(ERROR_RESIZING), C(ERROR_STARTING),
        C(ERROR_STOPPING), C(ERROR_DELETING), C(MAINTENANCE), and C(MAINTENANCE_ERROR).
    type: str
  engine_id:
    description:
      - Return only instances that use the database engine with this ID (UUID).
    type: str
  parameter_group_id:
    description:
      - Return only instances that use the parameter group with this ID (UUID).
    type: str
  deletion_protected:
    description:
      - Return only instances whose deletion protection matches this value.
    type: bool
  include_replicas:
    description:
      - Whether to include the read replicas of each instance in RV(instances[].replicas).
    type: bool
    default: false
notes:
  - The API key needs permission to list database instances, or to get a database instance when O(id) is set.
  - Supports check mode. The module only reads data, so it behaves the same in check mode.
  - When O(id) is set and the API responds with HTTP 404 Not Found, the module succeeds and returns an empty
    RV(instances) list. Any other error, including authentication and permission errors, fails the module.
  - The API returns instances in pages. The DBaaS API documents no sort order, so instances created or deleted while the
    module reads the pages may be missed or returned twice.
  - The DBaaS API documents no filter by instance name. Filter the returned list instead, as shown in the examples.
  - The DBaaS API reference does not state whether instances in status C(DELETED) are returned when O(status) is not set.
seealso:
  - module: dennisurtubia.magalu_cloud.database_instance
"""

EXAMPLES = r"""
- name: List all database instances in a region
  dennisurtubia.magalu_cloud.database_instance_info:
    region: br-se1
  register: db_instances

- name: List the active instances that are protected against deletion
  dennisurtubia.magalu_cloud.database_instance_info:
    region: br-se1
    status: ACTIVE
    deletion_protected: true
  register: protected_instances

- name: Get an instance and its read replicas
  dennisurtubia.magalu_cloud.database_instance_info:
    api_key: "{{ magalu_cloud_api_key }}"
    region: br-ne1
    id: 497f6eca-6276-4993-bfeb-53cbbbba6f08
    include_replicas: true
  register: db_instance

- name: Fail when the instance does not exist
  ansible.builtin.assert:
    that: db_instance.instances | length == 1

- name: Show the IDs of the instances named my-db-instance
  ansible.builtin.debug:
    msg: "{{ db_instances.instances | selectattr('name', 'equalto', 'my-db-instance') | map(attribute='id') | list }}"
"""

RETURN = r"""
instances:
  description:
    - Instances returned by the API, each one as the API describes it.
    - Empty when no instance matches, or when O(id) is set and the API responds with HTTP 404 Not Found.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description: ID (UUID) of the instance.
      returned: always
      type: str
      sample: 497f6eca-6276-4993-bfeb-53cbbbba6f08
    name:
      description: Name of the instance.
      returned: always
      type: str
      sample: my-db-instance
    engine_id:
      description: ID (UUID) of the database engine.
      returned: always
      type: str
      sample: b1d2d00a-6e57-4e4b-9c8e-447d4c2457d0
    instance_type_id:
      description: ID (UUID) of the instance type.
      returned: always
      type: str
      sample: b67afca2-5b6f-43dd-b5de-7627dae240c8
    parameter_group_id:
      description: ID (UUID) of the parameter group.
      returned: always
      type: str
      sample: 60517f0f-1194-4a4f-8234-33197a1e7381
    port_id:
      description: ID (UUID) of the port that the Magalu Cloud Network API uses for the instance.
      returned: when provided by the API
      type: str
      sample: 2b97437e-648a-4484-9174-d069ca9706be
    apply_parameters_pending:
      description: Whether the instance must be restarted to apply its parameters.
      returned: always
      type: bool
      sample: false
    deletion_protected:
      description: Whether the instance is protected against deletion.
      returned: always
      type: bool
      sample: true
    volume:
      description: Storage volume of the instance.
      returned: always
      type: dict
      contains:
        size:
          description: Volume size in GiB.
          returned: always
          type: int
          sample: 30
        type:
          description: Volume type.
          returned: always
          type: str
          sample: CLOUD_NVME15K
        encrypted:
          description: Whether the volume is encrypted.
          returned: always
          type: bool
          sample: true
    addresses:
      description: Network addresses of the instance.
      returned: always
      type: list
      elements: dict
      contains:
        access:
          description: Whether the address is reachable from the internet (C(PUBLIC)) or not (C(PRIVATE)).
          returned: always
          type: str
          sample: PRIVATE
        type:
          description: IP version of the address, C(IPv4) or C(IPv6).
          returned: when provided by the API
          type: str
          sample: IPv4
        address:
          description: IP address.
          returned: when provided by the API
          type: str
          sample: 172.53.10.82
    status:
      description: Status of the instance.
      returned: always
      type: str
      sample: ACTIVE
    availability_zone:
      description: Availability zone of the instance.
      returned: always
      type: str
      sample: br-se1-a
    generation:
      description: Generation of the instance.
      returned: always
      type: str
      sample: G10
    backup_retention_days:
      description: Number of days each automated backup is kept.
      returned: always
      type: int
      sample: 7
    backup_start_at:
      description: Time of day, in UTC, from which the automated backup process may start.
      returned: always
      type: str
      sample: "04:00:00"
    created_at:
      description: Creation date and time.
      returned: always
      type: str
      sample: "2026-10-16T12:00:00Z"
    updated_at:
      description: Date and time of the last update.
      returned: when provided by the API
      type: str
      sample: "2026-10-16T12:30:00Z"
    started_at:
      description: Date and time when the initial setup started.
      returned: when provided by the API
      type: str
      sample: "2026-10-16T12:00:05Z"
    finished_at:
      description: Date and time when the initial setup finished.
      returned: when provided by the API
      type: str
      sample: "2026-10-16T12:10:00Z"
    maintenance_scheduled_at:
      description: Date and time of the next scheduled maintenance.
      returned: when provided by the API
      type: str
      sample: "2026-10-20T03:00:00Z"
    replicas:
      description:
        - Read replicas of the instance, as the API describes them.
        - Each replica has, among others, the keys C(id), C(source_id), C(name), C(engine_id), C(instance_type_id),
          C(parameter_group_id), C(volume), C(addresses), C(status), C(availability_zone), C(generation), and C(created_at).
      returned: when O(include_replicas=true) and provided by the API
      type: list
      elements: dict
status:
  description: HTTP status code of the API response.
  returned: when the API responds with an error or an unexpected status
  type: int
  sample: 403
error:
  description: Error returned by the API.
  returned: when the API responds with an error and a JSON body
  type: dict
  contains:
    slug:
      description: Short error identifier.
      returned: always
      type: str
      sample: forbidden
    message:
      description: Error message.
      returned: always
      type: str
      sample: Access Forbidden
    details:
      description: Additional error details.
      returned: when provided by the API
      type: dict
body:
  description: Raw response body, when the API responds with an error that is not JSON.
  returned: when the API responds with an error and a body that is not JSON
  type: str
"""

from urllib.parse import quote

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
from ansible_collections.dennisurtubia.magalu_cloud.plugins.module_utils.database import (
    argument_spec,
    fail_with_api_error,
    parse_json,
    request,
)

# Contract: GET /v2/instances and GET /v2/instances/{instance_id} in the DBaaS API spec 2.33.3,
# https://docs.magalu.cloud/redocusaurus/dbaas-openapi.yaml
# TODO(source): the list operation is described as returning the instances "for a x-tenant-id". The documentation does not
# say whether the x-tenant-id header is required with an API key; like database_instance, this module does not send it.

# Largest _limit the API accepts for GET /v2/instances.
PAGE_SIZE = 25

# Options sent to the list operation as query parameters, under the same names.
FILTERS = ("status", "engine_id", "parameter_group_id", "deletion_protected")


class DatabaseInstanceInfo:
    """Reads DBaaS instances from the Magalu Cloud API."""

    def __init__(self, module):
        self.module = module

    @classmethod
    def define_module(cls):
        return AnsibleModule(
            argument_spec=dict(
                argument_spec(),
                id=dict(type="str"),
                status=dict(type="str"),
                engine_id=dict(type="str"),
                parameter_group_id=dict(type="str"),
                deletion_protected=dict(type="bool"),
                include_replicas=dict(type="bool", default=False),
            ),
            mutually_exclusive=[("id", key) for key in FILTERS],
            supports_check_mode=True,
        )

    def gather(self):
        if self.module.params["id"] is not None:
            return dict(changed=False, instances=self._get())
        return dict(changed=False, instances=self._list())

    def _expand(self):
        return {"_expand": "replicas"} if self.module.params["include_replicas"] else {}

    def _get(self):
        path = "/instances/{0}".format(quote(self.module.params["id"], safe=""))
        response, info = request(self.module, path, query=self._expand())
        if info["status"] == 404:
            return []

        instance = self._read(response, info, "get database instance")
        if not isinstance(instance, dict) or not instance.get("id"):
            self.module.fail_json(msg="The API response for the database instance has no instance ID.", changed=False)
        return [instance]

    def _list(self):
        params = self.module.params
        query = {key: self._query_value(params[key]) for key in FILTERS if params[key] is not None}
        query.update(self._expand())

        instances = []
        while True:
            response, info = request(self.module, "/instances", query=dict(query, _limit=PAGE_SIZE, _offset=len(instances)))
            results, total = self._parse_page(self._read(response, info, "list database instances"))
            instances.extend(results)
            # An empty page ends the listing even when fewer instances than the total were read, so a total that changes
            # while the pages are read can never cause an endless loop.
            if not results or len(instances) >= total:
                return instances

    def _read(self, response, info, action):
        status = info["status"]

        if status == -1:
            self.module.fail_json(msg="Failed to {0}: {1}".format(action, info.get("msg")), changed=False)

        if status >= 400:
            fail_with_api_error(self.module, action, info)

        if status != 200:
            self.module.fail_json(msg="Unexpected HTTP status {0} from the DBaaS API.".format(status), changed=False, status=status)

        return parse_json(to_text(response.read(), errors="surrogate_or_replace"))

    def _parse_page(self, page):
        meta = page.get("meta") if isinstance(page, dict) else None
        page_info = meta.get("page") if isinstance(meta, dict) else None
        results = page.get("results") if isinstance(page, dict) else None
        total = page_info.get("total") if isinstance(page_info, dict) else None

        valid_results = isinstance(results, list) and all(isinstance(item, dict) for item in results)
        valid_total = isinstance(total, int) and not isinstance(total, bool)
        if not valid_results or not valid_total:
            self.module.fail_json(msg="The API response for the database instance list is malformed.", changed=False)
        return results, total

    @staticmethod
    def _query_value(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        return value


def main():
    module = DatabaseInstanceInfo.define_module()
    result = DatabaseInstanceInfo(module).gather()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
