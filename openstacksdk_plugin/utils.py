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

try:
    from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


def set_ctx(_ctx):
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if _ctx._context.get('is_target', True):
            return _ctx.target
        return _ctx.source
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. However, this indicates a problem.')
    return _ctx
