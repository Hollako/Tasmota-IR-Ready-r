"""Provides the constants needed for component."""

from homeassistant.components.climate.const import HVACMode

# States
STATE_AUTO = "auto"
STATE_COOL = "cool"
STATE_DRY = "dry"
STATE_FAN_ONLY = "fan_only"
STATE_HEAT = "heat"

# Fan speeds
HVAC_FAN_AUTO = "auto"
HVAC_FAN_MIN = "min"
HVAC_FAN_MEDIUM = "medium"
HVAC_FAN_MAX = "max"

# Some devices have "auto" and "fan_only" changed
HVAC_MODE_AUTO_FAN = "auto_fan_only"

# Some devices have "fan_only" and "auto" changed
HVAC_MODE_FAN_AUTO = "fan_only_auto"

# Some devices say max,but it is high, and auto which is max
HVAC_FAN_MAX_HIGH = "max_high"
HVAC_FAN_AUTO_MAX = "auto_max"

# HVAC mode list
HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.HEAT_COOL,
    HVACMode.AUTO,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVAC_MODE_AUTO_FAN,
    HVAC_MODE_FAN_AUTO,
]

# Platform specific config entry names
CONF_EXCLUSIVE_GROUP_VENDOR = "exclusive_group_vendor"
CONF_VENDOR = "vendor"
CONF_PROTOCOL = "protocol"  # Soon to be deprecated
CONF_COMMAND_TOPIC = "command_topic"
CONF_STATE_TOPIC = "state_topic"
CONF_AVAILABILITY_TOPIC = "availability_topic"
CONF_TEMP_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_MQTT_DELAY = "mqtt_delay"
CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"
CONF_TARGET_TEMP = "target_temp"
CONF_INITIAL_OPERATION_MODE = "initial_operation_mode"
CONF_AWAY_TEMP = "away_temp"
CONF_PRECISION = "precision"
CONF_TEMP_STEP = "temp_step"
CONF_MODES_LIST = "supported_modes"
CONF_FAN_LIST = "supported_fan_speeds"
CONF_SWING_LIST = "supported_swing_list"
CONF_QUIET = "default_quiet_mode"
CONF_TURBO = "default_turbo_mode"
CONF_ECONO = "default_econo_mode"
CONF_MODEL = "hvac_model"
CONF_CELSIUS = "celsius_mode"
CONF_LIGHT = "default_light_mode"
CONF_FILTER = "default_filter_mode"
CONF_CLEAN = "default_clean_mode"
CONF_BEEP = "default_beep_mode"
CONF_SLEEP = "default_sleep_mode"
CONF_KEEP_MODE = "keep_mode_when_off"
CONF_SWINGV = "default_swingv"
CONF_SWINGH = "default_swingh"
CONF_TOGGLE_LIST = "toggle_list"
CONF_IGNORE_OFF_TEMP = "ignore_off_temp"
CONF_SPECIAL_MODE = "special_mode"
CONF_DEVICE_TYPE = "device_type"
CONF_MEDIA_PROTOCOL = "media_protocol"
CONF_MEDIA_BITS = "media_bits"
CONF_MEDIA_POWER_DATA = "media_power_data"
CONF_MEDIA_POWER_ON_DATA = "media_power_on_data"
CONF_MEDIA_POWER_OFF_DATA = "media_power_off_data"
CONF_MEDIA_VOLUME_UP_DATA = "media_volume_up_data"
CONF_MEDIA_VOLUME_DOWN_DATA = "media_volume_down_data"
CONF_MEDIA_MUTE_DATA = "media_mute_data"
CONF_MEDIA_PLAY_DATA = "media_play_data"
CONF_MEDIA_PAUSE_DATA = "media_pause_data"
CONF_MEDIA_PLAY_PAUSE_DATA = "media_play_pause_data"
CONF_MEDIA_STOP_DATA = "media_stop_data"
CONF_MEDIA_NEXT_DATA = "media_next_data"
CONF_MEDIA_PREVIOUS_DATA = "media_previous_data"
CONF_MEDIA_FAST_FORWARD_DATA = "media_fast_forward_data"
CONF_MEDIA_REWIND_DATA = "media_rewind_data"
CONF_MEDIA_CHANNEL_UP_DATA = "media_channel_up_data"
CONF_MEDIA_CHANNEL_DOWN_DATA = "media_channel_down_data"
CONF_MEDIA_SOURCE_1_NAME = "media_source_1_name"
CONF_MEDIA_SOURCE_1_DATA = "media_source_1_data"
CONF_MEDIA_SOURCE_2_NAME = "media_source_2_name"
CONF_MEDIA_SOURCE_2_DATA = "media_source_2_data"
CONF_MEDIA_SOURCE_3_NAME = "media_source_3_name"
CONF_MEDIA_SOURCE_3_DATA = "media_source_3_data"
CONF_MEDIA_SOURCE_4_NAME = "media_source_4_name"
CONF_MEDIA_SOURCE_4_DATA = "media_source_4_data"
CONF_MEDIA_SOURCE_5_NAME = "media_source_5_name"
CONF_MEDIA_SOURCE_5_DATA = "media_source_5_data"
CONF_MEDIA_SOURCE_6_NAME = "media_source_6_name"
CONF_MEDIA_SOURCE_6_DATA = "media_source_6_data"
CONF_REMOTE_DIGIT_0_DATA = "remote_digit_0_data"
CONF_REMOTE_DIGIT_1_DATA = "remote_digit_1_data"
CONF_REMOTE_DIGIT_2_DATA = "remote_digit_2_data"
CONF_REMOTE_DIGIT_3_DATA = "remote_digit_3_data"
CONF_REMOTE_DIGIT_4_DATA = "remote_digit_4_data"
CONF_REMOTE_DIGIT_5_DATA = "remote_digit_5_data"
CONF_REMOTE_DIGIT_6_DATA = "remote_digit_6_data"
CONF_REMOTE_DIGIT_7_DATA = "remote_digit_7_data"
CONF_REMOTE_DIGIT_8_DATA = "remote_digit_8_data"
CONF_REMOTE_DIGIT_9_DATA = "remote_digit_9_data"
CONF_REMOTE_UP_DATA = "remote_up_data"
CONF_REMOTE_DOWN_DATA = "remote_down_data"
CONF_REMOTE_LEFT_DATA = "remote_left_data"
CONF_REMOTE_RIGHT_DATA = "remote_right_data"
CONF_REMOTE_OK_DATA = "remote_ok_data"
CONF_REMOTE_BACK_DATA = "remote_back_data"
CONF_REMOTE_HOME_DATA = "remote_home_data"
CONF_REMOTE_MENU_DATA = "remote_menu_data"
CONF_REMOTE_SETTINGS_DATA = "remote_settings_data"
CONF_REMOTE_INFO_DATA = "remote_info_data"
CONF_REMOTE_EXIT_DATA = "remote_exit_data"
CONF_REMOTE_CHANNEL_UP_DATA = "remote_channel_up_data"
CONF_REMOTE_CHANNEL_DOWN_DATA = "remote_channel_down_data"
CONF_REMOTE_RED_DATA = "remote_red_data"
CONF_REMOTE_GREEN_DATA = "remote_green_data"
CONF_REMOTE_YELLOW_DATA = "remote_yellow_data"
CONF_REMOTE_BLUE_DATA = "remote_blue_data"
CONF_LEARN_TOPIC = "learn_topic"
CONF_MEDIA_SOURCE_MODE = "media_source_mode"
CONF_MEDIA_SOURCE_CYCLE_DATA = "media_source_cycle_data"
CONF_MEDIA_SOURCE_CYCLE_DELAY = "media_source_cycle_delay"

SOURCE_MODE_DIRECT = "direct"
SOURCE_MODE_CYCLE = "cycle"

# Fan entity constants
CONF_FAN_POWER_DATA = "fan_power_data"
CONF_FAN_POWER_ON_DATA = "fan_power_on_data"
CONF_FAN_POWER_OFF_DATA = "fan_power_off_data"
CONF_FAN_SPEED_1_NAME = "fan_speed_1_name"
CONF_FAN_SPEED_1_DATA = "fan_speed_1_data"
CONF_FAN_SPEED_2_NAME = "fan_speed_2_name"
CONF_FAN_SPEED_2_DATA = "fan_speed_2_data"
CONF_FAN_SPEED_3_NAME = "fan_speed_3_name"
CONF_FAN_SPEED_3_DATA = "fan_speed_3_data"
CONF_FAN_SPEED_4_NAME = "fan_speed_4_name"
CONF_FAN_SPEED_4_DATA = "fan_speed_4_data"
CONF_FAN_SPEED_5_NAME = "fan_speed_5_name"
CONF_FAN_SPEED_5_DATA = "fan_speed_5_data"
CONF_FAN_SPEED_6_NAME = "fan_speed_6_name"
CONF_FAN_SPEED_6_DATA = "fan_speed_6_data"
CONF_FAN_OSCILLATE_DATA = "fan_oscillate_data"
CONF_FAN_OSCILLATE_ON_DATA = "fan_oscillate_on_data"
CONF_FAN_OSCILLATE_OFF_DATA = "fan_oscillate_off_data"
CONF_FAN_DIRECTION_FORWARD_DATA = "fan_direction_forward_data"
CONF_FAN_DIRECTION_REVERSE_DATA = "fan_direction_reverse_data"
CONF_FAN_POWER_SENSOR = "fan_power_sensor"

# Humidifier entity constants
CONF_HUMIDIFIER_POWER_DATA = "humidifier_power_data"
CONF_HUMIDIFIER_POWER_ON_DATA = "humidifier_power_on_data"
CONF_HUMIDIFIER_POWER_OFF_DATA = "humidifier_power_off_data"
CONF_HUMIDIFIER_MODE_1_NAME = "humidifier_mode_1_name"
CONF_HUMIDIFIER_MODE_1_DATA = "humidifier_mode_1_data"
CONF_HUMIDIFIER_MODE_2_NAME = "humidifier_mode_2_name"
CONF_HUMIDIFIER_MODE_2_DATA = "humidifier_mode_2_data"
CONF_HUMIDIFIER_MODE_3_NAME = "humidifier_mode_3_name"
CONF_HUMIDIFIER_MODE_3_DATA = "humidifier_mode_3_data"
CONF_HUMIDIFIER_MODE_4_NAME = "humidifier_mode_4_name"
CONF_HUMIDIFIER_MODE_4_DATA = "humidifier_mode_4_data"
CONF_HUMIDIFIER_MODE_5_NAME = "humidifier_mode_5_name"
CONF_HUMIDIFIER_MODE_5_DATA = "humidifier_mode_5_data"
CONF_HUMIDIFIER_MODE_6_NAME = "humidifier_mode_6_name"
CONF_HUMIDIFIER_MODE_6_DATA = "humidifier_mode_6_data"
CONF_HUMIDIFIER_HUMIDITY_SENSOR = "humidifier_humidity_sensor"
CONF_HUMIDIFIER_MIN_HUMIDITY = "humidifier_min_humidity"
CONF_HUMIDIFIER_MAX_HUMIDITY = "humidifier_max_humidity"
CONF_HUMIDIFIER_HUMIDITY_STEP = "humidifier_humidity_step"
CONF_HUMIDIFIER_POWER_SENSOR = "humidifier_power_sensor"

# Platform specific default values
DEFAULT_NAME = "IR AirConditioner"
DEFAULT_MEDIA_NAME = "IR Media Player"
DEFAULT_REMOTE_NAME = "IR Remote"
DEFAULT_FAN_NAME = "IR Fan"
DEFAULT_HUMIDIFIER_NAME = "IR Humidifier"
DEFAULT_HUMIDIFIER_MIN_HUMIDITY = 30
DEFAULT_HUMIDIFIER_MAX_HUMIDITY = 80
DEFAULT_HUMIDIFIER_HUMIDITY_STEP = 5
DEFAULT_STATE_TOPIC = "state"
DEFAULT_COMMAND_TOPIC = "topic"
DEFAULT_IRSEND_COMMAND_TOPIC = "cmnd/tasmota_ir/IRSend"
DEFAULT_MEDIA_PROTOCOL = "NEC"
DEFAULT_MEDIA_BITS = 32
DEFAULT_MEDIA_SOURCE_MODE = SOURCE_MODE_DIRECT
DEFAULT_MEDIA_SOURCE_CYCLE_DELAY = 0.5
DEFAULT_MQTT_DELAY = 0
DEFAULT_TARGET_TEMP = 26
DEFAULT_MIN_TEMP = 16
DEFAULT_MAX_TEMP = 32
DEFAULT_PRECISION = 1
DEFAULT_FAN_LIST = [HVAC_FAN_AUTO_MAX, HVAC_FAN_MAX_HIGH, HVAC_FAN_MEDIUM, HVAC_FAN_MIN]
DEFAULT_CONF_QUIET = "off"
DEFAULT_CONF_TURBO = "off"
DEFAULT_CONF_ECONO = "off"
DEFAULT_CONF_MODEL = "-1"
DEFAULT_CONF_CELSIUS = "on"
DEFAULT_CONF_LIGHT = "off"
DEFAULT_CONF_FILTER = "off"
DEFAULT_CONF_CLEAN = "off"
DEFAULT_CONF_BEEP = "off"
DEFAULT_CONF_SLEEP = "-1"
DEFAULT_CONF_KEEP_MODE = False
DEFAULT_STATE_MODE = "SendStore"
DEFAULT_IGNORE_OFF_TEMP = False

ATTR_NAME = "name"
ATTR_VALUE = "value"

DATA_KEY = "tasmota_ir_ready.climate"
DATA_MEDIA_KEY = "tasmota_ir_ready.media_player"
DATA_REMOTE_KEY = "tasmota_ir_ready.remote"
DATA_FAN_KEY = "tasmota_ir_ready.fan"
DATA_HUMIDIFIER_KEY = "tasmota_ir_ready.humidifier"
DOMAIN = "tasmota_ir_ready"

DEVICE_TYPE_CLIMATE = "climate"
DEVICE_TYPE_MEDIA_PLAYER = "media_player"
DEVICE_TYPE_REMOTE = "remote"
DEVICE_TYPE_FAN = "fan"
DEVICE_TYPE_HUMIDIFIER = "humidifier"
DEVICE_TYPE_HUB = "hub"

ATTR_ECONO = "econo"
ATTR_TURBO = "turbo"
ATTR_QUIET = "quiet"
ATTR_LIGHT = "light"
ATTR_FILTERS = "filters"
ATTR_CLEAN = "clean"
ATTR_BEEP = "beep"
ATTR_SLEEP = "sleep"
ATTR_LAST_ON_MODE = "last_on_mode"
ATTR_SWINGV = "swingv"
ATTR_SWINGH = "swingh"
ATTR_FIX_SWINGV = "fix_swingv"
ATTR_FIX_SWINGH = "fix_swingh"
ATTR_STATE_MODE = "state_mode"

SERVICE_ECONO_MODE = "set_econo"
SERVICE_TURBO_MODE = "set_turbo"
SERVICE_QUIET_MODE = "set_quiet"
SERVICE_LIGHT_MODE = "set_light"
SERVICE_FILTERS_MODE = "set_filters"
SERVICE_CLEAN_MODE = "set_clean"
SERVICE_BEEP_MODE = "set_beep"
SERVICE_SLEEP_MODE = "set_sleep"
SERVICE_SET_SWINGV = "set_swingv"
SERVICE_SET_SWINGH = "set_swingh"

# Map attributes to properties of the state object
ATTRIBUTES_IRHVAC = {
    ATTR_ECONO: "econo",
    ATTR_TURBO: "turbo",
    ATTR_QUIET: "quiet",
    ATTR_LIGHT: "light",
    ATTR_FILTERS: "filter",
    ATTR_CLEAN: "clean",
    ATTR_BEEP: "beep",
    ATTR_SLEEP: "sleep",
    ATTR_LAST_ON_MODE: "last_on_mode",
    ATTR_SWINGV: "swingv",
    ATTR_SWINGH: "swingh",
    ATTR_FIX_SWINGV: "fix_swingv",
    ATTR_FIX_SWINGH: "fix_swingh",
}

ON_OFF_LIST = ["ON", "OFF", "On", "Off", "on", "off"]

SWING_VERTICAL_POSITIONS = ["highest", "high", "middle", "low", "lowest"]
SWING_HORIZONTAL_POSITIONS = [
    "left max",
    "left",
    "horizontal middle",
    "right",
    "right max",
    "wide",
]
SWING_HORIZONTAL_PAYLOAD = {
    "left max": "left max",
    "left": "left",
    "horizontal middle": "middle",
    "right": "right",
    "right max": "right max",
    "wide": "wide",
}
SWING_HORIZONTAL_MODE = {payload: mode for mode, payload in SWING_HORIZONTAL_PAYLOAD.items()}
SWING_MODES = [
    "off",
    "both",
    "vertical",
    "horizontal",
    *SWING_VERTICAL_POSITIONS,
    *SWING_HORIZONTAL_POSITIONS,
]

# Canonical display order for fan speeds in the climate card.
# Any speed not in this list is appended at the end.
FAN_MODES_ORDER = [
    "off",
    "on",
    "min",
    "low",
    "middle",
    "medium",
    "high",
    "max",
    "top",
    "focus",
    "diffuse",
    "auto",
    "max_high",
    "auto_max",
]

DEFAULT_MODES_LIST = [
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.DRY,
    HVAC_MODE_AUTO_FAN,
    HVAC_MODE_FAN_AUTO,
]
DEFAULT_SWING_LIST = ["off", "vertical"]
DEFAULT_INITIAL_OPERATION_MODE = "off"  # HVACMode.OFF

TOGGLE_ALL_LIST = [
    "SwingV",
    "SwingH",
    "Quiet",
    "Turbo",
    "Econo",
    "Light",
    "Filter",
    "Clean",
    "Beep",
    "Sleep",
]

STATE_MODE_LIST = ["StoreOnly", "SendStore"]
