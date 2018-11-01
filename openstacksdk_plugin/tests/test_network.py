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

from cloudify.state import current_ctx


@mock.patch('openstack.connect')
class TestNetwork(OpenStackTestBase):

    def setUp(self):
        super(TestNetwork, self).setUp()
        self._ctx = self.get_mock_ctx('TestNetwork')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        network.create()

    def test_delete(self, _cx):
        network.delete()


@mock.patch('openstack.connect')
class TestSubnet(OpenStackTestBase):

    def setUp(self):
        super(TestSubnet, self).setUp()
        self._ctx = self.get_mock_ctx('TestSubnet')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        subnet.create()

    def test_delete(self, _cx):
        subnet.delete()


@mock.patch('openstack.connect')
class TestRouter(OpenStackTestBase):

    def setUp(self):
        super(TestRouter, self).setUp()
        self._ctx = self.get_mock_ctx('TestRouter')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        router.create()

    def test_delete(self, _cx):
        router.delete()


@mock.patch('openstack.connect')
class TestPort(OpenStackTestBase):

    def setUp(self):
        super(TestPort, self).setUp()
        self._ctx = self.get_mock_ctx('TestPort')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        port.create()

    def test_delete(self, _cx):
        port.delete()


@mock.patch('openstack.connect')
class TestSecurityGroup(OpenStackTestBase):

    def setUp(self):
        super(TestSecurityGroup, self).setUp()
        self._ctx = self.get_mock_ctx('TestSecurityGroup')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        security_group.create()

    def test_delete(self, _cx):
        security_group.delete()


@mock.patch('openstack.connect')
class TestSecurityGroupRule(OpenStackTestBase):

    def setUp(self):
        super(TestSecurityGroupRule, self).setUp()
        self._ctx = self.get_mock_ctx('TestSecurityGroupRule')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        security_group_rule.create()

    def test_delete(self, _cx):
        security_group_rule.delete()


@mock.patch('openstack.connect')
class TestFloatingIP(OpenStackTestBase):

    def setUp(self):
        super(TestFloatingIP, self).setUp()
        self._ctx = self.get_mock_ctx('TestFloatingIP')
        current_ctx.set(self._ctx)

    def test_create(self, _cx):
        floating_ip.create()

    def test_delete(self, _cx):
        floating_ip.delete()
