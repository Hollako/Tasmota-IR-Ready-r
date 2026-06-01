"""Media player entities for Tasmota IRSend devices."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_AVAILABILITY_TOPIC,
    CONF_COMMAND_TOPIC,
    CONF_MEDIA_BITS,
    CONF_POWER_SENSOR,
    CONF_MEDIA_CHANNEL_DOWN_DATA,
    CONF_MEDIA_CHANNEL_UP_DATA,
    CONF_MEDIA_FAST_FORWARD_DATA,
    CONF_MEDIA_MUTE_DATA,
    CONF_MEDIA_NEXT_DATA,
    CONF_MEDIA_PAUSE_DATA,
    CONF_MEDIA_PLAY_DATA,
    CONF_MEDIA_PLAY_PAUSE_DATA,
    CONF_MEDIA_POWER_DATA,
    CONF_MEDIA_POWER_OFF_DATA,
    CONF_MEDIA_POWER_ON_DATA,
    CONF_MEDIA_PREVIOUS_DATA,
    CONF_MEDIA_PROTOCOL,
    CONF_MEDIA_REWIND_DATA,
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
    CONF_MEDIA_STOP_DATA,
    CONF_MEDIA_VOLUME_DOWN_DATA,
    CONF_MEDIA_VOLUME_UP_DATA,
    DATA_MEDIA_KEY,
    DEFAULT_IRSEND_COMMAND_TOPIC,
    DEFAULT_MEDIA_BITS,
    DEFAULT_MEDIA_NAME,
    DEFAULT_MEDIA_PROTOCOL,
    DEFAULT_MEDIA_SOURCE_CYCLE_DELAY,
    DEFAULT_MEDIA_SOURCE_MODE,
    DOMAIN,
    SOURCE_MODE_CYCLE,
    SOURCE_MODE_DIRECT,
)

_LOGGER = logging.getLogger(__name__)

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
    """Set up a Tasmota IR media player from a config entry."""
    config = {
        CONF_COMMAND_TOPIC: DEFAULT_IRSEND_COMMAND_TOPIC,
        CONF_NAME: DEFAULT_MEDIA_NAME,
        **config_entry.data,
        **config_entry.options,
        CONF_UNIQUE_ID: config_entry.entry_id,
    }

    if DATA_MEDIA_KEY not in hass.data:
        hass.data[DATA_MEDIA_KEY] = {}

    entity = TasmotaIrMediaPlayer(hass, config)
    hass.data[DATA_MEDIA_KEY][config_entry.entry_id] = entity
    async_add_entities([entity])


class TasmotaIrMediaPlayer(RestoreEntity, MediaPlayerEntity):
    """A basic media player backed by Tasmota IRSend commands."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._attr_unique_id = config[CONF_UNIQUE_ID]
        self._attr_name = config[CONF_NAME]
        self._command_topic = config[CONF_COMMAND_TOPIC]
        self._protocol = str(
            config.get(CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL)
        ).upper()
        self._bits = int(config.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS))

        self._commands = {
            CONF_MEDIA_POWER_DATA: config.get(CONF_MEDIA_POWER_DATA) or "",
            CONF_MEDIA_POWER_ON_DATA: config.get(CONF_MEDIA_POWER_ON_DATA) or "",
            CONF_MEDIA_POWER_OFF_DATA: config.get(CONF_MEDIA_POWER_OFF_DATA) or "",
            CONF_MEDIA_VOLUME_UP_DATA: config.get(CONF_MEDIA_VOLUME_UP_DATA) or "",
            CONF_MEDIA_VOLUME_DOWN_DATA: config.get(CONF_MEDIA_VOLUME_DOWN_DATA) or "",
            CONF_MEDIA_MUTE_DATA: config.get(CONF_MEDIA_MUTE_DATA) or "",
            CONF_MEDIA_PLAY_DATA: config.get(CONF_MEDIA_PLAY_DATA) or "",
            CONF_MEDIA_PAUSE_DATA: config.get(CONF_MEDIA_PAUSE_DATA) or "",
            CONF_MEDIA_PLAY_PAUSE_DATA: config.get(CONF_MEDIA_PLAY_PAUSE_DATA) or "",
            CONF_MEDIA_STOP_DATA: config.get(CONF_MEDIA_STOP_DATA) or "",
            CONF_MEDIA_NEXT_DATA: config.get(CONF_MEDIA_NEXT_DATA) or "",
            CONF_MEDIA_PREVIOUS_DATA: config.get(CONF_MEDIA_PREVIOUS_DATA) or "",
            CONF_MEDIA_FAST_FORWARD_DATA: config.get(CONF_MEDIA_FAST_FORWARD_DATA) or "",
            CONF_MEDIA_REWIND_DATA: config.get(CONF_MEDIA_REWIND_DATA) or "",
            CONF_MEDIA_CHANNEL_UP_DATA: config.get(CONF_MEDIA_CHANNEL_UP_DATA) or "",
            CONF_MEDIA_CHANNEL_DOWN_DATA: config.get(CONF_MEDIA_CHANNEL_DOWN_DATA) or "",
        }

        # Source mode setup
        self._source_mode: str = config.get(CONF_MEDIA_SOURCE_MODE, DEFAULT_MEDIA_SOURCE_MODE)
        self._cycle_data: str = (config.get(CONF_MEDIA_SOURCE_CYCLE_DATA) or "").strip()
        self._cycle_delay: float = float(
            config.get(CONF_MEDIA_SOURCE_CYCLE_DELAY, DEFAULT_MEDIA_SOURCE_CYCLE_DELAY)
        )

        if self._source_mode == SOURCE_MODE_CYCLE:
            self._source_commands: dict[str, str] = {}
            # Cycle mode: expose a single virtual source so HA's media-player
            # card shows a pressable button.  No named source list — every press
            # just sends one IR pulse.  After each press we reset _attr_source
            # to None so HA allows the user to press the same button again
            # immediately (HA normally blocks re-selecting the current source).
            self._attr_source_list = ["Input"] if self._cycle_data else []
            self._attr_source: str | None = None
        else:
            self._source_commands = self._build_direct_source_commands(config)
            self._attr_source_list = list(self._source_commands)
            self._attr_source = self._attr_source_list[0] if self._attr_source_list else None

        self._has_power_controls = bool(
            self._command(
                CONF_MEDIA_POWER_ON_DATA,
                CONF_MEDIA_POWER_OFF_DATA,
                CONF_MEDIA_POWER_DATA,
            )
        )
        self._attr_assumed_state = True
        self._attr_state = self._default_state()
        self._available = True
        self._unsubscribes = []
        self._power_sensor: str | None = (config.get(CONF_POWER_SENSOR) or "").strip() or None

        self._availability_topic = config.get(CONF_AVAILABILITY_TOPIC)
        if not self._availability_topic:
            self._availability_topic = self._derive_availability_topic(
                self._command_topic
            )

        features = MediaPlayerEntityFeature(0)
        if self._command(CONF_MEDIA_POWER_ON_DATA, CONF_MEDIA_POWER_DATA):
            features |= MediaPlayerEntityFeature.TURN_ON
        if self._command(CONF_MEDIA_POWER_OFF_DATA, CONF_MEDIA_POWER_DATA):
            features |= MediaPlayerEntityFeature.TURN_OFF
        if self._commands[CONF_MEDIA_VOLUME_UP_DATA] or self._commands[CONF_MEDIA_VOLUME_DOWN_DATA]:
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if self._commands[CONF_MEDIA_MUTE_DATA]:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if self._command(CONF_MEDIA_PLAY_DATA, CONF_MEDIA_PLAY_PAUSE_DATA):
            features |= MediaPlayerEntityFeature.PLAY
        if self._command(CONF_MEDIA_PAUSE_DATA, CONF_MEDIA_PLAY_PAUSE_DATA):
            features |= MediaPlayerEntityFeature.PAUSE
        if self._commands[CONF_MEDIA_STOP_DATA]:
            features |= MediaPlayerEntityFeature.STOP
        if self._command(CONF_MEDIA_NEXT_DATA, CONF_MEDIA_CHANNEL_UP_DATA):
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        if self._command(CONF_MEDIA_PREVIOUS_DATA, CONF_MEDIA_CHANNEL_DOWN_DATA):
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if self._commands[CONF_MEDIA_FAST_FORWARD_DATA]:
            features |= MediaPlayerEntityFeature.SEEK
        if self._commands[CONF_MEDIA_REWIND_DATA]:
            features |= MediaPlayerEntityFeature.SEEK
        if self._attr_source_list:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        self._attr_supported_features = features

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_availability_topic(command_topic: str) -> str | None:
        """Derive the default Tasmota LWT topic from cmnd/<device>/IRSend."""
        path = command_topic.split("/")
        if len(path) >= 3:
            return f"tele/{path[1]}/LWT"

        _LOGGER.warning(
            "Unable to derive availability_topic from command_topic '%s'. "
            "Set availability_topic explicitly to enable availability tracking.",
            command_topic,
        )
        return None

    @property
    def available(self) -> bool:
        """Return whether the Tasmota IR sender is available."""
        return self._available

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this IR media player."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Tasmota",
            model="IR media player",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return configured IR command names and source mode for diagnostics."""
        return {
            "source_mode": self._source_mode,
            "configured_commands": [
                key.removeprefix("media_").removesuffix("_data")
                for key, value in self._commands.items()
                if value
            ],
            "configured_sources": (
                list(self._source_commands)
                if self._source_mode == SOURCE_MODE_DIRECT
                else self._attr_source_list or []
            ),
        }

    def _command(self, *keys: str) -> str:
        """Return the first configured hex data value for the requested keys."""
        for key in keys:
            value = self._commands.get(key)
            if value:
                return value.strip()
        return ""

    def _default_state(self) -> MediaPlayerState:
        """Return the best default state for an IR-only media device."""
        if self._has_power_controls:
            return MediaPlayerState.OFF
        return MediaPlayerState.ON

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

    async def _async_publish_command(self, data: str) -> None:
        """Publish an IRSend payload to Tasmota."""
        if not data:
            return
        await mqtt.async_publish(
            self.hass,
            self._command_topic,
            self._build_irsend_payload(data),
        )

    # ------------------------------------------------------------------
    # HA lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Restore state and subscribe to Tasmota availability."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None:
            if last_state.state in (STATE_ON, STATE_OFF, MediaPlayerState.PLAYING):
                self._attr_state = (
                    last_state.state if self._has_power_controls else self._default_state()
                )
            last_source = last_state.attributes.get("source")
            if last_source and last_source in (self._attr_source_list or []):
                # Only restore source in direct mode; cycle mode always resets to None.
                if self._source_mode == SOURCE_MODE_DIRECT:
                    self._attr_source = last_source

        if self._availability_topic:

            async def available_message_received(message):
                payload = message.payload.strip().lower()
                self._available = payload == "online"
                self.async_write_ha_state()

            self._unsubscribes.append(
                await mqtt.async_subscribe(
                    self.hass,
                    self._availability_topic,
                    available_message_received,
                )
            )

        if self._power_sensor:
            self._unsubscribes.append(
                async_track_state_change_event(
                    self.hass,
                    [self._power_sensor],
                    self._async_power_sensor_changed,
                )
            )
            # Seed with the current sensor value if already available.
            sensor_state = self.hass.states.get(self._power_sensor)
            if sensor_state and sensor_state.state not in ("unknown", "unavailable"):
                self._attr_state = (
                    MediaPlayerState.ON if sensor_state.state == STATE_ON
                    else MediaPlayerState.OFF
                )

    @callback
    def _async_power_sensor_changed(self, event) -> None:
        """Update on/off state when the external power sensor reports a change."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return
        self._attr_state = (
            MediaPlayerState.ON if new_state.state == STATE_ON
            else MediaPlayerState.OFF
        )
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed."""
        for unsubscribe in self._unsubscribes:
            unsubscribe()

    # ------------------------------------------------------------------
    # Media player commands
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        """Turn the media device on."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_POWER_ON_DATA, CONF_MEDIA_POWER_DATA)
        )
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the media device off."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_POWER_OFF_DATA, CONF_MEDIA_POWER_DATA)
        )
        self._attr_state = MediaPlayerState.OFF
        self.async_write_ha_state()

    async def async_toggle(self) -> None:
        """Toggle the media device when a power-toggle command is configured."""
        await self._async_publish_command(self._commands[CONF_MEDIA_POWER_DATA])
        self._attr_state = (
            MediaPlayerState.OFF
            if self._attr_state == MediaPlayerState.ON
            else MediaPlayerState.ON
        )
        self.async_write_ha_state()

    async def async_volume_up(self) -> None:
        """Send the volume-up IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_VOLUME_UP_DATA])

    async def async_volume_down(self) -> None:
        """Send the volume-down IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_VOLUME_DOWN_DATA])

    async def async_mute_volume(self, mute: bool) -> None:
        """Send the mute IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_MUTE_DATA])

    async def async_media_play(self) -> None:
        """Send the play IR command."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_PLAY_DATA, CONF_MEDIA_PLAY_PAUSE_DATA)
        )
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Send the pause IR command."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_PAUSE_DATA, CONF_MEDIA_PLAY_PAUSE_DATA)
        )
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_media_play_pause(self) -> None:
        """Send the play/pause IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_PLAY_PAUSE_DATA])
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Send the stop IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_STOP_DATA])
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None:
        """Send the next-track or channel-up IR command."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_NEXT_DATA, CONF_MEDIA_CHANNEL_UP_DATA)
        )

    async def async_media_previous_track(self) -> None:
        """Send the previous-track or channel-down IR command."""
        await self._async_publish_command(
            self._command(CONF_MEDIA_PREVIOUS_DATA, CONF_MEDIA_CHANNEL_DOWN_DATA)
        )

    async def async_media_seek(self, position: float) -> None:
        """Send a stateless seek IR command.

        Home Assistant's media_player seek service requires a position, but IR
        devices usually expose only fast-forward/rewind buttons. Treat positive
        positions as fast-forward and zero/negative positions as rewind.
        """
        if position > 0:
            await self._async_publish_command(self._commands[CONF_MEDIA_FAST_FORWARD_DATA])
        else:
            await self._async_publish_command(self._commands[CONF_MEDIA_REWIND_DATA])

    async def async_media_channel_up(self) -> None:
        """Send the channel-up IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_CHANNEL_UP_DATA])

    async def async_media_channel_down(self) -> None:
        """Send the channel-down IR command."""
        await self._async_publish_command(self._commands[CONF_MEDIA_CHANNEL_DOWN_DATA])

    # ------------------------------------------------------------------
    # Source selection
    # ------------------------------------------------------------------

    async def async_select_source(self, source: str) -> None:
        """Select an input source."""
        if self._source_mode == SOURCE_MODE_CYCLE:
            await self._async_select_source_cycle(source)
        else:
            await self._async_select_source_direct(source)

    async def _async_select_source_direct(self, source: str) -> None:
        """Send the unique IR code for the requested source."""
        if source not in self._source_commands:
            _LOGGER.warning("Unknown source '%s' selected.", source)
            return
        await self._async_publish_command(self._source_commands[source])
        self._attr_source = source
        self.async_write_ha_state()

    async def _async_select_source_cycle(self, source: str) -> None:
        """Send one cycle IR press and reset source so it can be pressed again.

        HA's source selector blocks re-selecting the currently active source.
        By resetting _attr_source to None after every press the card always
        treats the button as "not selected", allowing unlimited re-presses.
        """
        if not self._cycle_data:
            _LOGGER.warning(
                "Source mode is 'cycle' but no cycle IR code is configured. "
                "Set 'Cycle Button IR Code' in Configure."
            )
            return
        await self._async_publish_command(self._cycle_data)
        # Reset to None so HA allows the user to press the same button again.
        self._attr_source = None
        self.async_write_ha_state()
