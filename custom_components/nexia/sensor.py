"""Support for Nexia / Trane XL Thermostats."""

from nexia.const import UNIT_CELSIUS

from homeassistant.const import (
    ATTR_ATTRIBUTION,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity

from . import (
    ATTR_FIRMWARE,
    ATTR_MODEL,
    ATTR_THERMOSTAT_ID,
    ATTR_THERMOSTAT_NAME,
    ATTR_ZONE_ID,
    ATTRIBUTION,
    DATA_NEXIA,
    NEXIA_DEVICE,
    UPDATE_COORDINATOR,
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up sensors for a Nexia device."""
    nexia_home = hass.data[DATA_NEXIA][NEXIA_DEVICE]
    coordinator = hass.data[DATA_NEXIA][UPDATE_COORDINATOR]

    sensors = list()

    ###########################################################################
    # Thermostat / System Sensors
    ###########################################################################
    for thermostat_id in nexia_home.get_thermostat_ids():
        thermostat = nexia_home.get_thermostat_by_id(thermostat_id)
        #######################################################################
        # System Status
        sensors.append(
            NexiaSensor(
                coordinator,
                thermostat,
                "get_system_status",
                "System Status",
                None,
                None,
            )
        )
        #######################################################################
        # Air cleaner
        sensors.append(
            NexiaSensor(
                coordinator,
                thermostat,
                "get_air_cleaner_mode",
                "Air Cleaner Mode",
                None,
                None,
            )
        )
        #######################################################################
        # Compressor Speed
        if thermostat.has_variable_speed_compressor():
            sensors.append(
                NexiaSensor(
                    coordinator,
                    thermostat,
                    "get_current_compressor_speed",
                    "Current Compressor Speed",
                    None,
                    "%",
                    percent_conv,
                )
            )
            sensors.append(
                NexiaSensor(
                    coordinator,
                    thermostat,
                    "get_requested_compressor_speed",
                    "Requested Compressor Speed",
                    None,
                    "%",
                    percent_conv,
                )
            )
        #######################################################################
        # Outdoor Temperature
        if thermostat.has_outdoor_temperature():
            unit = (
                TEMP_CELSIUS
                if thermostat.get_unit() == UNIT_CELSIUS
                else TEMP_FAHRENHEIT
            )
            sensors.append(
                NexiaSensor(
                    coordinator,
                    thermostat,
                    "get_outdoor_temperature",
                    "Outdoor Temperature",
                    DEVICE_CLASS_TEMPERATURE,
                    unit,
                )
            )
        #######################################################################
        # Relative Humidity
        if thermostat.has_relative_humidity():
            sensors.append(
                NexiaSensor(
                    coordinator,
                    thermostat,
                    "get_relative_humidity",
                    "Relative Humidity",
                    DEVICE_CLASS_HUMIDITY,
                    "%",
                    percent_conv,
                )
            )

        #######################################################################
        # Zone Sensors
        #######################################################################
        for zone_id in thermostat.get_zone_ids():
            zone = thermostat.get_zone_by_id(zone_id)
            unit = (
                TEMP_CELSIUS
                if thermostat.get_unit() == UNIT_CELSIUS
                else TEMP_FAHRENHEIT
            )
            ###################################################################
            # Temperature
            sensors.append(
                NexiaZoneSensor(
                    coordinator,
                    zone,
                    "get_temperature",
                    "Temperature",
                    DEVICE_CLASS_TEMPERATURE,
                    unit,
                    None,
                )
            )
            ###################################################################
            # Zone Status
            sensors.append(
                NexiaZoneSensor(
                    coordinator, zone, "get_status", "Zone Status", None, None,
                )
            )
            ###################################################################
            # Setpoint Status
            sensors.append(
                NexiaZoneSensor(
                    coordinator,
                    zone,
                    "get_setpoint_status",
                    "Zone Setpoint Status",
                    None,
                    None,
                )
            )

    add_entities(sensors, True)


def percent_conv(val):
    """
    Converts an actual percentage (0.0 - 1.0) to 0-100 scale
    :param val: float (0.0 - 1.0)
    :return: val * 100.0
    """
    return val * 100.0


class NexiaSensor(Entity):
    """Provides Nexia sensor support."""

    def __init__(
        self,
        coordinator,
        device,
        sensor_call,
        sensor_name,
        sensor_class,
        sensor_unit,
        modifier=None,
    ):
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._device = device
        self._call = sensor_call
        self._sensor_name = sensor_name
        self._class = sensor_class
        self._state = None
        self._unit_of_measurement = sensor_unit
        self._modifier = modifier

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._device.thermostat_id}_{self._call}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._device.get_name() + " " + self._sensor_name

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_MODEL: self._device.get_model(),
            ATTR_FIRMWARE: self._device.get_firmware(),
            ATTR_THERMOSTAT_NAME: self._device.get_name(),
            ATTR_THERMOSTAT_ID: self._device.thermostat_id,
        }

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._class

    @property
    def state(self):
        """Return the state of the sensor."""
        val = getattr(self._device, self._call)()
        if self._modifier:
            val = self._modifier(val)
        if isinstance(val, float):
            val = round(val, 1)
        return val

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """Update are handled by the coordinator."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Undo subscription."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)


class NexiaZoneSensor(NexiaSensor):
    """ Nexia Zone Sensor Support """

    def __init__(
        self,
        coordinator,
        device,
        sensor_call,
        sensor_name,
        sensor_class,
        sensor_unit,
        modifier=None,
    ):
        super().__init__(
            coordinator,
            device,
            sensor_call,
            sensor_name,
            sensor_class,
            sensor_unit,
            modifier,
        )
        self._device = device

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._device.zone_id}_{self._call}"

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_MODEL: self._device.thermostat.get_model(),
            ATTR_FIRMWARE: self._device.thermostat.get_firmware(),
            ATTR_THERMOSTAT_NAME: self._device.thermostat.get_name(),
            ATTR_THERMOSTAT_ID: self._device.thermostat.thermostat_id,
            ATTR_ZONE_ID: self._device.zone_id,
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        val = getattr(self._device, self._call)()
        if self._modifier:
            val = self._modifier(val)
        if isinstance(val, float):
            val = round(val, 1)
        return val
