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

# Local imports
from openstacksdk_plugin.constants import RESOURCE_ID
from openstacksdk_plugin.constants import USE_EXTERNAL_RESOURCE_PROPERTY


def with_openstack_resource(class_decl=None):
    """
    :param class_decl: This is a class for the openstack resource need to b
    invoked
    :return: a wrapper object encapsulating the invoked function
    """
    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            ctx = kwargs.pop('ctx', CloudifyContext)
            # Get the operation name
            _, _, _, operation_name = ctx.operation.name.split('.')

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
            resource = class_decl(client_config=client_config,
                                  resource_config=resource_config,
                                  logger=ctx.logger)

            # # Check if "use_external_resource" is set to True
            is_external = get_property_by_name(USE_EXTERNAL_RESOURCE_PROPERTY)
            if is_external and operation_name in ['create', 'delete']:
                ctx.logger.info(
                    'Using external resource {0}'.format(RESOURCE_ID))

                # Get the remote resource
                try:
                    resource = resource.get()
                except exceptions.SDKException as error:
                    _, _, tb = sys.exc_info()
                    raise NonRecoverableError(
                        'Failure while trying to request '
                        'Openstack API: {}'.format(error.message),
                        causes=[exception_to_error_cause(error, tb)])

                # Check the operation type and based on that decide what to do
                if operation_name == 'create':
                    ctx.logger.info(
                        'not creating resource {0}'
                        ' since an external resource is being used'
                        ''.format(resource.name))
                    ctx.instance.runtime_properties[RESOURCE_ID] = resource.id
                elif operation_name == 'delete':
                    ctx.logger.info(
                        'not deleting resource {0}'
                        ' since an external resource is being used'
                        ''.format(resource.name))
                return
            try:
                kwargs['openstack_resource'] = resource
                func(**kwargs)
            except exceptions.SDKException as error:
                _, _, tb = sys.exc_info()
                raise NonRecoverableError(
                    'Failure while trying to request '
                    'Openstack API: {}'.format(error.message),
                    causes=[exception_to_error_cause(error, tb)])

        return wrapper_inner
    return wrapper_outer
