import logging
import aiohttp
import asyncio
from datetime import timedelta, datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, API_BASE_URL, SENSOR_MAP

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors from config entry using DataUpdateCoordinator."""
    data = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    api_interval = data.get("API_POLL_INTERVAL", 15)

    coordinator = DeviceCoordinator(
        hass=hass,
        session=session,
        token=data["token"],
        api_poll_interval=api_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    device_id = coordinator.data.get("deviceId", "unknown") if coordinator.data else "unknown"
    entities = []

    # einfache Werte
    for key, (name, unit, icon, force_int) in SENSOR_MAP.items():
        entities.append(DeviceValueSensor(coordinator, key, name, unit, device_id, icon, force_int))

    # converter array
    for i, _ in enumerate(coordinator.data.get("convertersInfo", []) if coordinator.data else [], start=1):
        entities.append(
            DeviceArraySensor(
                coordinator,
                f"Converter {i} Version",
                "convertersInfo",
                i - 1,
                "version",
                device_id,
                icon=None,
            )
        )

    # battery array
    for i, _ in enumerate(coordinator.data.get("batteriesInfo", []) if coordinator.data else [], start=1):
        entities.append(
            DeviceArraySensor(
                coordinator,
                f"Battery {i} Capacity",
                "batteriesInfo",
                i - 1,
                "batteryCapacity",
                device_id,
                unit="Wh",
                icon="mdi:battery",
            )
        )

    async_add_entities(entities, True)


class DeviceCoordinator(DataUpdateCoordinator):
    """Koordiniert periodisches Abrufen der API-Daten (zentrales Polling)."""

    def __init__(self, hass, session, token, api_poll_interval: int):
        self._session = session
        self._token = token

        super().__init__(
            hass,
            _LOGGER,
            name="Maxxisun Device Coordinator",
            update_interval=timedelta(seconds=api_poll_interval),
        )

    async def _async_update_data(self):
        """Ruft periodisch Daten von der REST-API ab."""
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/plain, */*',
            "Authorization": f"Bearer {self._token}",
        }
        url = f"{API_BASE_URL}/api/device/last"

        try:
            async with self._session.get(url, headers=headers) as resp:
                if resp.status not in (200, 202):
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"API request error: {err}") from err


class BaseDeviceSensor(SensorEntity):
    """Basisklasse mit Device-Zuordnung."""

    def __init__(self, coordinator, name, unique_id, device_id, unit=None, icon=None):
        self.coordinator = coordinator
        self._attr_name = name
        self._attr_unique_id = f"{device_id}_{unique_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._device_id = device_id
        self._state = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"{self._device_id}",
            manufacturer="Maxxisun",
            model="Rest API",
        )

    async def async_update(self):
        """Erzwingt manuelles Update (nur bei Serviceaufruf nötig)."""
        await self.coordinator.async_request_refresh()


class DeviceValueSensor(BaseDeviceSensor):
    """Sensor für einfache Werte."""

    def __init__(self, coordinator, key, name, unit, device_id, icon=None, force_int=False):
        super().__init__(coordinator, name, key, device_id, unit, icon)
        self._key = key
        self._force_int = force_int

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None
        value = data.get(self._key)
        if value is not None and self._force_int:
            try:
                value = int(round(float(value)))
            except (ValueError, TypeError):
                value = None
        return value

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        ts = data.get("date")
        if ts:
            return {"last_update": datetime.fromtimestamp(ts / 1000).isoformat()}
        return {}


class DeviceArraySensor(BaseDeviceSensor):
    """Sensor für Werte in Arrays (Converter / Battery)."""

    def __init__(self, coordinator, name, array_key, index, value_key, device_id, unit=None, icon=None):
        super().__init__(coordinator, name, f"{array_key}_{index}_{value_key}", device_id, unit, icon)
        self._array_key = array_key
        self._index = index
        self._value_key = value_key

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None
        array = data.get(self._array_key, [])
        if len(array) > self._index:
            return array[self._index].get(self._value_key)
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        ts = data.get("date")
        if ts:
            return {"last_update": datetime.fromtimestamp(ts / 1000).isoformat()}
        return {}
