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


class OpenstackServer(OpenstackResource):

    def list(self):
        return self.connection.compute.servers()

    def get(self):
        self.logger.debug(
            'Attempting to find this server: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        server = self.connection.compute.get_server(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found server with this result: {0}'.format(server))
        return server

    def create(self):
        self.logger.debug(
            'Attempting to create server with these args: {0}'.format(
                self.config))
        server = self.connection.compute.create_server(**self.config)
        self.logger.debug(
            'Created server with this result: {0}'.format(server))
        return server

    def delete(self):
        server = self.get()
        self.logger.debug(
            'Attempting to delete this server: {0}'.format(server))
        result = self.connection.compute.delete_server(server)
        self.logger.debug(
            'Deleted server with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        server = self.get()
        self.logger.debug(
            'Attempting to update this server: {0} with args {1}'.format(
                server, new_config))
        result = self.connection.compute.update_server(server, new_config)
        self.logger.debug(
            'Updated server with this result: {0}'.format(result))
        return result


class OpenstackServerGroup(OpenstackResource):

    def list(self):
        return self.connection.compute.server_groups()

    def get(self):
        self.logger.debug(
            'Attempting to find this server group: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        server_group = self.connection.compute.get_server_group(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found server group with this result: {0}'.format(server_group))
        return server_group

    def create(self):
        self.logger.debug(
            'Attempting to create server group with these args: {0}'.format(
                self.config))
        server_group =\
            self.connection.compute.create_server_group(**self.config)
        self.logger.debug(
            'Created server group with this result: {0}'.format(server_group))
        return server_group

    def delete(self):
        server_group = self.get()
        self.logger.debug(
            'Attempting to delete this server group: {0}'.format(server_group))
        result = self.connection.compute.delete_server_group(server_group)
        self.logger.debug(
            'Deleted server group with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        pass


class OpenstackKeyPair(OpenstackResource):

    def list(self):
        return self.connection.compute.keypairs()

    def get(self):
        self.logger.debug(
            'Attempting to find this key pair: {0}'.format(self.name))

        key_pair = self.connection.compute.get_keypair(self.name,
                                                       ignore_missing=False)

        self.logger.debug(
            'Found key pair with this result: {0}'.format(key_pair))
        return key_pair

    def create(self):
        self.logger.debug(
            'Attempting to create key pair with these args: {0}'.format(
                self.config))
        key_pair = self.connection.compute.create_keypair(**self.config)
        self.logger.debug(
            'Created key pair with this result: {0}'.format(key_pair))
        return key_pair

    def delete(self):
        key_pair = self.get()
        self.logger.debug(
            'Attempting to delete this key pair: {0}'.format(key_pair))
        result = self.connection.compute.delete_keypair(key_pair)
        self.logger.debug(
            'Deleted key pair with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        pass


class OpenstackFlavor(OpenstackResource):

    def list(self):
        return self.connection.compute.flavors()

    def get(self):
        self.logger.debug(
            'Attempting to find this flavor: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        flavor = self.connection.compute.get_flavor(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found flavor with this result: {0}'.format(flavor))
        return flavor

    def create(self):
        self.logger.debug(
            'Attempting to create flavor with these args: {0}'.format(
                self.config))
        flavor = self.connection.compute.create_flavor(**self.config)
        self.logger.debug(
            'Created server image with this result: {0}'.format(flavor))
        return flavor

    def delete(self):
        flavor = self.get()
        self.logger.debug(
            'Attempting to delete this flavor: {0}'.format(flavor))
        result = self.connection.compute.delete_flavor(flavor)
        self.logger.debug(
            'Deleted flavor with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        flavor = self.get()
        self.logger.debug(
            'Attempting to update this flavor:'
            ' {0} with args {1}'.format(flavor, new_config))
        result = self.connection.compute.update_server(flavor, new_config)
        self.logger.debug(
            'Updated flavor with this result: {0}'.format(result))
        return result
