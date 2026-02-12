import logging
from typing import Optional

import aiohttp
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONTROL_SELECT_MAP, DOMAIN
from .coordinator import APICoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up select entities using the shared APICoordinator."""
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

    # Ensure we have initial data/config to populate current_option
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Initial load failed: %s", err)

    device_id = coordinator.data.get("deviceId", "unknown") if coordinator.data else "unknown"

    entities: list[SelectEntity] = []
    for field, (name, _unit, icon, is_writable, options) in CONTROL_SELECT_MAP.items():
        entities.append(
            DeviceConfigSelect(
                coordinator=coordinator,
                name=name,
                field=field,
                device_id=device_id,
                icon=icon,
                read_only=not bool(is_writable),
                options=options,
            )
        )

    async_add_entities(entities, True)


class DeviceConfigSelect(CoordinatorEntity, SelectEntity):
    """Select entity bound to a config field from CONTROL_SELECT_MAP."""

    def __init__(
        self,
        coordinator: APICoordinator,
        name: str,
        field: str,
        device_id: str,
        icon: Optional[str],
        read_only: bool,
        options: list[dict],
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{device_id}_test_{field}"
        self._attr_suggested_object_id = f"{device_id}_{field}".lower()
        self._attr_has_entity_name = True
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG

        self._field = field
        self._device_id = device_id
        self._read_only = read_only

        # Map display label <-> stored value
        self._value_by_label: dict[str, int] = {}
        self._label_by_value: dict[int, str] = {}
        for item in options or []:
            label = str(item.get("Key"))
            value = item.get("Value")
            try:
                value_int = int(value)
            except (TypeError, ValueError):
                continue
            self._value_by_label[label] = value_int
            self._label_by_value[value_int] = label

        self._attr_options = list(self._value_by_label.keys())

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"Test_{self._device_id}",
            manufacturer="Maxxisun",
            model=f"{self._device_id}".upper(),
        )

    @property
    def current_option(self) -> Optional[str]:
        cfg = self.coordinator.config or {}
        if isinstance(cfg, dict) and "data" in cfg and isinstance(cfg["data"], dict):
            cfg = cfg["data"]

        raw_value = cfg.get(self._field) if isinstance(cfg, dict) else None
        if raw_value is None:
            return None
        try:
            value_int = int(raw_value)
        except (TypeError, ValueError):
            return None
        return self._label_by_value.get(value_int)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        if self._read_only:
            _LOGGER.warning("%s is read-only, ignoring select", self._field)
            return

        if option not in self._value_by_label:
            _LOGGER.warning("Unknown option '%s' for %s", option, self._field)
            return

        value = self._value_by_label[option]
        try:
            await self.coordinator.async_set_config_field(self._field, value)
            self.async_write_ha_state()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Failed updating %s: %s", self._field, err)
