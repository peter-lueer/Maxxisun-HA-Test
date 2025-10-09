DOMAIN = "Maxxisun_Test"
API_BASE_URL = "https://maxxisun.app:3000"
DEFAULT_POLL_INTERVAL: int = 30
SENSOR_MAP = {
    "SOC": ("State of Charge", "%", "mdi:battery", False),
    "wifiStrength": ("WiFi Signal", "dBm", "mdi:wifi", False),
    "Pccu": ("Power Out", "W", "mdi:power-plug-battery-outline", True),
    "Pr": ("Power from Grid", "W", "mdi:transmission-tower-export", True),
    "PV_power_total": ("PV Power Total", "W", "mdi:solar-power-variant", False),
    "firmwareVersion": ("Firmware Version", None, "mdi:information-outline", False),
}
