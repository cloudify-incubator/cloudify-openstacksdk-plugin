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
import base64


# Third part imports
from cloudify import compute
from cloudify import ctx

try:
    from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


PS_OPEN = '<powershell>'
PS_CLOSE = '</powershell>'


def set_ctx(_ctx):
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if _ctx._context.get('is_target', True):
            return _ctx.target
        return _ctx.source
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. Tthis indicates a problem.'.format(
                NODE_INSTANCE, RELATIONSHIP_INSTANCE))
    return _ctx


def handle_userdata(existing_userdata):
    """
    This method will be responsible for handle user data provided by the
    user on the following cases:
    1. When user specify "user_data" to create server on openstack
    2. When "install_method" for agent is set to "Init-script" the plugin
     should be able to inject/update "user_data" for server
    :param existing_userdata:
    :return: final_userdata
    """
    # Check the agent init script so that it can be injected to the target
    # machine to install the agent daemon
    install_agent_userdata = ctx.agent.init_script()
    # Get the "os_family" type, by default all node instances extend
    # "cloudify.nodes.Compute" node will have "os_family" set to "Linux"
    # It can be override for Windows which is need to be handled differently
    os_family = ctx.node.properties['os_family']

    if not (existing_userdata or install_agent_userdata):
        return None

    if not existing_userdata:
        existing_userdata = ''

    if install_agent_userdata and os_family == 'windows':

        # Get the powershell content from install_agent_userdata
        install_agent_userdata = \
            extract_powershell_content(install_agent_userdata)

        # Get the powershell content from existing_userdata
        # (If it exists.)
        existing_userdata_powershell = \
            extract_powershell_content(existing_userdata)

        # Combine the powershell content from two sources.
        install_agent_userdata = \
            '#ps1_sysnative\n{0}\n{1}\n{2}\n{3}\n'.format(
                PS_OPEN,
                existing_userdata_powershell,
                install_agent_userdata,
                PS_CLOSE)

        # Additional work on the existing_userdata.
        # Remove duplicate Powershell content.
        # Get rid of unnecessary newlines.
        existing_userdata = \
            existing_userdata.replace(
                existing_userdata_powershell,
                '').replace(
                    PS_OPEN,
                    '').replace(
                        PS_CLOSE,
                        '').strip()

    if not existing_userdata or existing_userdata.isspace():
        final_userdata = install_agent_userdata
    elif not install_agent_userdata:
        final_userdata =\
            compute.create_multi_mimetype_userdata([existing_userdata])
    else:
        final_userdata = compute.create_multi_mimetype_userdata(
            [existing_userdata, install_agent_userdata])

    final_userdata = base64.b64encode(final_userdata)
    return final_userdata


def extract_powershell_content(string_with_powershell):
    """We want to filter user data for powershell scripts.
    However, Openstack allows only one segment that is Powershell.
    So we have to concat separate Powershell scripts into one.
    First we separate all Powershell scripts without their tags.
    Later we will add the tags back.
    """

    split_string = string_with_powershell.splitlines()

    if not split_string:
        return ''

    if split_string[0] == '#ps1_sysnative' or \
            split_string[0] == '#ps1_x86':
        split_string.pop(0)

    if PS_OPEN not in split_string:
        script_start = -1  # Because we join at +1.
    else:
        script_start = split_string.index(PS_OPEN)

    if PS_CLOSE not in split_string:
        script_end = len(split_string)
    else:
        script_end = split_string.index(PS_CLOSE)

    # Return everything between Powershell back as a string.
    return '\n'.join(split_string[script_start + 1:script_end])
