"""The Automatic Solar Panel based HVAC."""
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_LIGHTS, CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CLIMATE,
    CONF_FRONIUS,
    CONF_HIGH_CONSUMPTION,
    CONF_LOW_CONSUMPTION,
    CONF_TURN_OFF_THRESHOLD,
    CONF_TURN_ON_THRESHOLD,
    CONFIG,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_DEVICE_ID): cv.string,
                vol.Required(CONF_FRONIUS): cv.url,
                vol.Optional(CONF_LOW_CONSUMPTION, default=100): cv.Number,
                vol.Optional(CONF_HIGH_CONSUMPTION, default=700): cv.Number,
                vol.Optional(CONF_TURN_ON_THRESHOLD, default=400): cv.Number,
                vol.Optional(CONF_TURN_OFF_THRESHOLD, default=800): cv.Number,
                vol.Optional(CONF_CLIMATE, default=[]): cv.entity_ids,
                vol.Optional(CONF_LIGHTS, default=[]): cv.entity_ids,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, base_config: ConfigEntry):
    """Async setup of the Iberdrola component."""

    config = base_config.get(DOMAIN)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][CONFIG] = config

    hass.helpers.discovery.load_platform("sensor", DOMAIN, None, config)
    hass.helpers.discovery.load_platform("climate", DOMAIN, None, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, None, config)
    hass.helpers.discovery.load_platform("lock", DOMAIN, None, config)

    return True
