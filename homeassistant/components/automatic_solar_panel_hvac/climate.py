"""Platform for climate integration."""
import logging
import threading

import pyfronius

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_DEVICE_ID,
    CONF_LIGHTS,
    CONF_NAME,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
from .queue_processor import QueueProcessor

_LOGGER = logging.getLogger(__name__)


class Mode:
    """This class define the HVAC operation mode."""

    Heat = 1
    Dry = 2
    Cool = 3
    Fan = 7
    Auto = 8


MIN_TEMP = 16
MAX_TEMP = 30


class AutomaticClimateSystem(ClimateEntity):
    """This class represent the HVAC for all entities."""

    def __init__(
        self,
        device_id,
        name,
        hass: HomeAssistant,
        climateList: list,
        lightList: list,
        fronius_url: str,
        lowConsumption: int,
        highConsumption: int,
        turnOnThreshold: int,
        turnOffThreshold: int,
    ):
        """Initialize the climate component."""
        self._device_id = device_id
        self._name = name
        self._temperature = 26
        self._mode = Mode.Auto
        self._isOn = False
        self._fan_speed = 3
        self._hass = hass
        self._climateEntityList: list = climateList
        self._lightsEntityList: list = lightList
        self._fronius = pyfronius.Fronius(async_get_clientsession(hass), fronius_url)
        self._queue_processor: QueueProcessor = QueueProcessor(
            self._lightsEntityList,
            self._climateEntityList,
            hass,
            lowConsumption,
            highConsumption,
            turnOnThreshold,
            turnOffThreshold,
        )
        self.__createTimer()

        self._fan_modes = ["Speed Auto", "Speed 1 (Min)"]
        for i in range(2, self._fan_speed):
            self._fan_modes.append("Speed " + str(i))
        self._fan_modes.append("Speed " + str(self._fan_speed) + " (Max)")

        self._swing_modes = [
            "Auto",
            "Top",
            "MiddleTop",
            "Middle",
            "MiddleBottom",
            "Bottom",
            "Swing",
        ]
        self._swing_id = [0, 1, 2, 3, 4, 5, 7]

    @property
    def supported_features(self):
        """Return the supported features for the climate component."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def should_poll(self):
        """Return if poll should be consider for the climate component."""
        return False

    @property
    def name(self):
        """Return the name for the climate component."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the temperature units for the climate component."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature for the climate component."""
        return self._temperature

    @property
    def target_temperature(self):
        """Set the target temperature for the climate component."""
        return self._temperature

    @property
    def precision(self) -> float:
        """Return the precision mode for the climate component."""
        return PRECISION_WHOLE

    @property
    def hvac_mode(self):
        """Return the HVAC mode for the climate component."""
        return self._mode

    @property
    def hvac_modes(self):
        """Return the supported HVAC modes for the climate component."""
        return [HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_FAN_ONLY, HVAC_MODE_OFF]

    def set_hvac_mode(self, operation_mode):
        """Set the HVAC mode for the climate component."""
        _LOGGER.debug(
            "set_hvac_mode operation_mode "
            + str(operation_mode)
            + " mode: "
            + str(self._mode)
        )

        for climate_item in self._climateEntityList:
            data = {
                "entity_id": climate_item,
                "hvac_mode": operation_mode,
            }
            self._hass.services.call("climate", "set_hvac_mode", data, False)

        self._mode = operation_mode
        self.schedule_update_ha_state()

    @property
    def fan_mode(self):
        """Return the fan mode for the climate component."""
        if self._fan_speed >= len(self._fan_modes):
            return self._fan_modes[0]

        return self._fan_modes[self._fan_speed]

    @property
    def fan_modes(self):
        """Return the fan modes for the climate component."""
        return self._fan_modes

    def set_fan_mode(self, fan_mode):
        """Set the fan mode for the climate component."""
        for climate_item in self._climateEntityList:
            data = {
                "entity_id": climate_item,
                "fan_mode": fan_mode,
            }
            self._hass.services.call("climate", "set_fan_mode", data, False)

    @property
    def swing_mode(self):
        """Return the swing mode for the climate component."""
        return self._swing_modes[0]  # Auto

    def set_swing_mode(self, swing_mode):
        """Set the swing mode for the climate component."""
        self.schedule_update_ha_state()
        return

    @property
    def swing_modes(self):
        """Return the swing modes for the climate component."""
        return self._swing_modes

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMP

    def set_temperature(self, **kwargs):
        """Set the temperature for the climate component."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._temperature = int(round(kwargs.get(ATTR_TEMPERATURE)))

            for climate_item in self._climateEntityList:
                data = {
                    "entity_id": climate_item,
                    "temperature": self._temperature,
                }
                self._hass.services.call("climate", "set_temperature", data, False)

            self.schedule_update_ha_state()

    def __createTimer(self):
        self._working_timer = threading.Timer(5, self.__worker_timer)
        self._working_timer.start()

    def __worker_timer(self):
        self._hass.async_run_job(self.__async_worker)
        self.createTimer()

    async def __async_worker(self):
        if self._queue_processor.isEnabled():
            power_flow = await self._fronius.current_power_flow()
            power_photovoltaics = power_flow["power_photovoltaics"]["value"]
            power_grid = power_flow["power_grid"]["value"]
            power_load = power_flow["power_load"]["value"]

            await self._queue_processor.process_solar_queue(
                power_photovoltaics, power_grid, power_load
            )


def setup_platform(
    hass: HomeAssistant, config: ConfigEntry, add_devices, discovery_info=None
):
    """Define the setup for the climate component."""
    _LOGGER.debug("Adding component: Automatic Solar Panel Hvac ...")

    config = hass.data[DOMAIN][CONFIG]

    device_list = []

    device_list.append(
        AutomaticClimateSystem(
            config.get(CONF_DEVICE_ID),
            config.get(CONF_NAME),
            hass,
            config.get(CONF_CLIMATE),
            config.get(CONF_LIGHTS),
            config.get(CONF_FRONIUS),
            config.get(CONF_LOW_CONSUMPTION),
            config.get(CONF_HIGH_CONSUMPTION),
            config.get(CONF_TURN_ON_THRESHOLD),
            config.get(CONF_TURN_OFF_THRESHOLD),
        )
    )
    add_devices(device_list)

    return True
