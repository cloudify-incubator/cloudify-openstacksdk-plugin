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
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_sdk.resources.networks import (OpenstackRouter,
                                              OpenstackNetwork)
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           ROUTER_OPENSTACK_TYPE,
                                           NETWORK_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import (
    reset_dict_empty_keys,
    validate_resource_quota,
    add_resource_list_to_runtime_properties,
    find_openstack_ids_of_connected_nodes_by_openstack_type)


def _get_external_network_id(ext_gateway_info):
    """
    This method will lookup the external network id from external gateway
    info object
    :param dict ext_gateway_info: External info dict
    :return str: External network id
    """
    if ext_gateway_info and ext_gateway_info.get('network_id'):
        return ext_gateway_info['network_id']
    return None


def _get_connected_external_network_from_relationship(network_resource):
    """
    This method will lookup external network connected to network using
    relationship
    :param network_resource: Instance of openstack network resource
    :return str: External network id
    """
    # Get networks connected to router
    networks = \
        find_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx,
            NETWORK_OPENSTACK_TYPE)
    # List to save all external networks connected to router
    external_network_ids = []

    for net_id in networks:
        network_resource.resource_id = net_id
        remote_network = network_resource.get()
        if remote_network.is_router_external:
            external_network_ids.append(net_id)

    if len(external_network_ids) > 1:
        raise NonRecoverableError(
            'More than one external network is connected to router {0}'
            ' by a relationship; External network IDs: {0}'.format(
                external_network_ids))

    return external_network_ids[0] if external_network_ids else None


def _connect_router_to_external_network(router_resource):
    """
    This method will update router config with external network by checking
    if it is provided using node property "resource_config" or via
    relationship and we should only connect router to external network from
    one source
    :param router_resource: Instance of openstack router resource
    """
    if not router_resource or router_resource and not router_resource.config:
        return

    network_resource = \
        OpenstackNetwork(client_config=router_resource.client_config,
                         logger=ctx.logger)
    # Get network id from "resource_config" which represent "router_config"
    ext_net_id = \
        _get_external_network_id(
            router_resource.config.get('external_gateway_info'))

    # Get network id id from relationship connected to router
    rel_ext_net_id = \
        _get_connected_external_network_from_relationship(network_resource)

    if ext_net_id and rel_ext_net_id:
        raise NonRecoverableError('Router can\'t both have the '
                                  '"external_gateway_info" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    if 'external_gateway_info' not in router_resource.config:
        router_resource.config['external_gateway_info'] = {}

    router_resource.config['external_gateway_info']['network_id'] = \
        ext_net_id or rel_ext_net_id


def _handle_external_router_resource(openstack_resource):
    """
    This method is to do a validation for external router resource when it
    is connected to external network node resource
    :param openstack_resource: Instance of openstack router resource
    """
    remote_router = openstack_resource.get()
    rel_network_id = \
        _get_connected_external_network_from_relationship(openstack_resource)
    ext_network_id = \
        _get_external_network_id(remote_router.external_gateway_info)
    if rel_network_id and ext_network_id != rel_network_id:
        raise NonRecoverableError(
            'Expected external resources subnet {0} and network'
            ' {1} to be connected'.format(rel_network_id, ext_network_id))


@with_openstack_resource(
    OpenstackRouter,
    existing_resource_handler=_handle_external_router_resource)
def create(openstack_resource):
    """
    Create openstack router instance
    :param openstack_resource: Instance of openstack router resource
    """
    # Update router with the correct external network, so that they can be
    # connected to each other successfully
    _connect_router_to_external_network(openstack_resource)

    # Create router
    created_resource = openstack_resource.create()

    # Save router resource id as runtime property
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
