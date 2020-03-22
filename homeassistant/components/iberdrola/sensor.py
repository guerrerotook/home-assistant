"""Platform for sensor integration."""
from homeassistant.const import ATTR_DATE, CONF_USERNAME, POWER_WATT

from .const import DOMAIN
from .iberdrola_entity import IberdolaEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Define the setup for the sensor."""
    sensors = []

    account = config_entry.data.get(CONF_USERNAME)
    manager = hass.data[DOMAIN][account]

    prefix = "iberdrola_"

    sensors.append(
        PowerConsumption(
            prefix + "acumulado", manager.data["consumption"]["acumulado"], POWER_WATT,
        )
    )
    sensors.append(
        PowerConsumption(
            prefix + "consumoMedio",
            manager.data["consumption"]["consumoMedio"],
            POWER_WATT,
        )
    )
    sensors.append(
        PowerConsumption(
            prefix + "fechaPeriodo",
            manager.data["consumption"]["fechaPeriodo"],
            ATTR_DATE,
        )
    )
    sensors.append(
        PowerConsumption(
            prefix + "periodoMuestra",
            manager.data["consumption"]["periodoMuestra"],
            ATTR_DATE,
        )
    )
    sensors.append(
        PowerConsumption(
            prefix + "acumuladoCO2",
            manager.data["consumption"]["acumuladoCO2"],
            POWER_WATT,
        )
    )

    for key in manager.data["consumption"]["y"]["data"][0]:
        sensors.append(PowerConsumption(prefix + "diario", key["valor"], POWER_WATT,))

    async_add_entities(sensors, True)


class PowerConsumption(IberdolaEntity):
    """Representation of a Sensor."""

    def __init__(self, name, value, unit_of_measure):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._value = value
        self._unit_of_measure = unit_of_measure

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measure
