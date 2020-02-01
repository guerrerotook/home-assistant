# pylint: disable=redefined-outer-name
"""Tests for the Daikin config flow."""
import logging

from homeassistant.components.iberdrola import config_flow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME

USERNAME = "Username"
PASSWORD = "Password"

_LOGGER = logging.getLogger(__name__)


async def test_user(hass):
    """Test user config."""
    flow = config_flow.IberdrolaConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["step_id"] == "user"

    result = await flow.async_step_user(
        {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD, CONF_SCAN_INTERVAL: 10}
    )


# assert result["title"] == USERNAME
# assert result["data"][CONF_USERNAME] == USERNAME
