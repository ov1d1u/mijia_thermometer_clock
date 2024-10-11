from __future__ import annotations
from datetime import datetime
import voluptuous as vol

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.const import ATTR_DEVICE_ID

from .const import (
    DOMAIN,
    CONF_TIME,
    SERVICE_SET_TIME
)
from .mijia_clock import Mijia

SET_TIME_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): str,
    vol.Required(CONF_TIME): cv.datetime
})

def async_register_services(hass: HomeAssistant) -> None:
    async def async_set_time(call: ServiceCall) -> None:
        """Set time"""
        mac: str = _get_device_mac(hass, call)
        time: datetime = call.data["time"]

        for entry in hass.config_entries.async_entries(DOMAIN):
            instance: Mijia = entry.runtime_data
            if instance.mac != mac:
                continue

            timezone_offset = None
            if time.tzinfo is not None:
                timezone_offset = int(time.utcoffset().total_seconds() / 60)
            timestamp = int(time.timestamp())

            await instance.set_time(timestamp, timezone_offset)
            await instance.disconnect()

    def _get_device_mac(hass, call):
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(call.data[ATTR_DEVICE_ID])

        if device_entry is None:
            return

        mac = None
        for connection in device_entry.connections:
            if connection[0] == CONNECTION_BLUETOOTH:
                mac = connection[1]
                break

        return mac

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TIME,
        async_set_time,
        schema=SET_TIME_SCHEMA
    )