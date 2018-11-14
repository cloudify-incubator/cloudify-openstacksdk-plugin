from os import getenv
import unittest

import openstack
from cloudify.workflows import local

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

    Your node template names should end with the name of the
    type of resource separated by a dash.
    Your resource name should have a test_prefix followed by the type:

    ```yaml
      example-security_group:
        type: cloudify.nodes.openstack.SecurityGroup
        properties:
          client_config: *client_config
          resource_config:
            name: { concat: [ { get_input: name_prefix }, 'security_group' ] }
            description: >
                'A security group created by Cloudify OpenStack SDK plugin.'
    ```

    These values are used to resolve conflicts and cleanup.

    """

    def setUp(self):
        super(LiveUseCaseTests, self).setUp()

    def _get_get_call(self, _client_name, _node_instance):
        """ This method finds the client call for getting a resource.
        :param _client: The Openstack Client
        :param _node_instance: The Cloudify Node Instance
        :return: The appropriate method for getting a particular resource.
        """
        client = getattr(self.client, _client_name)
        name = _node_instance.node_id.split('-')[-1]
        function_name = 'get_{0}'.format(name)
        return getattr(client, function_name)

    def _get_delete_call(self, client_name, _node_instance):
        """ This method finds the client call for deleting a resource.
        :param _client: The Openstack Client
        :param _node_instance: The Cloudify Node Instance
        :return: The appropriate method for deleting a particular resource.
        """
        client = getattr(self.client, client_name)
        name = _node_instance.node_id.split('-')[-1]
        function_name = 'delete_{0}'.format(name)
        return getattr(client, function_name)

    def verify_no_conflicting_resources(self, client_name):
        """ This method checks that there are no conflicting resources in
        Openstack before we run a test.
        :param client_name: The appropriate client,
            such as "network" or "compute".
        :return: Nothing. Raises if a resource is found.
        """
        for node_instance in self.cfy_local.storage.get_node_instances():
            node_template = \
                self.cfy_local.storage.get_node(node_instance.node_id)
            if node_template.type == \
                    'cloudify.nodes.openstack.SecurityGroupRule':
                continue
            get_call = self._get_get_call(client_name, node_instance)
            try:
                conflicting_resource = get_call(
                    node_template.properties['resource_config']['name'])
            except openstack.exceptions.SDKException:
                continue
            raise Exception(
                'Conflicting resource found {0}'.format(conflicting_resource))

    def clean_up_script(self, client_name):
        try:
            for node_instance in self.cfy_local.storage.get_node_instances():
                delete_call = self._get_delete_call(client_name, node_instance)
                delete_call(node_instance.runtime_properties['id'])
        except openstack.exceptions.SDKException:
            pass

    @property
    def client_config(self):
        return {
            'auth_url': getenv('openstack_auth_url'),
            'username': getenv('openstack_username'),
            'password': getenv('openstack_password'),
            'project_name': getenv('openstack_project_name'),
            'region_name': getenv('openstack_region_name'),
        }

    def _check_primary_identifier_property_node_instances(self):
        for instance in self.instances:
            self.assertIn('id', instance.runtime_properties)

    def test_network_example_blueprint(self, *_):

        inputs = dict(self.client_config)
        inputs.update(
            {
                'example_subnet_cidr': '10.10.0.0/24',
                'example_fixed_ip': '10.10.0.11',
                'name_prefix': 'network_'
            }
        )

        self.cfy_local = local.init_env(
            './examples/local/network.yaml',
            name='example_network_blueprint',
            inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        self.client = openstack.connect(**self.client_config)
        self.verify_no_conflicting_resources('network')
        self.addCleanup(self.clean_up_script, 'network')

        # execute install workflow
        self.cfy_local.execute(
            'install', task_retries=30, task_retry_interval=1)
        self.instances = self.cfy_local.storage.get_node_instances()
        self.assertEqual(len(self.instances), 6)
        self._check_primary_identifier_property_node_instances()
        # execute uninstall workflow
        self.cfy_local.execute(
            'uninstall', task_retries=30, task_retry_interval=1)

    def test_keypair_example(self, *_):

        inputs = dict(self.client_config)
        inputs.update(
            {
                'name_prefix': 'compute_'
            }
        )

        self.cfy_local = local.init_env(
            './examples/local/keypair.yaml',
            name='example_keypair_blueprint',
            inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        self.client = openstack.connect(**self.client_config)
        self.verify_no_conflicting_resources('compute')
        self.addCleanup(self.clean_up_script, 'compute')

        # execute install workflow
        self.cfy_local.execute(
            'install', task_retries=30, task_retry_interval=1)
        self.instances = self.cfy_local.storage.get_node_instances()
        self.assertEqual(len(self.instances), 1)
        self._check_primary_identifier_property_node_instances()
        # execute uninstall workflow
        self.cfy_local.execute(
            'uninstall', task_retries=30, task_retry_interval=1)
