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


class OpenstackImage(OpenstackResource):

    def list(self, query=None):
        query = query or {}
        return self.connection.image.images(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this image: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        image = self.connection.image.get_image(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found image with this result: {0}'.format(image))
        return image

    def create(self):
        self.logger.debug(
            'Attempting to create image with these args: {0}'.format(
                self.config))
        image = self.connection.image.upload_image(**self.config)
        self.logger.debug(
            'Created image with this result: {0}'.format(image))
        return image

    def delete(self):
        image = self.get()
        self.logger.debug(
            'Attempting to delete this image: {0}'.format(image))
        result = self.connection.image.delete_image(image)
        self.logger.debug(
            'Deleted image with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        image = self.get()
        self.logger.debug(
            'Attempting to update this image: {0} with args {1}'.format(
                image, new_config))
        result = self.connection.image.update_image(image, new_config)
        self.logger.debug(
            'Updated image with this result: {0}'.format(result))
        return result
