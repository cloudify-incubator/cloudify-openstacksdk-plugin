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

# Standard imports
import mock

# Third party imports
import openstack.compute.v2.server

# Local imports
from openstack_sdk.tests import base
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

    def test_reboot_server(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.reboot_server = mock.MagicMock(return_value=None)

        response = self.server_instance.reboot(reboot_type='SOFT')
        self.assertIsNone(response)

    def test_resume_server(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.resume_server = mock.MagicMock(return_value=None)

        response = self.server_instance.resume()
        self.assertIsNone(response)

    def test_suspend_server(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.suspend_server = mock.MagicMock(return_value=None)

        response = self.server_instance.suspend()
        self.assertIsNone(response)

    def test_backup_server(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.backup_server = mock.MagicMock(return_value=None)

        response = self.server_instance.backup('test-backup', 'daily', 30)
        self.assertIsNone(response)

    def test_rebuild_server(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.rebuild_server = mock.MagicMock(return_value=None)

        response = self.server_instance.rebuild('12323')
        self.assertIsNone(response)

    def test_create_image(self):
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
            'status': 'ACTIVE',

        })

        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.create_server_image = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.create_image('test-image')
        self.assertIsNone(response)

    def test_start_server(self):
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
        self.fake_client.start_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.start()
        self.assertIsNone(response)

    def test_stop_server(self):
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
        self.fake_client.stop_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.stop()
        self.assertIsNone(response)

    def test_get_server_password(self):
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
        password = 'rasmuslerdorf'
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.get_server_password = \
            mock.MagicMock(return_value=password)

        response = self.server_instance.get_server_password()
        self.assertEqual(response, password)

    def test_list_volume_attachments(self):
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
        volume_attachments = [
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '1',
                'volume_id': '1',
                'attachment_id': '1',
            })
        ]
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.volume_attachments = \
            mock.MagicMock(return_value=volume_attachments)

        response = self.server_instance.list_volume_attachments()
        self.assertEqual(len(response), 1)

    def test_get_volume_attachment(self):
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
        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '2',
                'volume_id': '3',
                'attachment_id': '4',
            })
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.get_volume_attachment = \
            mock.MagicMock(return_value=volume_attachment)

        response = self.server_instance.get_volume_attachment('4')
        self.assertEqual(response.id, '1')
        self.assertEqual(response.server_id, '2')
        self.assertEqual(response.volume_id, '3')
        self.assertEqual(response.attachment_id, '4')

    def test_create_volume_attachment(self):
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

        volume_config = {
            'volume_id': '1',
            'device': 'auto'
        }
        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '2',
                'volume_id': '3',
                'attachment_id': '4',
            })
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.create_volume_attachment = \
            mock.MagicMock(return_value=volume_attachment)

        response = self.server_instance.create_volume_attachment(volume_config)
        self.assertEqual(response.id, '1')
        self.assertEqual(response.server_id, '2')
        self.assertEqual(response.volume_id, '3')
        self.assertEqual(response.attachment_id, '4')

    def test_delete_volume_attachment(self):
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
        self.fake_client.delete_volume_attachment = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.delete_volume_attachment('4')
        self.assertIsNone(response)

    def test_list_server_interfaces(self):
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
        server_interfaces = [
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': '1',
                'net_id': '2',
                'port_id': '3',
                'server_id': '1',
            }),
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': '2',
                'net_id': '3',
                'port_id': '4',
                'server_id': '1',
            })
        ]
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.server_interfaces = \
            mock.MagicMock(return_value=server_interfaces)

        response = self.server_instance.server_interfaces()
        self.assertEqual(len(response), 2)

    def test_get_server_interface(self):
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
        server_interface = \
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': '1',
                'net_id': '2',
                'port_id': '3',
                'server_id': '1',
            })
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.get_server_interface = \
            mock.MagicMock(return_value=server_interface)

        response = self.server_instance.get_server_interface('1')
        self.assertEqual(response.id, '1')
        self.assertEqual(response.net_id, '2')
        self.assertEqual(response.port_id, '3')
        self.assertEqual(response.server_id, '1')

    def test_create_server_interface(self):
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

        interface_config = {
            'port_id': '3',
        }
        server_interface = \
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': '1',
                'net_id': None,
                'port_id': '3',
                'server_id': '1',
            })
        self.server_instance.resource_id = '1'
        self.fake_client.get_server = mock.MagicMock(return_value=server)
        self.fake_client.create_server_interface = \
            mock.MagicMock(return_value=server_interface)

        response = \
            self.server_instance.create_server_interface(interface_config)
        self.assertEqual(response.id, '1')
        self.assertEqual(response.server_id, '1')
        self.assertEqual(response.port_id, '3')

    def test_delete_server_interface(self):
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
        self.fake_client.delete_server_interface = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.delete_server_interface('1')
        self.assertIsNone(response)

    def test_add_security_group_to_server(self):
        self.server_instance.resource_id = '1'
        self.fake_client.add_security_group_to_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.add_security_group_to_server('1')
        self.assertIsNone(response)

    def test_remove_security_group_from_server(self):
        self.server_instance.resource_id = '1'
        self.fake_client.remove_security_group_from_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.remove_security_group_from_server('1')
        self.assertIsNone(response)

    def test_add_floating_ip_to_server(self):
        self.server_instance.resource_id = '1'
        self.fake_client.add_floating_ip_to_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.add_floating_ip_to_server('1')
        self.assertIsNone(response)

    def test_remove_floating_ip_from_server(self):
        self.server_instance.resource_id = '1'
        self.fake_client.remove_floating_ip_from_server = \
            mock.MagicMock(return_value=None)

        response = self.server_instance.remove_floating_ip_from_server('1')
        self.assertIsNone(response)
