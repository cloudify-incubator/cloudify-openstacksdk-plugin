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
import openstack.compute.v2.server
import openstack.image.v2.image
from cloudify.state import current_ctx
from cloudify.exceptions import OperationRetry
from cloudify.mocks import (
    MockContext,
    MockNodeContext,
    MockNodeInstanceContext,
)


# Local imports
from openstacksdk_plugin.tests.base import OpenStackTestBase
from openstacksdk_plugin.resources.compute import server
from openstacksdk_plugin.utils import (get_snapshot_name,
                                       generate_attachment_volume_key)
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           OPENSTACK_NAME_PROPERTY,
                                           OPENSTACK_TYPE_PROPERTY,
                                           FLOATING_IP_OPENSTACK_TYPE,
                                           SECURITY_GROUP_OPENSTACK_TYPE,
                                           VOLUME_OPENSTACK_TYPE,
                                           SERVER_OPENSTACK_TYPE,
                                           SERVER_TASK_DELETE,
                                           SERVER_TASK_START,
                                           SERVER_TASK_STOP,
                                           SERVER_TASK_BACKUP_DONE,
                                           SERVER_TASK_RESTORE_STATE,
                                           VOLUME_ATTACHMENT_TASK,
                                           VOLUME_DETACHMENT_TASK,
                                           VOLUME_ATTACHMENT_ID,
                                           SERVER_ACTION_STATUS_DONE,
                                           SERVER_ACTION_STATUS_PENDING)


@mock.patch('openstack.connect')
class ServerTestCase(OpenStackTestBase):

    def setUp(self):
        super(ServerTestCase, self).setUp()
        self.type_hierarchy = ['cloudify.nodes.Root', 'cloudify.nodes.Compute']

    def _prepare_context_for_operation(self,
                                       node_id,
                                       operation_name,
                                       relationships=None,
                                       runtime_properties={}):
        self._ctx = self.get_mock_ctx(
            test_name=node_id,
            type_hierarchy=self.type_hierarchy,
            ctx_operation_name=operation_name,
            test_relationships=relationships,
            test_runtime_properties=runtime_properties)
        current_ctx.set(self._ctx)

    def _pepare_relationship_context_for_operation(self,
                                                   deployment_id,
                                                   source,
                                                   target,
                                                   node_id=None):

        self._ctx = self.get_mock_relationship_ctx(
            node_id=node_id,
            deployment_name=deployment_id,
            test_source=source,
            test_target=target)
        current_ctx.set(self._ctx)

    @property
    def node_properties(self):
        properties = super(ServerTestCase, self).node_properties
        properties['os_family'] = 'Linux'
        properties['device_name'] = 'test-device'
        return properties

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.lifecycle.create')

        server_instance = openstack.compute.v2.server.Server(**{
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
        mock_connection().compute.create_server = \
            mock.MagicMock(return_value=server_instance)
        server.create()

        # Check if the resource id is already set or not
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

        # Check if the server payload is assigned for the created server
        self.assertIn(
            SERVER_OPENSTACK_TYPE,
            self._ctx.instance.runtime_properties)

    @mock.patch('openstacksdk_plugin.resources.compute.server'
                '._get_user_password')
    @mock.patch('openstacksdk_plugin.resources.compute.server'
                '._set_server_ips_runtime_properties')
    def test_configure(self,
                       mock_ips_runtime_properties,
                       mock_user_password,
                       mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.lifecycle.configure')
        server_instance = openstack.compute.v2.server.Server(**{
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
            'status': 'ACTIVE'

        })
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        server.configure()
        mock_ips_runtime_properties.assert_called()
        mock_user_password.assert_called()

    def test_stop(self, mock_connection):
        # Prepare the context for stop operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.lifecycle.stop')
        server_instance = openstack.compute.v2.server.Server(**{
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

        stopped_server_instance = openstack.compute.v2.server.Server(**{
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
            'status': 'SHUTOFF',

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

        # Mock stop operation
        mock_connection().compute.stop_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.get_server = \
            mock.MagicMock(side_effect=[server_instance,
                                        stopped_server_instance,
                                        stopped_server_instance])

        # Mock get server interfaces operation
        mock_connection().compute.server_interfaces = \
            mock.MagicMock(return_value=server_interfaces)

        # Mock get server interfaces operation
        mock_connection().compute.delete_server_interface = \
            mock.MagicMock(return_value=None)

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Stop the server
        server.stop()

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_STOP,
            self._ctx.instance.runtime_properties)

    def test_reboot(self, mock_connection):
        # Prepare the context for reboot operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.lifecycle.reboot')
        server_instance = openstack.compute.v2.server.Server(**{
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

        rebooted_server_instance = openstack.compute.v2.server.Server(**{
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
            'status': 'REBOOT',

        })

        # Mock stop operation
        mock_connection().compute.reboot_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.get_server = \
            mock.MagicMock(side_effect=[server_instance,
                                        rebooted_server_instance])

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'
        self._ctx.operation.retry = mock.Mock(side_effect=OperationRetry())

        with self.assertRaises(OperationRetry):
            # Reboot the server
            server.reboot()
        self._ctx.operation.retry.assert_called_with(
            message='Server has REBOOT state. Waiting.', retry_after=30)

    def test_suspend(self, mock_connection):
        # Prepare the context for suspend operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.freeze.suspend')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Mock suspend operation
        mock_connection().compute.suspend_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Call suspend
        server.suspend()

    def test_resume(self, mock_connection):
        # Prepare the context for resume operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.freeze.resume')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Mock resume operation
        mock_connection().compute.resume_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Call resume
        server.resume()

    def test_create_snapshot(self, mock_connection):
        # Prepare the context for snapshot create operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.create')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[])

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_create(**snapshot_params)

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_BACKUP_DONE,
            self._ctx.instance.runtime_properties)

    def test_create_backup(self, mock_connection):
        # Prepare the context for backup create operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.create')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Mock backup operation
        mock_connection().compute.create_image = \
            mock.MagicMock(return_value=None)

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[])

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True,
            'snapshot_rotation': 2,
            'snapshot_type': 'Daily'
        }
        server.snapshot_create(**snapshot_params)

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_BACKUP_DONE,
            self._ctx.instance.runtime_properties)

    def test_apply_snapshot(self, mock_connection):
        # Prepare the context for snapshot apply operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.apply')

        server_instance = openstack.compute.v2.server.Server(**{
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
        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', False)
        image = openstack.image.v2.image.Image(**{
            'id': '1',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[image])

        # Set runtime properties for apply snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_PENDING
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_apply(**snapshot_params)

    def test_apply_backup(self, mock_connection):
        # Prepare the context for backup apply operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.apply')

        server_instance = openstack.compute.v2.server.Server(**{
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
        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', True)
        image = openstack.image.v2.image.Image(**{
            'id': '1',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[image])

        # Set runtime properties for apply snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_PENDING
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True
        }
        server.snapshot_apply(**snapshot_params)

    def test_delete_snapshot(self, mock_connection):
        # Prepare the context for snapshot delete operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.delete')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'
        # Set runtime properties for snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', False)
        image = openstack.image.v2.image.Image(**{
            'id': '1',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(side_effect=[[image], []])

        # Mock list image operation
        mock_connection().image.delete_image = \
            mock.MagicMock(return_value=None)

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_delete(**snapshot_params)

        for attr in [SERVER_TASK_RESTORE_STATE,
                     SERVER_ACTION_STATUS_DONE,
                     SERVER_TASK_STOP,
                     SERVER_TASK_START]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_delete_backup(self, mock_connection):
        # Prepare the context for snapshot delete backup
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.snapshot.delete')
        server_instance = openstack.compute.v2.server.Server(**{
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

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'
        # Set runtime properties for snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', True)
        image = openstack.image.v2.image.Image(**{
            'id': '1',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock get server operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(side_effect=[[image], []])

        # Mock list image operation
        mock_connection().image.delete_image = \
            mock.MagicMock(return_value=None)

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True
        }
        server.snapshot_delete(**snapshot_params)

        for attr in [SERVER_TASK_RESTORE_STATE,
                     SERVER_TASK_BACKUP_DONE,
                     SERVER_TASK_STOP,
                     SERVER_TASK_START]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    @mock.patch(
        'openstacksdk_plugin.resources.compute.server.wait_until_status')
    def test_attach_volume(self, mock_wait_status, mock_connection):
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '2'
            }})

        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '1',
                'volume_id': '3',
                'attachment_id': '4',
            })

        attachment_task_key = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_TASK,
                                           'volume-1', 'server-1')

        attachment_task_id = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                           'volume-1', 'server-1')

        mock_wait_status.return_value = volume_attachment

        # Mock list image operation
        mock_connection().compute.create_volume_attachment = \
            mock.MagicMock(return_value=volume_attachment)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.attach_volume()

        # Check if the resource id is already set or not
        self.assertIn(
            attachment_task_id,
            self._ctx.target.instance.runtime_properties)

        self.assertNotIn(
            attachment_task_key,
            self._ctx.target.instance.runtime_properties)

    @mock.patch(
        'openstacksdk_plugin.resources.compute.server.wait_until_status')
    def test_detach_volume(self, mock_wait_status, mock_connection):
        attachment_task_id = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                           'volume-1', 'server-1')

        detachment_task_key = \
            generate_attachment_volume_key(VOLUME_DETACHMENT_TASK,
                                           'volume-1', 'server-1')
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    attachment_task_id: '1'
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '2'
            }})

        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '1',
                'volume_id': '3',
                'attachment_id': '4',
            })

        mock_wait_status.return_value = volume_attachment

        # Mock list image operation
        mock_connection().compute.delete_volume_attachment = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.detach_volume()

        self.assertNotIn(
            detachment_task_key,
            self._ctx.target.instance.runtime_properties)

    def test_connect_floating_ip(self, mock_connection):
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        # Mock list image operation
        mock_connection().compute.add_floating_ip_to_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.connect_floating_ip(floating_ip='10.2.3.4')

    def test_disconnect_floating_ip(self, mock_connection):
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        # Mock list image operation
        mock_connection().compute.remove_floating_ip_from_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.disconnect_floating_ip(floating_ip='10.2.3.4')

    def test_connect_security_group(self, mock_connection):
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        # Mock list image operation
        mock_connection().compute.add_security_group_to_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.connect_security_group(security_group_id='1')

    @mock.patch(
        'openstacksdk_plugin.resources.compute.'
        'server._disconnect_security_group_from_server_ports')
    def test_disconnect_security_group(self,
                                       mock_clean_ports,
                                       mock_connection):
        target = MockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = MockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    'server': {
                        'name': 'test',
                        'security_groups': [
                            {
                                'id': '1'
                            },
                            {
                                'id': '2'
                            }
                        ]
                    }
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        # Mock list image operation
        mock_connection().compute.remove_security_group_from_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            node_id='1')

        # Call trigger attach volume
        server.disconnect_security_group(security_group_id='1')
        mock_clean_ports.assert_called()

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.lifecycle.delete')
        server_instance = openstack.compute.v2.server.Server(**{
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
        # Mock delete operation
        mock_connection().compute.delete_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=server_instance)

        # Set resource id as runtime properties
        self._ctx.instance.runtime_properties['id'] = '1'

        # Call delete server operation
        with self.assertRaises(OperationRetry):
            server.delete()
            # Check if the resource id is already set or not
            self.assertIn(
                SERVER_TASK_DELETE,
                self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.operations.update')
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
        mock_connection().compute.get_server = \
            mock.MagicMock(return_value=old_server)
        mock_connection().compute.update_server = \
            mock.MagicMock(return_value=new_server)

        server.update(args=new_config)

        # Check if the server payload is assigned for the created server
        self.assertIn(
            SERVER_OPENSTACK_TYPE,
            self._ctx.instance.runtime_properties)

        # Compare old name value against updated name
        self.assertNotEqual(
            self._ctx.instance.runtime_properties[SERVER_OPENSTACK_TYPE][
                'name'], old_server.name)

    def list_servers(self, mock_connection):
        # Prepare the context for list servers operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.operations.list')
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

        mock_connection().compute.servers = \
            mock.MagicMock(return_value=server_list)

        # Call list servers
        server.list_servers()

        # Check if the server list saved as runtime properties
        self.assertIn(
            'server_list',
            self._ctx.instance.runtime_properties)

        # Check the size of server list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['server_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation servers operation
        self._prepare_context_for_operation(
            node_id='ServerTestCase',
            operation_name='cloudify.interfaces.validation.creation')
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

        # Mock the server list API
        mock_connection().compute.servers = \
            mock.MagicMock(return_value=server_list)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        server.creation_validation()
