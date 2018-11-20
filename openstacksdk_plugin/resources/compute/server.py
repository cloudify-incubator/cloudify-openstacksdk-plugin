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
import base64

# Third party imports
from cloudify import ctx
from openstack import exceptions
from cloudify.exceptions import OperationRetry

# Local imports
from openstack_sdk.resources.compute import OpenstackServer
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           SERVER_STATUS_ACTIVE,
                                           SERVER_STATUS_SHUTOFF,
                                           SERVER_TASK_CREATE,
                                           SERVER_TASK_DELETE,
                                           SERVER_TASK_STOP,)


@with_openstack_resource(OpenstackServer)
def create(openstack_resource):
    if SERVER_TASK_CREATE not in ctx.instance.runtime_properties:

        # User Data must be encoded to base64 encode whenever
        # user_data provided
        if openstack_resource.config.get('user_data'):
            openstack_resource.config['user_data'] = \
                base64.b64encode(openstack_resource.config['user_data'])

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
    # Get the details for the created servers instance
    server = openstack_resource.get()

    # Get the server status
    status = server.status
    if status == SERVER_STATUS_ACTIVE:
        ctx.logger.info('Server is already started')
        return


@with_openstack_resource(OpenstackServer)
def delete(openstack_resource):
    # Get the details for the created servers instance
    try:
        server = openstack_resource.get()
    except exceptions.ResourceNotFound:
        ctx.logger.info('Server is deleted')
        return

    # Check if delete operation triggered or not before
    if SERVER_TASK_DELETE not in ctx.instance.runtime_properties:
        openstack_resource.delete()
        ctx.instance.runtime_properties[SERVER_TASK_DELETE] = True

    ctx.logger.info('Waiting for server "{0}" to be deleted.'
                    ' current status: {1}'.format(server.id, server.status))

    raise OperationRetry(message='Server has {} state.'.format(server.status))


@with_openstack_resource(OpenstackServer)
def stop(openstack_resource):
    # Get the details for the created servers instance
    server = openstack_resource.get()

    # Get the current server status
    status = server.status

    if status != SERVER_STATUS_SHUTOFF:
        # Trigger stop server API only if it is not stopped before
        if SERVER_TASK_STOP not in ctx.instance.runtime_properties:
            openstack_resource.stop()

        # Get the server instance to check the status of the server
        server = openstack_resource.get()
        if server.status != SERVER_STATUS_SHUTOFF:
            ctx.instance.runtime_properties[SERVER_TASK_STOP] = True
            raise OperationRetry(message='Server has {} state.'.format(
                server.status), retry_after=30)

    else:
        ctx.logger.info('Server is already stopped')


@with_openstack_resource(OpenstackServer)
def update(openstack_resource):
    pass
