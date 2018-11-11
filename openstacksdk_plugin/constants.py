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

RESOURCE_ID = 'id'
USE_EXTERNAL_RESOURCE_PROPERTY = 'use_external_resource'


# server status constants.
# Full lists here: http://docs.openstack.org/api/openstack-compute/2/content/List_Servers-d1e2078.html  # NOQA
SERVER_STATUS_ACTIVE = 'ACTIVE'
SERVER_STATUS_BUILD = 'BUILD'
SERVER_STATUS_SHUTOFF = 'SHUTOFF'
SERVER_STATUS_SUSPENDED = 'SUSPENDED'
SERVER_STATUS_ERROR = 'ERROR'
SERVER_STATUS_REBOOT = 'REBOOT'
SERVER_STATUS_HARD_REBOOT = 'HARD_REBOOT'
SERVER_STATUS_UNKNOWN = 'UNKNOWN'

SERVER_TASK_CREATE = 'CREATE_SERVER_TASK'
SERVER_TASK_STOP = 'STOP_SERVER_TASK'
SERVER_TASK_DELETE = 'DELETE_SERVER_TASK'
