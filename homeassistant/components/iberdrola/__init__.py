"""Iberdrola integration."""
from datetime import timedelta

from iberdrola_manager import IberdrolaManager
import voluptuous as vol

from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utcnow

from .const import COMPONENTS, DOMAIN, UPDATE_INTERVAL

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=timedelta(minutes=UPDATE_INTERVAL),
                ): vol.All(
                    cv.time_period, vol.Clamp(min=timedelta(minutes=UPDATE_INTERVAL)),
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Async setup of the Iberdrola component."""
    if hass.config_entries.async_entries(DOMAIN):
        return True

    if DOMAIN not in config:
        return True

    names = config[DOMAIN].get(CONF_NAME)
    if len(names) == 0:
        return True

    data = {}
    data[CONF_USERNAME] = config[DOMAIN].get(CONF_USERNAME)
    data[CONF_PASSWORD] = config[DOMAIN].get(CONF_PASSWORD)
    data[CONF_SCAN_INTERVAL] = config[DOMAIN].get(CONF_SCAN_INTERVAL).seconds / 60

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config.SOURCE_IMPORT}, data=data
        )
    )

    return True


async def async_setup_entry(hass, config):
    """Define the async setup."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN]["accounts"] = set()

    account = config.data.get(CONF_USERNAME)

    if account not in hass.data[DOMAIN]:
        data = hass.data[DOMAIN][account] = IberdrolaManager(hass, config,)
        data.initialize()
    else:
        data = hass.data[DOMAIN][account]

    hass.states.async_set("iberdrola.init", "True")

    # Return boolean to indicate that initialization was successful.
    return await data.update(utcnow())


async def async_unload_entry(hass, config_entry):
    """Async unload of the Iberdrola component."""
    account = config_entry.data.get(CONF_USERNAME)

    data = hass.data[DOMAIN][account]

    for component in COMPONENTS:
        await hass.config_entries.async_forward_entry_unload(
            data.config_entry, component
        )

    del hass.data[DOMAIN][account]

    return True
