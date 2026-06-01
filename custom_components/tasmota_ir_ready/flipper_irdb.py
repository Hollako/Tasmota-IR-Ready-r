"""Flipper Zero IRDB — fetch and convert IR profiles for Tasmota IR Ready.

Converts Flipper .ir "parsed" signals to Tasmota IRSend hex codes.
Raw signals (timing data) are skipped because they cannot be reliably
converted without knowing the underlying protocol.

Supported protocols: NEC, NECext, Samsung32, SIRC/SONY (12/15/20-bit),
RC5, LG.  Other protocols are skipped gracefully (counted in `skipped`).
"""
from __future__ import annotations

import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

FLIPPER_REPO = "UberGuidoZ/Flipper-IRDB"
GITHUB_API_BASE = f"https://api.github.com/repos/{FLIPPER_REPO}/contents"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{FLIPPER_REPO}/main"

# Top-level IRDB folders we expose in the panel, with their HA device type
CATEGORIES: dict[str, dict[str, str]] = {
    "TV_sets": {"label": "TV Sets", "device_type": "remote"},
    "Audio": {"label": "Audio", "device_type": "media_player"},
    "Projectors": {"label": "Projectors", "device_type": "remote"},
    "AC": {"label": "Air Conditioners", "device_type": "media_player"},
    "Fans": {"label": "Fans", "device_type": "remote"},
    "Misc": {"label": "Misc / Other", "device_type": "remote"},
}

# Flipper protocol name → (Tasmota protocol name, default bits)
PROTOCOL_MAP: dict[str, tuple[str, int]] = {
    "NEC": ("NEC", 32),
    "NECext": ("NEC", 32),
    "Samsung32": ("SAMSUNG", 32),
    "RC5": ("RC5", 12),
    "RC5X": ("RC5X", 13),
    "RC6": ("RC6", 20),
    "SIRC": ("SONY", 12),
    "SIRC15": ("SONY", 15),
    "SIRC20": ("SONY", 20),
    "LG": ("LG", 28),
    "NIKAI": ("NIKAI", 24),
}

# Normalized Flipper command name → Tasmota option field key
COMMAND_NAME_MAP: dict[str, str] = {
    "power": "media_power_data",
    "power_on": "media_power_on_data",
    "power_off": "media_power_off_data",
    "vol_up": "media_volume_up_data",
    "vol_dn": "media_volume_down_data",
    "vol_down": "media_volume_down_data",
    "volume_up": "media_volume_up_data",
    "volume_down": "media_volume_down_data",
    "mute": "media_mute_data",
    "ch_up": "remote_channel_up_data",
    "ch_dn": "remote_channel_down_data",
    "ch_down": "remote_channel_down_data",
    "channel_up": "remote_channel_up_data",
    "channel_down": "remote_channel_down_data",
    "up": "remote_up_data",
    "dpad_up": "remote_up_data",
    "down": "remote_down_data",
    "dpad_down": "remote_down_data",
    "left": "remote_left_data",
    "dpad_left": "remote_left_data",
    "right": "remote_right_data",
    "dpad_right": "remote_right_data",
    "ok": "remote_ok_data",
    "enter": "remote_ok_data",
    "select": "remote_ok_data",
    "center": "remote_ok_data",
    "ok_center": "remote_ok_data",
    "back": "remote_back_data",
    "return": "remote_back_data",
    "home": "remote_home_data",
    "menu": "remote_menu_data",
    "info": "remote_info_data",
    "exit": "remote_exit_data",
    "settings": "remote_settings_data",
    "setup": "remote_settings_data",
    "0": "remote_digit_0_data",
    "1": "remote_digit_1_data",
    "2": "remote_digit_2_data",
    "3": "remote_digit_3_data",
    "4": "remote_digit_4_data",
    "5": "remote_digit_5_data",
    "6": "remote_digit_6_data",
    "7": "remote_digit_7_data",
    "8": "remote_digit_8_data",
    "9": "remote_digit_9_data",
    "red": "remote_red_data",
    "green": "remote_green_data",
    "yellow": "remote_yellow_data",
    "blue": "remote_blue_data",
    "play": "media_play_data",
    "pause": "media_pause_data",
    "play_pause": "media_play_pause_data",
    "stop": "media_stop_data",
    "fast_forward": "media_fast_forward_data",
    "ffw": "media_fast_forward_data",
    "rewind": "media_rewind_data",
    "rw": "media_rewind_data",
    "next": "media_next_data",
    "previous": "media_previous_data",
    "prev": "media_previous_data",
}

# ---------------------------------------------------------------------------
# Byte helpers
# ---------------------------------------------------------------------------

def _parse_hex_bytes(s: str) -> list[int]:
    """Parse a Flipper hex byte string like '00 FF 40 BF' into a list of ints."""
    return [int(b, 16) for b in s.strip().split() if b]


def _hex(value: int) -> str:
    return f"0x{value:X}"


# ---------------------------------------------------------------------------
# Protocol converters
# Each function takes parsed address bytes and command bytes from Flipper and
# returns a Tasmota-compatible hex string, or None on failure.
# ---------------------------------------------------------------------------

def _convert_nec(addr_bytes: list[int], cmd_bytes: list[int], extended: bool) -> str | None:
    """NEC (32-bit).

    Standard: address(8) + ~address(8) + command(8) + ~command(8)
    Extended: address_lo(8) + address_hi(8) + command(8) + ~command(8)
    Flipper stores address/command as little-endian 4-byte fields.
    """
    if not addr_bytes or not cmd_bytes:
        return None
    cmd = cmd_bytes[0]
    if extended:
        # 16-bit address stored little-endian: bytes[0]=lo, bytes[1]=hi
        addr16 = addr_bytes[0] | ((addr_bytes[1] if len(addr_bytes) > 1 else 0) << 8)
        # IRremoteESP8266 encodeNEC extended: (address << 16) | (cmd << 8) | ~cmd
        data = (addr16 << 16) | (cmd << 8) | (~cmd & 0xFF)
    else:
        addr = addr_bytes[0]
        # Standard: addr, ~addr, cmd, ~cmd  (MSB first as a 32-bit integer)
        data = (addr << 24) | ((~addr & 0xFF) << 16) | (cmd << 8) | (~cmd & 0xFF)
    return _hex(data)


def _convert_samsung32(addr_bytes: list[int], cmd_bytes: list[int]) -> str | None:
    """Samsung32 (32-bit): address(8) + address(8) + command(8) + ~command(8)."""
    if not addr_bytes or not cmd_bytes:
        return None
    addr = addr_bytes[0]
    cmd = cmd_bytes[0]
    data = (addr << 24) | (addr << 16) | (cmd << 8) | (~cmd & 0xFF)
    return _hex(data)


def _convert_sony(addr_bytes: list[int], cmd_bytes: list[int], bits: int) -> str | None:
    """SONY/SIRC (12/15/20-bit)."""
    if not addr_bytes or not cmd_bytes:
        return None
    addr = addr_bytes[0]
    cmd = cmd_bytes[0]
    if bits == 12:
        # SIRC-12: 7-bit command + 5-bit address
        data = ((addr & 0x1F) << 7) | (cmd & 0x7F)
    elif bits == 15:
        # SIRC-15: 7-bit command + 8-bit address
        data = ((addr & 0xFF) << 7) | (cmd & 0x7F)
    elif bits == 20:
        # SIRC-20: 7-bit command + 5-bit address + 8-bit extended
        ext = addr_bytes[1] if len(addr_bytes) > 1 else 0
        data = ((ext & 0xFF) << 12) | ((addr & 0x1F) << 7) | (cmd & 0x7F)
    else:
        return None
    return _hex(data)


def _convert_rc5(addr_bytes: list[int], cmd_bytes: list[int]) -> str | None:
    """RC5 (12-bit): toggle(1) + address(5) + command(6).  Toggle set to 0."""
    if not addr_bytes or not cmd_bytes:
        return None
    addr = addr_bytes[0] & 0x1F
    cmd = cmd_bytes[0] & 0x3F
    data = (addr << 6) | cmd
    return _hex(data)


def _convert_lg(addr_bytes: list[int], cmd_bytes: list[int]) -> str | None:
    """LG (28-bit): address(8) + command(16) + checksum(4)."""
    if not addr_bytes or not cmd_bytes:
        return None
    addr = addr_bytes[0]
    # Command is 16-bit little-endian in Flipper
    cmd = cmd_bytes[0] | ((cmd_bytes[1] if len(cmd_bytes) > 1 else 0) << 8)
    # Checksum: sum of all 4-bit nibbles of the 24 data bits
    checksum = 0
    val = (addr << 16) | cmd
    for _ in range(6):
        checksum = (checksum + (val & 0xF)) & 0xF
        val >>= 4
    data = (addr << 20) | (cmd << 4) | checksum
    return _hex(data)


def _convert_signal(
    protocol: str, address_str: str, command_str: str
) -> tuple[str, str, int] | None:
    """Convert a Flipper parsed signal to (tasmota_protocol, hex_data, bits).

    Returns None if the protocol is unsupported or conversion fails.
    """
    info = PROTOCOL_MAP.get(protocol)
    if not info:
        return None
    tasmota_proto, bits = info

    try:
        addr = _parse_hex_bytes(address_str) if address_str else []
        cmd = _parse_hex_bytes(command_str) if command_str else []
    except ValueError:
        return None

    if protocol == "NEC":
        hex_data = _convert_nec(addr, cmd, extended=False)
    elif protocol == "NECext":
        hex_data = _convert_nec(addr, cmd, extended=True)
    elif protocol == "Samsung32":
        hex_data = _convert_samsung32(addr, cmd)
    elif protocol in ("SIRC", "SIRC15", "SIRC20"):
        hex_data = _convert_sony(addr, cmd, bits)
    elif protocol == "RC5":
        hex_data = _convert_rc5(addr, cmd)
    elif protocol == "LG":
        hex_data = _convert_lg(addr, cmd)
    else:
        return None

    if not hex_data:
        return None
    return (tasmota_proto, hex_data, bits)


# ---------------------------------------------------------------------------
# .ir file parser
# ---------------------------------------------------------------------------

def parse_flipper_ir(content: str) -> list[dict[str, str]]:
    """Parse Flipper .ir file content into a list of signal dicts."""
    signals: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for raw in content.splitlines():
        line = raw.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("Filetype:")
            or line.startswith("Version:")
        ):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "name":
            if current.get("name"):
                signals.append(current)
            current = {"name": v}
        else:
            current[k] = v

    if current.get("name"):
        signals.append(current)

    return signals


# ---------------------------------------------------------------------------
# Profile converter
# ---------------------------------------------------------------------------

def convert_to_profile(
    signals: list[dict[str, str]],
    title: str,
    brand: str,
    device_type: str,
) -> dict[str, Any]:
    """Convert parsed Flipper signals into a Tasmota IR Ready profile dict."""
    options: dict[str, Any] = {"device_type": device_type}
    extra_commands: list[dict[str, str]] = []
    detected_proto: str | None = None
    detected_bits: int | None = None
    converted = 0
    skipped = 0

    for sig in signals:
        if sig.get("type") != "parsed":
            skipped += 1
            continue

        result = _convert_signal(
            sig.get("protocol", ""),
            sig.get("address", ""),
            sig.get("command", ""),
        )
        if not result:
            skipped += 1
            continue

        tasmota_proto, hex_data, bits = result
        converted += 1

        if detected_proto is None:
            detected_proto = tasmota_proto
            detected_bits = bits

        # Normalize command name for field mapping
        name_norm = re.sub(r"[\s\-]+", "_", sig["name"]).lower()
        field_key = COMMAND_NAME_MAP.get(name_norm)

        if field_key:
            options[field_key] = hex_data
        else:
            extra_commands.append({"name": name_norm, "data": hex_data})

    options["media_protocol"] = detected_proto or "NEC"
    options["media_bits"] = detected_bits or 32
    if extra_commands:
        options["remote_extra_commands"] = extra_commands

    return {
        "title": title,
        "brand": brand,
        "model": "",
        "converted": converted,
        "skipped": skipped,
        "options": options,
    }


# ---------------------------------------------------------------------------
# GitHub fetchers
# ---------------------------------------------------------------------------

async def browse_path(session: Any, path: str = "") -> list[dict[str, str]]:
    """List dirs/.ir files at a Flipper IRDB path via the GitHub API."""
    url = f"{GITHUB_API_BASE}/{path}" if path else GITHUB_API_BASE
    async with session.get(
        url, headers={"Accept": "application/vnd.github.v3+json"}
    ) as resp:
        resp.raise_for_status()
        items = await resp.json()

    result: list[dict[str, str]] = []
    for item in items if isinstance(items, list) else []:
        name: str = item.get("name", "")
        if not name or name.startswith("."):
            continue
        itype: str = item.get("type", "")
        ipath: str = item.get("path", "")
        if itype == "dir":
            result.append({"name": name, "path": ipath, "type": "dir"})
        elif itype == "file" and name.lower().endswith(".ir"):
            result.append({"name": name[:-3].replace("_", " "), "path": ipath, "type": "file"})

    return sorted(result, key=lambda x: x["name"].lower())


async def fetch_and_convert(
    session: Any, path: str, device_type: str = "remote"
) -> dict[str, Any]:
    """Fetch a .ir file from raw GitHub and return a converted Tasmota profile."""
    url = f"{GITHUB_RAW_BASE}/{path}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        content = await resp.text()

    parts = path.split("/")
    filename = parts[-1].replace(".ir", "").replace("_", " ")
    brand = parts[-2].replace("_", " ") if len(parts) >= 2 else ""
    title = f"{brand} {filename}".strip()

    signals = parse_flipper_ir(content)
    return convert_to_profile(signals, title, brand, device_type)
