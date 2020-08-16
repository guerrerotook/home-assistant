"""This class will handle the processing of the queue."""
from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant, State

from .const import DOMAIN, SENSOR_KEY
from .sensor import OperationStatusSensor
from .state_machine import DeviceStateMachine

_LOGGER = logging.getLogger(__name__)


class QueueProcessor:
    """This class will execute a timer to check the system."""

    def __init__(
        self,
        light_list: list,
        hvac_list: list,
        hass: HomeAssistant,
        lowConsumption: int,
        highConsumption: int,
        turnOnThreshold: int,
        turnOffThreshold: int,
    ):
        """Initialize the class."""
        self._hass = hass
        self._lights = light_list
        self._hvacs = hvac_list
        self._last_domain = "none"
        self._last_domain_off = "none"
        self._light_state_machine = {}  # Dict[str, DeviceStateMachine]
        self._hvac_state_machine = {}  # Dict[str, DeviceStateMachine]
        self._low_consumption = lowConsumption
        self._high_consumption = highConsumption
        self._turn_on_threshold = turnOffThreshold
        self._turn_off_threshold = turnOffThreshold
        self._current_state_machine = None
        self._current_device = None
        self._shut_down_wait: bool = False
        self._last_time_shut_down: datetime = None
        self._sensor_on: OperationStatusSensor = None
        self._sensor_off: OperationStatusSensor = None
        self._time_to_shutdown: int = 60 * 10
        self._time_to_shutdown_next: int = 60 * 2
        self._last_time_high_power_consuption: datetime = None
        for item in light_list:
            self._light_state_machine[item] = DeviceStateMachine(
                item, hass, lowConsumption, highConsumption, "light"
            )

        for item in hvac_list:
            self._hvac_state_machine[item] = DeviceStateMachine(
                item, hass, lowConsumption, highConsumption, "climate"
            )

    def __checkForSensor(self):
        if self._sensor_off is None:
            self._sensor_off = self._hass.data[DOMAIN][SENSOR_KEY][1]
            self._sensor_on = self._hass.data[DOMAIN][SENSOR_KEY][0]

    def __isSunAvoveHorizon(self) -> bool:
        result: bool = False

        sun: State = self._hass.states.get("sun.sun")

        if sun.state == "above_horizon":
            result = True

        return result

    def __isSystemEnabled(self) -> bool:
        result: bool = True

        mainSwitch: State = self._hass.states.get("switch.solarpanel_automation")
        if mainSwitch is not None and mainSwitch.state == "off":
            result = False

        return result

    def isEnabled(self) -> bool:
        """Return is the system is enabled or not."""
        return self.__isSystemEnabled() or self.__isSunAvoveHorizon()

    async def process_solar_queue(
        self, power_photovoltaics: int, power_grid: int, power_load: int
    ):
        """Process the queue and make sure devices are on of off based on the power consumption."""
        self.__checkForSensor()

        if not self.isEnabled():
            return

        if power_grid < self._turn_on_threshold:
            # encender un dispositivo
            self._last_time_high_power_consuption = None
            # esperar dos minutos para encender otro, pero mientras se puede seguir apagando dispositivos
            if self._shut_down_wait:
                dateTimeDiff: timedelta = datetime.now() - self._last_time_shut_down
                if dateTimeDiff.total_seconds() >= self._time_to_shutdown_next:
                    self._shut_down_wait = False
                _LOGGER.debug(
                    "Esperando 2 minutos por a ver apagado un dispositivo para encender otro, %d "
                    % (dateTimeDiff.total_seconds())
                )
                return

            # ya se puede encender dispositivos
            if self._current_state_machine is None:
                self._current_device = self.__getNextDeviceToTurnOn()
                if self._current_device is not None:
                    if self._current_device.domain == "climate":
                        data = {
                            "entity_id": self._current_device.entity_id,
                            "hvac_mode": "cool",
                        }
                        self._current_state_machine: DeviceStateMachine = self._hvac_state_machine[
                            self._current_device.entity_id
                        ]
                        await self._hass.services.async_call(
                            "climate", "set_hvac_mode", data, False
                        )
                    elif self._current_device.domain == "light":
                        data = {"entity_id": self._current_device.entity_id}
                        self._current_state_machine: DeviceStateMachine = self._light_state_machine[
                            self._current_device.entity_id
                        ]
                        await self._hass.services.async_call(
                            "light", "turn_on", data, False
                        )
                    _LOGGER.debug(
                        "Entity %s acaba de encenderse"
                        % (self._current_device.entity_id)
                    )
                    self._sensor_on.setState(self._current_device.entity_id)
                    self._sensor_on.setLastTimeUpdate(datetime.now())
                    self._sensor_on.schedule_update_ha_state()

                    if self._current_state_machine is not None:
                        self._current_state_machine.innitStateMachine()
            if self._current_state_machine is not None:
                self._current_state_machine.executeWorkflow(
                    power_photovoltaics, power_grid, power_load
                )
            if (
                self._current_state_machine is not None
                and self._current_state_machine.isOff()
            ):
                data = {"entity_id": self._current_device.entity_id}
                await self._hass.services.async_call(
                    self._current_device.domain, "turn_off", data, False
                )
                _LOGGER.debug(
                    "Entity %s acaba de apagar" % (self._current_device.entity_id)
                )
            if (
                self._current_state_machine is not None
                and self._current_state_machine.isDone()
            ):
                self._current_state_machine = None

        elif power_grid > self._turn_off_threshold:
            # apagar un dispositivo
            if self._last_time_high_power_consuption is None:
                self._last_time_high_power_consuption: datetime = datetime.now()
                _LOGGER.debug(
                    "Consumo excesivo de %d se va a monitorizar duante 5 minutos el consumo"
                    % (power_grid)
                )
            else:
                dateTimeDiff: timedelta = datetime.now() - self._last_time_high_power_consuption
                _LOGGER.debug(
                    "Esperando 5 minutos para apagar un dispositivo, %d "
                    % (dateTimeDiff.total_seconds())
                )
                if dateTimeDiff.total_seconds() >= self._time_to_shutdown:
                    _LOGGER.debug(
                        "Consumo excesivo de %d han pasado 5 minutos, apagado un dispositivo "
                        % (power_grid)
                    )
                    device: State = self.__getNextDeviceToTurnOff()
                    if device is not None:
                        data = {"entity_id": device.entity_id}
                        await self._hass.services.async_call(
                            device.domain, "turn_off", data, False
                        )
                        _LOGGER.debug(
                            "Consumo excesivo de %d se apagará el dispositivo %s"
                            % (power_grid, device.entity_id)
                        )
                        self._last_time_shut_down = datetime.now()
                        self._sensor_off.setState(device.entity_id)
                        self._sensor_off.setLastTimeUpdate(datetime.now())
                        self._sensor_off.schedule_update_ha_state()
                        if (
                            self._current_state_machine is not None
                            and self._current_state_machine.getDeviceId
                            == device.entity_id
                        ):
                            self._current_state_machine.setStateOff()
                            self._current_state_machine = None
                        self._shut_down_wait = True
                    self._last_time_high_power_consuption: datetime = None

    def __getNextDeviceToTurnOn(self) -> State:
        if self._last_domain == "none":
            self._last_domain = "Light"

        entities_seach: list = self._lights
        state_condition: str = "On"

        if self._last_domain == "Light":
            entities_seach = self._hvacs
            state_condition = "off"
            self._last_domain = "Climate"
        elif self._last_domain == "Climate":
            entities_seach = self._lights
            state_condition = "off"
            self._last_domain = "Light"

        entity: State = self.__getNextEntityWhereStateIs(
            entities_seach, state_condition
        )
        return entity

    def __entityHasALock(self, entity: State) -> bool:
        result: bool = False

        entity_name: str = "switch." + entity.entity_id.replace(
            entity.domain + ".", ""
        ) + "_lock"

        state: State = self._hass.states.get(entity_name)
        if state is not None and state.state == "on":
            result = True

        return result

    def __getNextDeviceToTurnOff(self) -> State:
        if self._last_domain_off == "none":
            self._last_domain_off = "Light"

        entities_seach: list = self._lights
        state_condition: str = "on"
        entity: State = None

        if self._last_domain_off == "Light":
            entities_seach = self._hvacs.copy()
            entities_seach.reverse()
            self._last_domain_off = "Climate"
            entity = self.__getNextEntityWhereStateIs(entities_seach, state_condition)
            if entity is None:
                entity = self.__getNextEntityWhereStateIs(entities_seach, "cool")
                if entity is None:
                    entity = self.__getNextEntityWhereStateIs(entities_seach, "heat")

        elif self._last_domain_off == "Climate":
            entities_seach = self._lights.copy()
            entities_seach.reverse()
            self._last_domain_off = "Light"
            entity = self.getNextEntityWhereStateIs(entities_seach, state_condition)

        return entity

    def __getNextEntityWhereStateIs(self, entities: list, state: str) -> State:
        for entity_name in entities:
            entity: State = self._hass.states.get(entity_name)
            if (
                entity is not None
                and not self.entityHasALock(entity)
                and entity.state == state
            ):
                return entity

    def __getNextEntityWhereStateIsNot(self, entities: list, state: str) -> State:
        for entity_name in entities:
            entity: State = self._hass.states.get(entity_name)
            if (
                entity is not None
                and not self.entityHasALock(entity)
                and entity.state != state
            ):
                return entity
