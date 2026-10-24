# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations


class ModuleDocFragment:
    # Options shared by every DBaaS module, defined in plugins/module_utils/database.py.
    DOCUMENTATION = r"""
options:
  api_key:
    description:
      - Magalu Cloud API key, sent in the C(x-api-key) header.
      - The key needs permission for the database operations the module performs.
      - If not set, the value of the E(MAGALU_CLOUD_API_KEY) environment variable is used. This variable name is a convention
        of this collection, not of Magalu Cloud.
    type: str
    required: true
  region:
    description:
      - Magalu Cloud region of the database resources. It selects the API endpoint C(https://api.magalu.cloud/<region>/database).
    type: str
    required: true
    choices: [br-se1, br-ne1]
  timeout:
    description:
      - Number of seconds to wait for the API to respond to each request.
    type: int
    default: 30
notes:
  - The DBaaS API reference lists the northeast server as C(br-ne-1), while the Magalu Cloud API authentication guide uses
    C(br-ne1). The module follows the authentication guide.
  - The DBaaS API reference documents OAuth2 as its authentication scheme, while the Magalu Cloud API authentication guide
    documents the C(x-api-key) header. The module follows the authentication guide.
seealso:
  - name: DBaaS API reference
    description: Official Magalu Cloud DBaaS API documentation.
    link: https://docs.magalu.cloud/api/database
  - name: Magalu Cloud API authentication
    description: How to authenticate to Magalu Cloud APIs with an API key.
    link: https://docs.magalu.cloud/docs/devops-tools/apis/auth
"""
