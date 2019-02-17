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

# Standard imports
import sys
import base64


# Third part imports
import openstack.exceptions
from cloudify import compute
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

try:
    from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'

# Local imports
from openstacksdk_plugin.constants import (PS_OPEN,
                                           PS_CLOSE,
                                           QUOTA_VALID_MSG,
                                           QUOTA_INVALID_MSG,
                                           INFINITE_RESOURCE_QUOTA,
                                           RESOURCE_ID,
                                           OPENSTACK_TYPE_PROPERTY,
                                           OPENSTACK_NAME_PROPERTY)


def find_relationships_by_node_type(ctx_node_instance, node_type):
    """
    Finds all specified relationships of the Cloudify
    instance where the related node type is of a specified type.
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param node_type: Cloudify node type to search node_ctx.relationships for
    :return: List of Cloudify relationships
    """
    return [target_rel for target_rel in ctx_node_instance.relationships
            if node_type in target_rel.target.node.type_hierarchy]


def find_relationship_by_node_type(ctx_node_instance, node_type):
    """
    Finds a single relationship of the Cloudify
    instance where the related node type is of a specified type.
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param node_type: Cloudify node type to search node_ctx.relationships for
    :return: A Cloudify relationship or None
    """
    relationships = \
        find_relationships_by_node_type(ctx_node_instance, node_type)
    return relationships[0] if len(relationships) > 0 else None


def find_relationships_by_relationship_type(_ctx, type_name):
    """
    Find cloudify relationships by relationship type.
    Follows the inheritance tree.
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :param type_name: desired relationship type derived
    from cloudify.relationships.depends_on.
    :return: list of RelationshipSubjectContext
    """

    return [rel for rel in _ctx.instance.relationships if
            type_name in rel.type_hierarchy]


def get_resource_id_from_runtime_properties(ctx_node_instance):
    """
    This method will lookup the resource id which is stored as part of
    runtime properties
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :return: Resource id
    """
    return ctx_node_instance.instance.runtime_properties.get(RESOURCE_ID)


def resolve_node_ctx_from_relationship(_ctx):
    """
    This method is to decide where to get node from relationship context
    since this is not exposed correctly from cloudify
    :param _ctx: current cloudify context object
    :return: RelationshipSubjectContext instance
    """
    # Get the node_id for the current node in order to decide if that node
    # is source | target
    node_id = _ctx._context.get('node_id')

    source_node_id = _ctx.source._context.get('node_id')
    target_node_id = _ctx.target._context.get('node_id')

    if node_id == source_node_id:
        return _ctx.source
    elif node_id == target_node_id:
        return _ctx.target
    else:
        raise NonRecoverableError(
            'Unable to decide if current node is source or target')


def resolve_ctx(_ctx):
    """
    This method is to lookup right context instance which could be one of
    the following:
     1- Context for source relationship instance
     2- Context for target relationship instance
     3- Context for current node
    :param _ctx: current cloudify context object
    :return: This could be RelationshipSubjectContext or CloudifyContext
    instance
    """
    if _ctx.type == RELATIONSHIP_INSTANCE:
        return resolve_node_ctx_from_relationship(_ctx)
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. This indicates a problem.'.format(
                NODE_INSTANCE, RELATIONSHIP_INSTANCE))
    return _ctx


def handle_userdata(existing_userdata):
    """
    This method will be responsible for handle user data provided by the
    user on the following cases:
    1. When user specify "user_data" to create server on openstack
    2. When "install_method" for agent is set to "Init-script" the plugin
     should be able to inject/update "user_data" for server
    :param existing_userdata:
    :return: final_userdata
    """
    # Check the agent init script so that it can be injected to the target
    # machine to install the agent daemon
    install_agent_userdata = ctx.agent.init_script()
    # Get the "os_family" type, by default all node instances extend
    # "cloudify.nodes.Compute" node will have "os_family" set to "Linux"
    # It can be override for Windows which is need to be handled differently
    os_family = ctx.node.properties['os_family']

    if not (existing_userdata or install_agent_userdata):
        return None

    if not existing_userdata:
        existing_userdata = ''

    if install_agent_userdata and os_family == 'windows':

        # Get the powershell content from install_agent_userdata
        install_agent_userdata = \
            extract_powershell_content(install_agent_userdata)

        # Get the powershell content from existing_userdata
        # (If it exists.)
        existing_userdata_powershell = \
            extract_powershell_content(existing_userdata)

        # Combine the powershell content from two sources.
        install_agent_userdata = \
            '#ps1_sysnative\n{0}\n{1}\n{2}\n{3}\n'.format(
                PS_OPEN,
                existing_userdata_powershell,
                install_agent_userdata,
                PS_CLOSE)

        # Additional work on the existing_userdata.
        # Remove duplicate Powershell content.
        # Get rid of unnecessary newlines.
        existing_userdata = \
            existing_userdata.replace(
                existing_userdata_powershell,
                '').replace(
                    PS_OPEN,
                    '').replace(
                        PS_CLOSE,
                        '').strip()

    if not existing_userdata or existing_userdata.isspace():
        final_userdata = install_agent_userdata
    elif not install_agent_userdata:
        final_userdata =\
            compute.create_multi_mimetype_userdata([existing_userdata])
    else:
        final_userdata = compute.create_multi_mimetype_userdata(
            [existing_userdata, install_agent_userdata])

    final_userdata = base64.b64encode(final_userdata)
    return final_userdata


def extract_powershell_content(string_with_powershell):
    """We want to filter user data for powershell scripts.
    However, Openstack allows only one segment that is Powershell.
    So we have to concat separate Powershell scripts into one.
    First we separate all Powershell scripts without their tags.
    Later we will add the tags back.
    """

    split_string = string_with_powershell.splitlines()

    if not split_string:
        return ''

    if split_string[0] == '#ps1_sysnative' or \
            split_string[0] == '#ps1_x86':
        split_string.pop(0)

    if PS_OPEN not in split_string:
        script_start = -1  # Because we join at +1.
    else:
        script_start = split_string.index(PS_OPEN)

    if PS_CLOSE not in split_string:
        script_end = len(split_string)
    else:
        script_end = split_string.index(PS_CLOSE)

    # Return everything between Powershell back as a string.
    return '\n'.join(split_string[script_start + 1:script_end])


def reset_dict_empty_keys(dict_object):
    """
    Reset empty values for object and convert it to None object so that we
    can us them when initiate API request
    :param dict_object: dict of properties need to be reset
    :return dict_object: Updated dict_object
    """
    for key, value in dict_object.iteritems():
        if not key:
            dict_object[key] = None
    return dict_object


def update_runtime_properties(properties=None):
    """
    Update runtime properties for node instance
    :param properties: dict of properties need to be set for node instance
    """
    properties = properties or {}
    for key, value in properties.items():
        ctx.instance.runtime_properties[key] = value


def add_resource_list_to_runtime_properties(openstack_type_name, object_list):
    """
    Update runtime properties for node instance with list of available
    resources on openstack for certain openstack type
    :param openstack_type_name: openstack resource name type
    :param object_list: list of all available resources on openstack
    """
    objects = []
    for obj in object_list:
        if type(obj) not in [str, dict]:
            obj = obj.to_dict()
        objects.append(obj)

    key_list = '{0}_list'.format(openstack_type_name)

    # if the key already exists then we need to re-generate new data and
    # omits the old one if the list command multiple times
    if ctx.instance.runtime_properties.get(key_list):
        del ctx.instance.runtime_properties[key_list]

    ctx.instance.runtime_properties[key_list] = objects


def validate_resource_quota(resource, openstack_type):
    """
    Do a validation for openstack resource to make sure it is allowed to
    create resource based on available resources created and maximum quota
    :param resource: openstack resource instance
    :param openstack_type: openstack resource type
    """
    ctx.logger.info(
        'validating resource {0} (node {1})'
        ''.format(openstack_type, ctx.node.id)
    )
    openstack_type_plural = resource.resource_plural(openstack_type)

    resource_list = list(resource.list())

    # This is the available quota for provisioning the resource
    resource_amount = len(resource_list)

    # Log message to give an indication to the caller that there will be a
    # call trigger to fetch the quota for current resource
    ctx.logger.info(
        'Fetching quota for resource {0} (node {1})'
        ''.format(openstack_type, ctx.node.id)
    )

    # This represent the quota for the provided resource openstack type
    resource_quota = resource.get_quota_sets(openstack_type_plural)

    if resource_amount < resource_quota \
            or resource_quota == INFINITE_RESOURCE_QUOTA:
        ctx.logger.debug(
            QUOTA_VALID_MSG.format(
                openstack_type,
                ctx.node.id,
                openstack_type_plural,
                resource_amount,
                resource_quota)
        )
    else:
        err_message = \
            QUOTA_INVALID_MSG.format(
                openstack_type,
                ctx.node.id,
                openstack_type_plural,
                resource_amount,
                resource_quota
            )
        ctx.logger.error('VALIDATION ERROR: {0}'.format(err_message))
        raise NonRecoverableError(err_message)


def set_runtime_properties_from_resource(ctx_node_instance,
                                         openstack_resource):
    """
    Set openstack "type" & "name" as runtime properties for current cloudify
    node instance
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param openstack_resource: Openstack resource instance
    """
    if ctx_node_instance and openstack_resource:
        ctx_node_instance.instance.runtime_properties[
            OPENSTACK_TYPE_PROPERTY] = openstack_resource.resource_type

        ctx_node_instance.instance.runtime_properties[
            OPENSTACK_NAME_PROPERTY] = openstack_resource.name


def prepare_resource_instance(class_decl, ctx_node_instance, kwargs):
    """
    This method used to prepare and instantiate instance of openstack resource
    So that it can be used to make API request to execute required operations
    :param class_decl: Class name of the resource instance we need to create
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param kwargs: Some config contains data for openstack resource that
    could be provided via input task operation
    :return: Instance of openstack resource
    """
    def get_property_by_name(property_name):
        property_value = None
        # TODO: Improve this to be more thorough.
        if property_name in ctx_node_instance.node.properties:
            property_value = \
                ctx_node_instance.node.properties.get(property_name)

        if property_name in ctx_node_instance.instance.runtime_properties:
            if isinstance(property_value, dict):
                property_value.update(
                    ctx_node_instance.instance.runtime_properties.get(
                        property_name))
            else:
                property_value = \
                    ctx_node_instance.instance.runtime_properties.get(
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
    if RESOURCE_ID in ctx_node_instance.instance.runtime_properties:
        resource_config['id'] = \
            ctx_node_instance.instance.runtime_properties[RESOURCE_ID]

    resource = class_decl(client_config=client_config,
                          resource_config=resource_config,
                          logger=ctx.logger)

    return resource


def handle_external_resource(ctx_node_instance,
                             openstack_resource,
                             existing_resource_handler=None):
    """
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param openstack_resource: Openstack resource instance
    :param existing_resource_handler: Callback handler that used to be
    called in order to execute custom operation when "use_external_resource" is
    enabled
    """

    # Get the current operation name
    operation_name = get_current_operation()

    # Validate if the "is_external" is set and the resource
    # identifier (id|name) for the Openstack is invalid raise error and
    # abort the operation
    error_message = openstack_resource.validate_resource_identifier()

    # Raise error when validation failed
    if error_message:
        raise NonRecoverableError(error_message)

    # Cannot delete/create resource when it is external
    if operation_name in ['create', 'delete']:
        ctx.logger.info(
            'Using external resource {0}'.format(RESOURCE_ID))

        try:
            # Get the remote resource
            remote_resource = openstack_resource.get()
        except openstack.exceptions.SDKException as error:
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
                ''.format(remote_resource.name))
            ctx_node_instance.instance.runtime_properties[RESOURCE_ID] \
                = remote_resource.id

            # Check if we need to run custom operation for already existed
            # resource after create operation is done
            if existing_resource_handler:
                existing_resource_handler(remote_resource)

        # Just log message that we cannot delete resource
        elif operation_name == 'delete':
            ctx.logger.info(
                'not deleting resource {0}'
                ' since an external resource is being used'
                ''.format(remote_resource.name))


def get_openstack_id():
    """
    Get the openstack resource id
    :return str: Return openstack resource id
    """
    return ctx.instance.runtime_properties[RESOURCE_ID]


def get_snapshot_name(object_type, snapshot_name, snapshot_incremental):
    """
    Generate snapshot name
    :param str object_type: Object type that snapshot is generated for (vm,
    disk, ..etc)
    :param str snapshot_name: Snapshot name
    :param bool snapshot_incremental: Flag to create an incremental snapshots
     or full backup
    :return: Snapshot name
    """
    return "{0}-{1}-{2}-{3}".format(
        object_type, get_openstack_id(), snapshot_name,
        "increment" if snapshot_incremental else "backup")


def get_current_operation():
    """ Get the current task operation from current cloudify context
    :return str: Operation name
    """
    _, _, _, operation_name = ctx.operation.name.split('.')
    return operation_name
