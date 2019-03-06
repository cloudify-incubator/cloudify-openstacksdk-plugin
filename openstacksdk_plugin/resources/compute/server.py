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
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64

# Third party imports
from cloudify import ctx
from openstack import exceptions
from cloudify.exceptions import (OperationRetry,
                                 NonRecoverableError)

# Local imports
from openstack_sdk.resources.compute import OpenstackServer
from openstack_sdk.resources.compute import OpenstackKeyPair
from openstack_sdk.resources.images import OpenstackImage
from openstack_sdk.resources.volume import OpenstackVolume
from openstack_sdk.resources.networks import OpenstackPort
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           OPENSTACK_RESOURCE_UUID,
                                           SERVER_STATUS_ACTIVE,
                                           SERVER_STATUS_SHUTOFF,
                                           SERVER_STATUS_REBOOT,
                                           SERVER_STATUS_HARD_REBOOT,
                                           SERVER_STATUS_UNKNOWN,
                                           SERVER_STATUS_ERROR,
                                           SERVER_TASK_CREATE,
                                           SERVER_TASK_DELETE,
                                           SERVER_TASK_STOP,
                                           SERVER_TASK_START,
                                           SERVER_TASK_RESTORE_STATE,
                                           SERVER_TASK_BACKUP_DONE,
                                           SERVER_OPENSTACK_TYPE,
                                           SERVER_GROUP_NODE_TYPE,
                                           SERVER_REBOOT_HARD,
                                           SERVER_REBOOT_SOFT,
                                           SERVER_ACTION_STATUS_PENDING,
                                           SERVER_ACTION_STATUS_DONE,
                                           SERVER_REBUILD_SPAWNING_STATUS,
                                           SERVER_REBUILD_STATUS,
                                           SERVER_TASK_STATE,
                                           SERVER_INTERFACE_IDS,
                                           SERVER_ADMIN_PASSWORD,
                                           IMAGE_UPLOADING_PENDING,
                                           IMAGE_STATUS_ACTIVE,
                                           IMAGE_UPLOADING,
                                           INSTANCE_OPENSTACK_TYPE,
                                           VOLUME_DEVICE_NAME_PROPERTY,
                                           VOLUME_OPENSTACK_TYPE,
                                           VOLUME_STATUS_IN_USE,
                                           VOLUME_STATUS_AVAILABLE,
                                           VOLUME_ERROR_STATUSES,
                                           VOLUME_ATTACHMENT_TASK,
                                           VOLUME_DETACHMENT_TASK,
                                           VOLUME_ATTACHMENT_ID,
                                           VOLUME_BOOTABLE,
                                           KEYPAIR_NODE_TYPE,
                                           PORT_OPENSTACK_TYPE,
                                           KEYPAIR_OPENSTACK_TYPE,
                                           NETWORK_OPENSTACK_TYPE,
                                           OPENSTACK_PORT_ID,
                                           OPENSTACK_NETWORK_ID,
                                           OPENSTACK_TYPE_PROPERTY,
                                           USE_EXTERNAL_RESOURCE_PROPERTY)

from openstacksdk_plugin.utils import \
    (handle_userdata,
     validate_resource_quota,
     wait_until_status,
     add_resource_list_to_runtime_properties,
     find_relationship_by_node_type,
     find_openstack_ids_of_connected_nodes_by_openstack_type,
     reset_dict_empty_keys,
     get_resource_id_from_runtime_properties,
     get_snapshot_name,
     generate_attachment_volume_key,
     assign_resource_payload_as_runtime_properties)


def _stop_server(server):
    """
    Stop server instance
    :param server: Instance of openstack resource (OpenstackServer)
    """
    server_resource = server.get()
    if server_resource.status != SERVER_STATUS_SHUTOFF:
        # Trigger stop server API only if it is not stopped before
        if SERVER_TASK_STOP not in ctx.instance.runtime_properties:
            server.stop()
            ctx.instance.runtime_properties[SERVER_TASK_STOP]\
                = SERVER_ACTION_STATUS_PENDING

        # Get the server instance to check the status of the server
        server_resource = server.get()
        if server_resource.status != SERVER_STATUS_SHUTOFF:
            raise OperationRetry(message='Server has {} state.'.format(
                server_resource.status), retry_after=30)

        else:
            ctx.logger.info('Server {0} is already stopped'
                            ''.format(server.resource_id))
            ctx.instance.runtime_properties[SERVER_TASK_STOP] \
                = SERVER_ACTION_STATUS_DONE
    else:
        ctx.logger.info('Server {0} is already stopped'
                        ''.format(server.resource_id))
        ctx.instance.runtime_properties[SERVER_TASK_STOP]\
            = SERVER_ACTION_STATUS_DONE


def _start_server(server):
    """
    Start server instance
    :param server: Instance of openstack resource (OpenstackServer)
    """
    server_resource = server.get()
    if server_resource.status != SERVER_STATUS_ACTIVE:
        # Trigger stop server API only if it is not stopped before
        if SERVER_TASK_START not in ctx.instance.runtime_properties:
            server.start()
            ctx.instance.runtime_properties[SERVER_TASK_START]\
                = SERVER_ACTION_STATUS_PENDING

        # Get the server instance to check the status of the server
        server = server.get()
        if server.status != SERVER_STATUS_ACTIVE:
            raise OperationRetry(message='Server has {} state.'.format(
                server.status), retry_after=30)

        else:
            ctx.logger.info('Server is already started')
            ctx.instance.runtime_properties[SERVER_TASK_START] \
                = SERVER_ACTION_STATUS_DONE

    else:
        ctx.logger.info('Server is already started')
        ctx.instance.runtime_properties[SERVER_TASK_START]\
            = SERVER_ACTION_STATUS_DONE


def _set_server_ips_runtime_properties(server):
    """
    Populate required runtime properties from server in order to have all
    the information related to ips
    :param server: instance of openstack server
    `~openstack.compute.v2.server.Server
    """
    addresses = server.addresses
    if not addresses:
        return None

    ipv4_addresses = []
    ipv6_addresses = []

    for network, addresses in addresses.iteritems():
        for address in addresses:
            # ip config
            ipv4 = dict()
            ipv4['addr'] = address['addr']
            ipv4['type'] = address['OS-EXT-IPS:type']

            # Check where `ip_config` should be added
            if address['version'] == 4:
                ipv4_addresses.append(ipv4)
            elif address['version'] == 6:
                ipv6_addresses.append(address['addr'])

    # Check if access_ipv4 is set or not
    if server.access_ipv4:
        ctx.instance.runtime_properties['access_ipv4'] = server.access_ipv4

    # Check if access_ipv6 is set or not
    if server.access_ipv6:
        ctx.instance.runtime_properties['access_ipv6'] = server.access_ipv6

    # If "ipv4_addresses" is only contains one item, them we need to check
    # both private/public ip in order to set them as part of runtime_properties
    for ipv4 in ipv4_addresses:
        ip = ipv4['addr']

        # Only set the first "ip" as runtime property
        if ipv4['type'] == 'fixed'\
                and 'ip' not in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties['ip'] = ip

        # Only set the first "public_ip_address" as runtime property
        elif ipv4['type'] == 'floating'\
                and 'public_ip_address' not in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties['public_ip_address'] = ip

    for ipv6 in ipv6_addresses:
        ip_v6 = ipv6['addr']

        # Only set the first "ipv6" as runtime property
        if ipv6['type'] == 'fixed' \
                and 'ipv6' not in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties['ipv6'] = ip_v6

        # Only set the first "public_ip6_address" as runtime property
        elif ipv6['type'] == 'floating'\
                and 'public_ip6_address' not in\
                    ctx.instance.runtime_properties:
            ctx.instance.runtime_properties['public_ip6_address'] = ip_v6

    # Check to see if "use_public_ip" is set or not in order to update the
    # "ip" to use the public address
    if ctx.node.properties['use_public_ip']:
        pip = ctx.instance.runtime_properties.get('public_ip_address')
        if pip:
            ctx.instance.runtime_properties['ip'] = pip

    elif ctx.node.properties.get('use_ipv6_ip', False) and ipv6_addresses:
        ip_v6 = ctx.instance.runtime_properties['ipv6']
        ctx.instance.runtime_properties['ip'] = ip_v6

    # Get list of all ipv4 associated with server
    ipv4_list = map(lambda ipv4_conf: ipv4_conf['addr'], ipv4_addresses)

    # Get list of all ipv6 associated with server
    ipv6_list = map(lambda ipv6_conf: ipv6_conf['addr'], ipv6_addresses)

    ctx.instance.runtime_properties['ipv4_addresses'] = ipv4_list
    ctx.instance.runtime_properties['ipv6_addresses'] = ipv6_list


def _log_snapshot_message(resource_id,
                          snapshot_name,
                          snapshot_incremental):
    """
    Log message for backup operation
    :param str resource_id: Server resource id
    :param str snapshot_name: Server snapshot name
    :param bool snapshot_incremental: Flag to create an incremental snapshots
     or full backup
    """
    # Decide what is the backup type
    backup_type = 'snapshot' if snapshot_incremental else 'backup'

    # Format message to be logged when applying this task
    backup_msg = 'Apply {0} {1} for {2}' \
                 ''.format(backup_type, snapshot_name, resource_id)

    # Log message when start the snapshot restore operation
    ctx.logger.info(backup_msg)


def _handle_server_group(openstack_resource):
    """
    Associate server with server group if it is provided via the
    configuration in order to prepare and send them with the request
    :param openstack_resource: instance of openstack resource (OpenstackServer)
    """
    server_group_rel = \
        find_relationship_by_node_type(ctx.instance, SERVER_GROUP_NODE_TYPE)

    if server_group_rel:
        server_group_id = \
            get_resource_id_from_runtime_properties(server_group_rel.target)

        scheduler_hints = \
            openstack_resource.config.get('scheduler_hints', {})
        scheduler_hints['group'] = server_group_id
        openstack_resource.config['scheduler_hints'] = scheduler_hints


def _handle_generate_snapshot(server,
                              snapshot_name,
                              snapshot_type,
                              snapshot_rotation,
                              snapshot_incremental):
    """
    This method will generate snapshot for server
    :param server: instance of openstack resource (OpenstackServer)
    :param str snapshot_name: Snapshot name
    :param str snapshot_type: Snapshot type e.g (daily, weekly)
    :param int snapshot_rotation: Snapshot rotation period
    :param bool snapshot_incremental: Flag to create an incremental snapshots
     or full backup
    """

    # # we save backupstate for get last state of creation
    backup_done = ctx.instance.runtime_properties.get(SERVER_TASK_BACKUP_DONE)
    if not backup_done:
        if not snapshot_incremental:
            server.backup(snapshot_name, snapshot_type, snapshot_rotation)
            ctx.logger.info(
                'Server backup {0} creation started'.format(snapshot_name))
        else:
            server.create_image(snapshot_name)
            ctx.logger.info('Server snapshot {} creation started'
                            .format(snapshot_name))

        # Set initial value for backup status
        ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE] \
            = SERVER_ACTION_STATUS_PENDING

    # Wait for finish upload
    is_finished = \
        _check_finished_server_task(server,
                                    [IMAGE_UPLOADING,
                                     IMAGE_UPLOADING_PENDING])

    if is_finished:
        ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE]\
            = SERVER_ACTION_STATUS_DONE


def _handle_snapshot_restore(server, image_id, snapshot_name):
    """
    This method will handle the actual snapshot restore for certain image
    :param server: instance of openstack server resource (OpenstackServer)
    :param str image_id: Image id that should we restore from
    :param str snapshot_name: Snapshot name
    """
    # Get the restore state
    restore_state =\
        ctx.instance.runtime_properties.get(SERVER_TASK_RESTORE_STATE)

    # Get the server status in order to decide to stop it or not
    server_status = ctx.instance.runtime_properties.get(SERVER_TASK_STOP)

    # If restore is not set then we need to stop it and then try to rebuild
    # the server after server stopped successfully
    if not restore_state:
        # Stop server before rebuild it
        _stop_server(server)

        # Get the server status in order to decide to stop it or not
        server_status = ctx.instance.runtime_properties.get(SERVER_TASK_STOP)

        # Only continue to next step if the server status is actually
        # stopped, so that we can rebuild the server
        if server_status == SERVER_ACTION_STATUS_DONE:
            ctx.logger.info(
                'Rebuild {0} with {1}'.format(
                    server.resource_id, snapshot_name)
            )

            # Rebuild server after server stopped successfully
            server.rebuild(image=image_id)

            # Set the initial status of restore state
            ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE] \
                = SERVER_ACTION_STATUS_PENDING

    # Only check this logic if the server is already stopped
    if server_status == SERVER_ACTION_STATUS_DONE:
        # Check if the rebuild task is done or not
        is_finished = \
            _check_finished_server_task(server,
                                        [SERVER_REBUILD_SPAWNING_STATUS])

        if is_finished:
            ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
                = SERVER_REBUILD_STATUS

            # Try to start server to be available for usage
            _start_server(server)

            server_status = ctx.instance.runtime_properties[SERVER_TASK_START]
            if server_status == SERVER_ACTION_STATUS_DONE:
                ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
                    = SERVER_ACTION_STATUS_DONE


def _get_image(image_resource, snapshot_name):
    """
    Get target image based on its name (snapshot name)
    :param image_resource: instance of openstack image resource
    (OpenstackImage)
    :param str snapshot_name: The snapshot name
    :return: instance of openstack image openstack.compute.v2.image.ImageDetail
    """
    for image in image_resource.list(query={'name': snapshot_name}):
        ctx.logger.info('Found image {0}'.format(repr(image)))
        if image.name == snapshot_name:
            return image

    return None


def _check_finished_server_task(server_resource, waiting_list):
    """
    Check if the current server task is done or not
    :param server_resource: instance of openstack server resource
     (OpenstackServer)
    :param waiting_list: list of status that should be checked on
    :return: True if task is done, otherwise this should be retired again
    """
    ctx.logger.info("Check server task state....")

    server = server_resource.get()
    state = getattr(server, SERVER_TASK_STATE)
    if state not in waiting_list:
        return True

    return ctx.operation.retry(
        message='Server has {0}/{1} state.'
                ''.format(server.status, state), retry_after=30)


def _get_bootable_indexed_volumes(mapping_devices):
    """
    This method will retrieve all bootable devices from mapping device list
    in order to determine which device will be marked as bootable to the server
    :param list mapping_devices: List of `block_device_mapping_v2` object
    which is part of server config object
    :return: List of bootable indexed volumes
    """
    bootable_devices = None
    if mapping_devices:
        # Get the bootable devices which have boot_index specified
        bootable_devices = [
            device for device in mapping_devices if device.get('boot_index')
        ]
        # Check if there are bootable indexed volumes
        if bootable_devices:
            # Sort them in descending order in order to track the last index
            # of bootable device
            bootable_devices = sorted(bootable_devices,
                                      reverse=True,
                                      key=lambda x: x.get('boot_index'))

    return bootable_devices


def _get_boot_volume_targets():
    """
    This method will lookup all volume bootable targets associated with
    servers
    :return: This will return list of all target volume nodes associated
    with server so that we can use them for define bootable devices
    """
    targets = []
    for rel in ctx.instance.relationships:
        # Get runtime properties for target instance
        runtime_properties = rel.target.instance.runtime_properties
        # Check if the target instance openstack type is volume type and it
        # has bootable runtime property set on the target volume instance
        if runtime_properties.get(OPENSTACK_TYPE_PROPERTY)\
                == VOLUME_OPENSTACK_TYPE \
                and runtime_properties.get(VOLUME_BOOTABLE):

            # Add target to the list
            targets.append(rel.target)

    return targets


def _update_ports_config(server_config):
    """
    This method will try to update server config with port configurations
    using the relationships connected with server node
    :param dict server_config: The server configuration required in order to
    create the server instance using Openstack API
    """
    # Check to see if the network dict is provided on the server config
    # properties
    networks = server_config.get('networks', [])
    # Check if the server has already ports associated with its config so
    # that we can merge the different ports together
    server_ports = \
        [
            network[PORT_OPENSTACK_TYPE]
            for network in networks if network.get(PORT_OPENSTACK_TYPE)
        ]

    # Get the ports from relationships if they are existed
    port_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, PORT_OPENSTACK_TYPE)

    ports_to_add = []

    # if both are empty then server is not providing ports connection
    # neither via node properties nor via relationships and this will be
    # valid only one network created for the current tenant, the server will
    # attach automatically to that network
    if not (server_ports or port_ids):
        return
    # Try to merge them
    elif port_ids and server_ports:
        raise NonRecoverableError('Server can\'t both have the '
                                  '"networks" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    # Prepare the ports that should be added to the server networks
    for port_id in port_ids:
        ports_to_add.append({'port': port_id})

    # If server is not associated with any networks then we need to create
    # new networks object and attach port to it
    if not networks:
        server_config['networks'] = ports_to_add
    # If server already has networks object then we should update it with
    # the new ports that should be added to the server
    elif networks and isinstance(networks, list) and ports_to_add:
        server_config['networks'].extend(ports_to_add)


def _update_bootable_volume_config(server_config):
    """
    This method will help to get volume info from relationship
    :param server_config: The server configuration required in order to
    create the server instance using Openstack API
    """
    mapping_devices = server_config.get('block_device_mapping_v2', [])

    # Filter and get the uuids volume from block device mapping
    volume_uuids = [
        device['uuid'] for device in mapping_devices if device.get('uuid')
    ]
    # Get the indexed bootable devices
    bootable_devices = _get_bootable_indexed_volumes(mapping_devices)

    # Get the highest index from bootable devices
    boot_index = \
        bootable_devices[0]['boot_index'] if bootable_devices else None

    bootable_rel_volumes = []
    bootable_rel_uuids = []
    # Get the targets volume connected to the server
    volume_targets = _get_boot_volume_targets()
    for volume_target in volume_targets:
        resource_config = volume_target.node.properties.get('resource_config')
        volume_uuid = volume_target.instance.runtime_properties[RESOURCE_ID]

        # boot_index could be 0 and we do not need to valuate it as false
        # condition
        if boot_index is None:
            boot_index = 0
        else:
            boot_index += 1
        volume_device = {
            'boot_index': boot_index,
            'uuid': volume_uuid,
            'volume_size':  resource_config.get('size'),
            'device_name': volume_target.node.properties.get('device_name'),
            'source_type': 'volume',
            'delete_on_termination': False,
        }
        bootable_rel_volumes.append(volume_device)
        bootable_rel_uuids.append(volume_uuid)

    # if both are empty then server is not providing volumes connection
    # neither via node properties nor via relationships
    if not (bootable_rel_uuids or volume_uuids):
        return
    # Try to merge them
    elif bootable_rel_uuids and volume_uuids:
        raise NonRecoverableError('Server can\'t both have the '
                                  '"block_device_mapping_v2" property and be '
                                  'connected to a volume via a '
                                  'relationship at the same time')

    elif bootable_rel_uuids and not volume_uuids:
        mapping_devices = bootable_rel_volumes

    server_config['block_device_mapping_v2'] = mapping_devices


def _update_keypair_config(server_config):
    """
    This method will try to get key pair info connected with server node if
    there is any relationships
    :param server_config: The server configuration required in order to
    create the server instance using Openstack API
    """
    # Get the key name from server if it exists
    server_keyname = server_config.get('key_name')

    # Get the keyname from relationship if any
    rel_keyname = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, KEYPAIR_OPENSTACK_TYPE)
    # If server have two keyname from server node and from relationship then
    # we should raise error
    rel_keyname = rel_keyname[0] if rel_keyname else None
    if server_keyname and rel_keyname:
        raise NonRecoverableError('Server can\'t both have the '
                                  '"key_name" property and be '
                                  'connected to a keypair via a '
                                  'relationship at the same time')

    # At this point, only one of the keys will be set
    key_name = server_keyname or rel_keyname
    if key_name:
        server_config['key_name'] = key_name


def _update_networks_config(server_config):
    """
    This method will try to update server config with network configurations
    using the relationships connected with server node
    :param dict server_config: The server configuration required in order to
    create the server instance using Openstack API
    """

    # Check to see if the network dict is provided on the server config
    # properties
    networks = server_config.get('networks', [])
    # Check if the server has already networks associated with its config so
    # that we can merge the different networks together
    server_networks = \
        [
            network[OPENSTACK_RESOURCE_UUID]
            for network in networks if network.get(OPENSTACK_RESOURCE_UUID)
        ]

    # Get the networks from relationships if they are existed
    network_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)

    networks_to_add = []

    # if both are empty then server is not providing ports connection
    # neither via node properties nor via relationships and this will be
    # valid only one network created for the current tenant, the server will
    # attach automatically to that network
    if not (server_networks or network_ids):
        return
    # Try to merge them
    elif server_networks and network_ids:
        raise NonRecoverableError('Server can\'t both have the '
                                  '"networks" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    # Prepare the network uuids that should be added to the server networks
    for net_id in network_ids:
        networks_to_add.append({OPENSTACK_RESOURCE_UUID: net_id})

    # If server is not associated with any networks then we need to create
    # new networks object and attach network to it
    if not networks:
        server_config['networks'] = networks_to_add
    # If server already has networks object then we should update it with
    # the new networks that should be added to the server
    elif networks and isinstance(networks, list) and networks_to_add:
        server_config['networks'].extend(networks_to_add)


def _update_server_config(server_config):
    """
    This method will try to resolve if there are any nodes connected to the
    server node and try to use the configurations from nodes in order to
    help create server using these configurations
    :param dict server_config: The server configuration required in order to
    create the server instance using Openstack API
    """
    # Check if there are some ports configuration via relationships in order
    # to update server config
    _update_ports_config(server_config)

    # Check if there are some networks configuration in order to update
    # server config
    _update_networks_config(server_config)

    # Check if there are some bootable volumes via relationships in order
    # update server config
    _update_bootable_volume_config(server_config)

    # Check if there is a key pair connected to the server via relationship
    # so that we can update server config when create server instance
    _update_keypair_config(server_config)


def _validate_external_server_networks(openstack_resource, ports, networks):
    """
    This method will validate if we can attach ports and networks to an
    external server
    :param openstack_resource: An instance of OpenstackServer
    :param ports: List of ports uuid need to validate against them
    :param networks: List of networks uuid need to validate against them
    """
    interfaces = openstack_resource.server_interfaces()
    attached_ports = \
        [
            network[OPENSTACK_PORT_ID]
            for network in interfaces if network.get(OPENSTACK_PORT_ID)
        ]

    attached_networks = \
        [
            network[OPENSTACK_NETWORK_ID]
            for network in interfaces if network.get(OPENSTACK_NETWORK_ID)
        ]

    common_ports = set(attached_ports) & set(ports)
    common_networks = set(attached_networks) & set(networks)
    if common_networks or common_ports:
        raise NonRecoverableError(
            'Several ports/networks already connected to external server '
            '{0}: Networks - {1}; Ports - {2}'
            .format(openstack_resource.resource_id,
                    common_ports,
                    common_networks))


def _connect_keypair_to_external_server(server):
    """
    This method will validate if the connected keypair match the
    key already associated with the external server
    :param server: An instance of OpenstackServer
    """

    # Get list of ports associated with the external server
    keypair_rel = \
        find_relationship_by_node_type(ctx.instance, KEYPAIR_NODE_TYPE)

    # Prepare keypair instance
    keypair_instance = OpenstackKeyPair(client_config=server.client_config,
                                        logger=ctx.logger)

    if not keypair_rel:
        return
    # Get the keypair id from target relationship
    keypair_id = get_resource_id_from_runtime_properties(keypair_rel.target)
    # Get the node properties from target node
    keypair_node_properties = keypair_rel.target.node.properties
    # Raise NonRecoverableError error if the keypair node is not an external
    # resource
    if not keypair_node_properties.get(USE_EXTERNAL_RESOURCE_PROPERTY):
        raise NonRecoverableError(
            'Can\'t connect a new keypair node to a server node '
            'with \'{0}\'=True'.format(USE_EXTERNAL_RESOURCE_PROPERTY))

    keypair_instance.resource_id = keypair_id
    keypair = keypair_instance.get()
    if keypair_id != keypair.id:
        raise NonRecoverableError(
            'Expected external resources server {0} and keypair {1} to be '
            'connected'.format(server.id, keypair_id))


def _connect_networks_to_external_server(openstack_resource):
    """
    This method will try to connect networks to external server
    :param openstack_resource: Instance Of OpenstackServer in order to
    use it
    """
    # Prepare two lists for connected ports/networks in order to save them
    # as runtime properties so that we can remove them from server when run
    # stop operation
    added_interfaces = []

    # Get list of ports associated with the external server
    ports = \
        find_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx, PORT_OPENSTACK_TYPE)

    # Get list of ports associated with the external server
    networks = \
        find_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx, NETWORK_OPENSTACK_TYPE)

    # Validate if we can connect external server to the "ports" & "networks"
    _validate_external_server_networks(openstack_resource, ports, networks)

    # If we reach here that means we can connect ports & networks to the
    # external server and the validation passed successfully
    for port_id in ports:
        ctx.logger.info('Attaching port {0}...'.format(port_id))
        interface = \
            openstack_resource.create_server_interface({'port_id': port_id})
        ctx.logger.info(
            'Successfully attached port {0} to device (server) id {1}.'
            .format(port_id, openstack_resource.resource_id))
        added_interfaces.append(interface.id)

    # Check again the server after attaching the ports so that we can do
    # another check if already checked networks
    interfaces = openstack_resource.server_interfaces()
    attached_networks = \
        [
            network[OPENSTACK_NETWORK_ID]
            for network in interfaces if network.get(OPENSTACK_NETWORK_ID)
        ]

    for net_id in networks:
        if net_id not in attached_networks:
            ctx.logger.info('Attaching network {0}...'.format(net_id))
            interface = \
                openstack_resource.create_server_interface({'net_id': net_id})
            ctx.logger.info(
                'Successfully attached network {0} to device (server) id {1}.'
                .format(net_id, openstack_resource.resource_id))
            added_interfaces.append(interface.id)
        else:
            ctx.logger.info(
                'Skipping network {0} attachment, because it is already '
                'attached to device (server) id {1}.'
                .format(net_id, openstack_resource.resource_id))

    # Check if there are interfaces added to the external server and add
    # them as runtime properties
    if added_interfaces:
        ctx.instance.runtime_properties[SERVER_INTERFACE_IDS] =\
            added_interfaces

    # Set runtime properties for external server
    server = openstack_resource.get()
    _set_server_ips_runtime_properties(server)


def _connect_resources_to_external_server(openstack_resource):
    """
    This method will try to connect resources to external server
    :param openstack_resource: Instance Of OpenstackServer in order to
    use it
    """

    # Try to connect networks to external server
    _connect_networks_to_external_server(openstack_resource)

    # Validate external key pair connected to the external server
    _connect_keypair_to_external_server(openstack_resource)

    # Assign payload to server
    remote_server = openstack_resource.get()
    assign_resource_payload_as_runtime_properties(ctx,
                                                  remote_server,
                                                  SERVER_OPENSTACK_TYPE)


def _disconnect_resources_from_external_server(openstack_resource):
    """
    This method will disconnect networks from external server so that they
    can be removed without any issue
    :param openstack_resource: Instance Of OpenstackServer in order to
    use it
    """
    # Delete all interfaces added to the external server
    if SERVER_INTERFACE_IDS in ctx.instance.runtime_properties:
        interfaces = ctx.instance.runtime_properties.get(
            SERVER_INTERFACE_IDS, [])
        for interface in interfaces:
            openstack_resource.delete_server_interface(interface)
            ctx.logger.info(
                'Successfully detached network {0} to device (server) id {1}.'
                .format(interface, openstack_resource.resource_id))


def _get_server_private_key():
    """
    This method will check if server has connected to keypair
    so that we can get the private key content to use it for decryption
    operation for password generated when create server
    :return (st) private_key: Private key content
    """
    # Get the keyname from relationship if any
    rel_keyname = \
        find_relationship_by_node_type(ctx.instance, KEYPAIR_NODE_TYPE)
    if not rel_keyname:
        return None

    # Try to get the private key from keypair instance
    private_key = \
        rel_keyname.target.instance.runtime_properties.get('private_key')
    if not private_key:
        return None
    return private_key


def _decrypt_password(password, private_key):
    """
    This method will decrypt user password for server so that it can be used
    later on
    :param (str) password: Encrypted password
    :param (str) private_key: Private key
    :return (str) password: Return decrypted password
    """
    # Check if both password and private ket are provided
    if not (password or private_key):
        raise NonRecoverableError('Password and private key must'
                                  ' be both provided for password decryption')

    # Define variable to hold decrypted password
    decrypted_password = ''

    # Import the private key so that we can use it to decrypt password
    rsa_key = RSA.importKey(private_key)
    rsa_key = PKCS1_v1_5.new(rsa_key)

    # Decode password to base 64
    encrypted_password = base64.b64decode(password)

    # Do the encryption process
    chunk_size = 512
    offset = 0

    # keep loop going as long as we have chunks to decrypt
    while offset < len(encrypted_password):
        # The encrypted password chunk
        chunk_data = encrypted_password[offset: offset + chunk_size]

        # Append the decrypted password chunk to the overall decrypted
        # decrypted password
        error_decrypt = 'Error while trying to decrypt password'
        decrypted_password += rsa_key.decrypt(chunk_data, error_decrypt)

        # Increase the offset by chunk size
        offset += chunk_size

    return decrypted_password


def _get_user_password(openstack_resource):
    """
    This method will get the server password as encrypted for the current
    server
    :param openstack_resource: Instance Of OpenstackServer in order to
    use it
    """
    if ctx.node.properties.get('use_password'):
        # The current openstack sdk does not allow to send private key path
        # when trying to lookup the password which means the password
        # generated will be encrypted
        res = openstack_resource.get_server_password()
        password = json.loads(res.content) if res.content else None
        password = password['password'] if password.get('password') else None
        # If the password is not set then, again
        if not password:
            raise OperationRetry(
                message='Waiting for server to post generated password')
        else:
            # Encrypted password, in order to decrypt it, decrypt it manually
            private_key = _get_server_private_key()
            password = _decrypt_password(password, private_key)
            ctx.instance.runtime_properties[SERVER_ADMIN_PASSWORD] = password
            ctx.logger.info('Server has been set with a password')


def _disconnect_security_group_from_server_ports(client_config,
                                                 server_payload,
                                                 security_group_id):
    """
    This method will help to remove connection between port and security group
    Because when we attach security group to a server that has multiple
    ports connected to it, all the ports automatically are going to connect
    to the security group
    :param dict client_config: Openstack configuration required to connect
    to API
    :param dict server_payload: Server payload configuration from openstack
    :param str security_group_id: Security group ID
    """
    if server_payload:
        networks = server_payload.get('networks', [])
        server_ports = \
            [
                network[PORT_OPENSTACK_TYPE]
                for network in networks if network.get(PORT_OPENSTACK_TYPE)
            ]
        for port_id in server_ports:
            port = OpenstackPort(client_config=client_config,
                                 logger=ctx.logger)
            port.resource_id = port_id
            remote_port = port.get()
            port_security_groups = remote_port.security_group_ids
            if security_group_id in remote_port.security_group_ids:
                port_security_groups.remove(security_group_id)

            port.update({
                'security_groups': port_security_groups
            })


@with_openstack_resource(
    OpenstackServer,
    existing_resource_handler=_connect_resources_to_external_server)
def create(openstack_resource):
    """
    Create openstack server instance
    :param openstack_resource: instance of openstack server resource
    """
    if SERVER_TASK_CREATE not in ctx.instance.runtime_properties:
        blueprint_user_data = openstack_resource.config.get('user_data')
        user_data = handle_userdata(blueprint_user_data)

        # Handle user data
        if user_data:
            openstack_resource.config['user_data'] = user_data

        # Update server config by depending on relationships
        _update_server_config(openstack_resource.config)

        # Handle server group
        _handle_server_group(openstack_resource)

        # Create resource
        created_resource = openstack_resource.create()

        # Set the "id" as a runtime property for the created server
        ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id

        # Update the resource_id with the new "id" returned from API
        openstack_resource.resource_id = created_resource.id

        # Assign runtime properties for server
        assign_resource_payload_as_runtime_properties(ctx,
                                                      created_resource,
                                                      SERVER_OPENSTACK_TYPE)
    else:
        resource_id = ctx.instance.runtime_properties[RESOURCE_ID]
        openstack_resource.resource_id = resource_id


@with_openstack_resource(OpenstackServer)
def configure(openstack_resource):
    """
    Populate required runtime properties for server when it is in active status
    :param openstack_resource: instance of openstack server resource
    """
    # Get the details for the created servers instance
    server = openstack_resource.get()

    # Get the server status
    status = server.status
    if status == SERVER_STATUS_ACTIVE:
        ctx.logger.info('Server {0} is already started'.format(server.id))
        _set_server_ips_runtime_properties(server)
        _get_user_password(openstack_resource)
        return
    elif status == SERVER_STATUS_ERROR:
        raise NonRecoverableError(
            'Server {0} cannot be started, '
            'because it is on error state'.format(server.id))
    else:
        ctx.instance.runtime_properties[SERVER_TASK_CREATE] = True
        raise OperationRetry(
            message='Waiting for server to be in {0} state but is in {1} '
                    'state. Retrying...'.format(SERVER_STATUS_ACTIVE, status))


@with_openstack_resource(OpenstackServer)
def delete(openstack_resource):
    """
    Delete current openstack server
    :param openstack_resource: instance of openstack server resource
    """
    # Get the details for the created server instance
    try:
        server = openstack_resource.get()
    except exceptions.ResourceNotFound:
        msg = 'Server {0} is not found'.format(openstack_resource.resource_id)
        if SERVER_TASK_DELETE not in ctx.instance.runtime_properties:
            ctx.logger.error(msg)
            raise NonRecoverableError(msg)

        ctx.logger.info('Server {0} is deleted successfully'
                        .format(openstack_resource.resource_id))
        return

    # Check if delete operation triggered or not before
    if SERVER_TASK_DELETE not in ctx.instance.runtime_properties:
        openstack_resource.delete()
        ctx.instance.runtime_properties[SERVER_TASK_DELETE] = True

    ctx.logger.info('Waiting for server "{0}" to be deleted.'
                    ' current status: {1}'.format(server.id, server.status))

    raise OperationRetry(message='Server has {0} state.'.format(server.status))


@with_openstack_resource(
    OpenstackServer,
    existing_resource_handler=_disconnect_resources_from_external_server)
def stop(openstack_resource):
    """
    Stop current openstack server
    :param openstack_resource: instance of openstack server resource
    """

    # Clean any interfaces connected to the server
    for interface in openstack_resource.server_interfaces():
        openstack_resource.delete_server_interface(interface.id)
        ctx.logger.info('Successfully detached network'
                        ' {0} to device (server) id {1}.'
                        .format(interface, openstack_resource.resource_id))

    # Stop server instance
    _stop_server(openstack_resource)


@with_openstack_resource(OpenstackServer)
def reboot(openstack_resource, reboot_type='soft'):
    """
    This operation task is to rebot the current instance of the server
    :param openstack_resource: instance of openstack server resource
    :param str reboot_type: The type of reboot to perform.
                            "HARD" and "SOFT" are the current options.
    """
    if ctx.operation.retry_number == 0:
        if reboot_type.upper() not in [SERVER_REBOOT_HARD, SERVER_REBOOT_SOFT]:
            raise NonRecoverableError(
                'Unexpected reboot type: {}. '
                'Valid values: SOFT or HARD.'.format(reboot_type))
        openstack_resource.reboot(reboot_type.upper())

    # Get the details for the rebooted server instance
    server = openstack_resource.get()

    if server.status in [SERVER_STATUS_REBOOT,
                         SERVER_STATUS_HARD_REBOOT,
                         SERVER_STATUS_UNKNOWN]:
        return ctx.operation.retry(
            message="Server has {0} state. Waiting.".format(server.status),
            retry_after=30)

    elif server.status == SERVER_STATUS_ACTIVE:
        ctx.logger.info(
            'Reboot operation finished in {} state.'.format(server.status))

    elif server.status == SERVER_STATUS_ERROR:
        raise NonRecoverableError(
            'Reboot operation finished in {} state.'.format(
                server.status))

    else:
        raise NonRecoverableError(
            'Reboot operation finished in unexpected state: {}'.format(
                server.state))


@with_openstack_resource(OpenstackServer)
def suspend(openstack_resource):
    """
    Suspend server
    :param openstack_resource: instance of openstack server resource
    """
    ctx.logger.info('Suspend VM {}'.format(openstack_resource.resource_id))
    openstack_resource.suspend()


@with_openstack_resource(OpenstackServer)
def resume(openstack_resource):
    """
    Resume server
    :param openstack_resource: instance of openstack server resource
    """
    ctx.logger.info('Resume VM {}'.format(openstack_resource.resource_id))
    openstack_resource.resume()


@with_openstack_resource(OpenstackServer)
def snapshot_create(openstack_resource, **kwargs):
    """
    Create server backup.
    :param kwargs: snapshot information provided by workflow
    :param openstack_resource: instance of openstack server resource
    """
    ctx.logger.info('Create snapshot for {0}'.format(
        openstack_resource.resource_id))

    # Get snapshot information provided by workflow parameters
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_rotation = None
    if kwargs.get('snapshot_rotation'):
        snapshot_rotation = int(kwargs['snapshot_rotation'])

    snapshot_type = kwargs.get('snapshot_type')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Generate snapshot name
    snapshot_name = \
        get_snapshot_name('vm', snapshot_name, snapshot_incremental)

    # Create an instance if openstack image in order to check if the image
    # already exists or not
    image_resource = OpenstackImage(
        client_config=openstack_resource.client_config,
        logger=ctx.logger
    )

    # Try to lookup the image from openstack
    retry_number = ctx.operation.retry_number
    target_image = _get_image(image_resource, snapshot_name)

    # If retry_number == 0 and image exists then we should raise error,
    # otherwise if retry_number exceeds 0 then that means the image is still
    # uploading
    if retry_number == 0 and target_image:
        raise NonRecoverableError(
            'Snapshot {} already exists.'.format(snapshot_name))

    # Handle snapshot here
    _handle_generate_snapshot(openstack_resource,
                              snapshot_name,
                              snapshot_type,
                              snapshot_rotation,
                              snapshot_incremental)


@with_openstack_resource(OpenstackServer)
def snapshot_apply(openstack_resource, **kwargs):
    """
    Restore server from backup | snapshot.
    :param kwargs: snapshot information provided by workflow
    :param openstack_resource: instance of openstack server resource
    """
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Get the generated snapshot name
    snapshot_name = \
        get_snapshot_name('vm', snapshot_name, snapshot_incremental)

    _log_snapshot_message(openstack_resource.resource_id,
                          snapshot_name,
                          snapshot_incremental)

    # Create an instance if openstack image in order to check if the image
    # already exists or not
    image_resource = OpenstackImage(
        client_config=openstack_resource.client_config,
        logger=ctx.logger
    )

    # Check if the image need to be restored is existed
    target_image = _get_image(image_resource, snapshot_name)
    if not target_image:
        raise NonRecoverableError(
            'No snapshot found with name: {0}'.format(snapshot_name))

    _handle_snapshot_restore(openstack_resource,
                             target_image.id,
                             snapshot_name)


@with_openstack_resource(OpenstackServer)
def snapshot_delete(openstack_resource, **kwargs):
    """
    Delete server backup | snapshot.
    :param kwargs: snapshot information provided by workflow
    :param openstack_resource: instance of openstack server resource
    """
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Get the generated snapshot name
    snapshot_name = \
        get_snapshot_name('vm', snapshot_name, snapshot_incremental)

    # log the message for snapshot operation
    _log_snapshot_message(openstack_resource.resource_id,
                          snapshot_name,
                          snapshot_incremental)

    # Create an instance if openstack image in order delete uploaded image
    image_resource = OpenstackImage(
        client_config=openstack_resource.client_config,
        logger=ctx.logger
    )

    # Check if the image need to be deleted is existed
    target_image = _get_image(image_resource, snapshot_name)
    if not target_image:
        raise NonRecoverableError(
            'No snapshot found with name: {0}'.format(snapshot_name))

    if target_image.status == IMAGE_STATUS_ACTIVE:
        image_resource.resource_id = target_image.id
        image_resource.delete()

    # Check if the image need to be deleted is existed
    target_image = _get_image(image_resource, snapshot_name)
    if target_image:
        return ctx.operation.retry(
            message='{} is still alive'
                    ''.format(target_image.id), retry_after=30)
    else:
        # If image is remove then we need to reset the following
        # runtime properties:
        # - backup_done
        # - restore_state
        # - stop_server_task
        # - start_server_task

        # The reason for reset the above runtime properties is because of
        # the user want to start over again after running delete snapshot
        # operation # "cloudify.interfaces.snapshot.delete"
        for attr in [SERVER_TASK_BACKUP_DONE,
                     SERVER_TASK_RESTORE_STATE,
                     SERVER_TASK_STOP,
                     SERVER_TASK_START]:

            del ctx.instance.runtime_properties[attr]


@with_openstack_resource(OpenstackServer)
def attach_volume(openstack_resource, **kwargs):
    """
    This method will attach a volume to server
    :param openstack_resource: instance of openstack server resource
    :param kwargs: Additional information that could be provided via
    operation task inputs
    """
    # Get volume id from source instance
    volume_id = get_resource_id_from_runtime_properties(ctx.source)
    # Get the device property from volume node
    device = ctx.source.node.properties[VOLUME_DEVICE_NAME_PROPERTY]

    # Prepare volume attachment config required for adding attaching volume
    # to certain server
    attachment_config = {
        'volume_id': volume_id,
        'device': device if device != 'auto' else None
    }

    server_node_id = ctx.target.instance.id
    volume_node_id = ctx.source.instance.id
    attachment_task_key = \
        generate_attachment_volume_key(VOLUME_ATTACHMENT_TASK,
                                       volume_node_id,
                                       server_node_id)

    attachment_volume_id_key = \
        generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                       volume_node_id,
                                       server_node_id)
    # Create volume attachment
    if attachment_task_key not in ctx.target.instance.runtime_properties:
        attachment = \
            openstack_resource.create_volume_attachment(attachment_config)
        ctx.target.instance.runtime_properties[attachment_task_key] = True
        ctx.target.instance.runtime_properties[attachment_volume_id_key] = \
            attachment.id

    # Prepare volume instance in order to check the current status of the
    # volume being attached to the server
    volume_instance = OpenstackVolume(
        client_config=openstack_resource.client_config,
        logger=ctx.logger)
    volume_instance.resource_id = volume_id

    # Wait until final status of the attached volume becomes in-use so that
    # we can tell that the volume attachment is ready to use by the server
    volume = wait_until_status(volume_instance,
                               VOLUME_OPENSTACK_TYPE,
                               VOLUME_STATUS_IN_USE,
                               VOLUME_ERROR_STATUSES)
    # If the volume is ready, that means we do not need to keep the task
    # status anymore
    if volume:
        del ctx.target.instance.runtime_properties[attachment_task_key]


@with_openstack_resource(OpenstackServer)
def detach_volume(openstack_resource, **kwargs):
    """
    This method will detach a volume to server
    :param openstack_resource: instance of openstack server resource
    :param kwargs: Additional information that could be provided via
    operation task inputs
    """
    # Get volume id from source instance
    volume_id = get_resource_id_from_runtime_properties(ctx.source)

    # Get the ids for node, in order to generate the attachment volume key
    server_node_id = ctx.target.instance.id
    volume_node_id = ctx.source.instance.id

    # Attachment volume key
    attachment_volume_id_key = \
        generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                       volume_node_id,
                                       server_node_id)

    # Try to lookup the attachment volume id
    attachment_volume_id = \
        ctx.target.instance.runtime_properties.get(attachment_volume_id_key)
    if not attachment_volume_id:
        raise NonRecoverableError(
            'Attachment volume id {0} is missing'
            ' from runtime properties '.format(attachment_volume_id_key))

    # Detachment volume task key
    detachment_task_key = \
        generate_attachment_volume_key(VOLUME_DETACHMENT_TASK,
                                       volume_node_id,
                                       server_node_id)

    # Detach volume from server
    if detachment_task_key not in ctx.target.instance.runtime_properties:
        openstack_resource.delete_volume_attachment(attachment_volume_id)
        ctx.target.instance.runtime_properties[detachment_task_key] = True

    # Prepare volume instance in order to check the current status of the
    # volume being attached to the server
    volume_instance = OpenstackVolume(
        client_config=openstack_resource.client_config,
        logger=ctx.logger)
    volume_instance.resource_id = volume_id

    # Wait until final status of the attached volume becomes in-use so that
    # we can tell that the volume attachment is ready to use by the server
    volume = wait_until_status(volume_instance,
                               VOLUME_OPENSTACK_TYPE,
                               VOLUME_STATUS_AVAILABLE,
                               VOLUME_ERROR_STATUSES)

    # If the volume is available, that means we do not need to keep the task
    # status anymore
    if volume:
        del ctx.target.instance.runtime_properties[detachment_task_key]


@with_openstack_resource(OpenstackServer)
def connect_floating_ip(openstack_resource, floating_ip, fixed_ip=''):
    """
    This method will connect floating ip to server
    :param openstack_resource: Instance of openstack server resource
    :param str floating_ip: The floating IP
    :param str fixed_ip: The fixed IP address to be associated with the
    floating IP address. Used when the server is connected to multiple
    networks.
    """
    if not floating_ip:
        raise NonRecoverableError('floating_ip is required in order to '
                                  'connect floating ip to server {0}'
                                  ''.format(openstack_resource.resource_id))

    fixed_ip = fixed_ip or None
    openstack_resource.add_floating_ip_to_server(floating_ip,
                                                 fixed_ip=fixed_ip)


@with_openstack_resource(OpenstackServer)
def disconnect_floating_ip(openstack_resource, floating_ip):
    """
    This will disconnect floating ip address from server
    :param openstack_resource: Instance of openstack server resource
    :param floating_ip: The floating IP connetced to the server which should
    be disconnected
    """
    if not floating_ip:
        raise NonRecoverableError('floating_ip is required in order to '
                                  'disconnect floating ip from server {0}'
                                  ''.format(openstack_resource.resource_id))

    openstack_resource.remove_floating_ip_from_server(floating_ip)


@with_openstack_resource(OpenstackServer)
def connect_security_group(openstack_resource, security_group_id):
    """
    This method will connect security group to server
    :param openstack_resource: Instance of openstack server resource
    :param str security_group_id: The ID of a security group
    """
    if not security_group_id:
        raise NonRecoverableError('security_group_id is required in order to '
                                  'connect security group to server {0}'
                                  ''.format(openstack_resource.resource_id))

    openstack_resource.add_security_group_to_server(security_group_id)


@with_openstack_resource(OpenstackServer)
def disconnect_security_group(openstack_resource, security_group_id):
    """
    This will disconnect floating ip address from server
    :param openstack_resource: Instance of openstack server resource
    :param security_group_id: The ID of a security group
    """
    if not security_group_id:
        raise NonRecoverableError('security_group_id is required in order to '
                                  'disconnect security group from server {0}'
                                  ''.format(openstack_resource.resource_id))

    openstack_resource.remove_security_group_from_server(security_group_id)

    # Get the payload for server from runtime properties in order to get the
    # ports information attached to the server which will automatically
    # reference the disconnected security group which will cause an issue
    # when trying to delete security group, so we should break the
    # connection between the ports attached to the server and the security
    # group
    server_payload = \
        ctx.source.instance.runtime_properties.get(SERVER_OPENSTACK_TYPE)
    if server_payload:
        _disconnect_security_group_from_server_ports(
            openstack_resource.client_config,
            server_payload,
            security_group_id
        )


@with_openstack_resource(OpenstackServer)
def update(openstack_resource, args):
    """
    Update openstack server by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack server resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    updated_server = openstack_resource.update(args)
    # Update the runtime properties for the updated server
    assign_resource_payload_as_runtime_properties(ctx,
                                                  updated_server,
                                                  SERVER_OPENSTACK_TYPE)


@with_openstack_resource(OpenstackServer)
def list_servers(openstack_resource,
                 query=None,
                 all_projects=False,
                 details=True):
    """
    List openstack servers based on filters applied
    :param openstack_resource: Instance of current openstack server
    :param kwargs query: Optional query parameters to be sent to limit
            the servers being returned.
    :param bool all_projects: Flag to request servers be returned from all
                            projects, not just the currently scoped one.
    :param bool details: When set to ``False``
                :class:`~openstack.compute.v2.server.Server` instances
                will be returned. The default, ``True``, will cause
                :class:`~openstack.compute.v2.server.ServerDetail`
                instances to be returned.
    """
    servers = openstack_resource.list(details, all_projects, query)
    add_resource_list_to_runtime_properties(SERVER_OPENSTACK_TYPE, servers)


@with_openstack_resource(OpenstackServer)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create server resource in openstack
    :param openstack_resource: Instance of current openstack server
    """
    validate_resource_quota(openstack_resource, INSTANCE_OPENSTACK_TYPE)
    ctx.logger.debug('OK: server configuration is valid')
