import logging
from datetime import timedelta, datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import (
    DeviceInfo, 
    EntityCategory
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from .const import CONTROL_DIAGNOSTIC_MAP, DOMAIN, SENSOR_MAP
from .coordinator import APICoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors from config entry using DataUpdateCoordinator."""
    data = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    api_interval = int(data.get("API_POLL_INTERVAL"))

    _LOGGER.info("Coordinator init with Interval %s seconds", api_interval)

    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    if not coordinator:
        coordinator = APICoordinator(
            hass=hass,
            session=session,
            token=data["token"],
            api_poll_interval=api_interval,
            ignoreSSL=data["ignoreSSL"],
        )
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await coordinator.async_config_entry_first_refresh()

    device_id = coordinator.data.get("deviceId", "unknown") if coordinator.data else "unknown"
    entities = []

    # einfache Werte
    for key, (translation_key, unit, icon, force_int, stateClass, deviceClass) in SENSOR_MAP.items():
        _LOGGER.debug("Create ValueSensor %s", key)
        entities.append(DeviceValueSensor(coordinator, key, translation_key, unit, device_id, icon, force_int, stateClass, deviceClass))

    # converter array
    for i, _ in enumerate(coordinator.data.get("convertersInfo", []) if coordinator.data else [], start=1):
        entities.append(
            DeviceArraySensor(
                coordinator,
                "converter_version",
                "convertersInfo",
                i - 1,
                "version",
                device_id,
                icon="mdi:information-outline",
                translation_placeholders={"index": str(i)},
            )
        )

    # battery array
    for i, _ in enumerate(coordinator.data.get("batteriesInfo", []) if coordinator.data else [], start=1):
        entities.append(
            DeviceArraySensor(
                coordinator,
                "battery_capacity",
                "batteriesInfo",
                i - 1,
                "batteryCapacity",
                device_id,
                unit="Wh",
                icon="mdi:battery",
                translation_placeholders={"index": str(i)},
            )
        )

    # calced Sensors
    _LOGGER.debug("Create CalcedValueSensor BatteryCharging")
    entity_BatteryCharging = DeviceCalcedValueSensor(
        coordinator,
        "BatteryCharging",
        "battery_charging",
        None,
        device_id,
        "mdi:battery-outline",
        False,
    )
    entities.append(entity_BatteryCharging)

    _LOGGER.debug("Create CalcedValueSensor PowerBattery")
    entity_PowerBattery = DeviceCalcedValueSensor(
        coordinator,
        "PowerBattery",
        "power_battery",
        "W",
        device_id,
        "mdi:battery-outline",
        True,
        SensorStateClass.MEASUREMENT,
        SensorDeviceClass.POWER
    )
    entities.append(entity_PowerBattery)

    _LOGGER.debug("Create CalcedValueSensor BatteryCapacity")
    entity_BatteryCapacity = DeviceCalcedValueSensor(
        coordinator,
        "BatteryCapacity",
        "battery_capacity_total",
        "Wh",
        device_id,
        "mdi:battery-outline",
        True,
    )
    entities.append(entity_BatteryCapacity)

    # diagnostic config sensors
    for field, (translation_key, unit, icon, _is_writable) in CONTROL_DIAGNOSTIC_MAP.items():
        _LOGGER.debug("Create DiagnosticSensor %s", field)
        entities.append(
            DeviceConfigDiagnosticSensor(
                coordinator,
                translation_key,
                field,
                device_id,
                unit=unit,
                icon=icon,
            )
        )

    async_add_entities(entities, True)

    # Eigenes Intervall erzwingen
    poll_interval = timedelta(seconds=api_interval)

    async def force_refresh(_):
        _LOGGER.debug("Foreced refresh triggered")
        await coordinator.async_request_refresh()

    async_track_time_interval(hass, force_refresh, poll_interval)




class BaseDeviceSensor(SensorEntity):
    """Basisklasse mit Device-Zuordnung."""

    def __init__(
        self,
        coordinator,
        translation_key,
        unique_id,
        device_id,
        unit=None,
        icon=None,
        stateClass=None,
        deviceClass=None,
        name=None,
        translation_placeholders=None,
    ):
        self.coordinator = coordinator
        if name is not None:
            self._attr_name = name
        if translation_key is not None:
            self._attr_translation_key = translation_key
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders
        self._attr_unique_id = f"{device_id}_test_{unique_id}"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{device_id}_{unique_id}".lower()
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._device_id = device_id
        if deviceClass is not None:
            self._attr_device_class = deviceClass
        if stateClass is not None:
            self._attr_state_class = stateClass
        self._state = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"Test_{self._device_id}",
            manufacturer="Maxxisun",
            model=f"{self._device_id}".upper(),
        )

    async def async_update(self):
        """Erzwingt manuelles Update (nur bei Serviceaufruf nötig)."""
        _LOGGER.debug("Update triggered")
        await self.coordinator.async_request_refresh()


class DeviceValueSensor(BaseDeviceSensor):
    """Sensor für einfache Werte."""

    def __init__(
        self,
        coordinator,
        key,
        translation_key,
        unit,
        device_id,
        icon=None,
        force_int=False,
        stateClass=None,
        deviceClass=None,
    ):
        super().__init__(coordinator, translation_key, key, device_id, unit, icon, stateClass, deviceClass)
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
    def icon(self):
        if self._key != "SOC":
            return self._attr_icon
        data = self.coordinator.data or {}
        try:
            soc = float(data.get("SOC", 0) or 0)
        except (ValueError, TypeError):
            soc = 0.0
            return "mdi:battery-remove"
        d = round(soc / 10) * 10
        if d == 0:
            return "mdi:battery-outline"
        elif d == 100:
            return "mdi:battery"
        return "mdi:battery-" + str(d)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        ts = data.get("date")
        if ts:
            return {"last_update": datetime.fromtimestamp(ts / 1000).isoformat()}
        return {}


class DeviceCalcedValueSensor(BaseDeviceSensor):
    """Sensor für einfache Werte."""

    def __init__(
        self,
        coordinator,
        key,
        translation_key,
        unit,
        device_id,
        icon=None,
        force_int=True,
        stateClass=None,
        deviceClass=None
    ):
        super().__init__(coordinator, translation_key, key, device_id, unit, icon, stateClass, deviceClass)
        self._key = key
        self._force_int = force_int

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        if self._key == "BatteryCapacity":
            array = data.get("batteriesInfo", [])
            calcCapacity = 0.0
            try:
                for index in range(len(array)):
                    capacity = float(array[index].get("batteryCapacity", 0) or 0)
                    calcCapacity += capacity
            except (ValueError, TypeError):
                calcCapacity += 0.0
            val = round(calcCapacity)
            return int(val) if self._force_int else val

        try:
            pv = float(data.get("PV_power_total", 0) or 0)
            pccu = float(data.get("Pccu", 0) or 0)
        except (ValueError, TypeError):
            pv, pccu = 0.0, 0.0
        diff = pv - pccu

        if self._key == "BatteryCharging":
            d = round(diff)
            if d == 0:
                return "Idle"
            return "Charging" if d > 0 else "Discharging"

        # Default: PowerBattery -> round to zero decimals
        val = round(diff)
        return int(val) if self._force_int else val

    @property
    def icon(self):
        data = self.coordinator.data or {}
        if self._key == "BatteryCharging" or self._key == "PowerBattery":
            try:
                pv = float(data.get("PV_power_total", 0) or 0)
                pccu = float(data.get("Pccu", 0) or 0)
            except (ValueError, TypeError):
                pv, pccu = 0.0, 0.0
            d = round(pv - pccu)
            if d == 0:
                return "mdi:battery-outline"
            return "mdi:battery-arrow-up-outline" if d > 0 else "mdi:battery-arrow-down-outline"
        elif self._key == "BatteryCapacity":
            try:
                soc = float(data.get("SOC", 0) or 0)
            except (ValueError, TypeError):
                soc = 0.0
                return "mdi:battery-remove"
            d = round(soc / 10) * 10
            if d == 0:
                return "mdi:battery-outline"
            elif d == 100:
                return "mdi:battery"
            return "mdi:battery-" + str(d)
        return self._attr_icon

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        ts = data.get("date")
        if ts:
            return {"last_update": datetime.fromtimestamp(ts / 1000).isoformat()}
        return {}


class DeviceArraySensor(BaseDeviceSensor):
    """Sensor für Werte in Arrays (Converter / Battery)."""

    def __init__(
        self,
        coordinator,
        translation_key,
        array_key,
        index,
        value_key,
        device_id,
        unit=None,
        icon=None,
        translation_placeholders=None,
    ):
        super().__init__(
            coordinator,
            translation_key,
            f"{array_key}_{index}_{value_key}",
            device_id,
            unit,
            icon,
            translation_placeholders=translation_placeholders,
        )
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
    def icon(self):
        if self._value_key != "batteryCapacity":
            return self._attr_icon
        data = self.coordinator.data or {}
        try:
            soc = float(data.get("SOC", 0) or 0)
        except (ValueError, TypeError):
            soc = 0.0
        d = round(soc / 10) * 10
        if d == 0:
            return "mdi:battery-outline"
        elif d == 100:
            return "mdi:battery"
        return "mdi:battery-" + str(d)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        ts = data.get("date")
        if ts:
            return {"last_update": datetime.fromtimestamp(ts / 1000).isoformat()}
        return {}


class DeviceConfigDiagnosticSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor bound to a config field from CONTROL_DIAGNOSTIC_MAP."""

    def __init__(
        self,
        coordinator: APICoordinator,
        translation_key: str,
        field: str,
        device_id: str,
        unit=None,
        icon=None,
    ):
        super().__init__(coordinator)
        self._attr_translation_key = translation_key
        self._field = field
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_test_{field}"
        self._attr_suggested_object_id = f"{device_id}_{field}".lower()
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"Test_{self._device_id}",
            manufacturer="Maxxisun",
            model=f"{self._device_id}".upper(),
        )

    @property
    def native_value(self):
        cfg = self.coordinator.config or {}
        if isinstance(cfg, dict) and "data" in cfg and isinstance(cfg["data"], dict):
            cfg = cfg["data"]

        if not isinstance(cfg, dict):
            return None

        value = cfg.get(self._field)
        # Backward/alternate key naming
        if value is None and self._field == "meterIp":
            value = cfg.get("meterIP")
        return value
