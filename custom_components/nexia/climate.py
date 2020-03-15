"""Support for Nexia / Trane XL thermostats."""
import logging

from nexia.const import (
    FAN_MODES,
    OPERATION_MODE_AUTO,
    OPERATION_MODE_COOL,
    OPERATION_MODE_HEAT,
    OPERATION_MODE_OFF,
    OPERATION_MODES,
    SYSTEM_STATUS_COOL,
    SYSTEM_STATUS_HEAT,
    SYSTEM_STATUS_IDLE,
    UNIT_FAHRENHEIT,
)
import voluptuous as vol

from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    ATTR_AUX_HEAT,
    ATTR_CURRENT_HUMIDITY,
    ATTR_FAN_MODE,
    ATTR_FAN_MODES,
    ATTR_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_HUMIDITY,
    ATTR_MAX_TEMP,
    ATTR_MIN_HUMIDITY,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_STEP,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_AUX_HEAT,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_OFF,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_AIRCLEANER_MODE,
    ATTR_DEHUMIDIFY_SETPOINT,
    ATTR_DEHUMIDIFY_SUPPORTED,
    ATTR_HOLD_MODES,
    ATTR_HUMIDIFY_SETPOINT,
    ATTR_HUMIDIFY_SUPPORTED,
    ATTR_SETPOINT_STATUS,
    ATTR_THERMOSTAT_ID,
    ATTR_ZONE_ID,
    ATTR_ZONE_STATUS,
    ATTRIBUTION,
    DATA_NEXIA,
    DOMAIN,
    MANUFACTURER,
    NEXIA_DEVICE,
    UPDATE_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_AIRCLEANER_MODE = "set_aircleaner_mode"
SERVICE_SET_HUMIDIFY_SETPOINT = "set_humidify_setpoint"

SET_FAN_MIN_ON_TIME_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_AIRCLEANER_MODE): cv.string,
    }
)

SET_HUMIDITY_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_HUMIDITY): vol.All(
            vol.Coerce(int), vol.Range(min=35, max=65)
        ),
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up climate for a Nexia device."""

    nexia_data = hass.data[DOMAIN][config_entry.entry_id][DATA_NEXIA]
    nexia_home = nexia_data[NEXIA_DEVICE]
    coordinator = nexia_data[UPDATE_COORDINATOR]

    entities = []
    for thermostat_id in nexia_home.get_thermostat_ids():
        thermostat = nexia_home.get_thermostat_by_id(thermostat_id)
        for zone_id in thermostat.get_zone_ids():
            zone = thermostat.get_zone_by_id(zone_id)
            entities.append(NexiaZone(coordinator, zone))

    def humidify_set_service(service):
        entity_id = service.data.get(ATTR_ENTITY_ID)
        humidity = service.data.get(ATTR_HUMIDITY)
        target_zones = []

        for zone in entities:
            if entity_id and zone.entity_id not in entity_id:
                continue

            if (
                zone.thermostat.has_humidify_support()
                and zone.thermostat not in target_zones
            ):
                target_zones.append(zone)

        for zone in target_zones:
            thermostat.set_humidify_setpoint(int(humidity) / 100.0)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HUMIDIFY_SETPOINT,
        humidify_set_service,
        schema=SET_HUMIDITY_SCHEMA,
    )

    def aircleaner_set_service(service):
        entity_id = service.data.get(ATTR_ENTITY_ID)
        aircleaner_mode = service.data.get(ATTR_AIRCLEANER_MODE)
        target_zones = []

        for zone in entities:
            if entity_id and zone.entity_id not in entity_id:
                continue

            if zone.thermostat not in target_zones:
                target_zones.append(zone)

        for zone in target_zones:
            zone.set_aircleaner_mode(aircleaner_mode)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AIRCLEANER_MODE,
        aircleaner_set_service,
        schema=SET_FAN_MIN_ON_TIME_SCHEMA,
    )

    async_add_entities(entities, True)


class NexiaZone(ClimateDevice):
    """Provides Nexia Climate support."""

    def __init__(self, coordinator, device):
        """Initialize the thermostat."""
        self.thermostat = device.thermostat
        self._device = device
        self._coordinator = coordinator
        self._unique_id = f"{self._device.zone_id}_zone"

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return self._unique_id

    @property
    def supported_features(self):
        """Return the list of supported features."""
        supported = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE

        if self._device.thermostat.has_relative_humidity():
            supported |= SUPPORT_TARGET_HUMIDITY

        if self._device.thermostat.has_emergency_heat():
            supported |= SUPPORT_AUX_HEAT

        return supported

    @property
    def is_fan_on(self):
        """Blower is on."""
        return self._device.thermostat.is_blower_active()

    @property
    def name(self):
        """Name of the zone."""
        return self._device.get_name()

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return (
            TEMP_CELSIUS
            if self._device.thermostat.get_unit() == "C"
            else TEMP_FAHRENHEIT
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.get_temperature()

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._device.thermostat.get_fan_mode()

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._device.thermostat.set_fan_mode(fan_mode)
        self.schedule_update_ha_state()

    def set_hold_mode(self, hold_mode):
        """Set new target hold mode."""
        if hold_mode.lower() == "none":
            self._device.call_return_to_schedule()
        else:
            self._device.set_preset(hold_mode)
        self.schedule_update_ha_state()

    @property
    def preset_mode(self):
        """Preset that is active."""
        return self._device.get_preset()

    @property
    def preset_modes(self):
        """All presets."""
        return self._device.get_presets()

    def set_humidity(self, humidity):
        """Dehumidify target."""
        self._device.thermostat.set_dehumidify_setpoint(humidity / 100.0)
        self.schedule_update_ha_state()

    @property
    def current_humidity(self):
        """Humidity indoors."""
        if self._device.thermostat.has_relative_humidity():
            return round(self._device.thermostat.get_relative_humidity() * 100.0, 1)
        return "Not supported"

    @property
    def target_temperature(self):
        """Temperature we try to reach."""
        if self._device.get_current_mode() == "COOL":
            return self._device.get_cooling_setpoint()
        return self._device.get_heating_setpoint()

    @property
    def hvac_action(self) -> str:
        """Operation ie. heat, cool, idle."""
        system_status = self._device.thermostat.get_system_status()
        zone_called = self._device.is_calling()

        if self._device.get_requested_mode() == OPERATION_MODE_OFF:
            return STATE_OFF
        if not zone_called:
            return CURRENT_HVAC_IDLE
        if system_status == SYSTEM_STATUS_COOL:
            return CURRENT_HVAC_COOL
        if system_status == SYSTEM_STATUS_HEAT:
            return CURRENT_HVAC_HEAT
        if system_status == SYSTEM_STATUS_IDLE:
            return CURRENT_HVAC_IDLE
        return "idle"

    @property
    def hvac_mode(self):
        """Operation requested ie. heat, cool, idle."""
        return self.mode

    @property
    def hvac_modes(self):
        """List of HVAC available modes."""
        return [
            HVAC_MODE_OFF,
            HVAC_MODE_AUTO,
            HVAC_MODE_HEAT_COOL,
            HVAC_MODE_HEAT,
            HVAC_MODE_COOL,
        ]

    @property
    def mode(self):
        """Return current mode, as the user-visible name."""

        mode = self._device.get_requested_mode()
        hold = self._device.is_in_permanent_hold()

        if mode == OPERATION_MODE_OFF:
            return HVAC_MODE_OFF
        if not hold and mode == OPERATION_MODE_AUTO:
            return HVAC_MODE_AUTO
        if mode == OPERATION_MODE_AUTO:
            return HVAC_MODE_HEAT_COOL
        if mode == OPERATION_MODE_HEAT:
            return HVAC_MODE_HEAT
        if mode == OPERATION_MODE_COOL:
            return HVAC_MODE_COOL
        raise KeyError(f"Unhandled mode: {mode}")

    def set_temperature(self, **kwargs):
        """Set target temperature."""
        new_heat_temp = kwargs.get(ATTR_TARGET_TEMP_LOW, None)
        new_cool_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH, None)
        set_temp = kwargs.get(ATTR_TEMPERATURE, None)

        deadband = self._device.thermostat.get_deadband()
        cur_cool_temp = self._device.get_cooling_setpoint()
        cur_heat_temp = self._device.get_heating_setpoint()
        (min_temp, max_temp) = self._device.thermostat.get_setpoint_limits()

        # Check that we're not going to hit any minimum or maximum values
        if new_heat_temp and new_heat_temp + deadband > max_temp:
            new_heat_temp = max_temp - deadband
        if new_cool_temp and new_cool_temp - deadband < min_temp:
            new_cool_temp = min_temp + deadband

        # Check that we're within the deadband range, fix it if we're not
        if new_heat_temp and new_heat_temp != cur_heat_temp:
            if new_cool_temp - new_heat_temp < deadband:
                new_cool_temp = new_heat_temp + deadband
        if new_cool_temp and new_cool_temp != cur_cool_temp:
            if new_cool_temp - new_heat_temp < deadband:
                new_heat_temp = new_cool_temp - deadband

        self._device.set_heat_cool_temp(
            heat_temperature=new_heat_temp,
            cool_temperature=new_cool_temp,
            set_temperature=set_temp,
        )
        self.schedule_update_ha_state()

    @property
    def is_aux_heat(self):
        """Emergency heat state."""
        return "on" if self._device.thermostat.is_emergency_heat_active() else "off"

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self._device.zone_id)},
            "name": self._device.get_name(),
            "model": self._device.thermostat.get_model(),
            "sw_version": self._device.thermostat.get_firmware(),
            "manufacturer": MANUFACTURER,
            "via_device": (DOMAIN, self._device.thermostat.thermostat_id),
        }

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""

        (min_temp, max_temp) = self._device.thermostat.get_setpoint_limits()
        data = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_FAN_MODE: self._device.thermostat.get_fan_mode(),
            ATTR_HVAC_MODE: self.mode,
            ATTR_TARGET_TEMP_HIGH: self._device.get_cooling_setpoint(),
            ATTR_TARGET_TEMP_LOW: self._device.get_heating_setpoint(),
            ATTR_TARGET_TEMP_STEP: 1.0
            if self._device.thermostat.get_unit() == UNIT_FAHRENHEIT
            else 0.5,
            ATTR_MIN_TEMP: min_temp,
            ATTR_MAX_TEMP: max_temp,
            ATTR_FAN_MODES: FAN_MODES,
            ATTR_HVAC_MODES: self.hvac_modes,
            ATTR_PRESET_MODE: self._device.get_preset(),
            ATTR_HOLD_MODES: self._device.get_presets(),
            ATTR_SETPOINT_STATUS: self._device.get_setpoint_status(),
            ATTR_ZONE_STATUS: self._device.get_status(),
            ATTR_THERMOSTAT_ID: self._device.thermostat.thermostat_id,
            ATTR_ZONE_ID: self._device.zone_id,
        }

        if self._device.thermostat.has_emergency_heat():
            data.update(
                {
                    ATTR_AUX_HEAT: "on"
                    if self._device.thermostat.is_emergency_heat_active()
                    else "off"
                }
            )

        if self._device.thermostat.has_relative_humidity():
            data.update(
                {
                    ATTR_HUMIDIFY_SUPPORTED: self._device.thermostat.has_humidify_support(),
                    ATTR_DEHUMIDIFY_SUPPORTED: self._device.thermostat.has_dehumidify_support(),
                    ATTR_CURRENT_HUMIDITY: round(
                        self._device.thermostat.get_relative_humidity() * 100.0, 1
                    ),
                    ATTR_MIN_HUMIDITY: round(
                        self._device.thermostat.get_humidity_setpoint_limits()[0]
                        * 100.0,
                        1,
                    ),
                    ATTR_MAX_HUMIDITY: round(
                        self._device.thermostat.get_humidity_setpoint_limits()[1]
                        * 100.0,
                        1,
                    ),
                }
            )
            if self._device.thermostat.has_dehumidify_support():
                data.update(
                    {
                        ATTR_DEHUMIDIFY_SETPOINT: round(
                            self._device.thermostat.get_dehumidify_setpoint() * 100.0, 1
                        ),
                        ATTR_HUMIDITY: round(
                            self._device.thermostat.get_dehumidify_setpoint() * 100.0, 1
                        ),
                    }
                )
            if self._device.thermostat.has_humidify_support():
                data.update(
                    {
                        ATTR_HUMIDIFY_SETPOINT: round(
                            self._device.thermostat.get_humidify_setpoint() * 100.0, 1
                        )
                    }
                )
        return data

    def set_preset_mode(self, preset_mode: str):
        """Set the preset mode."""
        self._device.set_preset(preset_mode)
        self.schedule_update_ha_state()

    def turn_aux_heat_off(self):
        """Turn. Aux Heat off."""
        self._device.thermostat.set_emergency_heat(False)
        self.schedule_update_ha_state()

    def turn_aux_heat_on(self):
        """Turn. Aux Heat on."""
        self._device.thermostat.set_emergency_heat(True)
        self.schedule_update_ha_state()

    def turn_off(self):
        """Turn. off the zone."""
        self.set_hvac_mode(OPERATION_MODE_OFF)
        self.schedule_update_ha_state()

    def turn_on(self):
        """Turn. on the zone."""
        self.set_hvac_mode(OPERATION_MODE_AUTO)
        self.schedule_update_ha_state()

    def set_swing_mode(self, swing_mode):
        """Unsupported - Swing Mode."""
        raise NotImplementedError("set_swing_mode is not supported by this device")

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the system mode (Auto, Heat_Cool, Cool, Heat, etc)."""

        if hvac_mode == HVAC_MODE_AUTO:
            self._device.call_return_to_schedule()
            self._device.set_mode(mode=OPERATION_MODE_AUTO)
        else:
            if hvac_mode == HVAC_MODE_HEAT_COOL:
                hvac_mode = HVAC_MODE_AUTO
            self._device.call_permanent_hold()

            hvac_mode = hvac_mode.upper()

            if hvac_mode in OPERATION_MODES:

                self._device.set_mode(mode=hvac_mode,)
            else:
                raise KeyError(
                    f"Operation mode {hvac_mode} not in the supported "
                    + f"operations list {str(OPERATION_MODES)}"
                )
        self.schedule_update_ha_state()

    def set_aircleaner_mode(self, aircleaner_mode):
        """Set the aircleaner mode."""
        self._device.thermostat.set_air_cleaner(aircleaner_mode)
        self.schedule_update_ha_state()

    def set_humidify_setpoint(self, humidify_setpoint):
        """Set the humidify setpoint."""
        self._device.thermostat.set_humidify_setpoint(humidify_setpoint / 100.0)
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """Update use the coordinator."""
        return False

    @property
    def available(self):
        """Return true if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self._coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Undo subscription."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)
