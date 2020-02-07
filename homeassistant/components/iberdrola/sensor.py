"""Platform for sensor integration."""
from homeassistant.const import CONF_USERNAME, TEMP_CELSIUS

from .const import DOMAIN
from .iberdola_entity import IberdolaEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Define the setup for the sensor."""
    sensors = []

    account = config_entry.data.get(CONF_USERNAME)
    manager = hass.data[DOMAIN][account]

    for sensor in manager.iberdola_data:
        sensors.append(PowerConsumption(sensor))

    async_add_entities(sensors, True)


class PowerConsumption(IberdolaEntity):
    """Representation of a Sensor."""

    def __init__(self, data):
        """Initialize the sensor."""
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Example Temperature"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 23
