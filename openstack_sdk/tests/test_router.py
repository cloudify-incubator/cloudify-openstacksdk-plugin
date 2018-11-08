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

# Standard imports
import mock

# Third party imports
import openstack.network.v2.router

# Local imports
from . import base
from openstack_sdk.resources import networks


class RouterTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(RouterTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('router')
        self.router_instance = networks.OpenstackRouter(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.router_instance.connection = self.connection

    def test_get_router(self):
        router = openstack.network.v2.router.Router(**{
            'id': '1',
            'name': 'test_name',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {'4': 4},
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',

        })
        self.router_instance.resource_id = '1'
        self.fake_client.get_router = mock.MagicMock(return_value=router)

        response = self.router_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_name')
        self.assertEqual(response.flavor_id, '5')

    def test_list_ports(self):
        routers = [
            openstack.network.v2.router.Router(**{
                'id': '1',
                'name': 'test_name_1',
                'description': 'test_description_1',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {'4': 4},
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',

            }),
            openstack.network.v2.router.Router(**{
                'id': '2',
                'name': 'test_name_2',
                'description': 'test_description_2',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'created_at': 'timestamp1',
                'distributed': False,
                'external_gateway_info': {'4': 4},
                'flavor_id': '5',
                'ha': False,
                'revision': 7,
                'routes': ['8'],
                'status': '9',
                'tenant_id': '10',
                'updated_at': 'timestamp2',

            })
        ]

        self.fake_client.routers = mock.MagicMock(return_value=routers)
        response = self.router_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_router(self):
        router = {
            'name': 'test_name',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'distributed': False,
            'flavor_id': '5',
            'ha': False,
            'routes': ['8'],
            'tenant_id': '10',
        }

        new_res = openstack.network.v2.router.Router(**router)
        self.router_instance.config = router
        self.fake_client.create_router = mock.MagicMock(return_value=new_res)

        response = self.router_instance.create()
        self.assertEqual(response.name, router['name'])
        self.assertEqual(response.description, router['description'])

    def test_update_router(self):
        old_router = openstack.network.v2.router.Router(**{
            'id': '1',
            'name': 'test_name',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {'4': 4},
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',

        })

        new_config = {
            'name': 'test_name_update',
            'description': 'test_description_update',
            'distributed': True
        }

        new_router = openstack.network.v2.router.Router(**{
            'id': '1',
            'name': 'test_name_update',
            'description': 'test_description_update',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': True,
            'external_gateway_info': {'4': 4},
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',

        })

        self.router_instance.resource_id = '1'
        self.fake_client.get_router = mock.MagicMock(return_value=old_router)
        self.fake_client.update_router = \
            mock.MagicMock(return_value=new_router)

        response = self.router_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_router.name)
        self.assertNotEqual(response.description, old_router.description)
        self.assertNotEqual(response.is_distributed, old_router.is_distributed)

    def test_delete_router(self):
        router = openstack.network.v2.router.Router(**{
            'id': '1',
            'name': 'test_name',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'created_at': 'timestamp1',
            'distributed': False,
            'external_gateway_info': {'4': 4},
            'flavor_id': '5',
            'ha': False,
            'revision': 7,
            'routes': ['8'],
            'status': '9',
            'tenant_id': '10',
            'updated_at': 'timestamp2',

        })

        self.router_instance.resource_id = '1'
        self.fake_client.get_router = mock.MagicMock(return_value=router)
        self.fake_client.delete_router = mock.MagicMock(return_value=None)

        response = self.router_instance.delete()
        self.assertIsNone(response)
