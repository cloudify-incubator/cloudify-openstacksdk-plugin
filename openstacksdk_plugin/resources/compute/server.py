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

from openstack_sdk.resources.compute import OpenstackServer
from openstacksdk_plugin.decorators import with_openstack_resource


@with_openstack_resource(OpenstackServer)
def create(openstack_resource):
    openstack_resource.create()


@with_openstack_resource(OpenstackServer)
def start(openstack_resource):
    openstack_resource.start()


@with_openstack_resource(OpenstackServer)
def delete(openstack_resource):
    openstack_resource.delete()


@with_openstack_resource(OpenstackServer)
def stop(openstack_resource):
    openstack_resource.stop()


@with_openstack_resource(OpenstackServer)
def update(openstack_resource):
    openstack_resource.update()
