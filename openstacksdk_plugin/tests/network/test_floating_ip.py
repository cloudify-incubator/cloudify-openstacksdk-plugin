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

# Local imports
from openstacksdk_plugin.tests.base import OpenStackTestBase
from openstacksdk_plugin.resources.network import floating_ip
from openstacksdk_plugin.constants import RESOURCE_ID


MODULE_PATH = 'openstack.cloud.openstackcloud._OpenStackCloudMixin'


@mock.patch('openstack.connect')
class FloatingIPTestCase(OpenStackTestBase):

    def setUp(self):
        super(FloatingIPTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('FloatingIPTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_floating_ip'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        floating_ip.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        floating_ip.delete()
