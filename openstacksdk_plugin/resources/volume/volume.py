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
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


# Third party imports
from cloudify import ctx
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
import openstack.exceptions

# Local imports
from openstack_sdk.resources.volume import (OpenstackVolume,
                                            OpenstackVolumeBackup,
                                            OpenstackVolumeSnapshot)
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           OPENSTACK_AZ_PROPERTY,
                                           VOLUME_OPENSTACK_TYPE,
                                           IMAGE_OPENSTACK_TYPE,
                                           VOLUME_STATUS_AVAILABLE,
                                           VOLUME_ERROR_STATUSES,
                                           VOLUME_TASK_DELETE,
                                           VOLUME_BACKUP_TASK,
                                           VOLUME_SNAPSHOT_TASK,
                                           VOLUME_BACKUP_ID,
                                           VOLUME_SNAPSHOT_ID,
                                           VOLUME_BOOTABLE,
                                           VOLUME_BACKUP_OPENSTACK_TYPE,
                                           VOLUME_SNAPSHOT_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import\
    (validate_resource_quota,
     merge_resource_config,
     get_ready_resource_status,
     wait_until_status,
     get_snapshot_name,
     add_resource_list_to_runtime_properties,
     find_openstack_ids_of_connected_nodes_by_openstack_type)


def _populate_volume_with_image_id_from_relationship(volume_config):
    """
    This method will try to populate image id for volume if there is a
    relationship between volume & image
    """

    if volume_config:
        image_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx, IMAGE_OPENSTACK_TYPE)

        if image_ids:
            volume_config.update({'imageRef': image_ids[0]})


def _set_volume_runtime_properties(volume):
    """
    Set volume configuration as runtime properties so that it can be used
    when attach volume as bootable to server, so this configuration will be
    required when create a relationship between server and volume
    :param volume: Volume instance of openstack.volume.v2.volume.Volume
    """
    if volume:
        # Check if the availability_zone is set and part of the volume object
        if volume.availability_zone:
            ctx.instance.runtime_properties[OPENSTACK_AZ_PROPERTY] = \
                volume.availability_zone

        # Check if the volume is bootable so that we can set that as part og
        is_bootable = True if volume.is_bootable else False
        ctx.instance.runtime_properties[VOLUME_BOOTABLE] = is_bootable


def _prepare_volume_backup_instance(volume_resource, backup_config=None):
    """
    Prepare volume backup openstack instance so that we can use it to do
    backup volume
    :param volume_resource: instance of openstack volume resource
    :param dict backup_config: Snapshot config data
    :return: Return instance of openstack volume backup
    """

    # Prepare client config in order to apply backup
    client_config = volume_resource.client_config
    # Instance of backup volume
    backup = OpenstackVolumeBackup(client_config=client_config,
                                   logger=ctx.logger)
    if backup_config:
        backup.config = backup_config
    return backup


def _prepare_volume_snapshot_instance(volume_resource, snapshot_config=None):
    """
    Prepare volume snapshot openstack instance so that we can use it to do
    snapshot volume
    :param volume_resource: instance of openstack volume resource
    :param dict snapshot_config: Snapshot config data
    :return: Return instance of openstack volume snapshot
    """

    # Prepare client config in order to apply snapshot
    client_config = volume_resource.client_config
    # Instance of snapshot volume
    snapshot = OpenstackVolumeSnapshot(client_config=client_config,
                                       logger=ctx.logger)
    if snapshot_config:
        snapshot.config = snapshot_config

    return snapshot


def _create_volume_backup(volume_resource, backup_name):
    """
    This method will handle creating volume backup and make sure it is
    created successfully
    :param volume_resource: instance of openstack volume resource
    :param str backup_name: The backup name
    """
    # Prepare config for backup
    # Prepare config for backup
    backup_config = {
        'name': backup_name,
        'volume_id': volume_resource.resource_id
    }

    backup = _prepare_volume_backup_instance(volume_resource, backup_config)

    # Check if the backup id exists or not, if it exists that means the
    # backup volume created but still checking its status to make sure it
    # is ready to use
    if VOLUME_SNAPSHOT_ID in ctx.instance.runtime_properties:
        backup.resource_id = \
            ctx.instance.runtime_properties[VOLUME_BACKUP_ID]

    # Check if the backup call is called before or not, so that we can only
    # trigger it only once
    if VOLUME_BACKUP_TASK not in ctx.instance.runtime_properties:
        # Create backup
        backup_response = backup.create()
        backup_id = backup_response.id
        backup.resource_id = backup_id
        ctx.instance.runtime_properties[VOLUME_BACKUP_TASK] = True
        ctx.instance.runtime_properties[VOLUME_SNAPSHOT_ID] = backup_id

    backup_resource, ready = \
        get_ready_resource_status(backup,
                                  VOLUME_BACKUP_OPENSTACK_TYPE,
                                  VOLUME_STATUS_AVAILABLE,
                                  VOLUME_ERROR_STATUSES)

    if not ready:
        raise OperationRetry('Volume backup is still in {0} status'.format(
            backup_resource.status))
    else:
        del ctx.instance.runtime_properties[VOLUME_BACKUP_TASK]
        del ctx.instance.runtime_properties[VOLUME_BACKUP_ID]


def _create_volume_snapshot(volume_resource, snapshot_name, snapshot_type):
    """
    This method will handle creating volume snapshot and make sure it is
    created successfully
    :param volume_resource: instance of openstack volume resource
    :param str snapshot_name: The name of the snapshot
    :param str snapshot_type: The type of the snapshot
    """

    # Prepare config for snapshot
    snapshot_config = {
        'name': snapshot_name,
        'volume_id': volume_resource.resource_id,
        'force': True,
        'description': snapshot_type
    }

    # Get an instance of snapshot volume ready to create the desired
    # snapshot volume
    snapshot = \
        _prepare_volume_snapshot_instance(volume_resource, snapshot_config)

    # Check if the snapshot id exists or not, if it exists that mean the
    # snapshot volume created but still checking its status to make sure it
    # is ready to use
    if VOLUME_SNAPSHOT_ID in ctx.instance.runtime_properties:
        snapshot.resource_id = \
            ctx.instance.runtime_properties[VOLUME_SNAPSHOT_ID]

    # Check if the snapshot volume task exists or not, if it does not exist
    # that means, this is the first time we are running this operation task,
    # otherwise it still checking the status to make sure it is finished
    if VOLUME_SNAPSHOT_TASK not in ctx.instance.runtime_properties:
        # Create snapshot
        snapshot_response = snapshot.create()
        snapshot_id = snapshot_response.id
        snapshot.resource_id = snapshot_id
        ctx.instance.runtime_properties[VOLUME_SNAPSHOT_TASK] = True
        ctx.instance.runtime_properties[VOLUME_SNAPSHOT_ID] = snapshot_id

    # Check the status of the snapshot process
    snapshot_resource, ready = \
        get_ready_resource_status(snapshot,
                                  VOLUME_SNAPSHOT_OPENSTACK_TYPE,
                                  VOLUME_STATUS_AVAILABLE,
                                  VOLUME_ERROR_STATUSES)

    if not ready:
        raise OperationRetry('Volume snapshot is still in {0} status'.format(
            snapshot_resource.status))
    else:
        # Once the snapshot is ready to user, we should clear volume
        # snapshot task & snapshot volume id from runtime properties in order
        # to allow trigger the operation multiple times
        del ctx.instance.runtime_properties[VOLUME_SNAPSHOT_TASK]
        del ctx.instance.runtime_properties[VOLUME_SNAPSHOT_ID]


def _clean_volume_backups(backup_instance, backup_type, search_opts=None):
    """
    This method will clean all backups | snapshots volume based on provided
    backup type and on filter criteria
    :param backup_instance: This is an instance of volume backup or
    volume snapshot (OpenstackVolumeBackup | OpenstackVolumeSnapshot)
    required in order to clean all volume backups/snapshots
    :param str backup_type: The type of volume backup (Full backup or snapshot)
    :param dict search_opts: Search criteria used in order to lookup the
    backups
    """
    snapshot_name = search_opts.get('name')
    volume_id = search_opts.get('volume_id')
    if all([snapshot_name, volume_id, backup_instance]):
        # Right now list volume backup does not support to list backups
        # using backup name and volume id, so that we need to list all
        # volumes backups and then just do a compare to match the one we
        # need to delete
        for backup in backup_instance.list(query=search_opts):
            if backup.name == snapshot_name and backup.volume_id == volume_id:
                ctx.logger.debug(
                    'Check {0} before delete: {1}:{2}'
                    ' with state {3}'.format(backup_type, backup.id,
                                             backup.name, backup.status))

                # Check if the volume is ready to delete
                if backup.status == VOLUME_STATUS_AVAILABLE:
                    backup_instance.resource_id = backup.id
                    backup_instance.delete()
            else:
                continue

        for backup in backup_instance.list(query=search_opts):
            ctx.logger.debug('Check {0} after delete: {1}:{2} with state {3}'
                             .format(backup_type, backup.id,
                                     backup.name, backup.status))
            if backup.name == snapshot_name and backup.volume_id == volume_id:
                return ctx.operation.retry(
                    message='{0} is still alive'.format(backup.name),
                    retry_after=30)
    else:
        raise NonRecoverableError('Cannot clean volume backups without '
                                  'having volume_id, name and '
                                  'backup_instance variables set')


def _delete_volume_backup(volume_resource, snapshot_name):
    """
    This method will delete volume backup
    :param volume_resource: instance of openstack volume resource
    :param str snapshot_name: The name of the snapshot
    """
    search_opts = {
        'volume_id': volume_resource.resource_id,
        'name': snapshot_name
    }

    backup_volume = _prepare_volume_backup_instance(volume_resource)
    _clean_volume_backups(backup_volume,
                          VOLUME_BACKUP_OPENSTACK_TYPE,
                          search_opts)


def _delete_volume_snapshot(volume_resource, snapshot_name):
    """
    This method will delete volume snapshot
    :param volume_resource: instance of openstack volume resource
    :param str snapshot_name: The name of the snapshot
    """

    search_opts = {
        'volume_id': volume_resource.resource_id,
        'name': snapshot_name
    }

    snapshot_volume = _prepare_volume_snapshot_instance(volume_resource)
    _clean_volume_backups(snapshot_volume,
                          VOLUME_SNAPSHOT_OPENSTACK_TYPE,
                          search_opts)


def _restore_volume_from_backup(volume_resource, backup_name):
    """
    This method will use to restore volume backups
    :param volume_resource: instance of openstack volume resource
    :param str backup_name: The name of the backup
    """

    volume_id = volume_resource.resource_id
    backup_volume = _prepare_volume_backup_instance(volume_resource)
    # Since backup volume does not allow to filter backup volume, we are
    # iterating over all volume backup in order to match the backup name &
    # volume id so that we can restore it
    for backup in backup_volume.list():
        # if returned more than one backup, use first
        if backup.name == backup_name and backup.volume_id == volume_id:
            ctx.logger.debug(
                'Used first with {0} to {1}'.format(backup.id, volume_id))
            name = 'volume-restore-{0}'.format(backup_volume)
            backup.restore(backup.id, volume_id, name)
            break
    else:
        raise NonRecoverableError('No such {0} backup.'.format(backup_name))


@with_openstack_resource(OpenstackVolume)
def create(openstack_resource, args={}):
    """
    Create openstack volume instance
    :param openstack_resource: instance of openstack volume resource
    :param args User configuration that could merge/override with
    resource configuration
    """
    # Check to see if there are some configuration provided via operation
    # input so that we can merge them with volume config
    merge_resource_config(openstack_resource.config, args)

    # Before create volume we need to check if the current volume node has
    # no relationship with image node type, because if there is a
    # relationship with image then we need to get the image id from that
    # relationship
    _populate_volume_with_image_id_from_relationship(openstack_resource.config)

    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackVolume)
def start(openstack_resource, status_timeout=15, status_attempts=20,):
    """
    This opeeration task will try to check if the volume created is ready
    to use and available
    :param openstack_resource: current openstack volume instance
    :param int status_timeout: Number of seconds must wait before continue
    another try
    :param int status_attempts: Number of tries attempts in order to check the
    current status of resource
    """
    volume = wait_until_status(openstack_resource,
                               VOLUME_OPENSTACK_TYPE,
                               VOLUME_STATUS_AVAILABLE,
                               VOLUME_ERROR_STATUSES,
                               status_attempts,
                               status_timeout)

    # Set volume runtime properties needed when attach bootable volume to
    # server
    _set_volume_runtime_properties(volume)


@with_openstack_resource(OpenstackVolume)
def snapshot_create(openstack_resource, **kwargs):
    """
    Create volume backup.
    :param openstack_resource: instance of openstack volume resource
    :param kwargs: snapshot information provided by workflow
    """

    ctx.logger.info('Create snapshot for {0}'.format(
        openstack_resource.resource_id))

    # Get snapshot information provided by workflow parameters
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_type = kwargs.get('snapshot_type')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Generate snapshot name
    backup_name = \
        get_snapshot_name('volume', snapshot_name, snapshot_incremental)

    if not snapshot_incremental:
        # Create volume backup
        _create_volume_backup(openstack_resource, backup_name)
    else:
        # Create volume snapshot
        _create_volume_snapshot(openstack_resource, backup_name, snapshot_type)


@with_openstack_resource(OpenstackVolume)
def snapshot_apply(openstack_resource, **kwargs):
    """
    This operation task will restore volume from created volume backups
    :param openstack_resource: instance of openstack volume resource
    :param kwargs: snapshot information provided by workflow
    """
    # Get snapshot information provided by workflow parameters
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Generate snapshot name
    backup_name = \
        get_snapshot_name('volume', snapshot_name, snapshot_incremental)

    if not snapshot_incremental:
        _restore_volume_from_backup(openstack_resource, backup_name)
    else:
        raise NonRecoverableError('Apply snapshot is not supported')


@with_openstack_resource(OpenstackVolume)
def snapshot_delete(openstack_resource, **kwargs):
    """
     Delete volume backup.
    :param openstack_resource: instance of openstack volume resource
    :param kwargs: snapshot information provided by workflow
    """

    ctx.logger.info('Delete snapshot for {0}'.format(
        openstack_resource.resource_id))

    # Get snapshot information provided by workflow parameters
    snapshot_name = kwargs.get('snapshot_name')
    snapshot_incremental = kwargs.get('snapshot_incremental')

    # Generate snapshot name
    backup_name = \
        get_snapshot_name('volume', snapshot_name, snapshot_incremental)

    # This is a backup stored at object storage must be deleted
    if not snapshot_incremental:
        _delete_volume_backup(openstack_resource, backup_name)

    # This is a snapshot that need to be deleted
    else:
        _delete_volume_snapshot(openstack_resource, backup_name)


@with_openstack_resource(OpenstackVolume)
def delete(openstack_resource):
    """
    Delete current openstack volume instance
    :param openstack_resource: instance of openstack volume resource
    """
    # Only trigger delete api when it is the first time we run this task,
    # otherwise we should check the if the volume is really deleted or not
    # by keep calling get volume api
    if VOLUME_TASK_DELETE not in ctx.instance.runtime_properties:
        # Delete volume resource
        openstack_resource.delete()
        ctx.instance.runtime_properties[VOLUME_TASK_DELETE] = True

    # Make sure that volume are deleting
    try:
        openstack_resource.get()
        raise OperationRetry('Volume {0} is still deleting'.format(
            openstack_resource.resource_id))
    except openstack.exceptions.ResourceNotFound:
        ctx.logger.info('Volume {0} is deleted successfully'.format(
            openstack_resource.resource_id))


@with_openstack_resource(OpenstackVolume)
def list_volumes(openstack_resource, query=None):
    """
    List openstack volumes based on filters applied
    :param openstack_resource: Instance of current openstack volume
    :param kwargs query: Optional query parameters to be sent to limit
            the volumes being returned.
    """
    volumes = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(VOLUME_OPENSTACK_TYPE, volumes)


@with_openstack_resource(OpenstackVolume)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create volume resource in openstack
    :param openstack_resource: Instance of current openstack volume
    """
    validate_resource_quota(openstack_resource, VOLUME_OPENSTACK_TYPE)
    ctx.logger.debug('OK: volume configuration is valid')
