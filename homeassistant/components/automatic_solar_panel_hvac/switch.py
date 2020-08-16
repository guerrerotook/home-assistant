"""Platform for switch integration."""
from datetime import datetime

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SWITCH_KEY


class SystemEngine(SwitchEntity):
    """Representation of the main switch. This class enable or disable the system processing."""

    def __init__(self, name: str):
        """Initialize the switch."""
        self._name = name
        self._is_on: bool = False
        self._last_time_update: datetime = datetime.now()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return if the switch is on."""
        return self._is_on

    @property
    def lastTimeUpdate(self):
        """Return last time the switch was updated."""
        return self._last_time_update

    def setLastTimeUpdate(self, value):
        """Set lats time the switch was updated."""
        self._last_time_update = value

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._is_on = True

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._is_on = False


def setup_platform(
    hass: HomeAssistant, config: ConfigEntry, add_devices, discovery_info=None
):
    """Define the setup for the switch."""
    device_list = []
    device_list.append(SystemEngine("SolarPanel-Automation"))
    add_devices(device_list)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][SWITCH_KEY] = device_list

    return True
