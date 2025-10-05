from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from datetime import timedelta
import aiohttp
import asyncio
from .const import API_BASE_URL

SCAN_INTERVAL = timedelta(seconds=60)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RestExampleTextSensor(hass)], True)

class RestExampleTextSensor(SensorEntity):
    """Beispiel-Sensor für Textwerte über REST GET."""

    def __init__(self, hass):
        self._attr_name = "REST Example Text"
        self._state = None
        self._session = async_get_clientsession(hass)

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        try:
            async with self._session.get(f"{API_BASE_URL}/todos/1") as resp:
                data = await resp.json()
                self._state = data.get("title")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            self._state = "unavailable"
