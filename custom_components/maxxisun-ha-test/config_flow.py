import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
from .const import DOMAIN, API_BASE_URL

DATA_SCHEMA = vol.Schema({
    vol.Required("email"): str,
    vol.Required("ccu"): str,
    vol.Optional("ignore_ssl", default=False): bool,
})

class RestExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            login_url = f"{API_BASE_URL}/api/authentication/log-in"
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'Accept':'application/json, text/plain, */*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Content-Type': 'application/json'}

            # SSL-Kontext abhängig von ignore_ssl
            ssl_context = None
            if user_input.get("ignore_ssl"):
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            try:
                async with session.post(
                    login_url,
                    data='{"email":"' + user_input["email"] + '","ccu":"' + user_input["ccu"] + '"}',
                    headers=headers
                ) as resp:
                    if resp.status != 200 | resp.status != 202:
                        return self.async_show_form(
                            step_id="user",
                            data_schema=DATA_SCHEMA,
                            errors={"base": "auth_failed"}
                        )
                    data = await resp.json()
                    token = data.get("jwt")
                    if not token:
                        return self.async_show_form(
                            step_id="user",
                            data_schema=DATA_SCHEMA,
                            errors={"base": "no_token"}
                        )
            except aiohttp.ClientError:
                return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors={"base": "cannot_connect"})

            return self.async_create_entry(title="REST JWT Maxxisun", data={
                "email": user_input["email"],
                "ccu": user_input["ccu"],
                "token": token,
                "ignore_ssl": user_input.get("ignore_ssl", False)
            })

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
