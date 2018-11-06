# #######
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import mock

from openstacksdk_plugin.tests.base import OpenStackTestBase
from openstacksdk_plugin.resources.network import (
    network,
    subnet,
    router,
    port,
    security_group,
    security_group_rule,
    floating_ip)
from openstacksdk_plugin.constants import RESOURCE_ID

from cloudify.state import current_ctx

MODULE_PATH = 'openstack.cloud.openstackcloud._OpenStackCloudMixin'


@mock.patch('openstack.connect')
class NetworkTestCase(OpenStackTestBase):

    def setUp(self):
        super(NetworkTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('NetworkTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_network'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        network.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        network.delete()


@mock.patch('openstack.connect')
class SubnetTestCase(OpenStackTestBase):

    def setUp(self):
        super(SubnetTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('SubnetTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_subnet'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        subnet.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        subnet.delete()


@mock.patch('openstack.connect')
class RouterTestCase(OpenStackTestBase):

    def setUp(self):
        super(RouterTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('RouterTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_router'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        router.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        router.delete()


@mock.patch('openstack.connect')
class PortTestCase(OpenStackTestBase):

    def setUp(self):
        super(PortTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('PortTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_port'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        port.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        port.delete()


@mock.patch('openstack.connect')
class SecurityGroupTestCase(OpenStackTestBase):

    def setUp(self):
        super(SecurityGroupTestCase, self).setUp()
        self._ctx = self.get_mock_ctx('SecurityGroupTestCase')
        current_ctx.set(self._ctx)

    @mock.patch(
        '{0}.create_security_group'.format(MODULE_PATH),
        return_value=mock.MagicMock())
    def test_create(self, *_):
        security_group.create()
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

    def test_delete(self, *_):
        security_group.delete()


@mock.patch('openstack.connect')
class SecurityGroupTestCaseRule(OpenStackTestBase):

    def setUp(self):
        super(SecurityGroupTestCaseRule, self).setUp()
        self._ctx = self.get_mock_ctx('SecurityGroupTestCaseRule')
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
