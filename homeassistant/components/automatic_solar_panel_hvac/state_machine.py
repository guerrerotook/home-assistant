"""This is the state machine configuration for each entity."""
from datetime import datetime, timedelta
import enum
import logging

from homeassistant.core import HomeAssistant


class DeviceState(enum.Enum):
    """Define the state machine states."""

    Unknown = -1
    Off = 0
    On = 1
    JustStarted = 2
    WaitingLowerPowerGridReading = 3
    WaitingHigherPowerGridReading = 4
    CommitdedOn = 5
    WaitingOnNextPickup = 6
    WaitingOnLockHigherLimit = 7
    Started = 8
    LowerPowerGridReading = 9
    HigherPowerGridReading = 10
    LastWaiting = 11


_LOGGER = logging.getLogger(__name__)


class DeviceStateMachine:
    """Define the state machine class to handle the status of the Hvac component."""

    def __init__(
        self,
        device_id: str,
        hass: HomeAssistant,
        lowConsumption: int,
        highConsumption: int,
        domain: str,
    ):
        """Initialize the device state machine."""
        self._hass = hass
        self._device_id = device_id
        self._state: DeviceState = DeviceState.Unknown
        self._low_consumption: int = lowConsumption
        self._high_consumption: int = highConsumption
        self._high_power_limit_count: int = 0
        self._domain = domain

    @property
    def getDeviceId(self) -> str:
        """Return the device id."""
        return self._device_id

    def executeWorkflow(
        self, power_photovoltaics: int, power_grid: int, power_load: int
    ):
        """Execute the workflow."""
        _LOGGER.debug(f"Entity {self._device_id} está en el estado {self._state.name}")
        if self._state == DeviceState.Started:
            dateTimeDiff: timedelta = datetime.now() - self._working_time
            _LOGGER.debug(
                "Entity %s ya han pasado %d segundos del estado %s"
                % (self._device_id, dateTimeDiff.total_seconds(), self._state.name)
            )
            if dateTimeDiff.total_seconds() >= 60 * 2:
                _LOGGER.debug(
                    "Entity %s ya han pasado %d segundos" % (self._device_id, 60 * 2)
                )
                self._state = DeviceState.LowerPowerGridReading
                self._working_time: datetime = datetime.now()

        elif self._state == DeviceState.LowerPowerGridReading:
            _LOGGER.debug(
                "Entity %s la lectura de potencia de red es %d"
                % (self._device_id, power_grid)
            )
            if power_grid < self._low_consumption:
                self._state = DeviceState.LastWaiting
                self._working_time: datetime = datetime.now()
                _LOGGER.debug(
                    "Entity %s el dispositivo está autorizado a seguir funcionando con ese consumo eletrico"
                    % (self._device_id)
                )
                if self._domain == "light":
                    self._state = DeviceState.On
                    _LOGGER.debug(
                        "Entity %s el dispositivo es una luz, no tiene que esperar más minutos adicionales"
                        % (self._device_id)
                    )
            else:
                self._state = DeviceState.HigherPowerGridReading
        elif self._state == DeviceState.HigherPowerGridReading:
            _LOGGER.debug(
                "Entity %s la lectura de potencia de red es %d"
                % (self._device_id, power_grid)
            )
            if power_grid >= self._high_consumption:
                if self._high_power_limit_count > 1:
                    self._state = DeviceState.Off
                    _LOGGER.debug(
                        "Entity %s el dispositivo consume mucha electricidad %d se va a apagar automáticamente"
                        % (self._device_id, power_grid)
                    )
                else:
                    self._state = DeviceState.WaitingHigherPowerGridReading
                    self._working_time: datetime = datetime.now()
                    _LOGGER.debug(
                        "Entity %s el dispositivo consume menos de %d esperando 5 minutos"
                        % (self._device_id, self._high_power_limit_count)
                    )
            else:
                self._state = DeviceState.On
                _LOGGER.debug(
                    "Entity %s el dispositivo está autorizado a seguir funcionando con ese consumo eletrico"
                    % (self._device_id)
                )
        elif self._state == DeviceState.WaitingHigherPowerGridReading:
            dateTimeDiff: timedelta = self._working_time - datetime.now()
            if dateTimeDiff.total_seconds() >= 60 * 5:
                self._state = DeviceState.HigherPowerGridReading
                self._high_power_limit_count = self._high_power_limit_count + 1
                _LOGGER.debug(
                    "Entity %s el dispositivo sigue consumiendo más de 700W se van a esperar otros 5 minutos"
                    % (self._device_id)
                )
        elif self._state == DeviceState.LastWaiting:
            dateTimeDiff: timedelta = datetime.now() - self._working_time
            _LOGGER.debug(
                "Entity %s ya han pasado %d segundos del estado %s"
                % (self._device_id, dateTimeDiff.total_seconds(), self._state.name)
            )
            if dateTimeDiff.total_seconds() >= 60 * 5:
                self._state = DeviceState.On
                _LOGGER.debug(
                    "Entity %s se han esperado 5 minutos desde que se encendio el dispositivo"
                    % (self._device_id)
                )

    def isDone(self) -> bool:
        """Return if the state machie is done."""
        return self._state == DeviceState.On or self._state == DeviceState.Off

    def isOff(self) -> bool:
        """Return if entity is off machie is done."""
        return self._state == DeviceState.Off

    def innitStateMachine(self):
        """Initialize the state machine."""
        self._state = DeviceState.Started
        self._working_time: datetime = datetime.now()

    def checkHvacLowerLimit(self, power_grid: int) -> bool:
        """Check if the state machine is waiting on a lower power grid reading."""
        result: bool = False
        if power_grid <= self._low_consumption:
            result = True
            self._state = DeviceState.WaitingLowerPowerGridReading
        return result

    def checkHvacHigherLimit(self, power_grid: int) -> bool:
        """Check if the state machine is waiting on a higher power grid reading."""
        result: bool = False
        if power_grid <= self._high_consumption:
            result = True
            self._state = DeviceState.WaitingHigherPowerGridReading
        else:
            self._state = DeviceState.WaitingOnLockHigherLimit
        return result

    def isWaitingOnHigherLimit(self) -> bool:
        """Check if the state machine is waiting on a lock waiting."""
        return self._state == DeviceState.WaitingOnLockHigherLimit

    def setStateOn(self):
        """Set the state to on."""
        self._state = DeviceState.On

    def setStateOff(self):
        """Set the state to off."""
        self._sate = DeviceState.Off
