"""Switch entities for Tasmota IRHVAC selectable features.

The user chooses which features get switch entities via the "Feature Switches"
checklist in the options flow (Behavior step).  One switch entity is created
per checked item, and all switches are grouped under the same HA device as the
climate entity.
"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_TOGGLE_LIST, DATA_KEY, DEFAULT_STATE_MODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Maps every TOGGLE_ALL_LIST key to its switch configuration.
#
# Columns:
#   label         – friendly name shown in HA
#   climate_attr  – attribute on the climate entity that holds current value
#   method_name   – climate method to call (takes kwarg_name + state_mode)
#   kwarg_name    – keyword argument name expected by that method
#   turn_on_val   – value to pass when turning on
#   turn_off_val  – value to pass when turning off
#   on_check_val  – value compared against climate_attr for is_on;
#                   None → is_on when value != turn_off_val  (e.g. Sleep)
#   icon
SWITCH_FEATURE_MAP: dict[str, tuple] = {
    "Turbo":  ("Turbo",   "_turbo",  "async_set_turbo",   "turbo",   "on",   "off", "on",   "mdi:rocket-launch"),
    "Quiet":  ("Quiet",   "_quiet",  "async_set_quiet",   "quiet",   "on",   "off", "on",   "mdi:volume-off"),
    "Econo":  ("Econo",   "_econo",  "async_set_econo",   "econo",   "on",   "off", "on",   "mdi:leaf"),
    "Light":  ("Light",   "_light",  "async_set_light",   "light",   "on",   "off", "on",   "mdi:lightbulb"),
    "Filter": ("Filter",  "_filter", "async_set_filters", "filters", "on",   "off", "on",   "mdi:air-filter"),
    "Clean":  ("Clean",   "_clean",  "async_set_clean",   "clean",   "on",   "off", "on",   "mdi:broom"),
    "Beep":   ("Beep",    "_beep",   "async_set_beep",    "beep",    "on",   "off", "on",   "mdi:volume-high"),
    "SwingV": ("Swing V", "_swingv", "async_set_swingv",  "swingv",  "auto", "off", "auto", "mdi:arrow-up-down"),
    "SwingH": ("Swing H", "_swingh", "async_set_swingh",  "swingh",  "auto", "off", "auto", "mdi:arrow-left-right"),
    "Sleep":  ("Sleep",   "_sleep",  "async_set_sleep",   "sleep",   "0",    "-1",  None,   "mdi:sleep"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one switch per feature the user enabled in the options flow."""
    climate_entity = hass.data.get(DATA_KEY, {}).get(config_entry.entry_id)
    if climate_entity is None:
        _LOGGER.error(
            "Climate entity not found for entry %s — cannot create feature switches.",
            config_entry.entry_id,
        )
        return

    # Merged config (data takes base values, options override them).
    config = {**config_entry.data, **config_entry.options}
    enabled_keys: list[str] = config.get(CONF_TOGGLE_LIST, [])

    switches = []
    for key in enabled_keys:
        feature = SWITCH_FEATURE_MAP.get(key)
        if feature is None:
            _LOGGER.warning("Unknown feature key '%s' in toggle list — skipped.", key)
            continue
        label, climate_attr, method_name, kwarg_name, turn_on_val, turn_off_val, on_check_val, icon = feature
        switches.append(
            TasmotaIrhvacSwitch(
                hass=hass,
                entry_id=config_entry.entry_id,
                feature_key=key,
                label=label,
                climate_attr=climate_attr,
                method_name=method_name,
                kwarg_name=kwarg_name,
                turn_on_val=turn_on_val,
                turn_off_val=turn_off_val,
                on_check_val=on_check_val,
                icon=icon,
            )
        )

    async_add_entities(switches)


class TasmotaIrhvacSwitch(RestoreEntity, SwitchEntity):
    """A switch entity that controls one IRHVAC feature."""

    _attr_should_poll = False
    _attr_has_entity_name = True  # displayed as "{device_name} · {label}"

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        feature_key: str,
        label: str,
        climate_attr: str,
        method_name: str,
        kwarg_name: str,
        turn_on_val: str,
        turn_off_val: str,
        on_check_val: str | None,
        icon: str,
    ) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._climate_attr = climate_attr
        self._method_name = method_name
        self._kwarg_name = kwarg_name
        self._turn_on_val = turn_on_val
        self._turn_off_val = turn_off_val
        self._on_check_val = on_check_val   # None → is_on when != turn_off_val
        self._attr_name = label
        self._attr_icon = icon
        self._attr_unique_id = f"{entry_id}_{feature_key}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _climate(self):
        """Return the linked climate entity, or None if not available yet."""
        return self.hass.data.get(DATA_KEY, {}).get(self._entry_id)

    # ------------------------------------------------------------------
    # HA entity properties
    # ------------------------------------------------------------------

    @property
    def is_on(self) -> bool | None:
        """Return True when the feature is active."""
        climate = self._climate
        if climate is None:
            return None
        val = getattr(climate, self._climate_attr, self._turn_off_val)
        if self._on_check_val is not None:
            return val == self._on_check_val
        # Fallback (e.g. Sleep): on = anything other than the off value
        return val != self._turn_off_val

    @property
    def available(self) -> bool:
        """Mirror the climate entity's availability."""
        climate = self._climate
        return climate.available if climate is not None else False

    @property
    def device_info(self) -> DeviceInfo:
        """Group this switch under the same HA device as the climate entity."""
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Register with the climate entity for MQTT state-push updates."""
        await super().async_added_to_hass()
        climate = self._climate
        if climate is not None:
            climate.register_linked_entity(self)
        else:
            _LOGGER.warning(
                "Switch %s: climate entity not available at add time.",
                self._attr_unique_id,
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs) -> None:
        """Activate the feature."""
        climate = self._climate
        if climate is not None:
            await getattr(climate, self._method_name)(
                **{self._kwarg_name: self._turn_on_val, "state_mode": DEFAULT_STATE_MODE}
            )
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Deactivate the feature."""
        climate = self._climate
        if climate is not None:
            await getattr(climate, self._method_name)(
                **{self._kwarg_name: self._turn_off_val, "state_mode": DEFAULT_STATE_MODE}
            )
            self.async_write_ha_state()
