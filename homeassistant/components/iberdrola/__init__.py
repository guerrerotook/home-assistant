"""Iberdrola integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow

from .const import COMPONENTS, DOMAIN
from .iberdrola_manager import IberdrolaManager


async def async_setup(hass: HomeAssistant, config: dict):
    """Async setup of the Iberdrola component."""

    if config == {}:
        return True

    if "source" in config:
        await hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config["source"]}, data=config["data"]
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Define the async setup."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN]["accounts"] = set()

    account = entry.data.get(CONF_USERNAME)

    if account not in hass.data[DOMAIN]:
        data = hass.data[DOMAIN][account] = IberdrolaManager(hass, entry)
        data.initialize()
    else:
        data = hass.data[DOMAIN][account]

    hass.states.async_set("iberdrola.init", "True")

    # Return boolean to indicate that initialization was successful.
    return await data.update(utcnow())


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Async unload of the Iberdrola component."""
    account = entry.data.get(CONF_USERNAME)

    data = hass.data[DOMAIN][account]

    for component in COMPONENTS:
        await hass.config_entries.async_forward_entry_unload(data.entry, component)

    del hass.data[DOMAIN][account]

    return True
