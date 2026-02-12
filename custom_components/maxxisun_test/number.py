import logging
from typing import Optional

import aiohttp
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import (
    DeviceInfo,
    EntityCategory,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONTROL_NUMBER_MAP
from .coordinator import APICoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up number entities using the shared APICoordinator."""
    data = hass.data[DOMAIN][entry.entry_id]
    session = async_get_clientsession(hass)
    api_interval = int(data.get("API_POLL_INTERVAL"))

    coordinator: Optional[APICoordinator] = data.get("coordinator")
    if not coordinator:
        coordinator = APICoordinator(
            hass=hass,
            session=session,
            token=data["token"],
            api_poll_interval=api_interval,
        )
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Load config once to initialize values
    try:
        await coordinator.async_config_entry_first_refresh()
        # await coordinator.async_get_config()
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Initial config load failed: %s", err)

    device_id = coordinator.data.get("deviceId", "unknown") if coordinator.data else "unknown"
    entities = []

    for field, (name, unit, icon, is_writable) in CONTROL_NUMBER_MAP.items():
        _LOGGER.debug("Create ControlNumber %s", field)
        entities.append(
            DeviceConfigNumber(
                coordinator,
                name,
                field,
                device_id,
                unit=unit,
                icon=icon,
                read_only=not is_writable,
            )
        )

    async_add_entities(entities, True)


class DeviceConfigNumber(CoordinatorEntity, NumberEntity):
    """Number entity bound to a config field from CONTROL_NUMBER_MAP."""

    def __init__(
        self,
        coordinator: APICoordinator,
        name: str,
        field: str,
        device_id: str,
        unit: Optional[str] = None,
        icon: Optional[str] = None,
        read_only: bool = False,
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self._field = field
        self._device_id = device_id
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{device_id}_test_{field}"
        self._attr_suggested_object_id = f"{device_id}_{field}".lower()
        self._attr_icon = icon or "mdi:numeric"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_unit_of_measurement = unit
        # Reasonable bounds for numeric inputs (0-100 for percentages, 0-1000 for W, etc.)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 1000
        self._attr_native_step = 1
        self._read_only = read_only

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

        value = cfg.get(self._field) if isinstance(cfg, dict) else None
        if value is None:
            return None
        try:
            return int(round(float(value)))
        except (ValueError, TypeError):
            return None

    @property
    def read_only(self) -> bool:
        """Return True if entity is read-only."""
        return self._read_only

    async def async_set_native_value(self, value: float) -> None:
        """Update the config field via API and refresh cached config."""
        if self._read_only:
            _LOGGER.warning("%s is read-only, ignoring set attempt", self._field)
            return
        try:
            await self.coordinator.async_set_config_field(self._field, int(round(value)))
            # # await self.coordinator.async_get_config()  # refresh
            self.async_write_ha_state()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Failed updating %s: %s", self._field, err)
