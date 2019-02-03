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
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_sdk.resources.compute import OpenstackServerGroup
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           SERVER_GROUP_OPENSTACK_TYPE)

from openstacksdk_plugin.utils import (validate_resource,
                                       add_resource_list_to_runtime_properties)


@with_openstack_resource(OpenstackServerGroup)
def create(openstack_resource):
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackServerGroup)
def delete(openstack_resource):
    # Delete the server group resource after lookup the resource_id values
    openstack_resource.delete()


@with_openstack_resource(OpenstackServerGroup)
def update(openstack_resource):
    # Update server group not support right now with openstacksdk
    raise NonRecoverableError(
        'Openstacksdk library does not support update server group')


@with_openstack_resource(OpenstackServerGroup)
def list(openstack_resource, query):
    server_groups = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(SERVER_GROUP_OPENSTACK_TYPE,
                                            server_groups)


@with_openstack_resource(OpenstackServerGroup)
def creation_validation(openstack_resource):
    validate_resource(openstack_resource, SERVER_GROUP_OPENSTACK_TYPE)
    ctx.logger.debug('OK: server group configuration is valid')
