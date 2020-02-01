"""Iberdrola integration."""
DOMAIN = "iberdrola"


async def async_setup(hass, config):
    """Define the async setup."""

    hass.states.async_set("iberdrola.init", "True")

    # Return boolean to indicate that initialization was successful.
    return True
