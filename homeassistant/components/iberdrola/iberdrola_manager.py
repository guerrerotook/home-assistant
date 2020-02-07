"""This class will handle the iberdrola API and other functionality."""

from datetime import timedelta
import logging

from iberdrola_auth import IberdrolaAuthentication

from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util.dt import utcnow

from .const import SIGNAL_STATE_UPDATED

_LOGGER = logging.getLogger(__name__)


class IberdrolaManager:
    """This class will handle the iberdrola API."""

    def __init__(self, hass, config):
        """Initialize the component state."""
        self.hass = hass
        self.config = config
        self.interval = config.data.get(CONF_SCAN_INTERVAL)
        self.session = async_get_clientsession(hass)

    def initialize(self):
        """Initialize the internal API and get a valid cookie."""
        self._iberdrola_auth = IberdrolaAuthentication(
            self.session,
            self.config.data.get(CONF_USERNAME),
            self.config.data.get(CONF_PASSWORD),
        )

    async def update(self, now):
        """Update the last information from Iberdrola API."""
        try:
            resultLogin = await self._iberdrola_auth.login()
            if isinstance(resultLogin, tuple) and resultLogin[0] is False:
                _LOGGER.error(resultLogin[1])

            self.iberdrola_data = await self._iberdrola_auth.getConsumptionData()

            self.hass.async_add_job(
                self.hass.config_entries.async_forward_entry_setup(
                    self.config_entry, "sensor"
                )
            )

            async_dispatcher_send(self.hass, SIGNAL_STATE_UPDATED)

            return True
        finally:
            """Schedule the execution of the funtion in the future to update the component."""
            async_track_point_in_utc_time(
                self.hass, self.update, utcnow() + timedelta(minutes=self.interval)
            )
