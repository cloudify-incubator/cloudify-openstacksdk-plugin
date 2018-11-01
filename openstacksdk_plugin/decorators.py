# #######
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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

# Standard Imports
import sys

# Third party imports
from openstack import exceptions
from cloudify import ctx as CloudifyContext
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

from openstacksdk_plugin.constants import RESOURCE_ID


def with_openstack_resource(class_decl=None):
    """
    :param class_decl: This is a class for the openstack resource need to b
    invoked
    :return: a wrapper object encapsulating the invoked function
    """
    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            ctx = kwargs.pop('ctx', CloudifyContext)

            def get_property_by_name(property_name):
                property_value = None
                # TODO: Improve this to be more thorough.
                if property_name in ctx.node.properties:
                    property_value = ctx.node.properties.get(property_name)
                if property_name in ctx.instance.runtime_properties:
                    if isinstance(property_value, dict):
                        property_value.update(
                            ctx.instance.runtime_properties.get(property_name))
                    else:
                        property_value = ctx.instance.runtime_properties.get(
                            property_name)
                if property_name in kwargs:
                    kwargs_value = kwargs.pop(property_name)
                    if isinstance(property_value, dict):
                        property_value.update(kwargs_value)
                    else:
                        return kwargs_value
                return property_value

            client_config = get_property_by_name('client_config')
            resource_config = get_property_by_name('resource_config')
            resource_id = get_property_by_name(RESOURCE_ID)
            if resource_id:
                resource_config['id'] = resource_id
            try:
                kwargs['openstack_resource'] = class_decl(
                    client_config=client_config,
                    resource_config=resource_config,
                    logger=ctx.logger
                )
                func(**kwargs)
            except exceptions.SDKException as error:
                _, _, tb = sys.exc_info()
                raise NonRecoverableError(
                    'Failure while trying to request '
                    'NetApp API: {}'.format(error.message),
                    causes=[exception_to_error_cause(error, tb)])

        return wrapper_inner
    return wrapper_outer
