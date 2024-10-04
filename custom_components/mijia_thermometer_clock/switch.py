from __future__ import annotations

from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import SwitchEntity

from .const import CONFIG_UPDATED
from .entity import async_device_device_info_fn
from .mijia_clock import Mijia

async def async_setup_entry(hass, config_entry, async_add_entities):
    instance: Mijia = config_entry.runtime_data
    async_add_entities([MijiaTemperatureUnitSwitch(instance, config_entry)])


class MijiaTemperatureUnitSwitch(SwitchEntity):
    def __init__(self, instance: Mijia, config_entry: ConfigEntry):
        self._instance: Mijia = instance
        self._config_entry = config_entry
        self._attr_name = f"{config_entry.data[CONF_NAME]} Use Fahrenheit"
        self._attr_unique_id = f"{instance.name}_use_fahrenheit"
        self._attr_is_on = None
        self._attr_icon = "mdi:temperature-fahrenheit"
        self._attr_extra_state_attributes = {}

        instance.eventbus.add_listener(CONFIG_UPDATED, self.config_updated)

    @property
    def device_info(self) -> DeviceInfo:
        return async_device_device_info_fn(self._instance, self._config_entry.data[CONF_NAME])

    async def async_turn_on(self, **kwargs):
        await self._instance.set_use_fahrenheit(True)

    async def async_turn_off(self, **kwargs):
        await self._instance.set_use_fahrenheit(False)

    async def config_updated(self, instance: Mijia):
        self._attr_is_on = self._instance.use_fahrenheit
        self.async_write_ha_state()
