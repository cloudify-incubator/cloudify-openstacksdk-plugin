# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Standard imports
import mock

# Third party imports
import openstack.image.v2.image

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import images


class ImageTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(ImageTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('image')
        self.image_instance = images.OpenstackImage(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.image_instance.connection = self.connection

    def test_get_image(self):
        image = openstack.image.v2.image.Image(**{
            'id': '1',
            'name': 'test_image',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })
        self.image_instance.resource_id = '1'
        self.fake_client.get_image = mock.MagicMock(return_value=image)

        response = self.image_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_image')
        self.assertEqual(response.container_format, 'test_bare')

    def test_list_images(self):
        image_list = [
            openstack.image.v2.image.Image(**{
                'id': '1',
                'name': 'test_image_1',
                'container_format': 'test_bare',
                'disk_format': 'test_format_1',
                'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
                'size': 258540032
            }),
            openstack.image.v2.image.Image(**{
                'id': '2',
                'name': 'test_image_2',
                'container_format': 'test_bare',
                'disk_format': 'test_format',
                'checksum': '4d421c8cf05e1fbdc8b543ded23dfsaf',
                'size': 223540032
            })
        ]

        self.fake_client.images = mock.MagicMock(return_value=image_list)

        response = self.image_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_image(self):
        image = {
            'id': '2',
            'name': 'test_image_2',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '4d421c8cf05e1fbdc8b543ded23dfsaf',
            'size': 223540032,
        }
        new_res = openstack.image.v2.image.Image(**image)
        self.image_instance.config = image
        self.fake_client.upload_image = mock.MagicMock(return_value=new_res)

        response = self.image_instance.create()
        self.assertEqual(response.id, image['id'])
        self.assertEqual(response.name, image['name'])

    def test_update_image(self):
        old_image = openstack.image.v2.image.Image(**{
            'id': '2',
            'name': 'test_image_2',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '4d421c8cf05e1fbdc8b543ded23dfsaf',
            'size': 223540032,
            'visibility': True

        })

        new_config = {
            'visibility': False
        }

        new_image = openstack.image.v2.image.Image(**{
            'id': '2',
            'name': 'test_image_2',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '4d421c8cf05e1fbdc8b543ded23dfsaf',
            'size': 223540032,
            'visibility': False

        })

        self.image_instance.resource_id = '2'
        self.fake_client.get_image = mock.MagicMock(return_value=old_image)
        self.fake_client.update_image = mock.MagicMock(return_value=new_image)

        response = self.image_instance.update(new_config=new_config)
        self.assertNotEqual(response.visibility, old_image.visibility)

    def test_delete_image(self):
        image = openstack.image.v2.image.Image(**{
            'id': '2',
            'name': 'test_image_2',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '4d421c8cf05e1fbdc8b543ded23dfsaf',
            'size': 223540032,
            'visibility': True

        })

        self.image_instance.resource_id = '2'
        self.fake_client.get_image = mock.MagicMock(return_value=image)
        self.fake_client.delete_image = mock.MagicMock(return_value=None)

        response = self.image_instance.delete()
        self.assertIsNone(response)
