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
from openstacksdk_plugin.constants import RESOURCE_ID


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
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = \
        created_resource.id
    ctx.instance.runtime_properties['floating_ip_address'] = \
        created_resource.floating_ip_address


@with_openstack_resource(OpenstackFloatingIP)
def delete(openstack_resource):
    openstack_resource.delete()


@with_openstack_resource(OpenstackFloatingIP)
def update(openstack_resource, **new_config):
    # At some case like remove ip from port, openstack API refuse to to set
    # port_id to '' empty string in order to delete the port, it should be
    # set to None in order to set it, so it is required to change '' to None
    for key, item in new_config.iteritems():
        if not item:
            new_config[key] = None

    openstack_resource.update(new_config)
