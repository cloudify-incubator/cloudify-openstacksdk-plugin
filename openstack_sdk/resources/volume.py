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


class OpenstackVolumeType(OpenstackResource):
    service_type = 'volume'
    resource_type = 'volume_type'

    def list(self):
        return self.connection.block_storage.types()

    def get(self):
        self.logger.debug(
            'Attempting to find this volume type: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        volume_type = self.connection.block_storage.get_type(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found image with this result: {0}'.format(volume_type))
        return volume_type

    def create(self):
        self.logger.debug(
            'Attempting to create volume type with these args: {0}'.format(
                self.config))
        volume_type = self.connection.block_storage.create_type(**self.config)
        self.logger.debug(
            'Created volume type with this result: {0}'.format(volume_type))
        return volume_type

    def delete(self):
        volume_type = self.get()
        self.logger.debug(
            'Attempting to delete this volume type: {0}'.format(volume_type))
        result = self.connection.block_storage.delete_type(volume_type)
        self.logger.debug(
            'Deleted volume type with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        pass
