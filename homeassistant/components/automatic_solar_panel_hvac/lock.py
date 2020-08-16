"""This Lock helper let users lock what entity the system should avoid."""
from datetime import datetime

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant

from .const import CONF_CLIMATE, CONFIG, DOMAIN, SWITCH_KEY


class EntityLock(LockEntity):
    """Representation of the entity Lock."""

    def __init__(self, name: str):
        """Init the class."""
        self._name = name
        self._is_locked: bool = False
        self._last_time_update: datetime = datetime.now()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_locked(self) -> bool:
        """Return if the lock is locked."""
        return self._is_locked

    @property
    def lastTimeUpdate(self):
        """Return last time it was updated."""
        return self._last_time_update

    def setLastTimeUpdate(self, value):
        """Set last time it was updated."""
        self._last_time_update = value

    def lock(self, **kwargs) -> None:
        """Lock the entity."""
        self._is_locked = True

    def unlock(self, **kwargs):
        """Unlock the entity off."""
        self._is_locked = False


def setup_platform(
    hass: HomeAssistant, config: ConfigEntry, add_devices, discovery_info=None
):
    """Define the setup for the lock."""
    device_list = []

    config = hass.data[DOMAIN][CONFIG]
    climateEntity = config.get(CONF_CLIMATE)
    lightEntity = config.get(CONF_LIGHTS)

    for cliamte_item in climateEntity:
        device_list.append(EntityLock("%s-Lock" % cliamte_item.replace("climate.", "")))

    for cliamte_item in lightEntity:
        device_list.append(EntityLock("%s-Lock" % cliamte_item.replace("light.", "")))

    add_devices(device_list)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][SWITCH_KEY] = device_list

    return True
