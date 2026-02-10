import asyncio
import logging
import time
from struct import pack
from bleak import BleakClient

from homeassistant.core import HomeAssistant
from homeassistant.components.bluetooth import (
    async_ble_device_from_address
)

from .eventbus import EventBus
from ..const import (
    CONFIG_UPDATED,
    DEVICE_CONNECTED,
    DEVICE_DISCONNECTED,
    CONNECTION_TIMEOUT,
    RETRY_INTERVAL,
    DISCONNECT_DELAY
)
from ..exceptions import NotConnectedError

_LOGGER = logging.getLogger(__name__)
TIME_CHAR = "EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6"
SETTINGS_CHAR = "EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6"


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
            if device is None:
                _LOGGER.error(f"No adapters can reach the device with address {self.mac}")
                return False
            self.client = BleakClient(device, disconnected_callback=self._on_disconnect)

            _LOGGER.debug(f"Connecting to {self.mac}...")
            try:
                await self.client.connect()
            except Exception as e:
                _LOGGER.debug(f"Failed to connect to {self.mac}: {e}")
                return False

            await asyncio.sleep(2.0)  # give some time for service discovery

            _LOGGER.debug(f"Connected to {self.mac}")
            self.eventbus.send(DEVICE_CONNECTED, self)

            if self.use_fahrenheit is None:
                await self._read_config()

            return True

    async def connect_if_needed(self):
        if self.use_fahrenheit is None:
            await self.connect()
            await self.delayed_disconnect()

    async def disconnect(self) -> bool:
        if self.client and self.client.is_connected:
            _LOGGER.debug(f"Disconnecting from {self.mac}...")
            await self.client.disconnect()
            return True

        return False

    async def set_time(
        self,
        timestamp: int,
        timezone_offset: int | None = None
    ) -> bool:
        start_time = time.time()

        if timezone_offset is None:
            is_dst = time.daylight and time.localtime().tm_isdst > 0
            utc_offset = - (time.altzone if is_dst else time.timezone)
            timezone_offset = int(utc_offset / 3600)

        _LOGGER.debug(f"Set time to {timestamp}, tz offset: {timezone_offset}")

        await self._ensure_connected()

        # Account for time passed while connecting
        timestamp = int(timestamp + (time.time() - start_time))

        timestamp_bytes = self._get_bytes_from_time(
            timestamp,
            timezone_offset
        )

        await self._write_gatt_char(TIME_CHAR, timestamp_bytes)

        return True

    async def set_use_fahrenheit(self, use_fahrenheit: bool) -> bool:
        await self._ensure_connected()

        if use_fahrenheit:
            await self._write_gatt_char(SETTINGS_CHAR, b"\x01")
        else:
            await self._write_gatt_char(SETTINGS_CHAR, b"\xff")
        await self._read_config()

        return True

    async def delayed_disconnect(self):
        async def _delayed_disconnect():
            if not self.client.is_connected:
                return

            try:
                await asyncio.sleep(DISCONNECT_DELAY)
                await self.disconnect()
            except Exception as e:
                _LOGGER.debug(f"Failed to disconnect. Error: {e}")

        loop = asyncio.get_running_loop()
        if self._disconnect_task is not None:
            self._disconnect_task.cancel()
        self._disconnect_task = loop.create_task(_delayed_disconnect())

    async def _ensure_connected(self):
        async def wait_for_connected():
            while not self.client or not self.client.is_connected:
                success = await self.connect()
                if success:
                    _LOGGER.info("Successfully connected to the Bluetooth device.")
                    return
                else:
                    _LOGGER.error("Failed to connect. Retrying in %s seconds...", RETRY_INTERVAL)
                    await asyncio.sleep(RETRY_INTERVAL)

        try:
            await asyncio.wait_for(wait_for_connected(), CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            _LOGGER.error("Connection timeout.")
            raise NotConnectedError("Connection timeout")

    async def _read_gatt_char(self, uuid: str) -> bytes:
        if self.client and self.client.is_connected:
            return await self.client.read_gatt_char(uuid)
        else:
            raise NotConnectedError("Not connected")

    async def _write_gatt_char(self, uuid: str, data: bytes) -> bool:
        _LOGGER.debug(f">> {uuid}: {data.hex()}")
        await self.client.write_gatt_char(uuid, data)
        await self.delayed_disconnect()

    async def _read_config(self):
        use_fahrenheit = await self._read_gatt_char(SETTINGS_CHAR)
        self.use_fahrenheit = use_fahrenheit == b"\x01"
        self.eventbus.send(CONFIG_UPDATED, self)

    def _get_bytes_from_time(
        self,
        timestamp: int,
        timezone_offset: int
    ) -> bytes:
        """Generate the bytes to set the time on the LYWSD02MMC clock with Daylight Saving Time adjustment.
        Args:
            timestamp (int): The timestamp to set
            timezone_offset (int): The timezone offset in minutes

        Returns:
            bytes: The bytes needed to set the time of the device to `timestamp` considering the timezone offset.
        """
        return pack('<IB', timestamp, timezone_offset)

    def _on_disconnect(self, client: BleakClient):
        if self._disconnect_task is not None:
            self._disconnect_task.cancel()
            self._disconnect_task = None

        _LOGGER.debug(f"Disconnected from {self.mac}")
        self.eventbus.send(DEVICE_DISCONNECTED, self)
        self.client = None
