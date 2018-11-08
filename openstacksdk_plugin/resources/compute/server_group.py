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
from openstack_sdk.resources.compute import OpenstackServerGroup
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import RESOURCE_ID


@with_openstack_resource(OpenstackServerGroup)
def create(openstack_resource):
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackServerGroup)
def delete(openstack_resource):
    openstack_resource.delete()


@with_openstack_resource(OpenstackServerGroup)
def update(openstack_resource):
    openstack_resource.update()
