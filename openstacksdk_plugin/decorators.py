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
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause


def with_openstack_resource(class_decl=None):
    """
    :param class_decl: This is a class for the openstack resource need to b
    invoked
    :return: a wrapper object encapsulating the invoked function
    """
    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            def get_property_by_name(property_name):
                # TODO: Work out this logic.
                # Operation kwargs have the highest reliability.
                # Runtime properties have the next highest reliability.
                # Node Properties are considered seed information and lowest reliability.
                # The problem is we also want the default of operation kwargs to map to { get_property: node_property_name }
                # We either need to let go of this option, or we need to compare node properties to operation kwargs and if they are the same disqualify operation kwargs.
                # if property_name in ctx.instance.runtime_properties:
                #     return ctx.instance.runtime_properties.get(property_name)
                # if property_name in kwargs:
                #     return kwargs.pop(property_name)
                if property_name in ctx.node.properties:
                    return ctx.node.properties.get(property_name)
            client_config = get_property_by_name('client_config')
            resource_config = get_property_by_name('resource_config')
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
