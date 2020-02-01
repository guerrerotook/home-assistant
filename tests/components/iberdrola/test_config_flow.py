# pylint: disable=redefined-outer-name
"""Tests for the Daikin config flow."""
import pytest

from homeassistant import data_entry_flow
from homeassistant.components.iberdrola import config_flow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME

USERNAME = "username"
PASSWORD = "password"


def init_config_flow(hass):
    """Init a configuration flow."""
    flow = config_flow.FlowHandler()
    flow.hass = hass
    return flow


@pytest.fixture
async def test_user(hass, mock_daikin):
    """Test user config."""
    flow = init_config_flow(hass)

    result = await flow.async_step_user()
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user(
        {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD, CONF_SCAN_INTERVAL: 10}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"][USERNAME] == USERNAME
