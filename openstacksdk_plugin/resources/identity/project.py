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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Third party imports
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_sdk.resources.identity import (OpenstackProject,
                                              OpenstackUser,
                                              OpenstackRole)
from openstacksdk_plugin.decorators import with_openstack_resource
from openstacksdk_plugin.constants import (RESOURCE_ID,
                                           PROJECT_OPENSTACK_TYPE,
                                           IDENTITY_USERS,
                                           IDENTITY_ROLES,
                                           IDENTITY_QUOTA)
from openstacksdk_plugin.utils import (validate_resource_quota,
                                       reset_dict_empty_keys,
                                       add_resource_list_to_runtime_properties)


def _assign_users(project_resource, users):
    """
    Assign users to project
    :param project_resource: project resource instance (OpenstackProject)
    :param users: List of users that need to be assigned to project with roles
    """
    # Create user resource to be able to get info about user
    user_resource = OpenstackUser(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    # Create user role resource to be able to get info about role
    role_resource = OpenstackRole(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    for user in users:
        user_roles = user.get(IDENTITY_ROLES, [])
        user_item = user_resource.find_user(user.get('name'))
        if not user_item:
            raise NonRecoverableError('User {0} is not found'
                                      ''.format(user['name']))

        for role in user_roles:
            user_role = role_resource.find_role(role)
            if not user_role:
                raise NonRecoverableError('Role {0} is not found'.format(role))

            # Assign project role to user
            role_resource.assign_project_role_to_user(
                project_id=project_resource.resource_id,
                user_id=user_item.id,
                role_id=user_role.id)

            ctx.logger.info(
                'Assigned user {0} to project {1} with role {2}'.format(
                    user_item.id, project_resource.resource_id, user_role.id))


def _validate_users(client_config, users):
    """
    This method will validate if the users are already exists before doing
    any role assignment. Morever, it will check if the roles also exist or not
    :param list users: List of users (dict) that contains user names and
    roles associated
    :param client_config: Openstack configuration in order to connect to
    openstack
    """

    # Create user resource to be able to get info about user
    user_resource = OpenstackUser(client_config=client_config,
                                  logger=ctx.logger)

    # Create user role resource to be able to get info about role
    role_resource = OpenstackRole(client_config=client_config,
                                  logger=ctx.logger)

    user_names = [user.get('name') for user in users]
    if len(user_names) > len(set(user_names)):
        raise NonRecoverableError(' Provided users are not unique')

    for user_name in user_names:
        user = user_resource.find_user(user_name)
        if not user:
            raise NonRecoverableError(
                'User {0} is not found'.format(user_name))

    for user in users:
        if len(user[IDENTITY_ROLES]) > len(set(user[IDENTITY_ROLES])):
            msg = 'Roles for user {0} are not unique'
            raise NonRecoverableError(msg.format(user.get('name')))

    role_names = {role for user in users for role in user.get(IDENTITY_ROLES)}
    for role_name in role_names:
        user_role = role_resource.find_role(role_name)
        if not user_role:
            raise NonRecoverableError(
                'Role {0} is not found'.format(role_name))


@with_openstack_resource(OpenstackProject)
def create(openstack_resource):
    """
    Create openstack project resource
    :param openstack_resource: Instance of openstack project resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackProject)
def start(openstack_resource):
    """
    Prepare users to be added to created project
    :param openstack_resource: Instance of openstack project resource
    """

    # Check if project node has associated users that should be added
    if ctx.node.properties.get(IDENTITY_USERS):

        # Before start assigning roles user, there is a validation that must be
        # run first to check if the the provided users and their roles are
        # already exist
        users = ctx.node.properties[IDENTITY_USERS]
        _validate_users(openstack_resource.client_config, users)

        # Assign project role to users
        _assign_users(openstack_resource, users)

    # Check if project node has quota information that should be updated for
    # project
    # TODO The openstack should be extended in order to add support for
    #  quota update
    if ctx.node.properties.get(IDENTITY_QUOTA):
        raise NonRecoverableError('Openstack SDK does not support updating '
                                  'quota for project')


@with_openstack_resource(OpenstackProject)
def delete(openstack_resource):
    """
    Delete current openstack project
    :param openstack_resource: instance of openstack project resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackProject)
def update(openstack_resource, args):
    """
    Update openstack project by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack project resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackProject)
def list_projects(openstack_resource, query=None):
    """
    List openstack projects
    :param openstack_resource: Instance of openstack project.
    :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.
    """
    projects = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(PROJECT_OPENSTACK_TYPE, projects)


@with_openstack_resource(OpenstackProject)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create project resource in openstack
    :param openstack_resource: Instance of current openstack project
    """
    validate_resource_quota(openstack_resource, PROJECT_OPENSTACK_TYPE)
    ctx.logger.debug('OK: project configuration is valid')


@with_openstack_resource(OpenstackProject)
def get_project_quota(openstack_resource):
    """
    This method is to get quota for project resource in openstack
    :param openstack_resource: Instance of current openstack project
    """
    # TODO The openstack should be extended in order to add support for
    #  retrieving quota for project
    raise NonRecoverableError('Openstack SDK does not support retrieving '
                              'quota for project')


@with_openstack_resource(OpenstackProject)
def update_project_quota(openstack_resource):
    """
    This method is to update quota project resource in openstack
    :param openstack_resource: Instance of current openstack project
    """
    # TODO The openstack should be extended in order to add support for
    #  get update
    raise NonRecoverableError('Openstack SDK does not support updating '
                              'quota for project')
