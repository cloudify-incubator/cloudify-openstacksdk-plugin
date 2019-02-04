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

# Standard imports
import mock

# Third party imports
import openstack.compute.v2.aggregate

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import compute


class HostAggregateTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(HostAggregateTestCase, self).setUp()
        self.fake_client =\
            self.generate_fake_openstack_connection('host_aggregate')
        self.host_aggregate_instance = compute.OpenstackHostAggregate(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.host_aggregate_instance.connection = self.connection

    def test_get_host_aggregate(self):
        aggregate = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_aggregate',
            'availability_zone': 'test_availability_zone',
        })

        self.host_aggregate_instance.name = 'test_aggregate'
        self.host_aggregate_instance.id = '1'
        self.fake_client.get_aggregate = mock.MagicMock(return_value=aggregate)

        response = self.host_aggregate_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_aggregate')

    def test_list_aggregates(self):
        aggregate_list = [
            openstack.compute.v2.aggregate.Aggregate(**{
                'id': '1',
                'name': 'test_aggregate_1',
                'availability_zone': 'test_availability_zone_1',
            }),
            openstack.compute.v2.aggregate.Aggregate(**{
                'id': '2',
                'name': 'test_aggregate_2',
                'availability_zone': 'test_availability_zone_2',
            }),
        ]

        self.fake_client.aggregates = \
            mock.MagicMock(return_value=aggregate_list)
        response = self.host_aggregate_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_aggregate(self):
        config = {
            'name': 'test_aggregate',
            'availability_zone': 'test_availability_zone',
        }

        aggregate = {
            'id': '1',
            'name': 'test_aggregate',
            'availability_zone': 'test_availability_zone',
        }

        self.host_aggregate_instance.config = config
        new_res = openstack.compute.v2.aggregate.Aggregate(**aggregate)
        self.fake_client.create_aggregate = \
            mock.MagicMock(return_value=new_res)

        response = self.host_aggregate_instance.create()
        self.assertEqual(response.name, config['name'])

    def test_update_aggregate(self):
        old_aggregate = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_aggregate',
            'availability_zone': 'test_availability_zone',
        })

        new_config = {
            'name': 'update_test_aggregate',
        }

        new_aggregate = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'update_test_aggregate',
            'availability_zone': 'test_availability_zone',
        })

        self.host_aggregate_instance.resource_id = '1'
        self.fake_client.get_aggregate = \
            mock.MagicMock(return_value=old_aggregate)
        self.fake_client.update_aggregate =\
            mock.MagicMock(return_value=new_aggregate)

        response = self.host_aggregate_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_aggregate.name)

    def test_delete_server(self):
        aggregate = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_aggregate',
            'availability_zone': 'test_availability_zone',

        })

        self.host_aggregate_instance.resource_id = '1'
        self.fake_client.get_aggregate = mock.MagicMock(return_value=aggregate)
        self.fake_client.delete_aggregate = mock.MagicMock(return_value=None)

        response = self.host_aggregate_instance.delete()
        self.assertIsNone(response)
