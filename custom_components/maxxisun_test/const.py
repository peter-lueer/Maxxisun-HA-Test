from typing import Final
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)

DOMAIN = "maxxisun_test"
API_BASE_URL = "https://maxxisun.app:3000"
DEFAULT_POLL_INTERVAL: int = 30

# region Conf
LANG_DE: Final = "de"


SENSOR_MAP = {
    "SOC": ("state_of_charge", "%", "mdi:battery", False, None, None),
    "wifiStrength": ("wifi_strength", "dBm", "mdi:wifi", False, None, None),
    "Pccu": ("power_out", "W", "mdi:power-plug-battery-outline", True, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "Pr": ("power_from_grid", "W", "mdi:transmission-tower-export", True, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "PV_power_total": ("pv_power_total", "W", "mdi:solar-power-variant", False, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "firmwareVersion": ("firmware_version", None, "mdi:information-outline", False, None, None),
}
CONTROL_NUMBER_MAP = {
    "numberOfBatteries": ("number_of_batteries", None, "mdi:battery-plus-outline", True),
    "minSOC": ("min_soc", "%", "mdi:percent", True),
    "maxSOC": ("max_soc", "%", "mdi:percent", True),
    "maxOutputPower": ("max_output_power", "W", "mdi:power-plug-outline", True),
    "baseLoad": ("base_load", "W", None, True),
    "threshold": ("threshold", "W", None, True),
    "offlineOutput": ("offline_output", "W", "mdi:power-plug-outline", True),
}
CONTROL_SELECT_MAP = {
    "powerMeter": (
        "power_meter",
        None,
        "mdi:gauge",
        True,
        [
            {"Key": "none", "Value": 99},
            {"Key": "poweropti", "Value": 1},
            {"Key": "ecotracker", "Value": 4},
            {"Key": "shelly_3em", "Value": 9},
            {"Key": "shelly_3em_pro", "Value": 9},
        ],
    ),
    "ccuSpeed": (
        "ccu_speed",
        None,
        "mdi:speedometer",
        True,
        [
            {"Key": "slow", "Value": 1},
            {"Key": "normal", "Value": 2},
            {"Key": "fast", "Value": 3},
        ],
    ),
    "dcAlgorithm": (
        "dc_algorithm",
        None,
        "mdi:chip",
        True,
        [
            {"Key": "basic", "Value": 1},
            {"Key": "forced", "Value": 2},
        ],
    ),
}
CONTROL_DIAGNOSTIC_MAP = {
    "meterIp": ("meter_ip", None, "mdi:ip-network-outline", False),
}
