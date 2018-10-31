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

# Third party imports
import openstack


class OpenstackResource(object):

    def __init__(self, client_config, resource_config=None, logger=None):
        self.connection = openstack.connect(**client_config)
        self.config = resource_config or {}
        self.name = self.config.get('name')
        self.resource_id = None if 'id' not in self.config else self.config['id']
        self.logger = logger

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def update(self, new_config=None):
        raise NotImplementedError()
