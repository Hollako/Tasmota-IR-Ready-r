"""Config flow for Tasmota IRHVAC."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_MIDDLE,
    FAN_OFF,
    FAN_ON,
    FAN_TOP,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_NAME,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
)
from homeassistant.components import mqtt
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_AVAILABILITY_TOPIC,
    CONF_AWAY_TEMP,
    CONF_FAN_DIRECTION_FORWARD_DATA,
    CONF_FAN_DIRECTION_REVERSE_DATA,
    CONF_FAN_OSCILLATE_DATA,
    CONF_FAN_OSCILLATE_OFF_DATA,
    CONF_FAN_OSCILLATE_ON_DATA,
    CONF_FAN_POWER_DATA,
    CONF_FAN_POWER_OFF_DATA,
    CONF_FAN_POWER_ON_DATA,
    CONF_FAN_POWER_SENSOR,
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
    CONF_HUMIDIFIER_HUMIDITY_SENSOR,
    CONF_HUMIDIFIER_HUMIDITY_STEP,
    CONF_HUMIDIFIER_MAX_HUMIDITY,
    CONF_HUMIDIFIER_MIN_HUMIDITY,
    CONF_HUMIDIFIER_POWER_DATA,
    CONF_HUMIDIFIER_POWER_SENSOR,
    CONF_HUMIDIFIER_POWER_OFF_DATA,
    CONF_HUMIDIFIER_POWER_ON_DATA,
    CONF_LEARN_TOPIC,
    CONF_MEDIA_SOURCE_CYCLE_DATA,
    CONF_MEDIA_SOURCE_CYCLE_DELAY,
    CONF_MEDIA_SOURCE_MODE,
    DEFAULT_MEDIA_SOURCE_CYCLE_DELAY,
    DEFAULT_MEDIA_SOURCE_MODE,
    SOURCE_MODE_CYCLE,
    SOURCE_MODE_DIRECT,
    CONF_CELSIUS,
    CONF_COMMAND_TOPIC,
    CONF_DEVICE_TYPE,
    CONF_FAN_LIST,
    CONF_HUMIDITY_SENSOR,
    CONF_IGNORE_OFF_TEMP,
    CONF_INITIAL_OPERATION_MODE,
    CONF_KEEP_MODE,
    CONF_MAX_TEMP,
    CONF_MEDIA_BITS,
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
    CONF_MEDIA_STOP_DATA,
    CONF_MEDIA_VOLUME_DOWN_DATA,
    CONF_MEDIA_VOLUME_UP_DATA,
    CONF_MIN_TEMP,
    CONF_MODEL,
    CONF_MODES_LIST,
    CONF_MQTT_DELAY,
    CONF_POWER_SENSOR,
    CONF_PRECISION,
    CONF_SLEEP,
    CONF_SPECIAL_MODE,
    CONF_STATE_TOPIC,
    CONF_SWING_LIST,
    CONF_SWINGH,
    CONF_SWINGV,
    CONF_TARGET_TEMP,
    CONF_TEMP_SENSOR,
    CONF_TEMP_STEP,
    CONF_TOGGLE_LIST,
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
    CONF_VENDOR,
    DEFAULT_COMMAND_TOPIC,
    DEFAULT_CONF_CELSIUS,
    DEFAULT_CONF_KEEP_MODE,
    DEFAULT_CONF_MODEL,
    DEFAULT_CONF_SLEEP,
    DEFAULT_FAN_LIST,
    DEFAULT_IGNORE_OFF_TEMP,
    DEFAULT_IRSEND_COMMAND_TOPIC,
    DEFAULT_MAX_TEMP,
    DEFAULT_MEDIA_BITS,
    DEFAULT_MEDIA_NAME,
    DEFAULT_MEDIA_PROTOCOL,
    DEFAULT_MIN_TEMP,
    DEFAULT_MODES_LIST,
    DEFAULT_MQTT_DELAY,
    DEFAULT_NAME,
    DEFAULT_PRECISION,
    DEFAULT_FAN_NAME,
    DEFAULT_HUMIDIFIER_MAX_HUMIDITY,
    DEFAULT_HUMIDIFIER_MIN_HUMIDITY,
    DEFAULT_HUMIDIFIER_HUMIDITY_STEP,
    DEFAULT_HUMIDIFIER_NAME,
    DEFAULT_REMOTE_NAME,
    DEFAULT_STATE_TOPIC,
    DEFAULT_SWING_LIST,
    DEFAULT_TARGET_TEMP,
    DEVICE_TYPE_CLIMATE,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_HUB,
    DEVICE_TYPE_HUMIDIFIER,
    DEVICE_TYPE_MEDIA_PLAYER,
    DEVICE_TYPE_REMOTE,
    DOMAIN,
    HVAC_FAN_AUTO_MAX,
    HVAC_FAN_MAX,
    HVAC_FAN_MAX_HIGH,
    HVAC_FAN_MIN,
    HVAC_MODE_AUTO_FAN,
    HVAC_MODE_FAN_AUTO,
    TOGGLE_ALL_LIST,
)

_LOGGER = logging.getLogger(__name__)

_CONF_STATE_TOPIC_2 = CONF_STATE_TOPIC + "_2"
_SECTION_HVAC_MODES = "hvac_modes"
_SECTION_FAN_SPEEDS = "fan_speeds"
_SECTION_SWING_POSITIONS = "swing_positions"
_SECTION_MEDIA_CONNECTION = "media_connection"
_SECTION_MEDIA_COMMANDS = "media_commands"
_SECTION_MEDIA_SOURCES = "media_sources"
_SECTION_REMOTE_KEYPAD = "remote_keypad"
_SECTION_REMOTE_NAVIGATION = "remote_navigation"
_SECTION_REMOTE_EXTRA = "remote_extra"
_SECTION_REMOTE_SOURCES = "remote_sources"
_SECTION_FAN_CONNECTION = "fan_connection"
_SECTION_FAN_POWER = "fan_power"
_SECTION_FAN_SPEEDS = "fan_speeds"
_SECTION_FAN_OSCILLATION = "fan_oscillation"
_SECTION_HUMIDIFIER_CONNECTION = "humidifier_connection"
_SECTION_HUMIDIFIER_POWER = "humidifier_power"
_SECTION_HUMIDIFIER_MODES = "humidifier_modes"
_SECTION_HUMIDIFIER_SETTINGS = "humidifier_settings"

# ---------------------------------------------------------------------------
# Selector option lists
# ---------------------------------------------------------------------------

HVAC_MODE_OPTIONS = [
    {"value": HVACMode.HEAT, "label": "Heat"},
    {"value": HVACMode.COOL, "label": "Cool"},
    {"value": HVACMode.HEAT_COOL, "label": "Heat/Cool"},
    {"value": HVACMode.AUTO, "label": "Auto"},
    {"value": HVACMode.DRY, "label": "Dry"},
    {"value": HVACMode.FAN_ONLY, "label": "Fan Only"},
    {"value": HVAC_MODE_AUTO_FAN, "label": "Fan Only / Auto (swapped — tasmota says auto)"},
    {"value": HVAC_MODE_FAN_AUTO, "label": "Auto / Fan Only (swapped — tasmota says fan)"},
]

FAN_MODE_OPTIONS = [
    # Speed ladder — slowest to fastest
    {"value": FAN_OFF,         "label": "Off"},
    {"value": FAN_ON,          "label": "On"},
    {"value": HVAC_FAN_MIN,    "label": "Min (shown as Low in HA)"},
    {"value": FAN_LOW,         "label": "Low"},
    {"value": FAN_MIDDLE,      "label": "Middle"},
    {"value": FAN_MEDIUM,      "label": "Medium"},
    {"value": FAN_HIGH,        "label": "High"},
    {"value": HVAC_FAN_MAX,    "label": "Max (shown as High in HA)"},
    {"value": FAN_TOP,         "label": "Top"},
    {"value": FAN_FOCUS,       "label": "Focus"},
    {"value": FAN_DIFFUSE,     "label": "Diffuse"},
    # Automatic
    {"value": FAN_AUTO,        "label": "Auto"},
    # Electra-specific quirks
    {"value": HVAC_FAN_MAX_HIGH,  "label": "Max→High (Electra quirk)"},
    {"value": HVAC_FAN_AUTO_MAX,  "label": "Auto→Max (Electra quirk)"},
]

SWING_MODE_OPTIONS = [
    {"value": SWING_OFF, "label": "Off"},
    {"value": SWING_BOTH, "label": "Auto (all directions)"},
    {"value": SWING_VERTICAL, "label": "Auto (vertical sweep)"},
    {"value": SWING_HORIZONTAL, "label": "Auto (horizontal sweep)"},
    {"value": "highest", "label": "Vertical: Highest"},
    {"value": "high", "label": "Vertical: High"},
    {"value": "middle", "label": "Vertical: Middle"},
    {"value": "low", "label": "Vertical: Low"},
    {"value": "lowest", "label": "Vertical: Lowest"},
    {"value": "left max", "label": "Horizontal: Left Max"},
    {"value": "left", "label": "Horizontal: Left"},
    {"value": "horizontal middle", "label": "Horizontal: Middle"},
    {"value": "right", "label": "Horizontal: Right"},
    {"value": "right max", "label": "Horizontal: Right Max"},
    {"value": "wide", "label": "Horizontal: Wide"},
]

INITIAL_MODE_OPTIONS = [
    {"value": HVACMode.OFF, "label": "Off"},
    {"value": HVACMode.HEAT, "label": "Heat"},
    {"value": HVACMode.COOL, "label": "Cool"},
    {"value": HVACMode.HEAT_COOL, "label": "Heat/Cool"},
    {"value": HVACMode.AUTO, "label": "Auto"},
    {"value": HVACMode.DRY, "label": "Dry"},
    {"value": HVACMode.FAN_ONLY, "label": "Fan Only"},
    {"value": HVAC_MODE_AUTO_FAN, "label": "Auto/Fan Only"},
    {"value": HVAC_MODE_FAN_AUTO, "label": "Fan Only/Auto"},
]

PRECISION_OPTIONS = [
    {"value": str(PRECISION_TENTHS), "label": "0.1°"},
    {"value": str(PRECISION_HALVES), "label": "0.5°"},
    {"value": str(PRECISION_WHOLE), "label": "1°"},
]

TEMP_STEP_OPTIONS = [
    {"value": str(PRECISION_HALVES), "label": "0.5°"},
    {"value": str(PRECISION_WHOLE), "label": "1°"},
]

CELSIUS_OPTIONS = [
    {"value": "on", "label": "Celsius (°C)"},
    {"value": "off", "label": "Fahrenheit (°F)"},
]

SWINGV_OPTIONS = [
    {"value": "", "label": "— Not set —"},
    {"value": "off", "label": "Off"},
    {"value": "auto", "label": "Auto"},
    {"value": "highest", "label": "Highest"},
    {"value": "high", "label": "High"},
    {"value": "middle", "label": "Middle"},
    {"value": "low", "label": "Low"},
    {"value": "lowest", "label": "Lowest"},
]

TOGGLE_OPTIONS = [{"value": item, "label": item} for item in TOGGLE_ALL_LIST]

DEVICE_TYPE_OPTIONS = [
    {"value": DEVICE_TYPE_CLIMATE, "label": "Climate"},
    {"value": DEVICE_TYPE_MEDIA_PLAYER, "label": "Media Player"},
    {"value": DEVICE_TYPE_REMOTE, "label": "Remote"},
    {"value": DEVICE_TYPE_FAN, "label": "Fan"},
    {"value": DEVICE_TYPE_HUMIDIFIER, "label": "Humidifier"},
]

SOURCE_MODE_OPTIONS = [
    {"value": SOURCE_MODE_DIRECT, "label": "Direct — each source has its own IR code"},
    {"value": SOURCE_MODE_CYCLE, "label": "Cycle — one button cycles through sources"},
]

MEDIA_COMMAND_DATA_FIELDS = [
    CONF_MEDIA_POWER_DATA,
    CONF_MEDIA_POWER_ON_DATA,
    CONF_MEDIA_POWER_OFF_DATA,
    CONF_MEDIA_VOLUME_UP_DATA,
    CONF_MEDIA_VOLUME_DOWN_DATA,
    CONF_MEDIA_MUTE_DATA,
    CONF_MEDIA_PLAY_DATA,
    CONF_MEDIA_PAUSE_DATA,
    CONF_MEDIA_PLAY_PAUSE_DATA,
    CONF_MEDIA_STOP_DATA,
    CONF_MEDIA_NEXT_DATA,
    CONF_MEDIA_PREVIOUS_DATA,
    CONF_MEDIA_FAST_FORWARD_DATA,
    CONF_MEDIA_REWIND_DATA,
    CONF_MEDIA_CHANNEL_UP_DATA,
    CONF_MEDIA_CHANNEL_DOWN_DATA,
    CONF_MEDIA_SOURCE_1_DATA,
    CONF_MEDIA_SOURCE_2_DATA,
    CONF_MEDIA_SOURCE_3_DATA,
    CONF_MEDIA_SOURCE_4_DATA,
    CONF_MEDIA_SOURCE_5_DATA,
    CONF_MEDIA_SOURCE_6_DATA,
    CONF_MEDIA_SOURCE_CYCLE_DATA,
]

MEDIA_SOURCE_NAME_FIELDS = [
    CONF_MEDIA_SOURCE_1_NAME,
    CONF_MEDIA_SOURCE_2_NAME,
    CONF_MEDIA_SOURCE_3_NAME,
    CONF_MEDIA_SOURCE_4_NAME,
    CONF_MEDIA_SOURCE_5_NAME,
    CONF_MEDIA_SOURCE_6_NAME,
]

FAN_COMMAND_DATA_FIELDS = [
    CONF_FAN_POWER_DATA,
    CONF_FAN_POWER_ON_DATA,
    CONF_FAN_POWER_OFF_DATA,
    CONF_FAN_SPEED_1_DATA,
    CONF_FAN_SPEED_2_DATA,
    CONF_FAN_SPEED_3_DATA,
    CONF_FAN_SPEED_4_DATA,
    CONF_FAN_SPEED_5_DATA,
    CONF_FAN_SPEED_6_DATA,
    CONF_FAN_OSCILLATE_DATA,
    CONF_FAN_OSCILLATE_ON_DATA,
    CONF_FAN_OSCILLATE_OFF_DATA,
    CONF_FAN_DIRECTION_FORWARD_DATA,
    CONF_FAN_DIRECTION_REVERSE_DATA,
]

FAN_SPEED_NAME_FIELDS = [
    CONF_FAN_SPEED_1_NAME,
    CONF_FAN_SPEED_2_NAME,
    CONF_FAN_SPEED_3_NAME,
    CONF_FAN_SPEED_4_NAME,
    CONF_FAN_SPEED_5_NAME,
    CONF_FAN_SPEED_6_NAME,
]

HUMIDIFIER_COMMAND_DATA_FIELDS = [
    CONF_HUMIDIFIER_POWER_DATA,
    CONF_HUMIDIFIER_POWER_ON_DATA,
    CONF_HUMIDIFIER_POWER_OFF_DATA,
    CONF_HUMIDIFIER_MODE_1_DATA,
    CONF_HUMIDIFIER_MODE_2_DATA,
    CONF_HUMIDIFIER_MODE_3_DATA,
    CONF_HUMIDIFIER_MODE_4_DATA,
    CONF_HUMIDIFIER_MODE_5_DATA,
    CONF_HUMIDIFIER_MODE_6_DATA,
]

HUMIDIFIER_MODE_NAME_FIELDS = [
    CONF_HUMIDIFIER_MODE_1_NAME,
    CONF_HUMIDIFIER_MODE_2_NAME,
    CONF_HUMIDIFIER_MODE_3_NAME,
    CONF_HUMIDIFIER_MODE_4_NAME,
    CONF_HUMIDIFIER_MODE_5_NAME,
    CONF_HUMIDIFIER_MODE_6_NAME,
]

REMOTE_COMMAND_DATA_FIELDS = [
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
    CONF_REMOTE_UP_DATA,
    CONF_REMOTE_DOWN_DATA,
    CONF_REMOTE_LEFT_DATA,
    CONF_REMOTE_RIGHT_DATA,
    CONF_REMOTE_OK_DATA,
    CONF_REMOTE_BACK_DATA,
    CONF_REMOTE_HOME_DATA,
    CONF_REMOTE_MENU_DATA,
    CONF_REMOTE_SETTINGS_DATA,
    CONF_REMOTE_INFO_DATA,
    CONF_REMOTE_EXIT_DATA,
    CONF_REMOTE_CHANNEL_UP_DATA,
    CONF_REMOTE_CHANNEL_DOWN_DATA,
    CONF_REMOTE_RED_DATA,
    CONF_REMOTE_GREEN_DATA,
    CONF_REMOTE_YELLOW_DATA,
    CONF_REMOTE_BLUE_DATA,
]

SWINGH_OPTIONS = [
    {"value": "", "label": "— Not set —"},
    {"value": "off", "label": "Off"},
    {"value": "auto", "label": "Auto"},
    {"value": "left max", "label": "Left Max"},
    {"value": "left", "label": "Left"},
    {"value": "middle", "label": "Middle"},
    {"value": "right", "label": "Right"},
    {"value": "right max", "label": "Right Max"},
    {"value": "wide", "label": "Wide"},
]

_MEDIA_LEARN_OPTIONS = [
    {"value": "", "label": "— No learning, just save —"},
    {"value": CONF_MEDIA_POWER_DATA, "label": "Power Toggle"},
    {"value": CONF_MEDIA_POWER_ON_DATA, "label": "Power On"},
    {"value": CONF_MEDIA_POWER_OFF_DATA, "label": "Power Off"},
    {"value": CONF_MEDIA_VOLUME_UP_DATA, "label": "Volume Up"},
    {"value": CONF_MEDIA_VOLUME_DOWN_DATA, "label": "Volume Down"},
    {"value": CONF_MEDIA_MUTE_DATA, "label": "Mute"},
    {"value": CONF_MEDIA_PLAY_DATA, "label": "Play"},
    {"value": CONF_MEDIA_PAUSE_DATA, "label": "Pause"},
    {"value": CONF_MEDIA_PLAY_PAUSE_DATA, "label": "Play / Pause"},
    {"value": CONF_MEDIA_STOP_DATA, "label": "Stop"},
    {"value": CONF_MEDIA_NEXT_DATA, "label": "Next"},
    {"value": CONF_MEDIA_PREVIOUS_DATA, "label": "Previous"},
    {"value": CONF_MEDIA_FAST_FORWARD_DATA, "label": "Fast Forward"},
    {"value": CONF_MEDIA_REWIND_DATA, "label": "Rewind"},
    {"value": CONF_MEDIA_CHANNEL_UP_DATA, "label": "Channel Up"},
    {"value": CONF_MEDIA_CHANNEL_DOWN_DATA, "label": "Channel Down"},
    {"value": CONF_MEDIA_SOURCE_CYCLE_DATA, "label": "Source Cycle Button"},
    {"value": CONF_MEDIA_SOURCE_1_DATA, "label": "Source 1"},
    {"value": CONF_MEDIA_SOURCE_2_DATA, "label": "Source 2"},
    {"value": CONF_MEDIA_SOURCE_3_DATA, "label": "Source 3"},
    {"value": CONF_MEDIA_SOURCE_4_DATA, "label": "Source 4"},
    {"value": CONF_MEDIA_SOURCE_5_DATA, "label": "Source 5"},
    {"value": CONF_MEDIA_SOURCE_6_DATA, "label": "Source 6"},
]

_REMOTE_LEARN_OPTIONS = [
    {"value": "", "label": "— No learning, just save —"},
    {"value": CONF_MEDIA_POWER_DATA, "label": "Power Toggle"},
    {"value": CONF_MEDIA_POWER_ON_DATA, "label": "Power On"},
    {"value": CONF_MEDIA_POWER_OFF_DATA, "label": "Power Off"},
    {"value": CONF_MEDIA_VOLUME_UP_DATA, "label": "Volume Up"},
    {"value": CONF_MEDIA_VOLUME_DOWN_DATA, "label": "Volume Down"},
    {"value": CONF_MEDIA_MUTE_DATA, "label": "Mute"},
    {"value": CONF_MEDIA_SOURCE_CYCLE_DATA, "label": "Source Cycle Button"},
    {"value": CONF_MEDIA_SOURCE_1_DATA, "label": "Source 1"},
    {"value": CONF_MEDIA_SOURCE_2_DATA, "label": "Source 2"},
    {"value": CONF_MEDIA_SOURCE_3_DATA, "label": "Source 3"},
    {"value": CONF_MEDIA_SOURCE_4_DATA, "label": "Source 4"},
    {"value": CONF_MEDIA_SOURCE_5_DATA, "label": "Source 5"},
    {"value": CONF_MEDIA_SOURCE_6_DATA, "label": "Source 6"},
    {"value": CONF_REMOTE_DIGIT_0_DATA, "label": "Digit 0"},
    {"value": CONF_REMOTE_DIGIT_1_DATA, "label": "Digit 1"},
    {"value": CONF_REMOTE_DIGIT_2_DATA, "label": "Digit 2"},
    {"value": CONF_REMOTE_DIGIT_3_DATA, "label": "Digit 3"},
    {"value": CONF_REMOTE_DIGIT_4_DATA, "label": "Digit 4"},
    {"value": CONF_REMOTE_DIGIT_5_DATA, "label": "Digit 5"},
    {"value": CONF_REMOTE_DIGIT_6_DATA, "label": "Digit 6"},
    {"value": CONF_REMOTE_DIGIT_7_DATA, "label": "Digit 7"},
    {"value": CONF_REMOTE_DIGIT_8_DATA, "label": "Digit 8"},
    {"value": CONF_REMOTE_DIGIT_9_DATA, "label": "Digit 9"},
    {"value": CONF_REMOTE_UP_DATA, "label": "Up"},
    {"value": CONF_REMOTE_DOWN_DATA, "label": "Down"},
    {"value": CONF_REMOTE_LEFT_DATA, "label": "Left"},
    {"value": CONF_REMOTE_RIGHT_DATA, "label": "Right"},
    {"value": CONF_REMOTE_OK_DATA, "label": "OK"},
    {"value": CONF_REMOTE_BACK_DATA, "label": "Back"},
    {"value": CONF_REMOTE_HOME_DATA, "label": "Home"},
    {"value": CONF_REMOTE_MENU_DATA, "label": "Menu"},
    {"value": CONF_REMOTE_SETTINGS_DATA, "label": "Settings"},
    {"value": CONF_REMOTE_INFO_DATA, "label": "Info"},
    {"value": CONF_REMOTE_EXIT_DATA, "label": "Exit"},
    {"value": CONF_REMOTE_CHANNEL_UP_DATA, "label": "Channel Up"},
    {"value": CONF_REMOTE_CHANNEL_DOWN_DATA, "label": "Channel Down"},
    {"value": CONF_REMOTE_RED_DATA, "label": "Red"},
    {"value": CONF_REMOTE_GREEN_DATA, "label": "Green"},
    {"value": CONF_REMOTE_YELLOW_DATA, "label": "Yellow"},
    {"value": CONF_REMOTE_BLUE_DATA, "label": "Blue"},
]

_FAN_LEARN_OPTIONS = [
    {"value": "", "label": "— No learning, just save —"},
    {"value": CONF_FAN_POWER_DATA, "label": "Power Toggle"},
    {"value": CONF_FAN_POWER_ON_DATA, "label": "Power On"},
    {"value": CONF_FAN_POWER_OFF_DATA, "label": "Power Off"},
    {"value": CONF_FAN_SPEED_1_DATA, "label": "Speed 1"},
    {"value": CONF_FAN_SPEED_2_DATA, "label": "Speed 2"},
    {"value": CONF_FAN_SPEED_3_DATA, "label": "Speed 3"},
    {"value": CONF_FAN_SPEED_4_DATA, "label": "Speed 4"},
    {"value": CONF_FAN_SPEED_5_DATA, "label": "Speed 5"},
    {"value": CONF_FAN_SPEED_6_DATA, "label": "Speed 6"},
    {"value": CONF_FAN_OSCILLATE_DATA, "label": "Oscillate Toggle"},
    {"value": CONF_FAN_OSCILLATE_ON_DATA, "label": "Oscillate On"},
    {"value": CONF_FAN_OSCILLATE_OFF_DATA, "label": "Oscillate Off"},
    {"value": CONF_FAN_DIRECTION_FORWARD_DATA, "label": "Direction Forward"},
    {"value": CONF_FAN_DIRECTION_REVERSE_DATA, "label": "Direction Reverse"},
]

_HUMIDIFIER_LEARN_OPTIONS = [
    {"value": "", "label": "— No learning, just save —"},
    {"value": CONF_HUMIDIFIER_POWER_DATA, "label": "Power Toggle"},
    {"value": CONF_HUMIDIFIER_POWER_ON_DATA, "label": "Power On"},
    {"value": CONF_HUMIDIFIER_POWER_OFF_DATA, "label": "Power Off"},
    {"value": CONF_HUMIDIFIER_MODE_1_DATA, "label": "Mode 1"},
    {"value": CONF_HUMIDIFIER_MODE_2_DATA, "label": "Mode 2"},
    {"value": CONF_HUMIDIFIER_MODE_3_DATA, "label": "Mode 3"},
    {"value": CONF_HUMIDIFIER_MODE_4_DATA, "label": "Mode 4"},
    {"value": CONF_HUMIDIFIER_MODE_5_DATA, "label": "Mode 5"},
    {"value": CONF_HUMIDIFIER_MODE_6_DATA, "label": "Mode 6"},
]

_LEARN_COMMAND_LABEL: dict[str, str] = {
    opt["value"]: opt["label"]
    for opts in (
        _MEDIA_LEARN_OPTIONS,
        _REMOTE_LEARN_OPTIONS,
        _FAN_LEARN_OPTIONS,
        _HUMIDIFIER_LEARN_OPTIONS,
    )
    for opt in opts
    if opt["value"]
}


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------


class TasmotaIrhvacConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tasmota IRHVAC."""

    VERSION = 1

    async def async_step_import(self, import_data: dict[str, Any]) -> dict:
        """Create an entry programmatically from the IR Manager panel."""
        data = dict(import_data)
        # Ensure device_type is always set
        data.setdefault(CONF_DEVICE_TYPE, DEVICE_TYPE_CLIMATE)
        title = data.get(CONF_NAME) or "IR Device"
        command_topic = (data.get(CONF_COMMAND_TOPIC) or "").strip()
        if command_topic:
            unique_id = f"{data[CONF_DEVICE_TYPE]}:{title}".lower()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Initial setup step - choose the IR device type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_type = user_input[CONF_DEVICE_TYPE]
            if device_type == DEVICE_TYPE_MEDIA_PLAYER:
                return await self.async_step_media_player()
            if device_type == DEVICE_TYPE_REMOTE:
                return await self.async_step_remote()
            if device_type == DEVICE_TYPE_FAN:
                return await self.async_step_fan()
            if device_type == DEVICE_TYPE_HUMIDIFIER:
                return await self.async_step_humidifier()
            return await self.async_step_climate()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_TYPE,
                    default=DEVICE_TYPE_CLIMATE,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=DEVICE_TYPE_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_climate(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Collect the minimum required details for an IRHVAC climate entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_DEVICE_TYPE] = DEVICE_TYPE_CLIMATE
            await self.async_set_unique_id(f"{DEVICE_TYPE_CLIMATE}:{user_input[CONF_NAME]}".lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): TextSelector(),
                vol.Required(CONF_VENDOR): TextSelector(),
                vol.Required(
                    CONF_COMMAND_TOPIC,
                    default=DEFAULT_COMMAND_TOPIC,
                ): TextSelector(),
                vol.Required(
                    CONF_STATE_TOPIC,
                    default=DEFAULT_STATE_TOPIC,
                ): TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="climate", data_schema=schema, errors=errors
        )

    async def async_step_media_player(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Collect the minimum required details for an IR media player."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            for key in MEDIA_COMMAND_DATA_FIELDS:
                if key in user_input:
                    user_input[key] = user_input[key].strip()
            for key in MEDIA_SOURCE_NAME_FIELDS:
                if key in user_input:
                    user_input[key] = user_input[key].strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            user_input[CONF_DEVICE_TYPE] = DEVICE_TYPE_MEDIA_PLAYER
            unique_id = f"{DEVICE_TYPE_MEDIA_PLAYER}:{user_input[CONF_NAME]}".lower()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_MEDIA_NAME): TextSelector(),
                vol.Required(
                    CONF_COMMAND_TOPIC,
                    default=DEFAULT_IRSEND_COMMAND_TOPIC,
                ): TextSelector(),
                vol.Optional(
                    CONF_AVAILABILITY_TOPIC,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_LEARN_TOPIC,
                    default="",
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_PROTOCOL,
                    default=DEFAULT_MEDIA_PROTOCOL,
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_BITS,
                    default=DEFAULT_MEDIA_BITS,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=256,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_MEDIA_POWER_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_POWER_ON_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_POWER_OFF_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_VOLUME_UP_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_VOLUME_DOWN_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_MUTE_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_PLAY_PAUSE_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_NEXT_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_PREVIOUS_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_1_NAME,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_1_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_2_NAME,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_2_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_3_NAME,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_SOURCE_3_DATA,
                    default="",
                ): TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="media_player", data_schema=schema, errors=errors
        )

    async def async_step_remote(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Collect the minimum required details for an IR remote."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            for key in (*REMOTE_COMMAND_DATA_FIELDS, *MEDIA_COMMAND_DATA_FIELDS):
                if key in user_input:
                    user_input[key] = user_input[key].strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            user_input[CONF_DEVICE_TYPE] = DEVICE_TYPE_REMOTE
            unique_id = f"{DEVICE_TYPE_REMOTE}:{user_input[CONF_NAME]}".lower()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_REMOTE_NAME): TextSelector(),
                vol.Required(
                    CONF_COMMAND_TOPIC,
                    default=DEFAULT_IRSEND_COMMAND_TOPIC,
                ): TextSelector(),
                vol.Optional(
                    CONF_AVAILABILITY_TOPIC,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_LEARN_TOPIC,
                    default="",
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_PROTOCOL,
                    default=DEFAULT_MEDIA_PROTOCOL,
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_BITS,
                    default=DEFAULT_MEDIA_BITS,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=256,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_MEDIA_POWER_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_POWER_ON_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_POWER_OFF_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_VOLUME_UP_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_VOLUME_DOWN_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_MEDIA_MUTE_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_REMOTE_UP_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_REMOTE_DOWN_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_REMOTE_LEFT_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_REMOTE_RIGHT_DATA,
                    default="",
                ): TextSelector(),
                vol.Optional(
                    CONF_REMOTE_OK_DATA,
                    default="",
                ): TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="remote", data_schema=schema, errors=errors
        )

    async def async_step_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Collect the minimum required details for an IR fan."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            user_input[CONF_DEVICE_TYPE] = DEVICE_TYPE_FAN
            unique_id = f"{DEVICE_TYPE_FAN}:{user_input[CONF_NAME]}".lower()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_FAN_NAME): TextSelector(),
                vol.Required(
                    CONF_COMMAND_TOPIC,
                    default=DEFAULT_IRSEND_COMMAND_TOPIC,
                ): TextSelector(),
                vol.Optional(CONF_AVAILABILITY_TOPIC, default=""): TextSelector(),
                vol.Optional(CONF_LEARN_TOPIC, default=""): TextSelector(),
                vol.Required(
                    CONF_MEDIA_PROTOCOL,
                    default=DEFAULT_MEDIA_PROTOCOL,
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_BITS,
                    default=DEFAULT_MEDIA_BITS,
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=256, step=1, mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="fan", data_schema=schema, errors=errors
        )

    async def async_step_humidifier(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Collect the minimum required details for an IR humidifier."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            user_input[CONF_DEVICE_TYPE] = DEVICE_TYPE_HUMIDIFIER
            unique_id = f"{DEVICE_TYPE_HUMIDIFIER}:{user_input[CONF_NAME]}".lower()
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_HUMIDIFIER_NAME): TextSelector(),
                vol.Required(
                    CONF_COMMAND_TOPIC,
                    default=DEFAULT_IRSEND_COMMAND_TOPIC,
                ): TextSelector(),
                vol.Optional(CONF_AVAILABILITY_TOPIC, default=""): TextSelector(),
                vol.Optional(CONF_LEARN_TOPIC, default=""): TextSelector(),
                vol.Required(
                    CONF_MEDIA_PROTOCOL,
                    default=DEFAULT_MEDIA_PROTOCOL,
                ): TextSelector(),
                vol.Required(
                    CONF_MEDIA_BITS,
                    default=DEFAULT_MEDIA_BITS,
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=256, step=1, mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="humidifier", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TasmotaIrhvacOptionsFlow(config_entry)


# ---------------------------------------------------------------------------
# Options flow  (3 steps: connection → capabilities → behavior)
# ---------------------------------------------------------------------------


class TasmotaIrhvacOptionsFlow(OptionsFlow):
    """Handle options flow for all settings."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        self._options: dict[str, Any] = {}
        self._learning_task: asyncio.Task | None = None
        self._learn_command: str | None = None
        self._learned_value: str | None = None
        self._pending_input: dict[str, Any] | None = None
        self._device_type_learning: str = DEVICE_TYPE_MEDIA_PLAYER

    def _current(self) -> dict[str, Any]:
        base = {**self._entry.data, **self._entry.options}
        if self._pending_input is not None:
            base.update(self._pending_input)
        if self._learn_command and self._learned_value:
            base[self._learn_command] = self._learned_value
        return base

    # ------------------------------------------------------------------
    # Step 1 — Connection
    # ------------------------------------------------------------------

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Connection settings: topics, sensors, MQTT delay."""
        device_type = self._current().get(CONF_DEVICE_TYPE, DEVICE_TYPE_CLIMATE)
        if device_type == DEVICE_TYPE_MEDIA_PLAYER:
            return await self.async_step_media_player_options(user_input)
        if device_type == DEVICE_TYPE_REMOTE:
            return await self.async_step_remote_options(user_input)
        if device_type == DEVICE_TYPE_FAN:
            return await self.async_step_fan_options(user_input)
        if device_type == DEVICE_TYPE_HUMIDIFIER:
            return await self.async_step_humidifier_options(user_input)

        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_capabilities()

        current = self._current()

        base_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=current.get(CONF_NAME, DEFAULT_NAME)): TextSelector(),
                vol.Required(CONF_VENDOR, default=current.get(CONF_VENDOR, "")): TextSelector(),
                vol.Required(CONF_COMMAND_TOPIC, default=current.get(CONF_COMMAND_TOPIC, DEFAULT_COMMAND_TOPIC)): TextSelector(),
                vol.Required(CONF_STATE_TOPIC, default=current.get(CONF_STATE_TOPIC, DEFAULT_STATE_TOPIC)): TextSelector(),
                vol.Optional(_CONF_STATE_TOPIC_2): TextSelector(),
                vol.Optional(CONF_AVAILABILITY_TOPIC): TextSelector(),
                vol.Optional(
                    CONF_MQTT_DELAY,
                    default=float(current.get(CONF_MQTT_DELAY, DEFAULT_MQTT_DELAY)),
                ): NumberSelector(NumberSelectorConfig(min=0, max=10, step=0.1, mode=NumberSelectorMode.BOX)),
                vol.Optional(CONF_TEMP_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HUMIDITY_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_POWER_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain=["binary_sensor", "sensor", "switch"])
                ),
            }
        )

        suggested = {
            _CONF_STATE_TOPIC_2: current.get(_CONF_STATE_TOPIC_2),
            CONF_AVAILABILITY_TOPIC: current.get(CONF_AVAILABILITY_TOPIC),
            CONF_TEMP_SENSOR: current.get(CONF_TEMP_SENSOR),
            CONF_HUMIDITY_SENSOR: current.get(CONF_HUMIDITY_SENSOR),
            CONF_POWER_SENSOR: current.get(CONF_POWER_SENSOR),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(base_schema, suggested),
        )

    async def async_step_media_player_options(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Connection and command options for an IR media player."""
        if user_input is not None:
            learn_command = (user_input.pop("learn_command", None) or "").strip()
            if learn_command:
                pending = dict(user_input)
                for section_key in (
                    _SECTION_MEDIA_CONNECTION,
                    _SECTION_MEDIA_COMMANDS,
                    _SECTION_MEDIA_SOURCES,
                ):
                    pending.update(pending.pop(section_key, {}))
                self._pending_input = pending
                self._learn_command = learn_command
                self._device_type_learning = DEVICE_TYPE_MEDIA_PLAYER
                self._learning_task = None
                return await self.async_step_learn_ir()

            for section_key in (
                _SECTION_MEDIA_CONNECTION,
                _SECTION_MEDIA_COMMANDS,
                _SECTION_MEDIA_SOURCES,
            ):
                user_input.update(user_input.pop(section_key, {}))
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            user_input[CONF_POWER_SENSOR] = (
                user_input.get(CONF_POWER_SENSOR) or ""
            ).strip()
            for key in (*MEDIA_COMMAND_DATA_FIELDS, *MEDIA_SOURCE_NAME_FIELDS):
                user_input[key] = (user_input.get(key) or "").strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            if CONF_MEDIA_SOURCE_CYCLE_DELAY in user_input:
                user_input[CONF_MEDIA_SOURCE_CYCLE_DELAY] = float(user_input[CONF_MEDIA_SOURCE_CYCLE_DELAY])
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current = self._current()

        base_schema = vol.Schema(
            {
                vol.Optional("learn_command", default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=_MEDIA_LEARN_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(_SECTION_MEDIA_CONNECTION): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_NAME,
                                default=current.get(CONF_NAME, DEFAULT_MEDIA_NAME),
                            ): TextSelector(),
                            vol.Required(
                                CONF_COMMAND_TOPIC,
                                default=current.get(
                                    CONF_COMMAND_TOPIC, DEFAULT_IRSEND_COMMAND_TOPIC
                                ),
                            ): TextSelector(),
                            vol.Optional(
                                CONF_AVAILABILITY_TOPIC,
                                description={"suggested_value": current.get(CONF_AVAILABILITY_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_LEARN_TOPIC,
                                description={"suggested_value": current.get(CONF_LEARN_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_POWER_SENSOR,
                                description={"suggested_value": current.get(CONF_POWER_SENSOR, "")},
                            ): EntitySelector(EntitySelectorConfig(domain=["binary_sensor", "sensor", "switch"])),
                            vol.Required(
                                CONF_MEDIA_PROTOCOL,
                                default=current.get(
                                    CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL
                                ),
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_BITS,
                                default=int(
                                    current.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS)
                                ),
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=1,
                                    max=256,
                                    step=1,
                                    mode=NumberSelectorMode.BOX,
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_MEDIA_COMMANDS): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_MEDIA_POWER_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_POWER_ON_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_ON_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_POWER_OFF_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_OFF_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_VOLUME_UP_DATA, description={"suggested_value": current.get(CONF_MEDIA_VOLUME_UP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_VOLUME_DOWN_DATA, description={"suggested_value": current.get(CONF_MEDIA_VOLUME_DOWN_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_MUTE_DATA, description={"suggested_value": current.get(CONF_MEDIA_MUTE_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_PLAY_DATA, description={"suggested_value": current.get(CONF_MEDIA_PLAY_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_PAUSE_DATA, description={"suggested_value": current.get(CONF_MEDIA_PAUSE_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_PLAY_PAUSE_DATA, description={"suggested_value": current.get(CONF_MEDIA_PLAY_PAUSE_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_STOP_DATA, description={"suggested_value": current.get(CONF_MEDIA_STOP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_NEXT_DATA, description={"suggested_value": current.get(CONF_MEDIA_NEXT_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_PREVIOUS_DATA, description={"suggested_value": current.get(CONF_MEDIA_PREVIOUS_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_FAST_FORWARD_DATA, description={"suggested_value": current.get(CONF_MEDIA_FAST_FORWARD_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_REWIND_DATA, description={"suggested_value": current.get(CONF_MEDIA_REWIND_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_CHANNEL_UP_DATA, description={"suggested_value": current.get(CONF_MEDIA_CHANNEL_UP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_CHANNEL_DOWN_DATA, description={"suggested_value": current.get(CONF_MEDIA_CHANNEL_DOWN_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_MEDIA_SOURCES): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_MEDIA_SOURCE_MODE,
                                default=current.get(CONF_MEDIA_SOURCE_MODE, DEFAULT_MEDIA_SOURCE_MODE),
                            ): SelectSelector(SelectSelectorConfig(
                                options=SOURCE_MODE_OPTIONS,
                                mode=SelectSelectorMode.DROPDOWN,
                            )),
                            vol.Optional(
                                CONF_MEDIA_SOURCE_CYCLE_DATA,
                                description={"suggested_value": current.get(CONF_MEDIA_SOURCE_CYCLE_DATA, "")},
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_SOURCE_CYCLE_DELAY,
                                default=float(current.get(CONF_MEDIA_SOURCE_CYCLE_DELAY, DEFAULT_MEDIA_SOURCE_CYCLE_DELAY)),
                            ): NumberSelector(NumberSelectorConfig(
                                min=0.1, max=5.0, step=0.1, mode=NumberSelectorMode.BOX
                            )),
                            vol.Optional(CONF_MEDIA_SOURCE_1_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_1_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_1_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_1_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_2_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_2_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_2_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_2_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_3_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_3_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_3_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_3_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_4_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_4_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_4_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_4_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_5_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_5_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_5_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_5_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_6_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_6_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_6_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_6_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="media_player_options",
            data_schema=base_schema,
        )

    async def async_step_remote_options(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Connection and command options for an IR remote."""
        if user_input is not None:
            learn_command = (user_input.pop("learn_command", None) or "").strip()
            if learn_command:
                pending = dict(user_input)
                for section_key in (
                    _SECTION_MEDIA_CONNECTION,
                    _SECTION_MEDIA_COMMANDS,
                    _SECTION_REMOTE_KEYPAD,
                    _SECTION_REMOTE_NAVIGATION,
                    _SECTION_REMOTE_EXTRA,
                    _SECTION_REMOTE_SOURCES,
                ):
                    pending.update(pending.pop(section_key, {}))
                self._pending_input = pending
                self._learn_command = learn_command
                self._device_type_learning = DEVICE_TYPE_REMOTE
                self._learning_task = None
                return await self.async_step_learn_ir()

            for section_key in (
                _SECTION_MEDIA_CONNECTION,
                _SECTION_MEDIA_COMMANDS,
                _SECTION_REMOTE_KEYPAD,
                _SECTION_REMOTE_NAVIGATION,
                _SECTION_REMOTE_EXTRA,
                _SECTION_REMOTE_SOURCES,
            ):
                user_input.update(user_input.pop(section_key, {}))
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            user_input[CONF_POWER_SENSOR] = (
                user_input.get(CONF_POWER_SENSOR) or ""
            ).strip()
            for key in (*REMOTE_COMMAND_DATA_FIELDS, *MEDIA_COMMAND_DATA_FIELDS):
                user_input[key] = (user_input.get(key) or "").strip()
            for key in MEDIA_SOURCE_NAME_FIELDS:
                user_input[key] = (user_input.get(key) or "").strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            if CONF_MEDIA_SOURCE_CYCLE_DELAY in user_input:
                user_input[CONF_MEDIA_SOURCE_CYCLE_DELAY] = float(user_input[CONF_MEDIA_SOURCE_CYCLE_DELAY])
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current = self._current()

        base_schema = vol.Schema(
            {
                vol.Optional("learn_command", default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=_REMOTE_LEARN_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(_SECTION_MEDIA_CONNECTION): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_NAME,
                                default=current.get(CONF_NAME, DEFAULT_REMOTE_NAME),
                            ): TextSelector(),
                            vol.Required(
                                CONF_COMMAND_TOPIC,
                                default=current.get(
                                    CONF_COMMAND_TOPIC, DEFAULT_IRSEND_COMMAND_TOPIC
                                ),
                            ): TextSelector(),
                            vol.Optional(
                                CONF_AVAILABILITY_TOPIC,
                                description={"suggested_value": current.get(CONF_AVAILABILITY_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_LEARN_TOPIC,
                                description={"suggested_value": current.get(CONF_LEARN_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_POWER_SENSOR,
                                description={"suggested_value": current.get(CONF_POWER_SENSOR, "")},
                            ): EntitySelector(EntitySelectorConfig(domain=["binary_sensor", "sensor", "switch"])),
                            vol.Required(
                                CONF_MEDIA_PROTOCOL,
                                default=current.get(
                                    CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL
                                ),
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_BITS,
                                default=int(
                                    current.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS)
                                ),
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=1,
                                    max=256,
                                    step=1,
                                    mode=NumberSelectorMode.BOX,
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_MEDIA_COMMANDS): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_MEDIA_POWER_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_POWER_ON_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_ON_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_POWER_OFF_DATA, description={"suggested_value": current.get(CONF_MEDIA_POWER_OFF_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_VOLUME_UP_DATA, description={"suggested_value": current.get(CONF_MEDIA_VOLUME_UP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_VOLUME_DOWN_DATA, description={"suggested_value": current.get(CONF_MEDIA_VOLUME_DOWN_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_MUTE_DATA, description={"suggested_value": current.get(CONF_MEDIA_MUTE_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_REMOTE_KEYPAD): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_REMOTE_DIGIT_0_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_0_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_1_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_1_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_2_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_2_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_3_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_3_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_4_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_4_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_5_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_5_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_6_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_6_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_7_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_7_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_8_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_8_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DIGIT_9_DATA, description={"suggested_value": current.get(CONF_REMOTE_DIGIT_9_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(_SECTION_REMOTE_NAVIGATION): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_REMOTE_UP_DATA, description={"suggested_value": current.get(CONF_REMOTE_UP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_DOWN_DATA, description={"suggested_value": current.get(CONF_REMOTE_DOWN_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_LEFT_DATA, description={"suggested_value": current.get(CONF_REMOTE_LEFT_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_RIGHT_DATA, description={"suggested_value": current.get(CONF_REMOTE_RIGHT_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_OK_DATA, description={"suggested_value": current.get(CONF_REMOTE_OK_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_BACK_DATA, description={"suggested_value": current.get(CONF_REMOTE_BACK_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_HOME_DATA, description={"suggested_value": current.get(CONF_REMOTE_HOME_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_MENU_DATA, description={"suggested_value": current.get(CONF_REMOTE_MENU_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_SETTINGS_DATA, description={"suggested_value": current.get(CONF_REMOTE_SETTINGS_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_INFO_DATA, description={"suggested_value": current.get(CONF_REMOTE_INFO_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_EXIT_DATA, description={"suggested_value": current.get(CONF_REMOTE_EXIT_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(_SECTION_REMOTE_EXTRA): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_REMOTE_CHANNEL_UP_DATA, description={"suggested_value": current.get(CONF_REMOTE_CHANNEL_UP_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_CHANNEL_DOWN_DATA, description={"suggested_value": current.get(CONF_REMOTE_CHANNEL_DOWN_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_RED_DATA, description={"suggested_value": current.get(CONF_REMOTE_RED_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_GREEN_DATA, description={"suggested_value": current.get(CONF_REMOTE_GREEN_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_YELLOW_DATA, description={"suggested_value": current.get(CONF_REMOTE_YELLOW_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_REMOTE_BLUE_DATA, description={"suggested_value": current.get(CONF_REMOTE_BLUE_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(_SECTION_REMOTE_SOURCES): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_MEDIA_SOURCE_MODE,
                                default=current.get(CONF_MEDIA_SOURCE_MODE, DEFAULT_MEDIA_SOURCE_MODE),
                            ): SelectSelector(SelectSelectorConfig(
                                options=SOURCE_MODE_OPTIONS,
                                mode=SelectSelectorMode.DROPDOWN,
                            )),
                            vol.Optional(
                                CONF_MEDIA_SOURCE_CYCLE_DATA,
                                description={"suggested_value": current.get(CONF_MEDIA_SOURCE_CYCLE_DATA, "")},
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_SOURCE_CYCLE_DELAY,
                                default=float(current.get(CONF_MEDIA_SOURCE_CYCLE_DELAY, DEFAULT_MEDIA_SOURCE_CYCLE_DELAY)),
                            ): NumberSelector(NumberSelectorConfig(
                                min=0.1, max=5.0, step=0.1, mode=NumberSelectorMode.BOX
                            )),
                            vol.Optional(CONF_MEDIA_SOURCE_1_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_1_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_1_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_1_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_2_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_2_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_2_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_2_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_3_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_3_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_3_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_3_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_4_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_4_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_4_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_4_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_5_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_5_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_5_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_5_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_6_NAME, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_6_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_MEDIA_SOURCE_6_DATA, description={"suggested_value": current.get(CONF_MEDIA_SOURCE_6_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="remote_options",
            data_schema=base_schema,
        )

    async def async_step_fan_options(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """All options for an IR fan."""
        if user_input is not None:
            learn_command = (user_input.pop("learn_command", None) or "").strip()
            if learn_command:
                pending = dict(user_input)
                for section_key in (
                    _SECTION_FAN_CONNECTION,
                    _SECTION_FAN_POWER,
                    _SECTION_FAN_SPEEDS,
                    _SECTION_FAN_OSCILLATION,
                ):
                    pending.update(pending.pop(section_key, {}))
                self._pending_input = pending
                self._learn_command = learn_command
                self._device_type_learning = DEVICE_TYPE_FAN
                self._learning_task = None
                return await self.async_step_learn_ir()

            for section_key in (
                _SECTION_FAN_CONNECTION,
                _SECTION_FAN_POWER,
                _SECTION_FAN_SPEEDS,
                _SECTION_FAN_OSCILLATION,
            ):
                user_input.update(user_input.pop(section_key, {}))
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            user_input[CONF_FAN_POWER_SENSOR] = (
                user_input.get(CONF_FAN_POWER_SENSOR) or ""
            ).strip()
            if CONF_MQTT_DELAY in user_input:
                user_input[CONF_MQTT_DELAY] = float(user_input[CONF_MQTT_DELAY])
            for key in FAN_COMMAND_DATA_FIELDS:
                user_input[key] = (user_input.get(key) or "").strip()
            for key in FAN_SPEED_NAME_FIELDS:
                user_input[key] = (user_input.get(key) or "").strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current = self._current()

        base_schema = vol.Schema(
            {
                vol.Optional("learn_command", default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=_FAN_LEARN_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(_SECTION_FAN_CONNECTION): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_NAME,
                                default=current.get(CONF_NAME, DEFAULT_FAN_NAME),
                            ): TextSelector(),
                            vol.Required(
                                CONF_COMMAND_TOPIC,
                                default=current.get(CONF_COMMAND_TOPIC, DEFAULT_IRSEND_COMMAND_TOPIC),
                            ): TextSelector(),
                            vol.Optional(
                                CONF_AVAILABILITY_TOPIC,
                                description={"suggested_value": current.get(CONF_AVAILABILITY_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_LEARN_TOPIC,
                                description={"suggested_value": current.get(CONF_LEARN_TOPIC, "")},
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_PROTOCOL,
                                default=current.get(CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL),
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_BITS,
                                default=int(current.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS)),
                            ): NumberSelector(NumberSelectorConfig(min=1, max=256, step=1, mode=NumberSelectorMode.BOX)),
                            vol.Optional(
                                CONF_MQTT_DELAY,
                                default=float(current.get(CONF_MQTT_DELAY, DEFAULT_MQTT_DELAY)),
                            ): NumberSelector(NumberSelectorConfig(min=0, max=10, step=0.1, mode=NumberSelectorMode.BOX)),
                            vol.Optional(
                                CONF_FAN_POWER_SENSOR,
                                description={"suggested_value": current.get(CONF_FAN_POWER_SENSOR, "")},
                            ): EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_FAN_POWER): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_FAN_POWER_DATA, description={"suggested_value": current.get(CONF_FAN_POWER_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_POWER_ON_DATA, description={"suggested_value": current.get(CONF_FAN_POWER_ON_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_POWER_OFF_DATA, description={"suggested_value": current.get(CONF_FAN_POWER_OFF_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_FAN_SPEEDS): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_FAN_SPEED_1_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_1_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_1_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_1_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_2_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_2_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_2_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_2_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_3_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_3_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_3_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_3_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_4_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_4_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_4_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_4_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_5_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_5_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_5_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_5_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_6_NAME, description={"suggested_value": current.get(CONF_FAN_SPEED_6_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_SPEED_6_DATA, description={"suggested_value": current.get(CONF_FAN_SPEED_6_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(_SECTION_FAN_OSCILLATION): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_FAN_OSCILLATE_DATA, description={"suggested_value": current.get(CONF_FAN_OSCILLATE_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_OSCILLATE_ON_DATA, description={"suggested_value": current.get(CONF_FAN_OSCILLATE_ON_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_OSCILLATE_OFF_DATA, description={"suggested_value": current.get(CONF_FAN_OSCILLATE_OFF_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_DIRECTION_FORWARD_DATA, description={"suggested_value": current.get(CONF_FAN_DIRECTION_FORWARD_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_FAN_DIRECTION_REVERSE_DATA, description={"suggested_value": current.get(CONF_FAN_DIRECTION_REVERSE_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="fan_options",
            data_schema=base_schema,
        )

    async def async_step_humidifier_options(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """All options for an IR humidifier."""
        if user_input is not None:
            learn_command = (user_input.pop("learn_command", None) or "").strip()
            if learn_command:
                pending = dict(user_input)
                for section_key in (
                    _SECTION_HUMIDIFIER_CONNECTION,
                    _SECTION_HUMIDIFIER_POWER,
                    _SECTION_HUMIDIFIER_MODES,
                    _SECTION_HUMIDIFIER_SETTINGS,
                ):
                    pending.update(pending.pop(section_key, {}))
                self._pending_input = pending
                self._learn_command = learn_command
                self._device_type_learning = DEVICE_TYPE_HUMIDIFIER
                self._learning_task = None
                return await self.async_step_learn_ir()

            for section_key in (
                _SECTION_HUMIDIFIER_CONNECTION,
                _SECTION_HUMIDIFIER_POWER,
                _SECTION_HUMIDIFIER_MODES,
                _SECTION_HUMIDIFIER_SETTINGS,
            ):
                user_input.update(user_input.pop(section_key, {}))
            user_input[CONF_AVAILABILITY_TOPIC] = (
                user_input.get(CONF_AVAILABILITY_TOPIC) or ""
            ).strip()
            user_input[CONF_LEARN_TOPIC] = (
                user_input.get(CONF_LEARN_TOPIC) or ""
            ).strip()
            # Optional entity selectors return "" when unset
            user_input[CONF_HUMIDIFIER_HUMIDITY_SENSOR] = (
                user_input.get(CONF_HUMIDIFIER_HUMIDITY_SENSOR) or ""
            ).strip()
            user_input[CONF_HUMIDIFIER_POWER_SENSOR] = (
                user_input.get(CONF_HUMIDIFIER_POWER_SENSOR) or ""
            ).strip()
            if CONF_MQTT_DELAY in user_input:
                user_input[CONF_MQTT_DELAY] = float(user_input[CONF_MQTT_DELAY])
            for key in HUMIDIFIER_COMMAND_DATA_FIELDS:
                user_input[key] = (user_input.get(key) or "").strip()
            for key in HUMIDIFIER_MODE_NAME_FIELDS:
                user_input[key] = (user_input.get(key) or "").strip()
            if CONF_MEDIA_PROTOCOL in user_input:
                user_input[CONF_MEDIA_PROTOCOL] = user_input[
                    CONF_MEDIA_PROTOCOL
                ].strip().upper()
            if CONF_MEDIA_BITS in user_input:
                user_input[CONF_MEDIA_BITS] = int(user_input[CONF_MEDIA_BITS])
            for key in (
                CONF_HUMIDIFIER_MIN_HUMIDITY,
                CONF_HUMIDIFIER_MAX_HUMIDITY,
                CONF_HUMIDIFIER_HUMIDITY_STEP,
            ):
                if key in user_input:
                    user_input[key] = float(user_input[key])
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current = self._current()

        base_schema = vol.Schema(
            {
                vol.Optional("learn_command", default=""): SelectSelector(
                    SelectSelectorConfig(
                        options=_HUMIDIFIER_LEARN_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(_SECTION_HUMIDIFIER_CONNECTION): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_NAME,
                                default=current.get(CONF_NAME, DEFAULT_HUMIDIFIER_NAME),
                            ): TextSelector(),
                            vol.Required(
                                CONF_COMMAND_TOPIC,
                                default=current.get(CONF_COMMAND_TOPIC, DEFAULT_IRSEND_COMMAND_TOPIC),
                            ): TextSelector(),
                            vol.Optional(
                                CONF_AVAILABILITY_TOPIC,
                                description={"suggested_value": current.get(CONF_AVAILABILITY_TOPIC, "")},
                            ): TextSelector(),
                            vol.Optional(
                                CONF_LEARN_TOPIC,
                                description={"suggested_value": current.get(CONF_LEARN_TOPIC, "")},
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_PROTOCOL,
                                default=current.get(CONF_MEDIA_PROTOCOL, DEFAULT_MEDIA_PROTOCOL),
                            ): TextSelector(),
                            vol.Required(
                                CONF_MEDIA_BITS,
                                default=int(current.get(CONF_MEDIA_BITS, DEFAULT_MEDIA_BITS)),
                            ): NumberSelector(NumberSelectorConfig(min=1, max=256, step=1, mode=NumberSelectorMode.BOX)),
                            vol.Optional(
                                CONF_MQTT_DELAY,
                                default=float(current.get(CONF_MQTT_DELAY, DEFAULT_MQTT_DELAY)),
                            ): NumberSelector(NumberSelectorConfig(min=0, max=10, step=0.1, mode=NumberSelectorMode.BOX)),
                            vol.Optional(
                                CONF_HUMIDIFIER_HUMIDITY_SENSOR,
                                description={"suggested_value": current.get(CONF_HUMIDIFIER_HUMIDITY_SENSOR, "")},
                            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                            vol.Optional(
                                CONF_HUMIDIFIER_POWER_SENSOR,
                                description={"suggested_value": current.get(CONF_HUMIDIFIER_POWER_SENSOR, "")},
                            ): EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_HUMIDIFIER_POWER): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_HUMIDIFIER_POWER_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_POWER_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_POWER_ON_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_POWER_ON_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_POWER_OFF_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_POWER_OFF_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_HUMIDIFIER_MODES): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_HUMIDIFIER_MODE_1_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_1_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_1_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_1_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_2_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_2_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_2_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_2_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_3_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_3_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_3_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_3_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_4_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_4_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_4_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_4_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_5_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_5_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_5_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_5_DATA, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_6_NAME, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_6_NAME, "")}): TextSelector(),
                            vol.Optional(CONF_HUMIDIFIER_MODE_6_DATA, description={"suggested_value": current.get(CONF_HUMIDIFIER_MODE_6_DATA, "")}): TextSelector(),
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(_SECTION_HUMIDIFIER_SETTINGS): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_HUMIDIFIER_MIN_HUMIDITY,
                                default=float(current.get(CONF_HUMIDIFIER_MIN_HUMIDITY, DEFAULT_HUMIDIFIER_MIN_HUMIDITY)),
                            ): NumberSelector(NumberSelectorConfig(min=0, max=100, step=1, mode=NumberSelectorMode.BOX)),
                            vol.Required(
                                CONF_HUMIDIFIER_MAX_HUMIDITY,
                                default=float(current.get(CONF_HUMIDIFIER_MAX_HUMIDITY, DEFAULT_HUMIDIFIER_MAX_HUMIDITY)),
                            ): NumberSelector(NumberSelectorConfig(min=0, max=100, step=1, mode=NumberSelectorMode.BOX)),
                            vol.Required(
                                CONF_HUMIDIFIER_HUMIDITY_STEP,
                                default=float(current.get(CONF_HUMIDIFIER_HUMIDITY_STEP, DEFAULT_HUMIDIFIER_HUMIDITY_STEP)),
                            ): NumberSelector(NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)),
                        }
                    ),
                    {"collapsed": False},
                ),
            }
        )

        return self.async_show_form(
            step_id="humidifier_options",
            data_schema=base_schema,
        )

    # ------------------------------------------------------------------
    # IR Learning
    # ------------------------------------------------------------------

    async def async_step_learn_ir(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Show progress while waiting for a Tasmota IrReceived MQTT message."""
        if self._learning_task is None:
            self._learning_task = self.hass.async_create_task(
                self._async_wait_for_ir()
            )

        if not self._learning_task.done():
            command_label = _LEARN_COMMAND_LABEL.get(
                self._learn_command or "", self._learn_command or "unknown"
            )
            return self.async_show_progress(
                step_id="learn_ir",
                progress_action="wait_for_ir",
                progress_task=self._learning_task,
                description_placeholders={"command_name": command_label},
            )

        try:
            result = self._learning_task.result()
            if result:
                self._learned_value = result
        except Exception as err:
            _LOGGER.warning("IR learning task error: %s", err)
        self._learning_task = None

        if self._device_type_learning == DEVICE_TYPE_REMOTE:
            return self.async_show_progress_done(next_step_id="remote_options")
        if self._device_type_learning == DEVICE_TYPE_FAN:
            return self.async_show_progress_done(next_step_id="fan_options")
        if self._device_type_learning == DEVICE_TYPE_HUMIDIFIER:
            return self.async_show_progress_done(next_step_id="humidifier_options")
        return self.async_show_progress_done(next_step_id="media_player_options")

    async def _async_wait_for_ir(self) -> str:
        """Subscribe to the configured learn topic and return the first IrReceived Data hex string."""
        tele_topic = (self._current().get(CONF_LEARN_TOPIC) or "").strip()
        if not tele_topic:
            _LOGGER.warning(
                "IR learning: no receive topic configured. "
                "Set the 'IR Receive Topic' field in Connection & Protocol."
            )
            return ""
        future: asyncio.Future[str] = self.hass.loop.create_future()

        @callback
        def _on_message(msg: mqtt.ReceiveMessage) -> None:
            try:
                payload = json.loads(msg.payload)
                data = payload.get("IrReceived", {}).get("Data", "")
                if data and not future.done():
                    future.set_result(data)
            except Exception:
                pass

        unsub = await mqtt.async_subscribe(self.hass, tele_topic, _on_message)
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            return ""
        finally:
            unsub()
            if not future.done():
                future.cancel()

    # ------------------------------------------------------------------
    # Step 2 — Capabilities
    # ------------------------------------------------------------------

    async def async_step_capabilities(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """AC capability settings: modes, fan, swing, temperature range."""
        if user_input is not None:
            for section_key in (
                _SECTION_HVAC_MODES,
                _SECTION_FAN_SPEEDS,
                _SECTION_SWING_POSITIONS,
            ):
                user_input.update(user_input.pop(section_key, {}))
            self._options.update(user_input)
            return await self.async_step_behavior()

        current = self._current()

        schema = vol.Schema(
            {
                vol.Required(_SECTION_HVAC_MODES): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_MODES_LIST,
                                default=current.get(
                                    CONF_MODES_LIST, DEFAULT_MODES_LIST
                                ),
                            ): SelectSelector(
                                SelectSelectorConfig(
                                    options=HVAC_MODE_OPTIONS,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_FAN_SPEEDS): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_FAN_LIST,
                                default=current.get(CONF_FAN_LIST, DEFAULT_FAN_LIST),
                            ): SelectSelector(
                                SelectSelectorConfig(
                                    options=FAN_MODE_OPTIONS,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(_SECTION_SWING_POSITIONS): section(
                    vol.Schema(
                        {
                            vol.Required(
                                CONF_SWING_LIST,
                                default=current.get(
                                    CONF_SWING_LIST, DEFAULT_SWING_LIST
                                ),
                            ): SelectSelector(
                                SelectSelectorConfig(
                                    options=SWING_MODE_OPTIONS,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Required(
                    CONF_INITIAL_OPERATION_MODE,
                    default=current.get(CONF_INITIAL_OPERATION_MODE, HVACMode.OFF),
                ): SelectSelector(SelectSelectorConfig(options=INITIAL_MODE_OPTIONS)),
                vol.Required(
                    CONF_MIN_TEMP,
                    default=float(current.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)),
                ): NumberSelector(NumberSelectorConfig(min=0, max=35, step=0.5, mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_MAX_TEMP,
                    default=float(current.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)),
                ): NumberSelector(NumberSelectorConfig(min=15, max=50, step=0.5, mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_TARGET_TEMP,
                    default=float(current.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)),
                ): NumberSelector(NumberSelectorConfig(min=0, max=50, step=0.5, mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_PRECISION,
                    default=str(current.get(CONF_PRECISION, DEFAULT_PRECISION)),
                ): SelectSelector(SelectSelectorConfig(
                    options=PRECISION_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN,
                )),
                vol.Required(
                    CONF_TEMP_STEP,
                    default=str(current.get(CONF_TEMP_STEP, PRECISION_WHOLE)),
                ): SelectSelector(SelectSelectorConfig(
                    options=TEMP_STEP_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN,
                )),
                vol.Required(
                    CONF_CELSIUS,
                    default=current.get(CONF_CELSIUS, DEFAULT_CONF_CELSIUS),
                ): SelectSelector(SelectSelectorConfig(
                    options=CELSIUS_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN,
                )),
                vol.Optional(
                    CONF_MODEL,
                    default=current.get(CONF_MODEL, DEFAULT_CONF_MODEL),
                ): TextSelector(),
                vol.Optional(
                    CONF_AWAY_TEMP,
                    default=float(current.get(CONF_AWAY_TEMP) or 0),
                ): NumberSelector(NumberSelectorConfig(min=0, max=35, step=0.5, mode=NumberSelectorMode.BOX)),
            }
        )

        return self.async_show_form(step_id="capabilities", data_schema=schema)

    # ------------------------------------------------------------------
    # Step 3 — Behavior / defaults
    # ------------------------------------------------------------------

    async def async_step_behavior(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Behavioral options."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        current = self._current()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TOGGLE_LIST,
                    default=current.get(CONF_TOGGLE_LIST, []),
                ): SelectSelector(SelectSelectorConfig(
                    options=TOGGLE_OPTIONS,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )),
                vol.Required(CONF_SLEEP, default=current.get(CONF_SLEEP, DEFAULT_CONF_SLEEP)): TextSelector(),
                vol.Required(
                    CONF_SWINGV,
                    default=current.get(CONF_SWINGV) or "",
                ): SelectSelector(SelectSelectorConfig(options=SWINGV_OPTIONS)),
                vol.Required(
                    CONF_SWINGH,
                    default=current.get(CONF_SWINGH) or "",
                ): SelectSelector(SelectSelectorConfig(options=SWINGH_OPTIONS)),
                vol.Required(CONF_KEEP_MODE, default=current.get(CONF_KEEP_MODE, DEFAULT_CONF_KEEP_MODE)): BooleanSelector(),
                vol.Required(CONF_IGNORE_OFF_TEMP, default=current.get(CONF_IGNORE_OFF_TEMP, DEFAULT_IGNORE_OFF_TEMP)): BooleanSelector(),
                vol.Optional(CONF_SPECIAL_MODE, default=current.get(CONF_SPECIAL_MODE, "")): TextSelector(),
            }
        )

        return self.async_show_form(step_id="behavior", data_schema=schema)
