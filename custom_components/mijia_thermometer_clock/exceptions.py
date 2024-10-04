from homeassistant.exceptions import HomeAssistantError


class NotConnectedError(HomeAssistantError):
    """Error to indicate that the device is not connected."""
    pass