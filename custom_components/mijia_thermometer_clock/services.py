from __future__ import annotations
from datetime import datetime
import voluptuous as vol
import pytz

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.const import ATTR_DEVICE_ID

from .const import (
    DOMAIN,
    CONF_TIME,
    CONF_TIMEZONE,
    SERVICE_SET_TIME
)
from .mijia_clock import Mijia

SET_TIME_SCHEMA = vol.Schema({
    vol.Required(ATTR_DEVICE_ID): str,
    vol.Required(CONF_TIME): cv.datetime,
    vol.Required(CONF_TIMEZONE): cv.string
})

def async_register_services(hass: HomeAssistant) -> None:
    async def async_set_time(call: ServiceCall) -> None:
        """Set time"""
        mac: str = _get_device_mac(hass, call)
        time: datetime = call.data["time"]
        timezone: str = call.data["timezone"]

        timezone = await hass.async_add_executor_job(pytz.timezone, call.data["timezone"])
        localized_dt = timezone.localize(time)
        utc_dt = localized_dt.astimezone(pytz.utc)
        timestamp = int(utc_dt.timestamp())

        for entry in hass.config_entries.async_entries(DOMAIN):
            instance: Mijia = entry.runtime_data
            if instance.mac != mac:
                continue

            await instance.set_time(timestamp, timezone)
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