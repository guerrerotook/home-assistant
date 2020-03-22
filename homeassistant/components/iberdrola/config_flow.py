"""Config flow to configure the Iberdrola integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .iberdrola_auth import IberdrolaAuthentication

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SCAN_INTERVAL, default=10): int,
    },
    required=True,
    extra=vol.ALLOW_EXTRA,
)


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
        _LOGGER.info("IberdrolaConfigFlow __init__")

    async def async_step_user(self, user_input=None):
        """Show the setup form to the user."""
        errors = {}

        _LOGGER.info("empezando al configuration de usuario")

        if user_input is not None:
            _LOGGER.info("user_input is not none")
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._scan_interval = user_input[CONF_SCAN_INTERVAL]

            try:
                # pylint: disable=no-value-for-parameter
                session = async_get_clientsession(self.hass)

                connection = IberdrolaAuthentication(
                    session=session, username=self._username, password=self._password,
                )

                _LOGGER.info("iniciando sesion en Iberdrola")
                result = await connection.login()
                if isinstance(result, tuple) and result[0] is False:
                    errors[CONF_USERNAME] = result[1]
                    errors["base"] = result[1]
                    raise Exception(result[1])

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
        else:
            _LOGGER.error("user_input is none")

        _LOGGER.error("vamos a ejecutar el show form")

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors or {}
        )

    # async def async_step_import(self, user_input):
    #     """Import a config flow from configuration."""

    #     _LOGGER.info("async_step_import")
    #     _LOGGER.info("user_input")
    #     self._username = user_input[CONF_USERNAME]
    #     self._password = user_input[CONF_PASSWORD]
    #     errors = {}
    #     scan_interval = 10

    #     if user_input.get(CONF_SCAN_INTERVAL):
    #         scan_interval = user_input[CONF_SCAN_INTERVAL]

    #     if scan_interval < 5:
    #         scan_interval = 5

    #     try:
    #         session = async_get_clientsession(self.hass)
    #         connection = IberdrolaAuthentication(
    #             session=session, username=self._username, password=self._password,
    #         )

    #         result = await connection.login()
    #         if isinstance(result, tuple) and result[0] is False:
    #             errors[CONF_USERNAME] = result[1]
    #             errors["base"] = result[1]
    #             raise Exception(result[1])

    #     except Exception:
    #         _LOGGER.error("Invalid credentials for %s", self._username)
    #         return self.async_abort(reason="invalid_credentials")

    #     return self.async_create_entry(
    #         title=f"Iberdrola-{self._username} (from configuration)",
    #         data={
    #             CONF_USERNAME: self._username,
    #             CONF_PASSWORD: self._password,
    #             CONF_SCAN_INTERVAL: scan_interval,
    #         },
    #     )
