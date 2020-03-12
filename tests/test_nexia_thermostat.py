import json
import os
from os.path import dirname
import sys
import unittest

test_dir = dirname(__file__)
sys.path.append(f"{test_dir}/../custom_components")

from nexia.nexia_thermostat import NexiaThermostat


# TODO: breakout code so its easier to test
# - NexiaHome
# - NexiaThermostat
# - NexiaThermostatZone


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(test_dir, "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


class TestNexiaThermostat(unittest.TestCase):
    def test_idle_thermo(self):
        nexia = NexiaThermostat(
            offline_json=json.loads(load_fixture("mobile_houses_123456.json"))
        )

        self.assertEqual(nexia.get_thermostat_model(thermostat_id=2059661), "XL1050")
        self.assertEqual(nexia.get_thermostat_firmware(thermostat_id=2059661), "5.9.1")
        self.assertEqual(
            nexia.get_thermostat_dev_build_number(thermostat_id=2059661), "1581321824"
        )
        self.assertEqual(
            nexia.get_thermostat_device_id(thermostat_id=2059661), "000000"
        )
        self.assertEqual(nexia.get_thermostat_type(thermostat_id=2059661), "XL1050")
        self.assertEqual(
            nexia.get_thermostat_name(thermostat_id=2059661), "Downstairs East Wing"
        )
        self.assertEqual(nexia.get_deadband(thermostat_id=2059661), 3)
        self.assertEqual(nexia.get_setpoint_limits(thermostat_id=2059661), (55, 99))
        self.assertEqual(
            nexia.get_variable_fan_speed_limits(thermostat_id=2059661), (0.35, 1.0)
        )
        self.assertEqual(nexia.get_unit(thermostat_id=2059661), "F")
        self.assertEqual(
            nexia.get_humidity_setpoint_limits(thermostat_id=2059661), (0.35, 0.65)
        )
        self.assertEqual(nexia.get_fan_mode(thermostat_id=2059661), "auto")
        self.assertEqual(nexia.get_outdoor_temperature(thermostat_id=2059661), 88.0)
        self.assertEqual(nexia.get_relative_humidity(thermostat_id=2059661), 0.36)
        self.assertEqual(nexia.get_current_compressor_speed(thermostat_id=2059661), 0.0)
        self.assertEqual(
            nexia.get_requested_compressor_speed(thermostat_id=2059661), 0.0
        )
        self.assertEqual(nexia.get_fan_speed_setpoint(thermostat_id=2059661), 0.35)
        self.assertEqual(nexia.get_dehumidify_setpoint(thermostat_id=2059661), 0.50)
        self.assertEqual(nexia.has_dehumidify_support(thermostat_id=2059661), True)
        self.assertEqual(nexia.has_humidify_support(thermostat_id=2059661), False)
        self.assertEqual(nexia.get_system_status(thermostat_id=2059661), "System Idle")
        self.assertEqual(nexia.get_air_cleaner_mode(thermostat_id=2059661), "auto")

        zone_ids = nexia.get_zone_ids(thermostat_id=2059661)
        self.assertEqual(zone_ids, [83261002, 83261005, 83261008, 83261011])

    def test_active_thermo(self):
        nexia = NexiaThermostat(
            offline_json=json.loads(load_fixture("mobile_houses_123456.json"))
        )

        self.assertEqual(nexia.get_thermostat_model(thermostat_id=2293892), "XL1050")
        self.assertEqual(nexia.get_thermostat_firmware(thermostat_id=2293892), "5.9.1")
        self.assertEqual(
            nexia.get_thermostat_dev_build_number(thermostat_id=2293892), "1581321824"
        )
        self.assertEqual(
            nexia.get_thermostat_device_id(thermostat_id=2293892), "0281B02C"
        )
        self.assertEqual(nexia.get_thermostat_type(thermostat_id=2293892), "XL1050")
        self.assertEqual(
            nexia.get_thermostat_name(thermostat_id=2293892), "Master Suite"
        )
        self.assertEqual(nexia.get_deadband(thermostat_id=2293892), 3)
        self.assertEqual(nexia.get_setpoint_limits(thermostat_id=2293892), (55, 99))
        self.assertEqual(
            nexia.get_variable_fan_speed_limits(thermostat_id=2293892), (0.35, 1.0)
        )
        self.assertEqual(nexia.get_unit(thermostat_id=2293892), "F")
        self.assertEqual(
            nexia.get_humidity_setpoint_limits(thermostat_id=2293892), (0.35, 0.65)
        )
        self.assertEqual(nexia.get_fan_mode(thermostat_id=2293892), "auto")
        self.assertEqual(nexia.get_outdoor_temperature(thermostat_id=2293892), 87.0)
        self.assertEqual(nexia.get_relative_humidity(thermostat_id=2293892), 0.52)
        self.assertEqual(
            nexia.get_current_compressor_speed(thermostat_id=2293892), 0.69
        )
        self.assertEqual(
            nexia.get_requested_compressor_speed(thermostat_id=2293892), 0.69
        )
        self.assertEqual(nexia.get_fan_speed_setpoint(thermostat_id=2293892), 0.35)
        self.assertEqual(nexia.get_dehumidify_setpoint(thermostat_id=2293892), 0.45)
        self.assertEqual(nexia.has_dehumidify_support(thermostat_id=2293892), True)
        self.assertEqual(nexia.has_humidify_support(thermostat_id=2293892), False)
        self.assertEqual(nexia.get_system_status(thermostat_id=2293892), "Cooling")
        self.assertEqual(nexia.get_air_cleaner_mode(thermostat_id=2293892), "auto")

        zone_ids = nexia.get_zone_ids(thermostat_id=2293892)
        self.assertEqual(zone_ids, [83394133, 83394130, 83394136, 83394127, 83394139])


class TestNexiaHome(unittest.TestCase):
    def test_basic_thermo(self):
        nexia = NexiaThermostat(
            offline_json=json.loads(load_fixture("mobile_houses_123456.json"))
        )
        thermostat_ids = nexia.get_thermostat_ids()
        self.assertEqual(thermostat_ids, [2059661, 2059676, 2293892, 2059652])

        last_update = nexia.get_last_update()
        self.assertEqual(last_update, "0001-01-01T00:00:00")


class TestNexiaThermostatZone(unittest.TestCase):
    def test_zone_relieving_air(self):
        nexia = NexiaThermostat(
            offline_json=json.loads(load_fixture("mobile_houses_123456.json"))
        )

        self.assertEqual(
            nexia.get_zone_name(thermostat_id=2293892, zone_id=83394133), "Bath Closet"
        )
        self.assertEqual(
            nexia.get_zone_cooling_setpoint(thermostat_id=2293892, zone_id=83394133), 79
        )
        self.assertEqual(
            nexia.get_zone_heating_setpoint(thermostat_id=2293892, zone_id=83394133), 63
        )
        self.assertEqual(
            nexia.get_zone_current_mode(thermostat_id=2293892, zone_id=83394133), "AUTO"
        )
        self.assertEqual(
            nexia.get_zone_requested_mode(thermostat_id=2293892, zone_id=83394133),
            "AUTO",
        )
        self.assertEqual(
            nexia.get_zone_presets(thermostat_id=2293892, zone_id=83394133),
            ["None", "Home", "Away", "Sleep"],
        )
        self.assertEqual(
            nexia.get_zone_preset(thermostat_id=2293892, zone_id=83394133), "None",
        )
        self.assertEqual(
            nexia.get_zone_status(thermostat_id=2293892, zone_id=83394133),
            "Relieving Air",
        )
        self.assertEqual(
            nexia.get_zone_setpoint_status(thermostat_id=2293892, zone_id=83394133),
            "Permanent Hold",
        )

    def test_zone_cooling_air(self):
        nexia = NexiaThermostat(
            offline_json=json.loads(load_fixture("mobile_houses_123456.json"))
        )

        self.assertEqual(
            nexia.get_zone_name(thermostat_id=2293892, zone_id=83394130), "Master"
        )
        self.assertEqual(
            nexia.get_zone_cooling_setpoint(thermostat_id=2293892, zone_id=83394130), 71
        )
        self.assertEqual(
            nexia.get_zone_heating_setpoint(thermostat_id=2293892, zone_id=83394130), 63
        )
        self.assertEqual(
            nexia.get_zone_current_mode(thermostat_id=2293892, zone_id=83394130), "AUTO"
        )
        self.assertEqual(
            nexia.get_zone_requested_mode(thermostat_id=2293892, zone_id=83394130),
            "AUTO",
        )
        self.assertEqual(
            nexia.get_zone_presets(thermostat_id=2293892, zone_id=83394130),
            ["None", "Home", "Away", "Sleep"],
        )
        self.assertEqual(
            nexia.get_zone_preset(thermostat_id=2293892, zone_id=83394130), "None",
        )
        self.assertEqual(
            nexia.get_zone_status(thermostat_id=2293892, zone_id=83394130),
            "Damper Open",
        )
        self.assertEqual(
            nexia.get_zone_setpoint_status(thermostat_id=2293892, zone_id=83394130),
            "Permanent Hold",
        )
