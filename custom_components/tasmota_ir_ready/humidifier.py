"""Humidifier entity for Tasmota IRSend devices."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.humidifier import (
    HumidifierAction,
    HumidifierEntity,
    HumidifierEntityFeature,
)
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
    CONF_HUMIDIFIER_HUMIDITY_SENSOR,
    CONF_MQTT_DELAY,
    CONF_HUMIDIFIER_HUMIDITY_STEP,
    CONF_HUMIDIFIER_MAX_HUMIDITY,
    CONF_HUMIDIFIER_MIN_HUMIDITY,
    CONF_HUMIDIFIER_POWER_SENSOR,
    CONF_HUMIDIFIER_MODE_1_DATA,
    CONF_HUMIDIFIER_MODE_1_NAME,
    CONF_HUMIDIFIER_MODE_2_DATA,
    CONF_HUMIDIFIER_MODE_2_NAME,
    CONF_HUMIDIFIER_MODE_3_DATA,
    CONF_HUMIDIFIER_MODE_3_NAME,
    CONF_HUMIDIFIER_MODE_4_DATA,
    CONF_HUMIDIFIER_MODE_4_NAME,
    CONF_HUMIDIFIER_MODE_5_DATA,
    CONF_HUMIDIFIER_MODE_5_NAME,
    CONF_HUMIDIFIER_MODE_6_DATA,
    CONF_HUMIDIFIER_MODE_6_NAME,
    CONF_HUMIDIFIER_POWER_DATA,
    CONF_HUMIDIFIER_POWER_OFF_DATA,
    CONF_HUMIDIFIER_POWER_ON_DATA,
    CONF_MEDIA_BITS,
    CONF_MEDIA_PROTOCOL,
    DATA_HUMIDIFIER_KEY,
    DEFAULT_HUMIDIFIER_MAX_HUMIDITY,
    DEFAULT_HUMIDIFIER_MIN_HUMIDITY,
    DEFAULT_HUMIDIFIER_HUMIDITY_STEP,
    DEFAULT_HUMIDIFIER_NAME,
    DEFAULT_IRSEND_COMMAND_TOPIC,
    DEFAULT_MEDIA_BITS,
    DEFAULT_MEDIA_PROTOCOL,
    DEFAULT_MQTT_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_MODE_PAIRS = (
    (CONF_HUMIDIFIER_MODE_1_NAME, CONF_HUMIDIFIER_MODE_1_DATA),
    (CONF_HUMIDIFIER_MODE_2_NAME, CONF_HUMIDIFIER_MODE_2_DATA),
    (CONF_HUMIDIFIER_MODE_3_NAME, CONF_HUMIDIFIER_MODE_3_DATA),
    (CONF_HUMIDIFIER_MODE_4_NAME, CONF_HUMIDIFIER_MODE_4_DATA),
    (CONF_HUMIDIFIER_MODE_5_NAME, CONF_HUMIDIFIER_MODE_5_DATA),
    (CONF_HUMIDIFIER_MODE_6_NAME, CONF_HUMIDIFIER_MODE_6_DATA),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Tasmota IR humidifier from a config entry."""
    config = {
        CONF_COMMAND_TOPIC: DEFAULT_IRSEND_COMMAND_TOPIC,
        CONF_NAME: DEFAULT_HUMIDIFIER_NAME,
        **config_entry.data,
        **config_entry.options,
        CONF_UNIQUE_ID: config_entry.entry_id,
    }

    if DATA_HUMIDIFIER_KEY not in hass.data:
        hass.data[DATA_HUMIDIFIER_KEY] = {}

    entity = TasmotaIrHumidifier(hass, config)
    hass.data[DATA_HUMIDIFIER_KEY][config_entry.entry_id] = entity
    async_add_entities([entity])


class TasmotaIrHumidifier(RestoreEntity, HumidifierEntity):
    """A humidifier entity backed by Tasmota IRSend commands.

    All control is optimistic — IR devices cannot report their state back.
    Current humidity is read from an optional external HA sensor entity.
    Target humidity, min/max and step are stored optimistically in HA.
    The action is derived from the on/off state and humidity comparison.
    """

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the humidifier."""
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
        self._power_toggle = (config.get(CONF_HUMIDIFIER_POWER_DATA) or "").strip()
        self._power_on = (config.get(CONF_HUMIDIFIER_POWER_ON_DATA) or "").strip()
        self._power_off = (config.get(CONF_HUMIDIFIER_POWER_OFF_DATA) or "").strip()

        # Modes (name → IR code)
        self._mode_commands: dict[str, str] = {}
        for name_key, data_key in _MODE_PAIRS:
            name = (config.get(name_key) or "").strip()
            data = (config.get(data_key) or "").strip()
            if name and data:
                self._mode_commands[name] = data
        self._attr_available_modes = list(self._mode_commands) or None

        # External humidity sensor (HA entity ID)
        self._humidity_sensor = (
            config.get(CONF_HUMIDIFIER_HUMIDITY_SENSOR) or ""
        ).strip() or None

        # External power sensor (HA binary_sensor entity ID)
        self._power_sensor = (
            config.get(CONF_HUMIDIFIER_POWER_SENSOR) or ""
        ).strip() or None

        # Humidity setpoint range (exposed as HA capability attributes)
        self._attr_min_humidity = float(
            config.get(CONF_HUMIDIFIER_MIN_HUMIDITY, DEFAULT_HUMIDIFIER_MIN_HUMIDITY)
        )
        self._attr_max_humidity = float(
            config.get(CONF_HUMIDIFIER_MAX_HUMIDITY, DEFAULT_HUMIDIFIER_MAX_HUMIDITY)
        )
        # Step — stored as extra attribute; HA's HumidifierEntity has no native step
        self._humidity_step = float(
            config.get(CONF_HUMIDIFIER_HUMIDITY_STEP, DEFAULT_HUMIDIFIER_HUMIDITY_STEP)
        )

        # State
        self._attr_is_on: bool = False
        self._attr_mode: str | None = None
        self._attr_current_humidity: float | None = None
        self._attr_target_humidity: float | None = None
        self._attr_assumed_state = True
        self._available = True
        self._unsubscribes: list = []

        # Availability topic
        self._availability_topic = (
            config.get(CONF_AVAILABILITY_TOPIC) or ""
        ).strip() or None
        if not self._availability_topic:
            self._availability_topic = self._derive_availability_topic(
                self._command_topic
            )

        # Features
        features = HumidifierEntityFeature(0)
        if self._mode_commands:
            features |= HumidifierEntityFeature.MODES
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
    def action(self) -> HumidifierAction | None:
        """Return the current action, derived optimistically.

        * OFF  — device is off
        * IDLE — device is on, current humidity ≥ target humidity
        * HUMIDIFYING — device is on and still working toward the target
                        (or no target/sensor data, so we assume it's running)
        """
        if not self._attr_is_on:
            return HumidifierAction.OFF
        if (
            self._attr_current_humidity is not None
            and self._attr_target_humidity is not None
            and self._attr_current_humidity >= self._attr_target_humidity
        ):
            return HumidifierAction.IDLE
        return HumidifierAction.HUMIDIFYING

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this IR humidifier."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Tasmota",
            model="IR humidifier",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return configured mode names and humidity step for diagnostics."""
        return {
            "configured_modes": list(self._mode_commands),
            "humidity_step": self._humidity_step,
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
        """Restore state and subscribe to MQTT availability and humidity sensor."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == STATE_ON
            last_mode = last_state.attributes.get("mode")
            if last_mode and last_mode in (self._attr_available_modes or []):
                self._attr_mode = last_mode
            # Restore optimistic target humidity (HA stores it under "humidity")
            last_humidity = last_state.attributes.get("humidity")
            if last_humidity is not None:
                try:
                    self._attr_target_humidity = float(last_humidity)
                except (ValueError, TypeError):
                    pass

        # MQTT availability subscription
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

        # External humidity sensor subscription
        if self._humidity_sensor:
            self._unsubscribes.append(
                async_track_state_change_event(
                    self.hass,
                    [self._humidity_sensor],
                    self._async_sensor_changed,
                )
            )
            # Seed with the sensor's current value if it's already available
            sensor_state = self.hass.states.get(self._humidity_sensor)
            if sensor_state and sensor_state.state not in ("unknown", "unavailable"):
                try:
                    self._attr_current_humidity = float(sensor_state.state)
                except (ValueError, TypeError):
                    pass

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
            power_state = self.hass.states.get(self._power_sensor)
            if power_state and power_state.state not in ("unknown", "unavailable"):
                self._attr_is_on = power_state.state == STATE_ON

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed."""
        for unsubscribe in self._unsubscribes:
            unsubscribe()

    @callback
    def _async_sensor_changed(self, event) -> None:
        """Update current humidity when the external sensor reports a new value."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return
        try:
            self._attr_current_humidity = float(new_state.state)
            self.async_write_ha_state()
        except (ValueError, TypeError):
            pass

    @callback
    def _async_power_sensor_changed(self, event) -> None:
        """Update on/off state when the external power sensor reports a change."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return
        self._attr_is_on = new_state.state == STATE_ON
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Humidifier commands
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the humidifier on."""
        cmd = self._power_on or self._power_toggle
        await self._async_publish_command(cmd)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the humidifier off."""
        cmd = self._power_off or self._power_toggle
        await self._async_publish_command(cmd)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_mode(self, mode: str) -> None:
        """Set the humidifier operating mode."""
        if mode not in self._mode_commands:
            _LOGGER.warning(
                "Unknown mode '%s' for humidifier '%s'.", mode, self._attr_name
            )
            return
        await self._async_publish_command(self._mode_commands[mode])
        self._attr_mode = mode
        self.async_write_ha_state()

    async def async_set_humidity(self, humidity: float) -> None:
        """Set the target humidity (optimistic — stored in HA, no IR code sent)."""
        self._attr_target_humidity = humidity
        self.async_write_ha_state()
