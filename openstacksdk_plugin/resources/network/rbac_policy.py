# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
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
from openstack_sdk.resources.networks import OpenstackRBACPolicy
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           OPENSTACK_TYPE_PROPERTY,
                                           RBAC_POLICY_OPENSTACK_TYPE,
                                           RBAC_POLICY_RELATIONSHIP_TYPE)
from openstacksdk_plugin.utils import (reset_dict_empty_keys,
                                       validate_resource_quota,
                                       add_resource_list_to_runtime_properties,
                                       find_relationships_by_relationship_type)


def _get_rbac_policy_target_from_relationship():

    # Lookup the rbac policy relationship so that we can get the info that
    # we need to create rbac policy and apply it for target object
    rels = \
        find_relationships_by_relationship_type(
            ctx, RBAC_POLICY_RELATIONSHIP_TYPE
        )

    # It could be no relationship find for the current node context which
    # means that the node is not associated with any other node
    if len(rels) == 0:
        ctx.logger.info(
            'Resource for which RBAC policy may be applied '
            'not found using {0} relationship'
            .format(RBAC_POLICY_RELATIONSHIP_TYPE)
        )

        return None

    # Since rbac policy allow only to be applied to one object at a time
    # then we cannot define link rbac policy node with multiple nodes via
    # "cloudify.relationships.openstack.rbac_policy_applied_to"
    elif len(rels) > 1:
        raise NonRecoverableError(
            'Multiple ({0}) resources for which RBAC policy may be applied '
            'found using relationship {1}'
            .format(
                len(rels),
                RBAC_POLICY_RELATIONSHIP_TYPE
            )
        )

    # Lookup the target instance in order to get the target object
    # runtime properties which represent "type" & "id"
    resource = rels[0].target.instance
    ctx.logger.info(
        '{0} resource for which RBAC policy may be applied '
        'found using {1} relationship)'
        .format(resource, RBAC_POLICY_RELATIONSHIP_TYPE)
    )

    # Get the instance runtime properties for both "id" & "type"
    resource_id = resource.runtime_properties.get(RESOURCE_ID)
    resource_type = resource.runtime_properties.get(OPENSTACK_TYPE_PROPERTY)

    # If we cannot find these attributes then we can skip that and depend on
    # the rbac policy to resolve "object_type" & "object_id"
    if not resource_id or not resource_type:
        ctx.logger.warn(
            'Found using relationship resource has not defined either '
            '"id" or "type" runtime_property. Skipping.'
        )

        return None

    # Return the object info needed to be wrapped into API request when
    # create rbac request
    return {
        'object_type': resource_type,
        'object_id': resource_id
    }


def _validate_config_for_applied_rbac_resource(input_dict, target_object):
    if target_object:
        for key in target_object.keys():
            if input_dict.get(key):
                raise NonRecoverableError(
                    'Multiple definitions of resource for which '
                    'RBAC policy should be applied. '
                    'You specified it both using properties / operation '
                    'inputs and relationship.'
                )


def _get_rbac_policy_target_object(openstack_resource, args):
    # Try to lookup the object_type & object_id from relationships first
    object_info = _get_rbac_policy_target_from_relationship()

    # Validate the config rbac resources
    if object_info:
        for config in [openstack_resource.config, args]:
            _validate_config_for_applied_rbac_resource(config, object_info)

    return object_info


def _prepare_rbac_policy_object(openstack_resource, args):
    # Try to lookup if there is any target object that should be apply rabc on
    target_object = _get_rbac_policy_target_object(openstack_resource, args)
    if target_object:
        openstack_resource.config['object_id'] = target_object['object_id']
        openstack_resource.config['object_type'] = target_object['object_type']

    # If there is no target object (No relationship exists) then we need to
    # check if the current node config contains all the info needed for
    # target object
    else:
        object_id = openstack_resource.cofig.get('object_id')
        object_type = openstack_resource.cofig.get('object_type')
        if not (object_id and object_type):
            raise NonRecoverableError(
                'Both object_id & object_type should be provided in order'
                ' to create rbac policy'
            )


@with_openstack_resource(OpenstackRBACPolicy)
def create(openstack_resource, args):
    """
    Create openstack rbac policy instance
    :param openstack_resource: instance of openstack rbac policy resource
    """
    _prepare_rbac_policy_object(openstack_resource, args)
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackRBACPolicy)
def delete(openstack_resource):
    """
    Delete current openstack rbac policy instance
    :param openstack_resource: instance of openstack srbac policy resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackRBACPolicy)
def update(openstack_resource, args):
    """
    Update openstack rbac policy by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack rbac policy resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackRBACPolicy)
def list_rbac_policies(openstack_resource, query=None):
    """
    List openstack rbac policies based on filters applied
    :param openstack_resource: Instance of current openstack rbac policy
    :param kwargs query: Optional query parameters to be sent to limit
            the rbac policies being returned.
    """

    rbac_policies = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(RBAC_POLICY_OPENSTACK_TYPE,
                                            rbac_policies)


@with_openstack_resource(OpenstackRBACPolicy)
def find_and_delete(openstack_resource, args):
    _prepare_rbac_policy_object(openstack_resource, args)
    rbac_policy_config = openstack_resource.config
    rbac_policies = openstack_resource.list()

    for rbac_policy in rbac_policies:
        if all(item in rbac_policy.items()
               for item in rbac_policy_config.items()):

            # Found the target object which should be deleted
            ctx.logger.info(
                'Found RBAC policy with ID: {0} - deleting ...'
                ''.format(rbac_policy.id)
            )

            # We need to delete the matched object
            openstack_resource.resource_id = rbac_policy.id
            openstack_resource.delete()
            return

    ctx.logger.warn('No suitable RBAC policy found')


@with_openstack_resource(OpenstackRBACPolicy)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create rbac policy resource in openstack
    :param openstack_resource: Instance of current openstack rbac policy
    """
    validate_resource_quota(openstack_resource, RBAC_POLICY_OPENSTACK_TYPE)
    ctx.logger.debug('OK: rbac policy configuration is valid')
