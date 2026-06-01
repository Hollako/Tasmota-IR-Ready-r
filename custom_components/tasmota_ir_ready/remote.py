"""Remote entities for Tasmota IRSend devices."""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_AVAILABILITY_TOPIC,
    CONF_COMMAND_TOPIC,
    CONF_POWER_SENSOR,
    CONF_MEDIA_BITS,
    CONF_MEDIA_MUTE_DATA,
    CONF_MEDIA_POWER_DATA,
    CONF_MEDIA_POWER_OFF_DATA,
    CONF_MEDIA_POWER_ON_DATA,
    CONF_MEDIA_PROTOCOL,
    CONF_MEDIA_SOURCE_1_DATA,
    CONF_MEDIA_SOURCE_1_NAME,
    CONF_MEDIA_SOURCE_2_DATA,
    CONF_MEDIA_SOURCE_2_NAME,
    CONF_MEDIA_SOURCE_3_DATA,
    CONF_MEDIA_SOURCE_3_NAME,
    CONF_MEDIA_SOURCE_4_DATA,
    CONF_MEDIA_SOURCE_4_NAME,
    CONF_MEDIA_SOURCE_5_DATA,
    CONF_MEDIA_SOURCE_5_NAME,
    CONF_MEDIA_SOURCE_6_DATA,
    CONF_MEDIA_SOURCE_6_NAME,
    CONF_MEDIA_SOURCE_CYCLE_DATA,
    CONF_MEDIA_SOURCE_CYCLE_DELAY,
    CONF_MEDIA_SOURCE_MODE,
    CONF_MEDIA_VOLUME_DOWN_DATA,
    CONF_MEDIA_VOLUME_UP_DATA,
    CONF_REMOTE_BACK_DATA,
    CONF_REMOTE_BLUE_DATA,
    CONF_REMOTE_CHANNEL_DOWN_DATA,
    CONF_REMOTE_CHANNEL_UP_DATA,
    CONF_REMOTE_DIGIT_0_DATA,
    CONF_REMOTE_DIGIT_1_DATA,
    CONF_REMOTE_DIGIT_2_DATA,
    CONF_REMOTE_DIGIT_3_DATA,
    CONF_REMOTE_DIGIT_4_DATA,
    CONF_REMOTE_DIGIT_5_DATA,
    CONF_REMOTE_DIGIT_6_DATA,
    CONF_REMOTE_DIGIT_7_DATA,
    CONF_REMOTE_DIGIT_8_DATA,
    CONF_REMOTE_DIGIT_9_DATA,
    CONF_REMOTE_DOWN_DATA,
    CONF_REMOTE_EXIT_DATA,
    CONF_REMOTE_GREEN_DATA,
    CONF_REMOTE_HOME_DATA,
    CONF_REMOTE_INFO_DATA,
    CONF_REMOTE_LEFT_DATA,
    CONF_REMOTE_MENU_DATA,
    CONF_REMOTE_OK_DATA,
    CONF_REMOTE_RED_DATA,
    CONF_REMOTE_RIGHT_DATA,
    CONF_REMOTE_SETTINGS_DATA,
    CONF_REMOTE_UP_DATA,
    CONF_REMOTE_YELLOW_DATA,
    DATA_REMOTE_KEY,
    DEFAULT_IRSEND_COMMAND_TOPIC,
    DEFAULT_MEDIA_BITS,
    DEFAULT_MEDIA_PROTOCOL,
    DEFAULT_MEDIA_SOURCE_CYCLE_DELAY,
    DEFAULT_MEDIA_SOURCE_MODE,
    DEFAULT_REMOTE_NAME,
    DOMAIN,
    SOURCE_MODE_CYCLE,
    SOURCE_MODE_DIRECT,
)

_LOGGER = logging.getLogger(__name__)

COMMAND_FIELDS = {
    "power": CONF_MEDIA_POWER_DATA,
    "power_on": CONF_MEDIA_POWER_ON_DATA,
    "power_off": CONF_MEDIA_POWER_OFF_DATA,
    "volume_up": CONF_MEDIA_VOLUME_UP_DATA,
    "volume_down": CONF_MEDIA_VOLUME_DOWN_DATA,
    "mute": CONF_MEDIA_MUTE_DATA,
    "digit_0": CONF_REMOTE_DIGIT_0_DATA,
    "digit_1": CONF_REMOTE_DIGIT_1_DATA,
    "digit_2": CONF_REMOTE_DIGIT_2_DATA,
    "digit_3": CONF_REMOTE_DIGIT_3_DATA,
    "digit_4": CONF_REMOTE_DIGIT_4_DATA,
    "digit_5": CONF_REMOTE_DIGIT_5_DATA,
    "digit_6": CONF_REMOTE_DIGIT_6_DATA,
    "digit_7": CONF_REMOTE_DIGIT_7_DATA,
    "digit_8": CONF_REMOTE_DIGIT_8_DATA,
    "digit_9": CONF_REMOTE_DIGIT_9_DATA,
    "up": CONF_REMOTE_UP_DATA,
    "down": CONF_REMOTE_DOWN_DATA,
    "left": CONF_REMOTE_LEFT_DATA,
    "right": CONF_REMOTE_RIGHT_DATA,
    "ok": CONF_REMOTE_OK_DATA,
    "back": CONF_REMOTE_BACK_DATA,
    "home": CONF_REMOTE_HOME_DATA,
    "menu": CONF_REMOTE_MENU_DATA,
    "settings": CONF_REMOTE_SETTINGS_DATA,
    "info": CONF_REMOTE_INFO_DATA,
    "exit": CONF_REMOTE_EXIT_DATA,
    "channel_up": CONF_REMOTE_CHANNEL_UP_DATA,
    "channel_down": CONF_REMOTE_CHANNEL_DOWN_DATA,
    "red": CONF_REMOTE_RED_DATA,
    "green": CONF_REMOTE_GREEN_DATA,
    "yellow": CONF_REMOTE_YELLOW_DATA,
    "blue": CONF_REMOTE_BLUE_DATA,
}

COMMAND_ALIASES = {
    "0": "digit_0",
    "1": "digit_1",
    "2": "digit_2",
    "3": "digit_3",
    "4": "digit_4",
    "5": "digit_5",
    "6": "digit_6",
    "7": "digit_7",
    "8": "digit_8",
    "9": "digit_9",
    "center": "ok",       # Universal Remote Card D-pad center button
    "enter": "ok",
    "select": "ok",
    "dpad_center": "ok",  # Android TV / generic remote variant
    "return": "back",
    "setup": "settings",
    "options": "settings",
    "ch_up": "channel_up",
    "ch_down": "channel_down",
    "vol_up": "volume_up",
    "vol_down": "volume_down",
}

_SOURCE_PAIRS = (
    (CONF_MEDIA_SOURCE_1_NAME, CONF_MEDIA_SOURCE_1_DATA),
    (CONF_MEDIA_SOURCE_2_NAME, CONF_MEDIA_SOURCE_2_DATA),
    (CONF_MEDIA_SOURCE_3_NAME, CONF_MEDIA_SOURCE_3_DATA),
    (CONF_MEDIA_SOURCE_4_NAME, CONF_MEDIA_SOURCE_4_DATA),
    (CONF_MEDIA_SOURCE_5_NAME, CONF_MEDIA_SOURCE_5_DATA),
    (CONF_MEDIA_SOURCE_6_NAME, CONF_MEDIA_SOURCE_6_DATA),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Tasmota IR remote from a config entry."""
    config = {
        CONF_COMMAND_TOPIC: DEFAULT_IRSEND_COMMAND_TOPIC,
        CONF_NAME: DEFAULT_REMOTE_NAME,
        **config_entry.data,
        **config_entry.options,
        CONF_UNIQUE_ID: config_entry.entry_id,
    }

    if DATA_REMOTE_KEY not in hass.data:
        hass.data[DATA_REMOTE_KEY] = {}

    entity = TasmotaIrRemote(hass, config)
    hass.data[DATA_REMOTE_KEY][config_entry.entry_id] = entity
    async_add_entities([entity])


class TasmotaIrRemote(RestoreEntity, RemoteEntity):
    """A stateless remote backed by Tasmota IRSend commands."""

    _attr_should_poll = False
    _attr_is_on = True
    _attr_assumed_state = True

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the remote."""
        self.hass = hass
        self._attr_unique_id = config[CONF_UNIQUE_ID]
        self._device_id = config[CONF_UNIQUE_ID]
        self._attr_name = config[CONF_NAME]
        self._command_topic = config[CONF_COMMAND_TOPIC]
        self._protocol = str(
            config.get(CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL)
        ).upper()
        self._bits = int(config.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS))

        # Base named commands
        self._commands: dict[str, str] = {
            command: (config.get(field) or "").strip()
            for command, field in COMMAND_FIELDS.items()
            if (config.get(field) or "").strip()
        }

        # Custom commands added via the panel (list of {name, data} dicts)
        extra_cmds = config.get("remote_extra_commands") or []
        if isinstance(extra_cmds, str):
            try:
                extra_cmds = json.loads(extra_cmds)
            except Exception:
                extra_cmds = []
        for item in (extra_cmds if isinstance(extra_cmds, list) else []):
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                data = str(item.get("data") or "").strip()
                if name and data:
                    self._commands[name] = data

        # Source mode setup
        self._source_mode: str = config.get(CONF_MEDIA_SOURCE_MODE, DEFAULT_MEDIA_SOURCE_MODE)
        self._cycle_data: str = (config.get(CONF_MEDIA_SOURCE_CYCLE_DATA) or "").strip()
        self._cycle_delay: float = float(
            config.get(CONF_MEDIA_SOURCE_CYCLE_DELAY, DEFAULT_MEDIA_SOURCE_CYCLE_DELAY)
        )
        self._source_index: int | None = None
        self._availability_topic: str | None = config.get(CONF_AVAILABILITY_TOPIC) or None
        self._power_sensor: str | None = (config.get(CONF_POWER_SENSOR) or "").strip() or None
        self._available: bool = True
        self._unsubscribes: list = []

        # Always load per-source IR codes so direct jumps work in both modes.
        source_cmds = self._build_direct_source_commands(config)
        self._commands.update(source_cmds)

        if self._source_mode == SOURCE_MODE_CYCLE:
            self._source_names: list[str] = self._build_cycle_source_list(config)
            # Register cycle button as a plain named command so the card can
            # call remote.send_command("source_cycle") to send one press.
            if self._cycle_data:
                self._commands["source_cycle"] = self._cycle_data
        else:
            self._source_names = list(source_cmds)

    # ------------------------------------------------------------------
    # Source list builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_direct_source_commands(config: dict) -> dict[str, str]:
        """Map source name → IR data for direct mode (both name and data required)."""
        sources = {}
        for name_key, data_key in _SOURCE_PAIRS:
            name = (config.get(name_key) or "").strip()
            data = (config.get(data_key) or "").strip()
            if name and data:
                sources[name] = data
        return sources

    @staticmethod
    def _build_cycle_source_list(config: dict) -> list[str]:
        """Return ordered source names for cycle mode (name alone is sufficient)."""
        return [
            (config.get(name_key) or "").strip()
            for name_key, _ in _SOURCE_PAIRS
            if (config.get(name_key) or "").strip()
        ]

    # ------------------------------------------------------------------

    @property
    def device_info(self) -> DeviceInfo:
        """Group this remote under the media player device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._attr_name,
            manufacturer="Tasmota",
            model="IR remote",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return configured command names and source info for diagnostics."""
        attrs: dict[str, Any] = {"configured_commands": list(self._commands)}
        if self._power_sensor:
            attrs["power_sensor"] = self._power_sensor
        if self._source_names:
            attrs["source_mode"] = self._source_mode
            attrs["source_list"] = self._source_names
        if self._source_mode == SOURCE_MODE_CYCLE and self._source_index is not None:
            attrs["source_index"] = self._source_index
            attrs["current_source"] = self._source_names[self._source_index]
        return attrs

    # ------------------------------------------------------------------
    # HA lifecycle
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Return True when the Tasmota device is online."""
        return self._available

    async def async_added_to_hass(self) -> None:
        """Restore state and subscribe to Tasmota availability."""
        await super().async_added_to_hass()

        # Restore cycle source position
        if self._source_mode == SOURCE_MODE_CYCLE and self._source_names:
            last_state = await self.async_get_last_state()
            if last_state is not None:
                last_source = last_state.attributes.get("current_source")
                if last_source and last_source in self._source_names:
                    self._source_index = self._source_names.index(last_source)

        # Subscribe to availability topic if configured
        if self._availability_topic:
            from homeassistant.core import callback as ha_callback

            @ha_callback
            def _availability_received(message) -> None:
                self._available = message.payload.strip().lower() == "online"
                self.async_write_ha_state()

            self._unsubscribes.append(
                await mqtt.async_subscribe(
                    self.hass,
                    self._availability_topic,
                    _availability_received,
                )
            )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed."""
        for unsub in self._unsubscribes:
            unsub()

    # ------------------------------------------------------------------
    # Remote commands
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the remote entity."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Keep the remote available even if HA calls turn_off."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs: Any) -> None:
        """Keep the remote available when toggled."""
        self._attr_is_on = True
        self.async_write_ha_state()

    def _build_irsend_payload(self, data: str) -> str:
        """Build the JSON payload expected by Tasmota IRSend."""
        data = data.strip()
        if data and not data.lower().startswith("0x"):
            data = f"0x{data}"
        return json.dumps(
            {
                "Protocol": self._protocol,
                "Bits": self._bits,
                "Data": data,
            }
        )

    async def _async_publish_command(self, command: str) -> None:
        """Publish one configured remote command."""
        normalized = COMMAND_ALIASES.get(command.lower(), command.lower())
        # Try normalized (lowercase), then original casing, then case-insensitive scan
        # so commands stored with original casing are found regardless of how they are called.
        data = (
            self._commands.get(normalized)
            or self._commands.get(command)
            or next(
                (v for k, v in self._commands.items() if k.lower() == command.lower()),
                None,
            )
        )
        if not data:
            _LOGGER.warning("Unknown or unconfigured remote command '%s'.", command)
            return
        await mqtt.async_publish(
            self.hass,
            self._command_topic,
            self._build_irsend_payload(data),
        )

    async def _async_cycle_to_source(self, source: str) -> None:
        """Cycle to the requested source by pressing the cycle button N times."""
        if not self._cycle_data:
            _LOGGER.warning(
                "Source mode is 'cycle' but no cycle IR code configured. "
                "Set 'Source Cycle Hex Data' in Configure."
            )
            return
        target_idx = self._source_names.index(source)
        n = len(self._source_names)
        presses = (
            target_idx
            if self._source_index is None
            else (target_idx - self._source_index) % n
        )
        for i in range(presses):
            await mqtt.async_publish(
                self.hass,
                self._command_topic,
                self._build_irsend_payload(self._cycle_data),
            )
            if i < presses - 1:
                await asyncio.sleep(self._cycle_delay)
        self._source_index = target_idx
        self.async_write_ha_state()

    async def async_send_command(
        self,
        command: Iterable[str],
        **kwargs: Any,
    ) -> None:
        """Send one or more IR remote commands."""
        repeats = int(kwargs.get("num_repeats", 1))
        delay = float(kwargs.get("delay_secs", 0.4))
        commands = [command] if isinstance(command, str) else list(command)

        for repeat in range(repeats):
            for index, item in enumerate(commands):
                # Cycle mode: route to cycle logic only when no direct IR code
                # exists for this source (per-source direct codes take priority).
                cycle_target: str | None = None
                if self._source_mode == SOURCE_MODE_CYCLE:
                    norm = COMMAND_ALIASES.get(item.lower(), item.lower())
                    has_direct = bool(
                        self._commands.get(norm) or self._commands.get(item)
                    )
                    if not has_direct:
                        cycle_target = next(
                            (s for s in self._source_names if s.lower() == item.lower()),
                            None,
                        )
                if cycle_target is not None:
                    await self._async_cycle_to_source(cycle_target)
                else:
                    await self._async_publish_command(item)
                if delay and (repeat < repeats - 1 or index < len(commands) - 1):
                    await asyncio.sleep(delay)
