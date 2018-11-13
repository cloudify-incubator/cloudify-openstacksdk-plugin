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

# Based on this documentation:
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html.

# Local imports
from openstack_sdk.common import OpenstackResource


class OpenstackUser(OpenstackResource):

    def list(self):
        return self.connection.identity.users()

    def get(self):
        self.logger.debug(
            'Attempting to find this user: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        user = self.connection.identity.get_user(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug('Found user with this result: {0}'.format(user))
        return user

    def create(self):
        self.logger.debug(
            'Attempting to create user with these args: {0}'.format(
                self.config))
        user = self.connection.identity.create_user(**self.config)
        self.logger.debug('Created user with this result: {0}'.format(user))
        return user

    def delete(self):
        user = self.get()
        self.logger.debug('Attempting to delete this user: {0}'.format(user))
        result = self.connection.identity.delete_user(user)
        self.logger.debug('Deleted user with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        user = self.get()
        self.logger.debug(
            'Attempting to update this user: {0} with args {1}'.format(
                user, new_config))
        result = self.connection.identity.update_user(user, new_config)
        self.logger.debug('Updated user with this result: {0}'.format(result))
        return result


class OpenstackProject(OpenstackResource):

    def list(self):
        return self.connection.identity.projects()

    def get(self):
        self.logger.debug(
            'Attempting to find this project: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        project = self.connection.identity.get_project(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found project with this result: {0}'.format(project))
        return project

    def create(self):
        self.logger.debug(
            'Attempting to create project with these args: {0}'.format(
                self.config))
        project = self.connection.identity.create_project(**self.config)
        self.logger.debug(
            'Created project with this result: {0}'.format(project))
        return project

    def delete(self):
        project = self.get()
        self.logger.debug(
            'Attempting to delete this project: {0}'.format(project))
        result = self.connection.identity.delete_project(project)
        self.logger.debug(
            'Deleted project with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        project = self.get()
        self.logger.debug(
            'Attempting to update this project: {0} with args {1}'.format(
                project, new_config))
        result = self.connection.identity.update_project(project, new_config)
        self.logger.debug(
            'Updated project with this result: {0}'.format(result))
        return result
