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

# Runtime properties keys
RESOURCE_ID = 'id'
USE_EXTERNAL_RESOURCE_PROPERTY = 'use_external_resource'
SERVER_TASK_CREATE = 'create_server_task'
SERVER_TASK_STOP = 'stop_server_task'
SERVER_TASK_DELETE = 'delete_server_task'
SERVER_TASK_START = 'start_server_task'
SERVER_TASK_STATE = 'task_state'
SERVER_TASK_BACKUP_DONE = 'backup_done'
SERVER_TASK_RESTORE_STATE = 'restore_state'

# Openstack Server status constants.
# Full lists here: https://bit.ly/2UyB5V5 # NOQA
SERVER_STATUS_ACTIVE = 'ACTIVE'
SERVER_STATUS_BUILD = 'BUILD'
SERVER_STATUS_SHUTOFF = 'SHUTOFF'
SERVER_STATUS_SUSPENDED = 'SUSPENDED'
SERVER_STATUS_ERROR = 'ERROR'
SERVER_STATUS_REBOOT = 'REBOOT'
SERVER_STATUS_HARD_REBOOT = 'HARD_REBOOT'
SERVER_STATUS_UNKNOWN = 'UNKNOWN'

# Openstack Server reboot actions
SERVER_REBOOT_SOFT = 'SOFT'
SERVER_REBOOT_HARD = 'HARD'

# Openstack resources types
SERVER_OPENSTACK_TYPE = 'server'
SERVER_GROUP_OPENSTACK_TYPE = 'server_group'
INSTANCE_OPENSTACK_TYPE = 'instance'
HOST_AGGREGATE_TYPE = 'aggregate'
IMAGE_TYPE = 'image'
FLAVOR_TYPE = 'flavor'

# Openstack Image status
IMAGE_UPLOADING = 'image_uploading'
IMAGE_UPLOADING_PENDING = 'image_pending_upload'
IMAGE_STATUS_ACTIVE = 'active'

# Cloudify node types
SERVER_GROUP_TYPE = 'cloudify.nodes.openstack.ServerGroup'


# Message constants
QUOTA_VALID_MSG = \
    'OK: {0} (node {1}) can be created. provisioned {2}: {3}, quota: {4}'

QUOTA_INVALID_MSG = \
    '{0} (node {1}) cannot be created due to quota limitations.' \
    'provisioned {2}: {3}, quota: {4}'

# General constants
PS_OPEN = '<powershell>'
PS_CLOSE = '</powershell>'
INFINITE_RESOURCE_QUOTA = -1
SERVER_ACTION_STATUS_DONE = 'DONE'
SERVER_ACTION_STATUS_PENDING = 'PENDING'
SERVER_REBUILD_STATUS = 'rebuild_done'
SERVER_REBUILD_SPAWNING = 'rebuild_spawning'
