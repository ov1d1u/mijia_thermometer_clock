import asyncio
import logging
import time
import pytz
from struct import pack
from functools import wraps
from bleak import BleakClient
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.components.bluetooth import (
    async_ble_device_from_address
)

from .eventbus import EventBus
from ..const import (
    CONFIG_UPDATED,
    DEVICE_CONENCTED,
    DEVICE_DISCONNECTED
)
from ..exceptions import NotConnectedError

_LOGGER = logging.getLogger(__name__)
TIME_CHAR = "EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6"
SETTINGS_CHAR = "EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6"

def ensure_connected(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.client or not self.client.is_connected:
            await self.connect()
        try:
            result = await func(self, *args, **kwargs)
        finally:
            await self.disconnect()
        return result
    return wrapper


class Mijia:
    client: BleakClient = None
    eventbus = EventBus()

    use_fahrenheit = None
    _connect_lock = asyncio.Lock()
    _disconnect_task = None

    def __init__(
        self,
        hass: HomeAssistant,
        mac: str,
        name: str
    ):
        """Initialize the Mijia clock."""
        self.hass = hass
        self.mac = mac
        self.name = name

    @property
    def is_connected(self):
        return self.client and self.client.is_connected

    async def connect(self) -> bool:
        async with self._connect_lock:
            if self.client and self.client.is_connected:
                return True

            device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            self.client = BleakClient(device)

            _LOGGER.debug(f"Connecting to {self.mac}...")
            try:
                await self.client.connect()
            except Exception as e:
                _LOGGER.debug(f"Failed to connect to {self.mac}: {e}")
                return False

            await asyncio.sleep(2.0)  # give some time for service discovery

            _LOGGER.debug(f"Connected to {self.mac}")
            self.eventbus.send(DEVICE_CONENCTED, self)

            if self.use_fahrenheit is None:
                await self._read_config()

            return True

    async def connect_if_needed(self):
        if self.use_fahrenheit is None:
            await self.connect()

    async def disconnect(self) -> bool:
        if self.client and self.client.is_connected:
            _LOGGER.debug(f"Disconnecting from {self.mac}...")
            await self.client.disconnect()
            self.eventbus.send(DEVICE_DISCONNECTED, self)
            self.client = None
            return True

        return False

    async def set_time(
        self,
        timestamp: int,
        timezone: str
    ) -> bool:
        start_time = time.time()

        if not self.client or not self.client.is_connected:
            await self.connect()

        # Account for time passed while connecting
        timestamp = int(timestamp + (time.time() - start_time))

        data = self._get_bytes_from_time(
            timestamp,
            timezone
        )

        await self._write_gatt_char(TIME_CHAR, data)
        return True

    @ensure_connected
    async def set_use_fahrenheit(self, use_fahrenheit: bool) -> bool:
        if use_fahrenheit:
            await self._write_gatt_char(SETTINGS_CHAR, b"\x01")
        else:
            await self._write_gatt_char(SETTINGS_CHAR, b"\xff")
        await self._read_config()

        return True

    async def _read_gatt_char(self, uuid: str) -> bytes:
        if self.client and self.client.is_connected:
            return await self.client.read_gatt_char(uuid)
        else:
            raise NotConnectedError("Not connected")

    async def _write_gatt_char(self, uuid: str, data: bytes) -> bool:
        _LOGGER.debug(f">> {uuid}: {data.hex()}")
        await self.client.write_gatt_char(uuid, data)

    async def _read_config(self):
        use_fahrenheit = await self._read_gatt_char(SETTINGS_CHAR)
        self.use_fahrenheit = use_fahrenheit == b"\x01"
        self.eventbus.send(CONFIG_UPDATED, self)

    def _get_bytes_from_time(
        self,
        timestamp: int,
        timezone: pytz.BaseTzInfo
    ) -> bytes:
        """Generate the bytes to set the time on the LYWSD02MMC clock with Daylight Saving Time adjustment.
        Args:
            timestamp (int): The time encoded as a Unix timestamp.
            timezone (str, optional): The timezone identifier
            dst (bool, optional): Whether Daylight Saving Time should be applied. Defaults to False.

        Returns:
            bytes: The bytes needed to set the time of the device to `timestamp` considering the timezone and DST.
        """
        # Adjust timezone for DST if necessary

        current_time = datetime.now(timezone)
        tz_offset = int(current_time.utcoffset().total_seconds()/3600)

        return pack('<IB', timestamp, tz_offset)
