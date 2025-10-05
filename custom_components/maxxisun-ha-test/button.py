from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, API_BASE_URL

async def async_setup_entry(hass, entry, async_add_entities):
    auth_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SendDeviceCommandButton(hass, auth_data)], True)

class SendDeviceCommandButton(ButtonEntity):
    """Button zum Senden von Commands mit JWT Token."""

    def __init__(self, hass, auth_data):
        self._attr_name = "Send Device Command"
        self._session = async_get_clientsession(hass)
        self._token = auth_data["token"]

    async def async_press(self):
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {"command": "example"}
        try:
            async with self._session.post(f"{API_BASE_URL}/api/device/command", json=payload, headers=headers) as resp:
                result = await resp.json()
                self.hass.components.persistent_notification.create(
                    f"Command sent successfully: {result}", title="JWT Example"
                )
        except Exception as err:
            self.hass.components.persistent_notification.create(
                f"POST failed: {err}", title="JWT Example"
            )
