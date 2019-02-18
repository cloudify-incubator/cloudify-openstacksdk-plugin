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

# Based on this documentation:
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html.

# Local imports
from openstack_sdk.common import OpenstackResource


class OpenstackServer(OpenstackResource):
    service_type = 'compute'
    resource_type = 'server'

    def list(self, details=True, all_projects=False, query=None):
        query = query or {}
        self.logger.debug('Attempting to list servers')
        return self.connection.compute.servers(details, all_projects, **query)

    def get(self):
        self.logger.debug(
            'Attempting to find this server: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        server = self.connection.compute.get_server(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found server with this result: {0}'.format(server))
        return server

    def create(self):
        self.logger.debug(
            'Attempting to create server with these args: {0}'.format(
                self.config))
        server = self.connection.compute.create_server(**self.config)
        self.logger.debug(
            'Created server with this result: {0}'.format(server))
        return server

    def delete(self):
        server = self.get()
        self.logger.debug(
            'Attempting to delete this server: {0}'.format(server))
        result = self.connection.compute.delete_server(server)
        self.logger.debug(
            'Deleted server with this result: {0}'.format(result))
        return result

    def reboot(self, reboot_type):
        server = self.get()
        self.logger.debug(
            'Attempting to reboot this server: {0}'.format(server))
        self.connection.compute.reboot_server(server, reboot_type)

    def resume(self):
        server = self.get()
        self.logger.debug(
            'Attempting to resume this server: {0}'.format(server))
        self.connection.compute.resume_server(server)

    def suspend(self):
        server = self.get()
        self.logger.debug(
            'Attempting to suspend this server: {0}'.format(server))
        self.connection.compute.suspend_server(server)

    def backup(self, name, backup_type, rotation):
        server = self.get()
        self.logger.debug(
            'Attempting to backup this server: {0}'.format(server))
        self.connection.compute.backup_server(server,
                                              name,
                                              backup_type,
                                              rotation)

    def rebuild(self, image, name=None, admin_password='', **attr):
        server = self.get()
        name = name or server.name
        attr['image'] = image
        self.logger.debug(
            'Attempting to rebuild this server: {0}'.format(server))

        self.connection.compute.rebuild_server(server,
                                               name,
                                               admin_password,
                                               **attr)

    def create_image(self, name, metadata=None):
        server = self.get()
        self.logger.debug(
            'Attempting to create image for this server: {0}'.format(server))
        self.connection.compute.create_server_image(
            server, name, metadata=metadata
        )

    def update(self, new_config=None):
        server = self.get()
        self.logger.debug(
            'Attempting to update this server: {0} with args {1}'.format(
                server, new_config))
        result = self.connection.compute.update_server(server, **new_config)
        self.logger.debug(
            'Updated server with this result: {0}'.format(result))
        return result

    def start(self):
        server = self.get()
        self.logger.debug(
            'Attempting to start this server: {0}'.format(server))
        self.connection.compute.start_server(server)

    def stop(self):
        server = self.get()
        self.logger.debug(
            'Attempting to stop this server: {0}'.format(server))
        self.connection.compute.stop_server(server)

    def get_server_password(self):
        server = self.get()
        self.logger.debug(
            'Attempting to get server'
            ' password for this server: {0}'.format(server))
        return self.connection.compute.get_server_password(server)


class OpenstackHostAggregate(OpenstackResource):
    service_type = 'compute'
    resource_type = 'aggregate'

    def list(self):
        self.logger.debug('Attempting to list aggregates')
        return self.connection.compute.aggregates()

    def get(self):
        self.logger.debug(
            'Attempting to find this aggregate: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        aggregate = self.connection.compute.get_aggregate(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found aggregate with this result: {0}'.format(aggregate))
        return aggregate

    def create(self):
        self.logger.debug(
            'Attempting to create aggregate with these args: {0}'.format(
                self.config))
        aggregate = self.connection.compute.create_aggregate(**self.config)
        self.logger.debug(
            'Created aggregate with this result: {0}'.format(aggregate))
        return aggregate

    def update(self, new_config=None):
        aggregate = self.get()
        self.logger.debug(
            'Attempting to update this aggregate: {0} with args {1}'.format(
                aggregate, new_config))
        result =\
            self.connection.compute.update_aggregate(aggregate, **new_config)
        self.logger.debug(
            'Updated aggregate with this result: {0}'.format(result))
        return result

    def delete(self):
        aggregate = self.get()
        self.logger.debug(
            'Attempting to delete this aggregate: {0}'.format(aggregate))
        result = self.connection.compute.delete_aggregate(aggregate)
        self.logger.debug(
            'Deleted aggregate with this result: {0}'.format(result))
        return result

    def set_metadata(self, metadata):
        aggregate = self.get()
        self.logger.debug(
            'Attempting to set metadata to this aggregate: {0}'
            ''.format(aggregate))
        result = \
            self.connection.compute.set_aggregate_metadata(aggregate, metadata)
        self.logger.debug(
            'Set metadata to aggregate with this result: {0}'.format(
                result))
        return result

    def add_host(self, host):
        aggregate = self.get()
        self.logger.debug(
            'Attempting to add host to this aggregate: {0}'
            ''.format(aggregate))
        result = self.connection.compute.add_host_to_aggregate(aggregate, host)
        self.logger.debug(
            'Added host to aggregate with this result: {0}'.format(result))
        return result

    def remove_host(self, host):
        aggregate = self.get()
        self.logger.debug(
            'Attempting to delete this aggregate: {0}'.format(aggregate))
        result = \
            self.connection.compute.remove_host_from_aggregate(aggregate, host)
        self.logger.debug(
            'Deleted host to aggregate with this result: {0}'.format(result))
        return result


class OpenstackServerGroup(OpenstackResource):
    service_type = 'compute'
    resource_type = 'server_group'

    def list(self, query=None):
        query = query or {}
        return self.connection.compute.server_groups(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this server group: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        server_group = self.connection.compute.get_server_group(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found server group with this result: {0}'.format(server_group))
        return server_group

    def create(self):
        self.logger.debug(
            'Attempting to create server group with these args: {0}'.format(
                self.config))
        server_group =\
            self.connection.compute.create_server_group(**self.config)
        self.logger.debug(
            'Created server group with this result: {0}'.format(server_group))
        return server_group

    def delete(self):
        server_group = self.get()
        self.logger.debug(
            'Attempting to delete this server group: {0}'.format(server_group))
        result = self.connection.compute.delete_server_group(server_group)
        self.logger.debug(
            'Deleted server group with this result: {0}'.format(result))
        return result


class OpenstackKeyPair(OpenstackResource):
    service_type = 'compute'
    resource_type = 'keypair'

    def list(self):
        return self.connection.compute.keypairs()

    def get(self):
        self.logger.debug(
            'Attempting to find this key pair: {0}'.format(self.name))

        key_pair = self.connection.compute.get_keypair(self.name)

        self.logger.debug(
            'Found key pair with this result: {0}'.format(key_pair))
        return key_pair

    def create(self):
        self.logger.debug(
            'Attempting to create key pair with these args: {0}'.format(
                self.config))
        key_pair = self.connection.compute.create_keypair(**self.config)
        self.logger.debug(
            'Created key pair with this result: {0}'.format(key_pair))
        return key_pair

    def delete(self):
        key_pair = self.get()
        self.logger.debug(
            'Attempting to delete this key pair: {0}'.format(key_pair))
        result = self.connection.compute.delete_keypair(key_pair)
        self.logger.debug(
            'Deleted key pair with this result: {0}'.format(result))
        return result


class OpenstackFlavor(OpenstackResource):
    service_type = 'compute'
    resource_type = 'flavor'

    def list(self, details=True, query=None):
        query = query or {}
        return self.connection.compute.flavors(details, **query)

    def get(self):
        self.logger.debug(
            'Attempting to find this flavor: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        flavor = self.connection.compute.get_flavor(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found flavor with this result: {0}'.format(flavor))
        return flavor

    def create(self):
        self.logger.debug(
            'Attempting to create flavor with these args: {0}'.format(
                self.config))
        flavor = self.connection.compute.create_flavor(**self.config)
        self.logger.debug(
            'Created flavor image with this result: {0}'.format(flavor))
        return flavor

    def delete(self):
        flavor = self.get()
        self.logger.debug(
            'Attempting to delete this flavor: {0}'.format(flavor))
        result = self.connection.compute.delete_flavor(flavor)
        self.logger.debug(
            'Deleted flavor with this result: {0}'.format(result))
        return result


class OpenstackVolumeAttachment(OpenstackResource):
    service_type = 'compute'
    resource_type = 'volume_attachment'

    def __init__(self, *args, **kwargs):
        self.server_id = kwargs.pop('server_id', None)
        super(OpenstackVolumeAttachment, self).__init__(*args, **kwargs)

    def list(self, query=None):
        return self.connection.compute.volume_attachments(self.server_id)

    def get(self):
        self.logger.debug(
            'Attempting to find this volume attachment: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        volume_attachment = \
            self.connection.compute.get_volume_attachment(
                self.resource_id, self.server_id)
        self.logger.debug(
            'Found volume attachment with this result: {0}'
            ''.format(volume_attachment))
        return volume_attachment

    def create(self):
        self.logger.debug(
            'Attempting to create volume attachment'
            ' with these args: {0}'.format(self.config))
        volume_attachment = \
            self.connection.compute.create_volume_attachment(
                self.server_id, **self.config)
        self.logger.debug(
            'Created volume attachment with this result: {0}'
            ''.format(volume_attachment))
        return volume_attachment

    def delete(self):
        volume_attachment = self.get()
        self.logger.debug(
            'Attempting to delete this volume attachment: {0}'
            ''.format(volume_attachment))
        result = \
            self.connection.compute.delete_volume_attachment(volume_attachment,
                                                             self.server_id)
        self.logger.debug(
            'Deleted volume attachment with this result: {0}'.format(result))
        return result
