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
import openstack.identity.v3.user

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import identity


class UserTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(UserTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('user')
        self.user_instance = identity.OpenstackUser(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.user_instance.connection = self.connection

    def test_get_user(self):
        user = openstack.identity.v3.user.User(**{
            'id': '1',
            'name': 'test_user',
            'description': 'Testing User',
            'domain_id': 'test_domain_id',
            'default_project_id': 'test_default_project_id',
            'enabled': True,
            'password': 'test_password',
            'email': 'test_email',
            'links': ['test1', 'test2'],
            'password_expires_at': 'test_date'

        })
        self.user_instance.resource_id = '1'
        self.fake_client.get_user = mock.MagicMock(return_value=user)

        response = self.user_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_user')
        self.assertEqual(response.domain_id, 'test_domain_id')

    def test_list_users(self):
        users = [
            openstack.identity.v3.user.User(**{
                'id': '1',
                'name': 'test_user_1',
                'description': 'Testing User 1',
                'domain_id': 'test_domain_id',
                'default_project_id': 'test_default_project_id',
                'enabled': True,
                'password': 'test_password',
                'email': 'test_email',
                'links': ['test1', 'test2'],
                'password_expires_at': 'test_date'
            }),
            openstack.identity.v3.user.User(**{
                'id': '2',
                'name': 'test_user_2',
                'description': 'Testing User 2',
                'domain_id': 'test_domain_id',
                'default_project_id': 'test_default_project_id',
                'enabled': True,
                'password': 'test_password',
                'email': 'test_email',
                'links': ['test1', 'test2'],
                'password_expires_at': 'test_date'
            }),
        ]

        self.fake_client.users = mock.MagicMock(return_value=users)

        response = self.user_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_user(self):
        user = {
            'name': 'test_user',
            'description': 'Testing User',
            'domain_id': 'test_domain_id',
            'default_project_id': 'test_default_project_id',
            'enabled': True,
            'password': 'test_password',
            'email': 'test_email',
        }

        new_res = openstack.identity.v3.user.User(**user)
        self.user_instance.config = user
        self.fake_client.create_user = mock.MagicMock(return_value=new_res)

        response = self.user_instance.create()
        self.assertEqual(response.name, user['name'])
        self.assertEqual(response.description, user['description'])

    def test_update_user(self):
        old_user = openstack.identity.v3.user.User(**{
            'id': '1',
            'name': 'test_user_1',
            'description': 'Testing User 1',
            'domain_id': 'test_domain_id',
            'default_project_id': 'test_default_project_id',
            'enabled': True,
            'password': 'test_password',
            'email': 'test_email',
            'links': ['test1', 'test2'],
            'password_expires_at': 'test_date'

        })

        new_config = {
            'name': 'test_updated_name',
            'domain_id': 'test_updated_domain_id',
            'enabled': False,
            'password': 'test_password_updated',
        }

        new_user = openstack.identity.v3.user.User(**{
            'id': '1',
            'name': 'test_updated_name',
            'description': 'Testing User 1',
            'domain_id': 'test_updated_domain_id',
            'default_project_id': 'test_default_project_id',
            'enabled': False,
            'password': 'test_password_updated',
            'email': 'test_email',
            'links': ['test1', 'test2'],
            'password_expires_at': 'test_date'

        })

        self.user_instance.resource_id = '1'
        self.fake_client.get_user = mock.MagicMock(return_value=old_user)
        self.fake_client.update_user = mock.MagicMock(return_value=new_user)

        response = self.user_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_user.name)
        self.assertNotEqual(response.is_enabled, old_user.is_enabled)
        self.assertNotEqual(response.password, old_user.password)
        self.assertNotEqual(response.domain_id, old_user.domain_id)

    def test_delete_user(self):
        user = openstack.identity.v3.user.User(**{
            'id': '1',
            'name': 'test_user',
            'description': 'Testing User',
            'domain_id': 'test_domain_id',
            'default_project_id': 'test_default_project_id',
            'enabled': True,
            'password': 'test_password',
            'email': 'test_email',
            'links': ['test1', 'test2'],
            'password_expires_at': 'test_date'
        })

        self.user_instance.resource_id = '1'
        self.fake_client.get_user = mock.MagicMock(return_value=user)
        self.fake_client.delete_user = mock.MagicMock(return_value=None)

        response = self.user_instance.delete()
        self.assertIsNone(response)
