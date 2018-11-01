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

from openstack_sdk.resources.networks import OpenstackPort
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import RESOURCE_ID

from cloudify import ctx


@with_openstack_resource(OpenstackPort)
def create(openstack_resource):
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackPort)
def delete(openstack_resource):
    openstack_resource.delete()


def update():
    pass
