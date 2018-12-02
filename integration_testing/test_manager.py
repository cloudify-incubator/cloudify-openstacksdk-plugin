########
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

import os
import uuid
from integration_tests.tests.test_cases import AgentTestWithPlugins
from integration_tests.tests import utils as test_utils


class PluginWagonBuilderMixin(object):

    # TODO: Building Wagon on a Docker Container.
    # TODO: It will override the build _create_test_wagon method of AgentTestWithPlugins.
    pass


class OpenstackAgentlessTestCase(AgentTestWithPlugins, PluginWagonBuilderMixin):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def client_config(self):
        return {
            'auth_url': os.getenv('openstack_auth_url'),
            'username': os.getenv('openstack_username'),
            'password': os.getenv('openstack_password'),
            'project_name': os.getenv('openstack_project_name'),
            'region_name': os.getenv('openstack_region_name'),
        }

    def check_main_blueprint(self):
        blueprint_id = uuid.uuid4()
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'example_subnet_cidr': '10.10.0.0/24',
                'example_fixed_ip': '10.10.0.11',
                'name_prefix': 'manager_'
            }
        )
        self.deploy_application(
            test_utils.get_resource(os.path.join(
                self.base_path, 'examples/local/blueprint.yaml')),
            blueprint_id=blueprint_id,
            deployment_id=blueprint_id,
            inputs=self.inputs)

    def test_blueprints(self):
        package_dir = os.path.abspath(os.path.join(self.base_path, '..'))
        self.upload_mock_plugin('cloudify-openstacksdk-plugin', package_dir)
        self.check_main_blueprint()
