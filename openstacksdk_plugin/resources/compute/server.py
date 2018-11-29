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

from openstacksdk_plugin.utils import handle_userdata


def _set_server_ips_runtime_properties(server):
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


@with_openstack_resource(OpenstackServer)
def create(openstack_resource):
    if SERVER_TASK_CREATE not in ctx.instance.runtime_properties:
        blueprint_user_data = openstack_resource.config.get('user_data')
        user_data = handle_userdata(blueprint_user_data)
        if user_data:
            openstack_resource.config['user_data'] = user_data

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
        _set_server_ips_runtime_properties(server)

        # The password returned from `Win` instances return always empty
        res = openstack_resource.get_server_password()
        password = json.loads(res.content) if res.content else None
        ctx.instance.runtime_properties['password'] = password
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
