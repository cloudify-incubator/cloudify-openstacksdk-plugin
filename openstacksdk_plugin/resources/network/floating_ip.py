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
from cloudify.exceptions import RecoverableError

# Local imports
from openstack_sdk.resources.networks import OpenstackFloatingIP
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           FLOATING_IP_OPENSTACK_TYPE)
from openstacksdk_plugin.utils import (reset_dict_empty_keys,
                                       validate_resource,
                                       add_resource_list_to_runtime_properties)


def use_external_floating_ip(openstack_resource):
    status = openstack_resource.status
    floating_ip = openstack_resource.floating_ip_address
    if not ctx.node.properties['allow_reallocation'] and status == 'ACTIVE':
        raise RecoverableError(
            'Floating IP address {0} is already associated'.format(floating_ip)
        )
    # Set the floating ip address as runtime property if "allow_reallocation"
    # is set to "True"
    ctx.instance.runtime_properties['floating_ip_address'] = floating_ip


@with_openstack_resource(class_decl=OpenstackFloatingIP,
                         existing_resource_handler=use_external_floating_ip)
def create(openstack_resource):
    """
    Create openstack floating ip instance
    :param openstack_resource: instance of openstack floating ip  resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = \
        created_resource.id
    ctx.instance.runtime_properties['floating_ip_address'] = \
        created_resource.floating_ip_address


@with_openstack_resource(OpenstackFloatingIP)
def delete(openstack_resource):
    """
    Delete current openstack floating ip
    :param openstack_resource: instance of openstack floating ip resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackFloatingIP)
def update(openstack_resource, args):
    """
    Update openstack floating ip by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack floating ip resource
    :param args: dict of information need to be updated
    """
    # At some case like remove ip from port, openstack API refuse to to set
    # port_id to '' empty string in order to delete the port, it should be
    # set to None in order to set it, so it is required to change '' to None
    new_config = reset_dict_empty_keys(args)
    openstack_resource.update(new_config)


@with_openstack_resource(OpenstackFloatingIP)
def list_floating_ips(openstack_resource, query=None):
    """
    List openstack floating ips based on filters applied
    :param openstack_resource: Instance of current openstack floating ip
    :param kwargs query: Optional query parameters to be sent to limit
            the floating ips being returned.
    """
    floating_ips = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(
        FLOATING_IP_OPENSTACK_TYPE, floating_ips)


@with_openstack_resource(OpenstackFloatingIP)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create floating ip resource in openstack
    :param openstack_resource: Instance of current openstack floating ip
    """
    validate_resource(openstack_resource, FLOATING_IP_OPENSTACK_TYPE)
    ctx.logger.debug('OK: floating ip configuration is valid')
