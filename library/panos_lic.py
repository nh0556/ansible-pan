#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: panos_lic
short_description: apply and authcode to a device/instance
description:
    - Apply an authcode to a device.
    - The authcode should have been previously registered on the Palo Alto Networks support portal.
    - The device should have Internet access.
author: 
    - Palo Alto Networks 
    - Luigi Mori (jtschichold)
version_added: "0.0"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    auth_code:
        description:
            - authcode to be applied
        required: true
    force:
        description:
            - whether to apply authcode even if device is already licensed
        required: false
        default: "false"
'''

EXAMPLES = '''
  - name: fetch license
    panos_lic:
        ip_address: "192.168.1.1"
        password: "admin"
        auth_code: "IBADCODE"
'''

import sys

try:
    import pan.xapi
except ImportError:
    print "failed=True msg='pan-python required for this module'"
    sys.exit(1)


def get_serial(xapi, module):
    xapi.op(cmd="show system info", cmd_xml=True)
    r = xapi.element_root
    serial = r.find('.//serial')
    if serial is None:
        module.fail_json(msg="No <serial> tag in show system info")

    serial = serial.text

    return serial


def apply_authcode(xapi, module, auth_code):
    try:
        xapi.op(cmd='request license fetch auth-code "%s"' % auth_code,
                cmd_xml=True)
    except pan.xapi.PanXapiError:
        if hasattr(xapi, 'xml_document'):
            if 'Successfully' in xapi.xml_document:
                return

        if 'Invalid Auth Code' in xapi.xml_document:
            module.fail_json(msg="Invalid Auth Code")

        raise

    return


def fetch_authcode(xapi, module):
    try:
        xapi.op(cmd='request license fetch', cmd_xml=True)
    except pan.xapi.PanXapiError:
        if hasattr(xapi, 'xml_document'):
            if 'Successfully' in xapi.xml_document:
                return

        if 'Invalid Auth Code' in xapi.xml_document:
            module.fail_json(msg="Invalid Auth Code")

        raise

    return


def main():
    argument_spec = dict(
        ip_address=dict(default=None),
        password=dict(default=None, no_log=True),
        auth_code=dict(default=None),
        username=dict(default='admin'),
        force=dict(type='bool', default=False)
    )
    module = AnsibleModule(argument_spec=argument_spec)

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    auth_code = module.params["auth_code"]
    force = module.params['force']
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    if not force:
        serialnumber = get_serial(xapi, module)
        if serialnumber != 'unknown':
            return module.exit_json(changed=False, serialnumber=serialnumber)
    if auth_code:
        apply_authcode(xapi, module, auth_code)
    else:
        fetch_authcode(xapi, module)

    module.exit_json(changed=True, msg="okey dokey")

from ansible.module_utils.basic import *  # noqa

main()
