"""Base class for all Iberdrola entities in the system."""
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_STATE_UPDATED


class IberdolaEntity(Entity):
    """Base class for all entities."""

    def __init__(self, data):
        """Initialize the entity."""
        self._data = data

    async def async_added_to_hass(self):
        """Register update dispatcher."""
        async_dispatcher_connect(
            self.hass, SIGNAL_STATE_UPDATED, self.async_schedule_update_ha_state
        )

    @property
    def device_info(self):
        """Get the device info."""

        return {
            "identifiers": {(DOMAIN, self._instrument.vehicle_name)},
            "manufacturer": "Audi",
            "name": self._vehicle_name,
            "device_type": self._component,
        }
