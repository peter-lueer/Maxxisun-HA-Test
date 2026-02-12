from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, DEFAULT_POLL_INTERVAL


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "email": entry.data.get("email"),
        "ccu": entry.data.get("ccu"),
        "token": entry.data.get("token"),
        "API_POLL_INTERVAL": entry.data.get("API_POLL_INTERVAL", DEFAULT_POLL_INTERVAL),
        "ignoreSSL": entry.data.get("ignoreSSL"),
    }
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number", "select"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "number", "select"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
