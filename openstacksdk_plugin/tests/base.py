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

import copy
import unittest

from cloudify.manager import DirtyTrackingDict
from cloudify.mocks import MockCloudifyContext


class OpenStackTestBase(unittest.TestCase):

    def setUp(self):
        super(OpenStackTestBase, self).setUp()

    def tearDown(self):
        super(OpenStackTestBase, self).tearDown()

    def _to_DirtyTrackingDict(self, origin):
        if not origin:
            origin = {}
        dirty_dict = DirtyTrackingDict()
        for k in origin:
            dirty_dict[k] = copy.deepcopy(origin[k])
        return dirty_dict

    @property
    def client_config(self):
        return {
            'auth_url': 'foo',
            'username': 'foo',
            'password': 'foo',
            'region_name': 'foo',
            'project_name': 'foo'
        }

    @property
    def resource_config(self):
        return {
            'name': 'foo',
            'description': 'foo'
        }

    @property
    def node_properties(self):
        return {
            'client_config': self.client_config,
            'resource_config': self.resource_config
        }

    @property
    def runtime_properties(self):
        return {
            'resource_config': self.resource_config
        }

    def get_mock_ctx(self,
                     test_name,
                     test_properties={},
                     test_runtime_properties={},
                     test_relationships=None,
                     type_hierarchy=['cloudify.nodes.Root'],
                     ctx_operation_name=None):

        operation_ctx = {
            'retry_number': 0, 'name': 'cloudify.interfaces.lifecycle.'
        } if not ctx_operation_name else {
            'retry_number': 0, 'name': ctx_operation_name
        }

        ctx = MockCloudifyContext(
            node_id=test_name,
            node_name=test_name,
            deployment_id=test_name,
            properties=copy.deepcopy(test_properties or self.node_properties),
            runtime_properties=self._to_DirtyTrackingDict(
                test_runtime_properties or self.runtime_properties
            ),
            relationships=test_relationships,
            operation=operation_ctx
        )

        ctx.node.type_hierarchy = type_hierarchy

        return ctx

    def get_mock_relationship_ctx(self,
                                  deployment_name,
                                  test_properties={},
                                  test_runtime_properties={},
                                  test_source=None,
                                  test_target=None,
                                  type_hierarchy=['cloudify.nodes.Root']):

        ctx = MockCloudifyContext(
            deployment_id=deployment_name,
            properties=copy.deepcopy(test_properties),
            source=test_source,
            target=test_target,
            runtime_properties=copy.deepcopy(test_runtime_properties))
        return ctx
