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
import openstack.network.v2.router
import openstack.network.v2.network

# Local imports
from openstacksdk_plugin.tests.base import OpenStackTestBase
from openstacksdk_plugin.resources.network import router
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           OPENSTACK_NAME_PROPERTY,
                                           OPENSTACK_TYPE_PROPERTY,
                                           ROUTER_OPENSTACK_TYPE,
                                           NETWORK_OPENSTACK_TYPE,
                                           NETWORK_NODE_TYPE)


@mock.patch('openstack.connect')
class RouterTestCase(OpenStackTestBase):

    def setUp(self):
        super(RouterTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_router',
            'description': 'router_description',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        rel_specs = [
            {
                'node': {
                    'id': 'ext-network-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-network',
                        }
                    }
                },
                'instance': {
                    'id': 'ext-network-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe4',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-ext-network'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
        ]

        router_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_relationships=router_rels)

        router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })

        network_instance = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'name': 'test_network',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'is_router_external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'description': '4',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 8,
            'port_security_enabled': True,
            'project_id': '10',
            'provider:network_type': '11',
            'provider:physical_network': '12',
            'provider:segmentation_id': '13',
            'qos_policy_id': '14',
            'revision_number': 15,
            'router:external': True,
            'segments': '16',
            'shared': True,
            'status': '17',
            'subnets': ['18', '19'],
            'updated_at': '2016-07-09T12:14:57.233772',
            'vlan_transparent': False,

        })

        # Mock create router response
        mock_connection().network.create_router = \
            mock.MagicMock(return_value=router_instance)

        # Mock get network response
        mock_connection().network.get_network = \
            mock.MagicMock(return_value=network_instance)

        # Call create router
        router.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_router')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            ROUTER_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })
        # Mock delete router response
        mock_connection().network.delete_router = \
            mock.MagicMock(return_value=None)

        # Mock get router response
        mock_connection().network.get_port = \
            mock.MagicMock(return_value=router_instance)

        # Call delete router
        router.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })

        new_config = {
            'name': 'test_updated_router',
        }

        new_router_instance = \
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_updated_router',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            })

        # Mock get router response
        mock_connection().network.get_router = \
            mock.MagicMock(return_value=old_router_instance)

        # Mock update router response
        mock_connection().network.update_router = \
            mock.MagicMock(return_value=new_router_instance)

        # Call update router
        router.update(args=new_config)

    def test_add_routes(self, mock_connection):
        # Prepare the context for start operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.start',
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        old_router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': [],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })

        new_config = {
            'routes': [
                {
                    'destination': '10.10.4.0/24',
                    'nexthop': '192.168.123.123'
                }
            ]
        }

        new_router_instance = \
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_updated_router',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': [
                    {
                        'destination': '10.10.4.0/24',
                        'nexthop': '192.168.123.123'
                    }
                ],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            })

        # Mock get router response
        mock_connection().network.get_router = \
            mock.MagicMock(return_value=old_router_instance)

        # Mock update router response
        mock_connection().network.update_router = \
            mock.MagicMock(return_value=new_router_instance)

        # Call start router
        router.start(**new_config)

        self.assertEqual(self._ctx.instance.runtime_properties['routes'],
                         new_config['routes'])

    def test_remove_routes(self, mock_connection):
        # Prepare the context for start operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.stop',
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'routes': [
                    {
                        'destination': '10.10.4.0/24',
                        'nexthop': '192.168.123.123'
                    }
                ]
            })

        old_router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': [
                {
                    'destination': '10.10.4.0/24',
                    'nexthop': '192.168.123.123'
                }
            ],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })

        new_router_instance = \
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_updated_router',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': [],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            })

        # Mock get router response
        mock_connection().network.get_router = \
            mock.MagicMock(return_value=old_router_instance)

        # Mock update router response
        mock_connection().network.update_router = \
            mock.MagicMock(return_value=new_router_instance)

        # Call stop router
        router.stop()

    def test_add_interface_to_router(self, mock_connection):
        # Prepare the context for postconfigure operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name=
            'cloudify.interfaces.relationship_lifecycle.postconfigure',
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': [],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })
        # Mock get router response
        mock_connection().network.get_router = \
            mock.MagicMock(return_value=router_instance)

        # Mock add interface router response
        mock_connection().network.add_interface_to_router = \
            mock.MagicMock(return_value=router_instance)

        # Call add interface to router
        router.add_interface_to_router(
            **{'port_id': 'a95b5509-c122-4c2f-823e-884bb559afe3'})

    def test_remove_interface_from_router(self, mock_connection):
        # Prepare the context for unlink operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name=
            'cloudify.interfaces.relationship_lifecycle.unlink',
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        router_instance = openstack.network.v2.router.Router(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_router',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {
                'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
            },
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': [],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',
        })
        # Mock get router response
        mock_connection().network.get_router = \
            mock.MagicMock(return_value=router_instance)

        # Mock remove router interface response
        mock_connection().network.remove_interface_from_router = \
            mock.MagicMock(return_value=router_instance)

        # Call remove interface from router
        router.remove_interface_from_router(
            **{'port_id': 'a95b5509-c122-4c2f-823e-884bb559afe3'})

    def test_list_routers(self, mock_connection):
        # Prepare the context for list routers operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        routers = [
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_router_1',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            }),
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afr8',
                'name': 'test_router_2',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            }),
        ]

        # Mock list routers response
        mock_connection().network.routers = \
            mock.MagicMock(return_value=routers)

        # Call list routers
        router.list_routers()

        # Check if the routers list saved as runtime properties
        self.assertIn(
            'router_list',
            self._ctx.instance.runtime_properties)

        # Check the size of routers list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['router_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for list routers operation
        self._prepare_context_for_operation(
            test_name='RouterTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        routers = [
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_router_1',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            }),
            openstack.network.v2.router.Router(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afr8',
                'name': 'test_router_2',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {
                    'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                },
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',
            }),
        ]

        # Mock list router response
        mock_connection().network.routers = \
            mock.MagicMock(return_value=routers)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        router.creation_validation()
