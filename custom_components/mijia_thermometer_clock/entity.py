from __future__ import annotations
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH

from .mijia_clock import Mijia

@callback
def async_device_device_info_fn(mijia: Mijia, name: str) -> DeviceInfo:
    return DeviceInfo(
        connections={(CONNECTION_BLUETOOTH, mijia.mac)},
        manufacturer="Xiaomi",
        model="LYWSD02MMC",
        name=name
    )