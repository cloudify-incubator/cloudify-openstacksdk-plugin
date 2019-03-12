# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Third party imports
import mock
from cloudify.state import current_ctx

# local imports
from openstacksdk_plugin.tests.base import OpenStackTestBase
from openstacksdk_plugin.resources.network import security_group_rule
from openstacksdk_plugin.constants import RESOURCE_ID


MODULE_PATH = 'openstack.cloud.openstackcloud._OpenStackCloudMixin'


@mock.patch('openstack.connect')
class SecurityGroupRuleTestCase(OpenStackTestBase):

    def setUp(self):
        super(SecurityGroupRuleTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('SecurityGroupRuleTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_security_group_rule'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        security_group_rule.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        security_group_rule.delete()
