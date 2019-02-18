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

# Third part imports
from cloudify import ctx

# Local imports
from openstack_sdk.resources.networks import OpenstackNetwork
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import RESOURCE_ID
from openstacksdk_plugin.utils import (validate_resource_quota,
                                       reset_dict_empty_keys,
                                       add_resource_list_to_runtime_properties)
from openstacksdk_plugin.constants import NETWORK_OPENSTACK_TYPE


@with_openstack_resource(OpenstackNetwork)
def create(openstack_resource):
    """
    Create openstack network instance
    :param openstack_resource: instance of openstack network resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackNetwork)
def delete(openstack_resource):
    """
    Delete current openstack network
    :param openstack_resource: instance of openstack network resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackNetwork)
def update(openstack_resource, args):
    """
    Update openstack network by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack network resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackNetwork)
def list_networks(openstack_resource, query=None):
    """
    List openstack networks based on filters applied
    :param openstack_resource: Instance of current openstack network
    :param kwargs query: Optional query parameters to be sent to limit
            the networks being returned.
    """
    networks = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(NETWORK_OPENSTACK_TYPE, networks)


@with_openstack_resource(OpenstackNetwork)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create network resource in openstack
    :param openstack_resource: Instance of current openstack network
    """
    validate_resource_quota(openstack_resource, NETWORK_OPENSTACK_TYPE)
    ctx.logger.debug('OK: network configuration is valid')
