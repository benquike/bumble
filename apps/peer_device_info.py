# Copyright 2021-2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import click
import asyncio

from bumble.device import Device, DeviceConfiguration
from bumble.core import BT_BR_EDR_TRANSPORT, BT_LE_TRANSPORT
from bumble.hci import (
    OwnAddressType,
    HCI_READ_REMOTE_SUPPORTED_FEATURES_COMMAND,
    HCI_Read_Remote_Supported_Features_Command,
    HCI_Read_Remote_Supported_Features_Complete_Event,
    HCI_READ_REMOTE_EXTENDED_FEATURES_COMMAND,
    HCI_Read_Remote_Extended_Features_Command,
    HCI_Read_Remote_Extended_Features_Complete_Event,
    HCI_LE_READ_REMOTE_FEATURES_COMMAND,
    HCI_LE_Read_Remote_Features_Command,
    HCI_LE_Read_Remote_Features_Complete_Event,
)

from bumble.transport import open_transport_or_link


async def async_main(controller, address, address_type, transport):
    print('<<< connecting to HCI...')
    async with await open_transport_or_link(controller) as (hci_source, hci_sink):
        device_config_dict = {
            'le_enabled': True,
            'classic_enabled': True,
        }

        device_config = DeviceConfiguration()
        device_config.load_from_dict(device_config_dict)
        device = Device.from_config_with_hci(device_config, hci_source, hci_sink)

        if transport == "BR/EDR":
            transport = BT_BR_EDR_TRANSPORT
            address_type = None
        else:
            transport = BT_LE_TRANSPORT
            _addr_type_name_to_value = {
                'public': OwnAddressType.PUBLIC,
                'random': OwnAddressType.RANDOM,
                'random/resolvable': OwnAddressType.RESOLVABLE_OR_PUBLIC,
                'random/non-resolvable': OwnAddressType.RESOLVABLE_OR_RANDOM
            }
            address_type = _addr_type_name_to_value.get(address_type, OwnAddressType.PUBLIC)

        await device.power_on()
        logging.debug(f"device: classic_enabled:{device.classic_enabled}, le_enabled:{device.le_enabled}")
        logging.debug(f'connecting to {address}, addr_type: {address_type}, transport: {transport}')
        acl_connection = await device.connect(peer_address=address,
                                              transport = transport,
                                              own_address_type = address_type)

        logging.debug(f'connection done, handle: {acl_connection.handle}')

        if transport == BT_BR_EDR_TRANSPORT:
            pass
        else: # BLE
            pass

        logging.debug(f'disconnecting')
        await acl_connection.disconnect()
        logging.debug(f'disconnected')

@click.command()
@click.option('--controller', type=str, required=True, help='transport of local controller')
@click.option('--address', type=str, required=True, help='address of peer device')
@click.option('--address_type', type=click.Choice(['public', 'static',
                                                 'random/resolvable',
                                                 'random/non-resolvable']),
              default='public',
              help='address type of peer device')
@click.option('--transport', type=click.Choice(["BR/EDR", "BLE"]), default="BR/EDR", required=True,
              help='the transport to connect to peer device')
def main(controller, address, address_type, transport):
    logging.basicConfig(level=os.environ.get('BUMBLE_LOGLEVEL', 'WARNING').upper())
    asyncio.run(async_main(controller, address, address_type, transport))

if __name__ == '__main__':
    main()
