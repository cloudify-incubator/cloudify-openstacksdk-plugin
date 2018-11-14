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

from os import getenv
import unittest

import openstack
from cloudify.workflows import local

import resource_interface_mappings


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations',
)


class LiveUseCaseTests(unittest.TestCase):
    """ Test a use case using a "local" Cloudify Workflow.

    Write a blueprint for a particular use case,
    for example creating a port with allowed address pairs.

    You need the client config in your inputs, e.g.:
    ```yaml
      auth_url:
        type: string

      username:
        type: string

      password:
        type: string

      region_name:
        type: string

      project_name:
        type: string
    ```

    To setup your test environment in PyCharm,
    add the following environment variables:

    ```bash
    openstack_username=.......;openstack_password=.........;
    openstack_project_name=.....;openstack_region_name=RegionOne;
    openstack_auth_url=https://....;=
    ```

    """

    def setUp(self):
        super(LiveUseCaseTests, self).setUp()

    @property
    def client_config(self):
        return {
            'auth_url': getenv('openstack_auth_url'),
            'username': getenv('openstack_username'),
            'password': getenv('openstack_password'),
            'project_name': getenv('openstack_project_name'),
            'region_name': getenv('openstack_region_name'),
        }

    @staticmethod
    def resolve_resource_interface(node_type):
        try:
            return getattr(resource_interface_mappings, node_type.split('.')[-1])
        except AttributeError:
            return None

    def get_resource_interfaces(self):
        resource_interface_list = []
        for node_instance in self.cfy_local.storage.get_node_instances():
            node_template = \
                self.cfy_local.storage.get_node(node_instance.node_id)
            resource_interface = \
                self.resolve_resource_interface(
                    node_template.type)
            if not resource_interface:
                continue
            resource_interface_list.append(
                resource_interface(
                    node_instance.node_id,
                    self.client_config
                ))
        return resource_interface_list

    def verify_no_conflicting_resources(self):
        """ This method checks that there are no conflicting resources in
        Openstack before we run a test.
        :return: Nothing.
        :Raises Exception: Raises an exception if there are such resources.
        """
        for resource_interface in self.get_resource_interfaces():
            try:
                conflicting_resource = resource_interface.get()
            except openstack.exceptions.SDKException:
                continue
            raise Exception(
                'Conflicting resource found {0}'.format(conflicting_resource))

    def delete_all_resources(self):
        """Deletes orphan resources in Openstack.
        :return: Nothing.
        """
        for resource_interface in self.get_resource_interfaces():
            try:
                resource_interface.delete()
            except openstack.exceptions.SDKException:
                pass

    def initialize_local_blueprint(self):
        self.cfy_local = local.init_env(
            self.blueprint_path,
            self.test_name,
            inputs=self.inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        self.verify_no_conflicting_resources()
        self.addCleanup(self.delete_all_resources)

    def test_network_example(self, *_):
        self.test_name = 'test_network_example'
        self.blueprint_path = './examples/local/network.yaml'
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'example_subnet_cidr': '10.10.0.0/24',
                'example_fixed_ip': '10.10.0.11',
                'name_prefix': 'network_'
            }
        )
        self.initialize_local_blueprint()
        # execute install workflow
        self.cfy_local.execute(
            'install', task_retries=30, task_retry_interval=1)
        # execute uninstall workflow
        self.cfy_local.execute(
            'uninstall', task_retries=30, task_retry_interval=1)

    def test_keypair_example(self, *_):
        self.test_name = 'test_keypair_example'
        self.blueprint_path = './examples/local/keypair.yaml'
        self.inputs = dict(self.client_config)
        self.initialize_local_blueprint()
        # execute install workflow
        self.cfy_local.execute(
            'install',
            task_retries=30,
            task_retry_interval=1)
        # execute uninstall workflow
        self.cfy_local.execute(
            'uninstall',
            task_retries=30,
            task_retry_interval=1)
