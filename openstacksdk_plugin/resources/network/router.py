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

from openstack_sdk.resources.networks import OpenstackRouter
from openstacksdk_plugin.decorators import with_openstack_resource

from openstacksdk_plugin.constants import RESOURCE_ID

from cloudify import ctx


@with_openstack_resource(OpenstackRouter)
def create(openstack_resource):
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackRouter)
def delete(openstack_resource):
    openstack_resource.delete()


@with_openstack_resource(OpenstackRouter)
def add_interface_to_router(openstack_resource, **kwargs):
    openstack_resource.add_interface(kwargs)


@with_openstack_resource(OpenstackRouter)
def remove_interface_from_router(openstack_resource, **kwargs):
    openstack_resource.remove_interface(kwargs)


@with_openstack_resource(OpenstackRouter)
def start(openstack_resource, **kwargs):
    if kwargs and kwargs.get('routes'):
        # Store routes in order to use them later on in order to remove them
        # when the stop operation for router trigger
        ctx.instance.runtime_properties['routes'] = kwargs['routes']
        routes = dict()
        routes['routes'] = kwargs['routes']
        openstack_resource.update(routes)


@with_openstack_resource(OpenstackRouter)
def stop(openstack_resource, **kwargs):
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
