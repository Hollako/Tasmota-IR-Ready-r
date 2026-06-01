"""Fan entity for Tasmota IRSend devices."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.fan import DIRECTION_FORWARD, DIRECTION_REVERSE, FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_AVAILABILITY_TOPIC,
    CONF_COMMAND_TOPIC,
    CONF_FAN_DIRECTION_FORWARD_DATA,
    CONF_MQTT_DELAY,
    CONF_FAN_DIRECTION_REVERSE_DATA,
    CONF_FAN_OSCILLATE_DATA,
    CONF_FAN_POWER_SENSOR,
    CONF_FAN_OSCILLATE_OFF_DATA,
    CONF_FAN_OSCILLATE_ON_DATA,
    CONF_FAN_POWER_DATA,
    CONF_FAN_POWER_OFF_DATA,
    CONF_FAN_POWER_ON_DATA,
    CONF_FAN_SPEED_1_DATA,
    CONF_FAN_SPEED_1_NAME,
    CONF_FAN_SPEED_2_DATA,
    CONF_FAN_SPEED_2_NAME,
    CONF_FAN_SPEED_3_DATA,
    CONF_FAN_SPEED_3_NAME,
    CONF_FAN_SPEED_4_DATA,
    CONF_FAN_SPEED_4_NAME,
    CONF_FAN_SPEED_5_DATA,
    CONF_FAN_SPEED_5_NAME,
    CONF_FAN_SPEED_6_DATA,
    CONF_FAN_SPEED_6_NAME,
    CONF_MEDIA_BITS,
    CONF_MEDIA_PROTOCOL,
    DATA_FAN_KEY,
    DEFAULT_FAN_NAME,
    DEFAULT_IRSEND_COMMAND_TOPIC,
    DEFAULT_MEDIA_BITS,
    DEFAULT_MEDIA_PROTOCOL,
    DEFAULT_MQTT_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_SPEED_PAIRS = (
    (CONF_FAN_SPEED_1_NAME, CONF_FAN_SPEED_1_DATA),
    (CONF_FAN_SPEED_2_NAME, CONF_FAN_SPEED_2_DATA),
    (CONF_FAN_SPEED_3_NAME, CONF_FAN_SPEED_3_DATA),
    (CONF_FAN_SPEED_4_NAME, CONF_FAN_SPEED_4_DATA),
    (CONF_FAN_SPEED_5_NAME, CONF_FAN_SPEED_5_DATA),
    (CONF_FAN_SPEED_6_NAME, CONF_FAN_SPEED_6_DATA),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Tasmota IR fan from a config entry."""
    config = {
        CONF_COMMAND_TOPIC: DEFAULT_IRSEND_COMMAND_TOPIC,
        CONF_NAME: DEFAULT_FAN_NAME,
        **config_entry.data,
        **config_entry.options,
        CONF_UNIQUE_ID: config_entry.entry_id,
    }

    if DATA_FAN_KEY not in hass.data:
        hass.data[DATA_FAN_KEY] = {}

    entity = TasmotaIrFan(hass, config)
    hass.data[DATA_FAN_KEY][config_entry.entry_id] = entity
    async_add_entities([entity])


class TasmotaIrFan(RestoreEntity, FanEntity):
    """A fan entity backed by Tasmota IRSend commands."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the fan."""
        self.hass = hass
        self._attr_unique_id = config[CONF_UNIQUE_ID]
        self._attr_name = config[CONF_NAME]
        self._command_topic = config[CONF_COMMAND_TOPIC]
        self._protocol = str(
            config.get(CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL)
        ).upper()
        self._bits = int(config.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS))
        self._mqtt_delay = float(config.get(CONF_MQTT_DELAY, DEFAULT_MQTT_DELAY))

        # Power commands
        self._power_toggle = (config.get(CONF_FAN_POWER_DATA) or "").strip()
        self._power_on = (config.get(CONF_FAN_POWER_ON_DATA) or "").strip()
        self._power_off = (config.get(CONF_FAN_POWER_OFF_DATA) or "").strip()

        # Speed presets (name → IR code)
        self._speed_commands: dict[str, str] = {}
        for name_key, data_key in _SPEED_PAIRS:
            name = (config.get(name_key) or "").strip()
            data = (config.get(data_key) or "").strip()
            if name and data:
                self._speed_commands[name] = data
        self._attr_preset_modes = list(self._speed_commands) or None

        # Oscillation
        self._oscillate_toggle = (config.get(CONF_FAN_OSCILLATE_DATA) or "").strip()
        self._oscillate_on = (config.get(CONF_FAN_OSCILLATE_ON_DATA) or "").strip()
        self._oscillate_off = (config.get(CONF_FAN_OSCILLATE_OFF_DATA) or "").strip()
        self._attr_oscillating: bool = False

        # Direction
        self._direction_forward = (config.get(CONF_FAN_DIRECTION_FORWARD_DATA) or "").strip()
        self._direction_reverse = (config.get(CONF_FAN_DIRECTION_REVERSE_DATA) or "").strip()
        self._attr_current_direction: str | None = None

        # External power sensor (HA binary_sensor entity ID)
        self._power_sensor = (
            config.get(CONF_FAN_POWER_SENSOR) or ""
        ).strip() or None

        # State
        self._attr_is_on: bool = False
        self._attr_preset_mode: str | None = None
        self._attr_assumed_state = True
        self._available = True
        self._unsubscribes: list = []

        # Availability topic
        self._availability_topic = (config.get(CONF_AVAILABILITY_TOPIC) or "").strip() or None
        if not self._availability_topic:
            self._availability_topic = self._derive_availability_topic(self._command_topic)

        # Build supported features
        features = FanEntityFeature(0)
        if self._power_on or self._power_toggle:
            features |= FanEntityFeature.TURN_ON
        if self._power_off or self._power_toggle:
            features |= FanEntityFeature.TURN_OFF
        if self._speed_commands:
            features |= FanEntityFeature.PRESET_MODE
        if self._oscillate_toggle or self._oscillate_on or self._oscillate_off:
            features |= FanEntityFeature.OSCILLATE
        if self._direction_forward and self._direction_reverse:
            features |= FanEntityFeature.DIRECTION
        self._attr_supported_features = features

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_availability_topic(command_topic: str) -> str | None:
        """Derive the Tasmota LWT topic from cmnd/<device>/IRSend."""
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
        """Return device info for this IR fan."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Tasmota",
            model="IR fan",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return configured speed names for diagnostics."""
        return {
            "configured_speeds": list(self._speed_commands),
        }

    def _build_irsend_payload(self, data: str) -> str:
        """Build the JSON payload expected by Tasmota IRSend."""
        data = data.strip()
        if data and not data.lower().startswith("0x"):
            data = f"0x{data}"
        return json.dumps({
            "Protocol": self._protocol,
            "Bits": self._bits,
            "Data": data,
        })

    async def _async_publish_command(self, data: str) -> None:
        """Publish an IRSend payload to Tasmota."""
        if not data:
            return
        if self._mqtt_delay != DEFAULT_MQTT_DELAY:
            await asyncio.sleep(self._mqtt_delay)
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
            self._attr_is_on = last_state.state == STATE_ON
            last_preset = last_state.attributes.get("preset_mode")
            if last_preset and last_preset in (self._attr_preset_modes or []):
                self._attr_preset_mode = last_preset
            last_oscillating = last_state.attributes.get("oscillating")
            if last_oscillating is not None:
                self._attr_oscillating = bool(last_oscillating)
            last_direction = last_state.attributes.get("current_direction")
            if last_direction:
                self._attr_current_direction = last_direction

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

        # External power sensor subscription
        if self._power_sensor:
            self._unsubscribes.append(
                async_track_state_change_event(
                    self.hass,
                    [self._power_sensor],
                    self._async_power_sensor_changed,
                )
            )
            # Seed with the sensor's current value if already available
            sensor_state = self.hass.states.get(self._power_sensor)
            if sensor_state and sensor_state.state not in ("unknown", "unavailable"):
                self._attr_is_on = sensor_state.state == STATE_ON

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed."""
        for unsubscribe in self._unsubscribes:
            unsubscribe()

    @callback
    def _async_power_sensor_changed(self, event) -> None:
        """Update on/off state when the external power sensor reports a change."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return
        self._attr_is_on = new_state.state == STATE_ON
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Fan commands
    # ------------------------------------------------------------------

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on, optionally selecting a preset speed."""
        cmd = self._power_on or self._power_toggle
        await self._async_publish_command(cmd)
        self._attr_is_on = True
        if preset_mode and preset_mode in self._speed_commands:
            await self._async_publish_command(self._speed_commands[preset_mode])
            self._attr_preset_mode = preset_mode
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        cmd = self._power_off or self._power_toggle
        await self._async_publish_command(cmd)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a fan speed preset."""
        if preset_mode not in self._speed_commands:
            _LOGGER.warning("Unknown preset_mode '%s' for fan '%s'.", preset_mode, self._attr_name)
            return
        await self._async_publish_command(self._speed_commands[preset_mode])
        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()

    async def async_oscillate(self, oscillating: bool) -> None:
        """Toggle fan oscillation."""
        if oscillating:
            cmd = self._oscillate_on or self._oscillate_toggle
        else:
            cmd = self._oscillate_off or self._oscillate_toggle
        await self._async_publish_command(cmd)
        self._attr_oscillating = oscillating
        self.async_write_ha_state()

    async def async_set_direction(self, direction: str) -> None:
        """Set fan rotation direction."""
        if direction == DIRECTION_FORWARD:
            await self._async_publish_command(self._direction_forward)
        elif direction == DIRECTION_REVERSE:
            await self._async_publish_command(self._direction_reverse)
        self._attr_current_direction = direction
        self.async_write_ha_state()
