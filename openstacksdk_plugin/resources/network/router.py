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

# Third party imports
from cloudify import ctx

# Local imports
from openstack_sdk.resources.networks import OpenstackRouter
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID, ROUTER_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import (reset_dict_empty_keys,
                                       validate_resource_quota,
                                       add_resource_list_to_runtime_properties)


@with_openstack_resource(OpenstackRouter)
def create(openstack_resource):
    """
    Create openstack router instance
    :param openstack_resource: instance of openstack router resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackRouter)
def delete(openstack_resource):
    """
    Delete current openstack router
    :param openstack_resource: instance of openstack router resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackRouter)
def update(openstack_resource, args):
    """
    Update openstack router by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack router resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackRouter)
def list_routers(openstack_resource, query=None):
    """
    List openstack routers based on filters applied
    :param openstack_resource: Instance of current openstack router
    :param kwargs query: Optional query parameters to be sent to limit
            the routers being returned.
    """
    routers = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(ROUTER_OPENSTACK_TYPE, routers)


@with_openstack_resource(OpenstackRouter)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create router resource in openstack
    :param openstack_resource: Instance of current openstack router
    """
    validate_resource_quota(openstack_resource, ROUTER_OPENSTACK_TYPE)
    ctx.logger.debug('OK: router configuration is valid')


@with_openstack_resource(OpenstackRouter)
def add_interface_to_router(openstack_resource, **kwargs):
    """
    Add interface to router in order to link router with other services like
    (port, subnet)
    :param openstack_resource: instance of openstack router resource
    :param kwargs: Configuration must be provided in order to connect with
    router and these configuration are subnet_id, port_id
    """
    openstack_resource.add_interface(kwargs)


@with_openstack_resource(OpenstackRouter)
def remove_interface_from_router(openstack_resource, **kwargs):
    """
    Remove interface to router in order to unlink router with other services
    like (port, subnet)
    :param openstack_resource: instance of openstack router resource
    :param kwargs: Configuration must be provided in order to connect with
    router and these configuration are subnet_id, port_id
    """
    openstack_resource.remove_interface(kwargs)


@with_openstack_resource(OpenstackRouter)
def start(openstack_resource, **kwargs):
    """
    Add static routes for router
    :param openstack_resource: instance of openstack router resource
    :param kwargs: Routes configuration which should be added to router table
    """
    if kwargs and kwargs.get('routes'):
        # Store routes in order to use them later on in order to remove them
        # when the stop operation for router trigger
        ctx.instance.runtime_properties['routes'] = kwargs['routes']
        routes = dict()
        routes['routes'] = kwargs['routes']
        openstack_resource.update(routes)


@with_openstack_resource(OpenstackRouter)
def stop(openstack_resource):
    """
    Remove static routes which added before for router
    :param openstack_resource: instance of openstack router resource
    """
    if 'routes' in ctx.instance.runtime_properties:
        # There are some routes need to be deleted since it is part of the
        # runtime properties

        # Routes need to be removed
        routes_to_delete = ctx.instance.runtime_properties['routes']

        # Get the remote router info
        router = openstack_resource.get()

        updated_routes = []
        remote_routes = router['routes'] or {}
        for remote_route in remote_routes:
            if remote_route not in routes_to_delete:
                updated_routes.append(remote_route)

        routes = dict()
        routes['routes'] = updated_routes
        openstack_resource.update(routes)
