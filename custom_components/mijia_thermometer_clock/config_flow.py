"""Config flow for Mijia Temperature and Humidity Monitor Clock integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, FlowResult
from homeassistant.helpers.device_registry import format_mac
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.components.bluetooth import (
    async_discovered_service_info
)

from .mijia_clock import Mijia
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

XIAOMI_INC = "0000fe95-0000-1000-8000-00805f9b34fb"
MANUAL_MAC = "manual_mac"


class MijiaTemperatureClockConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mijia Temperature and Humidity Monitor Clock."""

    VERSION = 1

    def __init__(self):
        self.mac = None
        self.name = "Mijia Temperature and Humidity Monitor Clock"

    def _is_device_supported(self, device_info):
        service_data = device_info.service_data.get(XIAOMI_INC)
        if not service_data:
            return False

        if service_data and len(service_data) >= 4:
            if service_data[2] + (service_data[3] << 8) == 0x2542 or \
                service_data[2] + (service_data[3] << 8) == 0x16e4:
                return True
        return False

    async def _validate_device(self, mijia):
        try:
            await mijia.connect()
            await mijia.disconnect()
        except Exception as e:
            _LOGGER.error(e)
            return "device_validation_error"

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if user_input[CONF_MAC] == MANUAL_MAC:
                return await self.async_step_manual_mac()

            self.mac = user_input[CONF_MAC]
            await self.async_set_unique_id(format_mac(self.mac), raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_validate()

        discovered_devices = []
        for device_info in async_discovered_service_info(self.hass):
            if self._is_device_supported(device_info):
                discovered_devices.append(device_info)

        device_options = {dev.address: f"{dev.address}" for dev in discovered_devices}
        device_options[MANUAL_MAC] = "Enter MAC address manually"

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_MAC): vol.In(device_options)
            }),
            description_placeholders={
                "description": "Please select a device to configure"
            },
            errors=errors
        )

    async def async_step_manual_mac(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual mac step."""
        if user_input is not None:
            self.mac = user_input[CONF_MAC]
            await self.async_set_unique_id(format_mac(self.mac), raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_validate()

        return self.async_show_form(
            step_id="manual_mac",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC): str
                }
            ),
            errors={})

    async def async_step_validate(
        self, user_input: "dict[str, Any] | None" = None
    ) -> ConfigFlowResult:
        """Handle validate step."""
        error = None
        mijia = Mijia(self.hass, self.mac, self.name)
        try:
            error = await self._validate_device(mijia)
        except Exception as e:
            error = str(e)
        finally:
            await mijia.disconnect()

        if error:
            return await self.async_step_user(errors={"base": error})

        return await self.async_step_name()

    async def async_step_name(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle name step."""
        if user_input is not None:
            self.name = user_input[CONF_NAME]

            return self.async_create_entry(
                title=self.name,
                data = {
                    CONF_MAC: self.mac,
                    CONF_NAME: self.name
                }
            )

        return self.async_show_form(
            step_id="name",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=self.name): str
                }
            ),
            errors={},
        )


class DeviceValidationError(HomeAssistantError):
    """Error to indicate there was a problem with the device."""