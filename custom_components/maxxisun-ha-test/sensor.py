from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from datetime import timedelta
from datetime import datetime
from .const import DOMAIN, API_BASE_URL, SENSOR_MAP

SCAN_INTERVAL = timedelta(seconds=15)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from config entry."""
    auth_data = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)

    coordinator = DeviceCoordinator(hass, session, auth_data)
    await coordinator.async_refresh()  # ersten Abruf machen

    device_id = coordinator.data.get("deviceId", "unknown")

    entities = []

    # einfache Werte
    for key, (name, unit, icon, forceInt) in SENSOR_MAP.items():
        entities.append(DeviceValueSensor(coordinator, key, name, unit, device_id, icon, forceInt))

    # converter array
    for i, _ in enumerate(coordinator.data.get("convertersInfo", []), start=1):
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
    for i, _ in enumerate(coordinator.data.get("batteriesInfo", []), start=1):
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


class DeviceCoordinator:
    """Kümmert sich um API-Aufrufe und cached die Daten."""

    def __init__(self, hass, session, auth_data):
        self.hass = hass
        self._session = session
        self._token = auth_data["token"]
        self.data = None

    async def async_refresh(self):
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'Accept':'application/json, text/plain, */*',"Authorization": f"Bearer {self._token}"}
        url = f"{API_BASE_URL}/api/device/last"


        async with self._session.get(url, headers=headers) as resp:
            self.data = await resp.json()
            return self.data


class BaseDeviceSensor(SensorEntity):
    """Basisklasse mit Device-Zuordnung."""

    def __init__(self, coordinator, name, unique_id, device_id, unit=None, icon=None):
        self.coordinator = coordinator
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{device_id}_{unique_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._device_id = device_id
        
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"{self._device_id}",
            manufacturer="Maxxisun",
            model="Custom Device",
        )


class DeviceValueSensor(BaseDeviceSensor):
    """Sensor für einfache Werte."""

    def __init__(self, coordinator, key, name, unit, device_id, icon=None, force_int=False):
        super().__init__(coordinator, name, f"{key}", device_id, unit, icon)
        self._key = key
        self._force_int = force_int
        self._last_update = None

    @property
    def extra_state_attributes(self):
        if self._last_update:
            return {"last_update": self._last_update.isoformat()}
        return {}

    async def async_update(self):
        data = await self.coordinator.async_refresh()
        if data:
            value = data.get(self._key)
            if value is not None and self._force_int:
                try:
                    value = int(round(float(value)))
                except (ValueError, TypeError):
                    value = None
            self._state = value
            ts = data.get("date")
            if ts:
                self._last_update = datetime.fromtimestamp(ts / 1000)


class DeviceArraySensor(BaseDeviceSensor):
    """Sensor für Werte in Arrays (Converter / Battery)."""

    def __init__(self, coordinator, name, array_key, index, value_key, device_id, unit=None, icon=None):
        super().__init__(coordinator, name, f"{array_key}_{index}_{value_key}", device_id, unit, icon)
        self._array_key = array_key
        self._index = index
        self._value_key = value_key
        self._attr_icon = icon
        self._last_update = None

    @property
    def extra_state_attributes(self):
        if self._last_update:
            return {"last_update": self._last_update.isoformat()}
        return {}

    async def async_update(self):
        data = await self.coordinator.async_refresh()
        if data:
            array = data.get(self._array_key, [])
            if len(array) > self._index:
                self._state = array[self._index].get(self._value_key)
            ts = data.get("date")
            if ts:
                self._last_update = datetime.fromtimestamp(ts / 1000)
