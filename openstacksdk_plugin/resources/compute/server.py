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
import json

# Third party imports
from cloudify import ctx
from openstack import exceptions
from cloudify.exceptions import (OperationRetry,
                                 NonRecoverableError)

# Local imports
from openstack_sdk.resources.compute import OpenstackServer
from openstack_sdk.resources.images import OpenstackImage
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
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
                                           SERVER_GROUP_TYPE,
                                           SERVER_REBOOT_HARD,
                                           SERVER_REBOOT_SOFT,
                                           SERVER_ACTION_STATUS_PENDING,
                                           SERVER_ACTION_STATUS_DONE,
                                           SERVER_REBUILD_SPAWNING,
                                           SERVER_REBUILD_STATUS,
                                           IMAGE_UPLOADING_PENDING,
                                           IMAGE_STATUS_ACTIVE,
                                           IMAGE_UPLOADING,
                                           SERVER_TASK_STATE,
                                           INSTANCE_OPENSTACK_TYPE)

from openstacksdk_plugin.utils import (handle_userdata,
                                       validate_resource,
                                       add_resource_list_to_runtime_properties,
                                       find_relationship_by_node_type,
                                       reset_dict_empty_keys,
                                       get_resource_id_from_runtime_properties,
                                       get_snapshot_name)


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
                server.status), retry_after=30)

        else:
            ctx.logger.info('Server is already stopped')
            ctx.instance.runtime_properties[SERVER_TASK_STOP] \
                = SERVER_ACTION_STATUS_DONE
    else:
        ctx.logger.info('Server is already stopped')
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
        find_relationship_by_node_type(ctx.instance, SERVER_GROUP_TYPE)

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
        is_finished = _check_finished_server_task(server,
                                                  [SERVER_REBUILD_SPAWNING])

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


@with_openstack_resource(OpenstackServer)
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

        # Handle server group
        _handle_server_group(openstack_resource)

        # Create resource
        created_resource = openstack_resource.create()

        # Set the "id" as a runtime property for the created server
        ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id

        # Update the resource_id with the new "id" returned from API
        openstack_resource.resource_id = created_resource.id
    else:
        resource_id = ctx.instance.runtime_properties[RESOURCE_ID]
        openstack_resource.resource_id = resource_id

    # Get the details for the created servers instance
    server = openstack_resource.get()

    # Get the server status
    status = server.status
    if server.status != SERVER_STATUS_ACTIVE:
        ctx.instance.runtime_properties[SERVER_TASK_CREATE] = True
        raise OperationRetry(
            message='Waiting for server to be in {0} state but is in {1} '
                    'state. Retrying...'.format(SERVER_STATUS_ACTIVE, status))


@with_openstack_resource(OpenstackServer)
def start(openstack_resource):
    """
    Populate required runtime properties for server when it is in active status
    :param openstack_resource: instance of openstack server resource
    """
    # Get the details for the created servers instance
    server = openstack_resource.get()

    # Get the server status
    status = server.status
    if status == SERVER_STATUS_ACTIVE:
        ctx.logger.info('Server is already started')
        _set_server_ips_runtime_properties(server)

        # The password returned from `Win` instances return always empty
        res = openstack_resource.get_server_password()
        password = json.loads(res.content) if res.content else None
        ctx.instance.runtime_properties['password'] = password
        return


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
        ctx.logger.info(msg)
        raise NonRecoverableError(msg)

    # Check if delete operation triggered or not before
    if SERVER_TASK_DELETE not in ctx.instance.runtime_properties:
        openstack_resource.delete()
        ctx.instance.runtime_properties[SERVER_TASK_DELETE] = True

    ctx.logger.info('Waiting for server "{0}" to be deleted.'
                    ' current status: {1}'.format(server.id, server.status))

    raise OperationRetry(message='Server has {} state.'.format(server.status))


@with_openstack_resource(OpenstackServer)
def stop(openstack_resource):
    """
    Stop current openstack server
    :param openstack_resource: instance of openstack server resource
    """
    # Get the details for server instance
    server = openstack_resource.get()

    # Stop server instance
    _stop_server(server)


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
def update(openstack_resource, args):
    """
    Update openstack server by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack server resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackServer)
def list_servers(openstack_resource, query, all_projects=False, details=True):
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
    servers = openstack_resource.list(details, all_projects, **query)
    add_resource_list_to_runtime_properties(SERVER_OPENSTACK_TYPE, servers)


@with_openstack_resource(OpenstackServer)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create server resource in openstack
    :param openstack_resource: Instance of current openstack server
    """
    validate_resource(openstack_resource, INSTANCE_OPENSTACK_TYPE)
    ctx.logger.debug('OK: server configuration is valid')
