from typing import Final
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)

DOMAIN = "maxxisun"
API_BASE_URL = "https://maxxisun.app:3000"
DEFAULT_POLL_INTERVAL: int = 30

# region Conf
LANG_DE: Final = "de"


SENSOR_MAP = {
    "SOC": ("State of Charge", "%", "mdi:battery", False, None, None),
    "wifiStrength": ("WiFi Signal", "dBm", "mdi:wifi", False, None, None),
    "Pccu": ("Power Out", "W", "mdi:power-plug-battery-outline", True, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "Pr": ("Power from Grid", "W", "mdi:transmission-tower-export", True, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "PV_power_total": ("PV Power Total", "W", "mdi:solar-power-variant", False, SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER),
    "firmwareVersion": ("Firmware Version", None, "mdi:information-outline", False, None, None),
}
CONTROL_NUMBER_MAP = {
    "numberOfBatteries": ("Batterien im System (Anzahl)", None, "mdi:battery-plus-outline", True),
    "minSOC": ("Minimale Entladung der Batterie", "%", "mdi:percent", True),
    "maxSOC": ("Maximale Batterieladung", "%", "mdi:percent", True),
    "maxOutputPower": ("Mikro-Wechselrichter maximale Leistung", "W", "mdi:power-plug-outline", True),
    "baseLoad": ("Ausgabe korrigieren", "W", None, True),
    "threshold": ("Reaktionstoleranz", "W", None, True),
    "offlineOutput": ("Offline-Ausgangsleistung", "W", "mdi:power-plug-outline", True),
}
CONTROL_SELECT_MAP = {
    "powerMeter": ("Messgerät Typ", None, "mdi:gauge", True, [{"Key": "None", "Value": 99},{"Key": "PowerOpti", "Value": 1},{"Key": "EcoTracker", "Value": 4},{"Key": "Shelly 3EM", "Value": 9},{"Key": "Shelly 3EM Pro", "Value": 9}]),
    "ccuSpeed": ("CCU-Geschwindigkeit", None, "mdi:speedometer", True, [{"Key": "Langsam", "Value": 1},{"Key": "Normal", "Value": 2},{"Key": "Schnell", "Value": 3}]),
    "dcAlgorithm": ("DC/DC Algorithmus", None, "mdi:chip", True, [{"Key": "Basic", "Value": 1},{"Key": "Forced", "Value": 2}]),
}
CONTROL_DIAGNOSTIC_MAP = {
    "meterIp": ("Messgerät ip", None, "mdi:ip-network-outline", False ),
}
