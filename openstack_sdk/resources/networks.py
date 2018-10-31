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

# Based on this documentation: https://docs.openstack.org/openstacksdk/latest/user/proxies/network.html.

from openstack_sdk.common import OpenstackResource


class OpenstackNetwork(OpenstackResource):

    def list(self):
        return self.connection.network.networks()

    def get(self):
        self.logger.debug(
            'Attempting to find this network: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        network = self.connection.network.find_network()
        self.logger.debug(
            'Found network with this result: {0}'.format(network))
        return network

    def create(self):
        self.logger.debug(
            'Attempting to create network with these args: {0}'.format(
                self.config))
        network = self.connection.network.create_network(**self.config)
        self.logger.debug(
            'Created network with this result: {0}'.format(network))
        return network

    def delete(self):
        network = self.get()
        self.logger.debug(
            'Attempting to delete this network: {0}'.format(network))
        result = self.connection.network.delete_network(network)
        self.logger.debug(
            'Deleted network with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        network = self.get()
        self.logger.debug(
            'Attempting to update this network: {0} with args {1}'.format(
                network, new_config))
        result = self.connection.network.update_network(network, new_config)
        self.logger.debug(
            'Updated network with this result: {0}'.format(result))
        return result


class OpenstackSubnet(OpenstackResource):

    def list(self):
        return self.connection.network.subnets()

    def get(self):
        self.logger.debug(
            'Attempting to find this subnet: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        subnet = self.connection.network.find_subnet()
        self.logger.debug(
            'Found subnet with this result: {0}'.format(subnet))
        return subnet

    def create(self):
        self.logger.debug(
            'Attempting to create subnet with these args: {0}'.format(
                self.config))
        subnet = self.connection.network.create_subnet(**self.config)
        self.logger.debug(
            'Created subnet with this result: {0}'.format(subnet))
        return subnet

    def delete(self):
        subnet = self.get()
        self.logger.debug(
            'Attempting to delete this subnet: {0}'.format(subnet))
        result = self.connection.network.delete_subnet(subnet)
        self.logger.debug(
            'Deleted subnet with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        subnet = self.get()
        self.logger.debug(
            'Attempting to update this subnet: {0} with args {1}'.format(
                subnet, new_config))
        result = self.connection.network.update_subnet(subnet, new_config)
        self.logger.debug(
            'Updated subnet with this result: {0}'.format(result))
        return result
