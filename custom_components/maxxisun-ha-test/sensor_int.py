from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from datetime import timedelta
from .const import DOMAIN, API_BASE_URL

SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass, entry, async_add_entities):
    auth_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LastDeviceIntegerSensor(hass, auth_data)], True)

class LastDeviceIntegerSensor(SensorEntity):
    """Integer-Sensor mit JWT Bearer Token."""

    def __init__(self, hass, auth_data):
        self._attr_name = "Device Last Integer"
        self._attr_native_unit_of_measurement = "items"
        self._state = None
        self._session = async_get_clientsession(hass)
        self._token = auth_data["token"]

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        headers = {"Authorization": f"Bearer {self._token}"}
        url = f"{API_BASE_URL}/api/device/last"
        try:
            async with self._session.get(url, headers=headers) as resp:
                data = await resp.json()
                self._state = int(data.get("value", 0))
        except Exception:
            self._state = None
