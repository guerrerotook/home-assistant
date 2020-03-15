# pylint: disable=redefined-outer-name
"""Tests for the Daikin config flow."""
from copy import deepcopy
import logging

from homeassistant.components import iberdrola
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME

from tests.common import MockConfigEntry

USERNAME = "Username"
PASSWORD = "Password"

_LOGGER = logging.getLogger(__name__)

ENTRY_CONFIG = {
    CONF_USERNAME: USERNAME,
    CONF_PASSWORD: PASSWORD,
    CONF_SCAN_INTERVAL: 10,
}


async def test_user(hass):
    """Test user config."""

    config_entry = MockConfigEntry(
        domain=iberdrola.const.DOMAIN,
        data=deepcopy(ENTRY_CONFIG),
        title="IberdrolaIntegrationTest",
    )

    await iberdrola.async_setup(hass, config_entry)
