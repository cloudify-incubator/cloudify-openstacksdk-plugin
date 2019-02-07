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

from openstack_sdk.resources.networks import OpenstackPort
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID, PORT_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import (update_runtime_properties,
                                       reset_dict_empty_keys,
                                       validate_resource,
                                       add_resource_list_to_runtime_properties)


@with_openstack_resource(OpenstackPort)
def create(openstack_resource):
    """
    Create openstack port instance
    :param openstack_resource: instance of openstack port resource
    """
    created_resource = openstack_resource.create()
    update_runtime_properties(
        {
            RESOURCE_ID: created_resource.id,
            'fixed_ips': created_resource.fixed_ips,
            'mac_address': created_resource.mac_address,
            'allowed_address_pairs': created_resource.allowed_address_pairs,
        }
    )


@with_openstack_resource(OpenstackPort)
def delete(openstack_resource):
    """
    Delete current openstack port
    :param openstack_resource: instance of openstack port resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackPort)
def update(openstack_resource, args):
    """
    Update openstack port by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack port resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackPort)
def list_ports(openstack_resource, query=None):
    """
    List openstack networks based on filters applied
    :param openstack_resource: Instance of current openstack network
    :param kwargs query: Optional query parameters to be sent to limit
            the networks being returned.
    """
    ports = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(PORT_OPENSTACK_TYPE, ports)


@with_openstack_resource(OpenstackPort)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create network resource in openstack
    :param openstack_resource: Instance of current openstack network
    """
    validate_resource(openstack_resource, PORT_OPENSTACK_TYPE)
    ctx.logger.debug('OK: port configuration is valid')
