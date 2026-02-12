import logging
from datetime import timedelta

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, CONTROL_NUMBER_MAP, CONTROL_SELECT_MAP, CONTROL_DIAGNOSTIC_MAP

_LOGGER = logging.getLogger(__name__)


class APICoordinator(DataUpdateCoordinator):
    """Koordiniert API-Zugriffe: Device-Daten und Config-GET/PUT."""

    def __init__(self, hass, session, token, api_poll_interval: int, ignore_ssl: bool = False):
        self._session = session
        self._token = token
        self.config = None
        self._device_id = None
        # When ignore_ssl=True, disable certificate verification for aiohttp requests
        # by passing ssl=False to calls. Otherwise, leave default verification behavior.
        self._ssl = False if ignore_ssl else None

        _LOGGER.debug("API Coordinator initialized: api_poll_interval=%s", api_poll_interval)

        super().__init__(
            hass,
            _LOGGER,
            name="Maxxisun API Coordinator",
            update_interval=timedelta(seconds=api_poll_interval),
        )

    async def _async_update_data(self):
        """Ruft periodisch Device-Daten und Config von der REST-API ab."""
        _LOGGER.debug("Requesting data from Maxxisun API")
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self._token}",
        }
        
        try:
            # Fetch device telemetry
            url_device = f"{API_BASE_URL}/api/device/last"
            async with self._session.get(url_device, headers=headers, ssl=self._ssl) as resp:
                if resp.status not in (200, 202):
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
                self._device_id = data.get("deviceId", self._device_id)
            
            # Fetch device config (for number entities)
            url_config = f"{API_BASE_URL}/api/device/config"
            async with self._session.get(url_config, headers=headers, ssl=self._ssl) as resp:
                if resp.status not in (200, 202):
                    _LOGGER.warning("Config fetch failed with status %s", resp.status)
                else:
                    self.config = await self._normalize_config_response(resp)
            
            return data
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"API request error: {err}") from err

    async def async_set_config_field(self, field: str, value):
        """Aktualisiert einzelnes Config-Feld via PUT."""
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        url = f"{API_BASE_URL}/api/device/config"
        # Ensure we have the latest config
        await self._ensure_config(headers)

        # Build payload with all known control fields and the updated value
        control_keys = set(CONTROL_NUMBER_MAP.keys()) | set(CONTROL_SELECT_MAP.keys()) | set(CONTROL_DIAGNOSTIC_MAP.keys())
        current = self.config or {}
        if isinstance(current, dict) and "data" in current and isinstance(current.get("data"), dict):
            current = current["data"]

        merged = {k: v for k, v in current.items() if k in control_keys}
        # merged["meterIp"] = current["meterIp"]
        merged[field] = value

        device_id = current.get("deviceId") if isinstance(current, dict) else None
        if not device_id:
            device_id = self._device_id
        if device_id:
            merged["deviceId"] = device_id

        _LOGGER.debug("Updating device config field %s=%s with merged payload", field, value)
        try:
            _LOGGER.warning("Logoutput Put-Config: %s",merged)
            return merged
            # async with self._session.put(url, headers=headers, json=merged, ssl=self._ssl) as resp:
            #     if resp.status not in (200, 202):
            #         raise UpdateFailed(f"HTTP {resp.status}")
            #     self.config = await self._normalize_config_response(resp, fallback_device_id=device_id)
            #     return self.config
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Config update error: {err}") from err

    async def _ensure_config(self, headers: dict):
        """Fetch config if not yet loaded."""
        if self.config is not None:
            return
        url_config = f"{API_BASE_URL}/api/device/config"
        async with self._session.get(url_config, headers=headers, ssl=self._ssl) as resp:
            if resp.status not in (200, 202):
                raise UpdateFailed(f"HTTP {resp.status}")
            self.config = await self._normalize_config_response(resp)

    async def _normalize_config_response(self, resp, fallback_device_id=None):
        """Normalize config response into a flat dict with deviceId if available."""
        raw = await resp.json()
        cfg = raw.get("data") if isinstance(raw, dict) and "data" in raw else raw
        if isinstance(cfg, dict):
            if self._device_id and not cfg.get("deviceId"):
                cfg["deviceId"] = self._device_id
            if fallback_device_id and not cfg.get("deviceId"):
                cfg["deviceId"] = fallback_device_id
            return cfg
        return None
