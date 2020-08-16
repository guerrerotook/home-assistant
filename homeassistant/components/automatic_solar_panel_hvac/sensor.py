"""Sensor file."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SENSOR_KEY


class OperationStatusSensor(Entity):
    """This class represent the status for the operation in the integration."""

    def __init__(self, name: str, state: str):
        """Init the class."""
        self._name = name
        self._state = state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def setState(self, value: str):
        """Set the state of the sensor."""
        self._state = value

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def lastTimeUpdate(self):
        """Return last time updated."""
        return self._last_time_update

    def setLastTimeUpdate(self, value):
        """Set last time updated."""
        self._last_time_update = value


def setup_platform(
    hass: HomeAssistant, config: ConfigEntry, add_devices, discovery_info=None
):
    """Define the setup for the sensor."""
    device_list = []
    sensor_on = OperationStatusSensor("AutomaticSolarPanel.LastOn", "Ninguno")
    sensor_off = OperationStatusSensor("AutomaticSolarPanel.LastOff", "Ninguno")
    device_list.append(sensor_on)
    device_list.append(sensor_off)
    add_devices(device_list)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][SENSOR_KEY] = device_list

    return True
