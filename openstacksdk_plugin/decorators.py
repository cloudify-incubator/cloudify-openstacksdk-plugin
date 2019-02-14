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
from openstacksdk_plugin.constants import USE_EXTERNAL_RESOURCE_PROPERTY
from openstacksdk_plugin.utils import (resolve_ctx,
                                       get_current_operation,
                                       prepare_resource_instance,
                                       handle_external_resource,
                                       set_runtime_properties_from_resource)


def with_openstack_resource(class_decl, existing_resource_handler=None):
    """
    :param class_decl: This is a class for the openstack resource need to be
    invoked
    :param existing_resource_handler: This is a method that handle any
    custom operation need to be done in case "use_external_resource" is set
    to true
    :return: a wrapper object encapsulating the invoked function
    """

    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            # Get the context for the current task operation
            ctx = kwargs.pop('ctx', CloudifyContext)

            # Resolve the actual context which need to run operation,
            # the context could be belongs to relationship context or actual
            # node context
            ctx_node = resolve_ctx(ctx)

            # Get the current operation name
            operation_name = get_current_operation()

            # Prepare the openstack resource that need to execute the
            # current task operation
            resource = \
                prepare_resource_instance(class_decl, ctx_node, kwargs)

            # Handle external resource when it is enabled
            if ctx_node.node.properties.get(USE_EXTERNAL_RESOURCE_PROPERTY):
                handle_external_resource(ctx_node,
                                         resource,
                                         existing_resource_handler)
                return
            try:
                kwargs['openstack_resource'] = resource
                func(**kwargs)
                # Set runtime properties for "name" & "type" when current
                # operation is create, so that they can be used later on
                if operation_name == 'create':
                    set_runtime_properties_from_resource(ctx_node, resource)

            except exceptions.SDKException as error:
                _, _, tb = sys.exc_info()
                raise NonRecoverableError(
                    'Failure while trying to request '
                    'Openstack API: {}'.format(error.message),
                    causes=[exception_to_error_cause(error, tb)])

        return wrapper_inner
    return wrapper_outer
