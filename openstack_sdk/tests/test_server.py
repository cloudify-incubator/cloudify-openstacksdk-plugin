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
import openstack.compute.v2.server

# Local imports
from . import base
from openstack_sdk.resources import compute


class ServerTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(ServerTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('server')
        self.server_instance = compute.OpenstackServer(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.server_instance.connection = self.connection

    def test_get_server(self):
        server = openstack.compute.v2.server.Server(**{
            'id': '1',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',

        })

        self.server_instance.name = 'test_server'
        self.server_instance.id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)

        response = self.server_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_server')

    def test_list_servers(self):
        server_list = [
            openstack.compute.v2.server.ServerDetail(**{
                'id': '1',
                'name': 'test_server_1',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {'region': '3'},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
            openstack.compute.v2.server.ServerDetail(**{
                'id': '2',
                'name': 'test_server_2',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {'region': '3'},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
        ]

        self.fake_client.servers = mock.MagicMock(return_value=server_list)
        response = self.server_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_server(self):
        config = {
            'name': 'test_server',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        }

        server = {
            'id': '1',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        }

        self.server_instance.config = config
        new_res = openstack.compute.v2.server.Server(**server)
        self.fake_client.create_server = mock.MagicMock(return_value=new_res)

        response = self.server_instance.create()
        self.assertEqual(response.name, config['name'])

    def test_update_server(self):
        old_server = openstack.compute.v2.server.Server(**{
            'id': '1',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        })

        new_config = {
            'name': 'update_test_server',
        }

        new_server = openstack.compute.v2.server.Server(**{
            'id': '1',
            'name': 'update_test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=old_server)
        self.fake_client.update_server =\
            mock.MagicMock(return_value=new_server)

        response = self.server_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_server.name)

    def test_delete_server(self):
        server = openstack.compute.v2.server.Server(**{
            'id': '1',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.delete_server = mock.MagicMock(return_value=None)

        response = self.server_instance.delete()
        self.assertIsNone(response)
