"""Config flow to configure the Iberdrola integration."""
from collections import OrderedDict
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .iberdrola_auth import IberdrolaAuthentication

_LOGGER = logging.getLogger(__name__)


@callback
def configured_accounts(hass):
    """Return tuple of configured usernames."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if entries:
        return (entry.data[CONF_USERNAME] for entry in entries)
    return ()


class IberdrolaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Iberdrola config flow."""

    def __init__(self):
        """Initialize."""
        self._username = vol.UNDEFINED
        self._password = vol.UNDEFINED
        self._scan_interval = 10

    async def async_step_user(self, user_input=None):
        """Show the setup form to the user."""
        errors = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]

            try:
                # pylint: disable=no-value-for-parameter
                session = async_get_clientsession(self.hass)
                connection = IberdrolaAuthentication(
                    session=session, username=self._username, password=self._password,
                )

                loginResult = await connection.login()
                _LOGGER.info("resultado de login")
                _LOGGER.info(loginResult)
                # if await connection.login() is False:
                #    raise Exception(
                #       "Unexpected error communicating with the Audi server"
                #    )

            except vol.Invalid:
                errors[CONF_USERNAME] = "invalid_username"
            except Exception:
                errors["base"] = "invalid_credentials"
            else:
                if self._username in configured_accounts(self.hass):
                    errors["base"] = "user_already_configured"
                else:
                    return self.async_create_entry(
                        title=f"Iberdrola-{self._username}",
                        data={
                            CONF_USERNAME: self._username,
                            CONF_PASSWORD: self._password,
                            CONF_SCAN_INTERVAL: self._scan_interval,
                        },
                    )

        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_USERNAME, default=self._username)] = str
        data_schema[vol.Required(CONF_PASSWORD, default=self._password)] = str
        data_schema[vol.Optional(CONF_SCAN_INTERVAL, default=10)] = int

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_import(self, user_input):
        """Import a config flow from configuration."""
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        scan_interval = 10

        if user_input.get(CONF_SCAN_INTERVAL):
            scan_interval = user_input[CONF_SCAN_INTERVAL]

        if scan_interval < 5:
            scan_interval = 5

        try:
            session = async_get_clientsession(self.hass)
            connection = IberdrolaAuthentication(
                session=session,
                username=vol.Email()(self._username),
                password=self._password,
            )

            if await connection.try_login(False) is False:
                raise Exception("Unexpected error communicating with Iberdrola")

        except Exception:
            _LOGGER.error("Invalid credentials for %s", username)
            return self.async_abort(reason="invalid_credentials")

        return self.async_create_entry(
            title=f"{username} (from configuration)",
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_SCAN_INTERVAL: scan_interval,
            },
        )
