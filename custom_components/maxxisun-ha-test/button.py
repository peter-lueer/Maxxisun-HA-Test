from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import API_BASE_URL
import aiohttp

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RestExamplePostButton(hass)], True)

class RestExamplePostButton(ButtonEntity):
    """Button zum Senden von Testdaten via REST POST."""

    def __init__(self, hass):
        self._attr_name = "REST Example POST Button"
        self._session = async_get_clientsession(hass)

    async def async_press(self):
        payload = {"title": "foo", "body": "bar", "userId": 1}
        try:
            async with self._session.post(f"{API_BASE_URL}/posts", json=payload) as resp:
                result = await resp.json()
                self.hass.components.persistent_notification.create(
                    f"POST successful: {result}", title="REST Example"
                )
        except aiohttp.ClientError as err:
            self.hass.components.persistent_notification.create(
                f"POST failed: {err}", title="REST Example"
            )
