import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
from .const import DOMAIN, API_BASE_URL

DATA_SCHEMA = vol.Schema({
    vol.Required("username"): str,
    vol.Required("password"): str,
})

class RestExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            login_url = f"{API_BASE_URL}/api/authentication/log-in"
            try:
                async with session.post(
                    login_url,
                    json={"username": user_input["username"], "password": user_input["password"]}
                ) as resp:
                    if resp.status != 200:
                        return self.async_show_form(
                            step_id="user",
                            data_schema=DATA_SCHEMA,
                            errors={"base": "auth_failed"}
                        )
                    data = await resp.json()
                    token = data.get("token")
                    if not token:
                        return self.async_show_form(
                            step_id="user",
                            data_schema=DATA_SCHEMA,
                            errors={"base": "no_token"}
                        )
            except aiohttp.ClientError:
                return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors={"base": "cannot_connect"})

            return self.async_create_entry(title="REST JWT Example", data={
                "username": user_input["username"],
                "password": user_input["password"],
                "token": token
            })

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
