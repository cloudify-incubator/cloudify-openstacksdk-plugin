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
from openstacksdk_plugin import utils


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
            ctx = kwargs.pop('ctx', CloudifyContext)
            node_instance = utils.set_ctx(ctx)
            _, _, _, operation_name = ctx.operation.name.split('.')

            def get_property_by_name(property_name):
                property_value = None
                # TODO: Improve this to be more thorough.
                if property_name in node_instance.node.properties:
                    property_value = \
                        node_instance.node.properties.get(property_name)
                if property_name in node_instance.instance.runtime_properties:
                    if isinstance(property_value, dict):
                        property_value.update(
                            node_instance.instance.runtime_properties.get(
                                property_name))
                    else:
                        property_value = \
                            node_instance.instance.runtime_properties.get(
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

            # If this arg is exist, that means user
            # provide extra/optional configuration for the defined node
            if resource_config.get('kwargs'):
                extra_config = resource_config.pop('kwargs')
                resource_config.update(extra_config)

            # Check if resource_id is part of runtime properties so that we
            # can add it to the resource_config
            if RESOURCE_ID in node_instance.instance.runtime_properties:
                resource_config['id'] = \
                    node_instance.instance.runtime_properties[RESOURCE_ID]

            resource = class_decl(client_config=client_config,
                                  resource_config=resource_config,
                                  logger=ctx.logger)

            # # Check if "use_external_resource" is set to True
            is_external = get_property_by_name(USE_EXTERNAL_RESOURCE_PROPERTY)

            # Validate if the "is_external" is set and the resource
            # identifier (id|name) for the Openstack is invalid raise error and
            # abort the operation
            if is_external:
                error_message = resource.validate_resource_identifier()
                if error_message:
                    raise NonRecoverableError(error_message)

                if operation_name in ['create', 'delete']:
                    ctx.logger.info(
                        'Using external resource {0}'.format(RESOURCE_ID))

                    # Get the remote resource
                    try:
                        remote_resource = resource.get()
                    except exceptions.SDKException as error:
                        _, _, tb = sys.exc_info()
                        raise NonRecoverableError(
                            'Failure while trying to request '
                            'Openstack API: {}'.format(error.message),
                            causes=[exception_to_error_cause(error, tb)])

                    # Check the operation type and based on that
                    # decide what to do
                    if operation_name == 'create':
                        ctx.logger.info(
                            'not creating resource {0}'
                            ' since an external resource is being used'
                            ''.format(remote_resource.name))
                        node_instance.instance.runtime_properties[RESOURCE_ID]\
                            = remote_resource.id

                        # Check if we need to add custom operation
                        # when resource is already created
                        if existing_resource_handler:
                            existing_resource_handler(remote_resource)

                    elif operation_name == 'delete':
                        ctx.logger.info(
                            'not deleting resource {0}'
                            ' since an external resource is being used'
                            ''.format(remote_resource.name))
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
