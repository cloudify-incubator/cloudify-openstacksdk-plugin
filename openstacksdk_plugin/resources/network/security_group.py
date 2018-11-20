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

from openstack_sdk.resources.networks import OpenstackSecurityGroup
from openstack_sdk.resources.networks import OpenstackSecurityGroupRule
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import RESOURCE_ID

from cloudify import ctx


@with_openstack_resource(OpenstackSecurityGroup)
def create(openstack_resource):
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackSecurityGroup)
def configure(openstack_resource, security_group_rules=None):
    # Get the security group id

    client_config = ctx.node.properties.get('client_config')
    security_group_id = openstack_resource.resource_id
    # Check the existing rules attached to current security groups in order to apply them to that group
    for rule_config in security_group_rules:
        # Check if the config contains the security group id or not
        if not rule_config.get('security_group_id'):
            rule_config['security_group_id'] = security_group_id

        # Create new instance for each security group id
        security_group_rule = OpenstackSecurityGroupRule(client_config=client_config,
                                                         resource_config=rule_config,
                                                         logger=ctx.logger)

        # Create security group rule
        security_group_rule.create()


@with_openstack_resource(OpenstackSecurityGroup)
def delete(openstack_resource):
    openstack_resource.delete()


def update():
    pass
