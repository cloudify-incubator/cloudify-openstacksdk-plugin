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
from openstack_sdk.resources.networks import OpenstackSubnet
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID, SUBNET_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import (reset_dict_empty_keys,
                                       validate_resource_quota,
                                       add_resource_list_to_runtime_properties)


@with_openstack_resource(OpenstackSubnet)
def create(openstack_resource):
    """
    Create openstack subnet instance
    :param openstack_resource: instance of openstack subnet resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackSubnet)
def delete(openstack_resource):
    """
    Delete current openstack subnet
    :param openstack_resource: instance of openstack subnet resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackSubnet)
def update(openstack_resource, args):
    """
    Update openstack subnet by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack subnet resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackSubnet)
def list_subnets(openstack_resource, query=None):
    """
    List openstack subnets based on filters applied
    :param openstack_resource: Instance of current openstack network
    :param kwargs query: Optional query parameters to be sent to limit
            the networks being returned.
    """
    subnets = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(SUBNET_OPENSTACK_TYPE, subnets)


@with_openstack_resource(OpenstackSubnet)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create subnet resource in openstack
    :param openstack_resource: Instance of current openstack subnet
    """
    validate_resource_quota(openstack_resource, SUBNET_OPENSTACK_TYPE)
    ctx.logger.debug('OK: port configuration is valid')
