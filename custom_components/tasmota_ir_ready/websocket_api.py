"""WebSocket API for the Tasmota IRHVAC panel."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import mqtt, websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import CONF_TEMP_SENSOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

_BUILTIN_DATABASE_DIR = Path(__file__).parent / "ir_database"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry_to_dict(entry) -> dict[str, Any]:
    """Flatten a config entry into a single options dict."""
    options = {**entry.data, **entry.options}
    if CONF_TEMP_SENSOR not in options and "temp_sensor" in options:
        options[CONF_TEMP_SENSOR] = options["temp_sensor"]
    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "options": options,
    }


def _database_dirs(hass: HomeAssistant) -> dict[str, Path]:
    """Return available IR database roots."""
    return {
        "builtin": _BUILTIN_DATABASE_DIR,
        "custom": Path(hass.config.path(DOMAIN, "ir_database")),
    }


def _safe_database_path(root: Path, relative_path: str) -> Path:
    """Resolve a database file path while keeping it inside the database root."""
    path = (root / relative_path).resolve()
    root = root.resolve()
    if path.suffix.lower() != ".json" or root not in path.parents:
        raise ValueError("Invalid database path")
    return path


def _profile_label(path: Path, data: dict[str, Any]) -> str:
    """Build a friendly label for a database profile."""
    parts = [
        str(data.get("brand") or "").strip(),
        str(data.get("model") or "").strip(),
    ]
    label = " ".join(part for part in parts if part)
    return label or str(data.get("title") or path.stem).replace("_", " ")


def _list_database_files(root: Path, source: str) -> list[dict[str, Any]]:
    """List JSON IR profiles below one database root."""
    if source == "custom":
        root.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        return []

    profiles: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Skipping invalid IR database profile %s: %s", path, exc)
            continue
        options = data.get("options") if isinstance(data.get("options"), dict) else data
        profiles.append({
            "source": source,
            "path": relative_path,
            "label": _profile_label(path, data),
            "device_type": options.get("device_type", data.get("device_type", "")),
            "brand": data.get("brand", ""),
            "model": data.get("model", ""),
        })
    return profiles


def _load_database_file(root: Path, relative_path: str) -> dict[str, Any]:
    """Load one IR database profile."""
    path = _safe_database_path(root, relative_path)
    return json.loads(path.read_text(encoding="utf-8"))


def _slugify_filename(value: str) -> str:
    """Return a conservative JSON filename for a database profile."""
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    slug = "_".join(part for part in slug.split("_") if part)
    return f"{slug or 'ir_profile'}.json"


def _save_database_file(root: Path, filename: str, data: dict[str, Any]) -> str:
    """Save a profile into the custom IR database folder."""
    root.mkdir(parents=True, exist_ok=True)
    path = _safe_database_path(root, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path.relative_to(root).as_posix()


# ---------------------------------------------------------------------------
# get_entries
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_entries"})
@websocket_api.async_response
async def ws_get_entries(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Return all tasmota_ir_ready config entries with their merged options."""
    entries = [
        _entry_to_dict(entry)
        for entry in hass.config_entries.async_entries(DOMAIN)
    ]
    connection.send_result(msg["id"], entries)


# ---------------------------------------------------------------------------
# IR database templates
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list_ir_database"})
@websocket_api.async_response
async def ws_list_ir_database(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Return available IR database profiles."""
    roots = _database_dirs(hass)
    profiles: list[dict[str, Any]] = []
    for source, root in roots.items():
        profiles.extend(await hass.async_add_executor_job(
            _list_database_files, root, source
        ))
    connection.send_result(msg["id"], profiles)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/load_ir_database",
    vol.Required("source"): str,
    vol.Required("path"): str,
})
@websocket_api.async_response
async def ws_load_ir_database(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Load one IR database profile."""
    roots = _database_dirs(hass)
    root = roots.get(msg["source"])
    if root is None:
        connection.send_error(msg["id"], "invalid_source", "Invalid database source")
        return
    try:
        data = await hass.async_add_executor_job(
            _load_database_file, root, msg["path"]
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        connection.send_error(msg["id"], "load_failed", str(exc))
        return
    connection.send_result(msg["id"], data)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_ir_database",
    vol.Required("title"): str,
    vol.Required("options"): dict,
    vol.Optional("filename"): str,
    vol.Optional("brand"): str,
    vol.Optional("model"): str,
})
@websocket_api.async_response
async def ws_save_ir_database(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Save the current editor values as a custom IR database profile."""
    title = msg["title"].strip() or "IR Profile"
    filename = (msg.get("filename") or title).strip()
    if not filename.lower().endswith(".json"):
        filename = _slugify_filename(filename)

    data = {
        "title": title,
        "brand": (msg.get("brand") or "").strip(),
        "model": (msg.get("model") or "").strip(),
        "options": dict(msg["options"]),
    }
    try:
        relative_path = await hass.async_add_executor_job(
            _save_database_file,
            _database_dirs(hass)["custom"],
            filename,
            data,
        )
    except (OSError, ValueError) as exc:
        connection.send_error(msg["id"], "save_failed", str(exc))
        return
    connection.send_result(msg["id"], {
        "success": True,
        "source": "custom",
        "path": relative_path,
    })


# ---------------------------------------------------------------------------
# save_options
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_options",
    vol.Required("entry_id"): str,
    vol.Required("options"): dict,
})
@websocket_api.async_response
async def ws_save_options(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Persist updated options for a config entry and reload it."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if not entry:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    new_opts: dict[str, Any] = dict(msg["options"])
    if "temp_sensor" in new_opts:
        new_opts.setdefault(CONF_TEMP_SENSOR, new_opts.pop("temp_sensor"))

    # Coerce numeric fields that arrive as strings from the panel
    for key in ("media_bits",):
        if key in new_opts:
            try:
                new_opts[key] = int(new_opts[key])
            except (TypeError, ValueError):
                pass
    for key in ("media_source_cycle_delay", "mqtt_delay",
                "min_temp", "max_temp", "target_temp", "away_temp",
                "precision", "temp_step"):
        if key in new_opts:
            try:
                new_opts[key] = float(new_opts[key])
            except (TypeError, ValueError):
                pass
    for key in ("keep_mode", "ignore_off_temp"):
        if key in new_opts and isinstance(new_opts[key], str):
            new_opts[key] = new_opts[key].lower() in ("true", "1", "yes", "on")
    if "media_protocol" in new_opts and new_opts["media_protocol"]:
        new_opts["media_protocol"] = str(new_opts["media_protocol"]).upper()

    # If the name changed, update the entry title so the sidebar reflects it
    new_title = str(new_opts.get("name") or "").strip()
    if new_title and new_title != entry.title:
        hass.config_entries.async_update_entry(entry, title=new_title, options=new_opts)
    else:
        hass.config_entries.async_update_entry(entry, options=new_opts)
    await hass.config_entries.async_reload(msg["entry_id"])
    connection.send_result(msg["id"], {"success": True})


# ---------------------------------------------------------------------------
# learn_ir  — subscribe to MQTT and wait for an IrReceived message
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/learn_ir",
    vol.Required("topic"): str,
})
@websocket_api.async_response
async def ws_learn_ir(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to a Tasmota telemetry topic and return the first IrReceived hex."""
    topic: str = msg["topic"].strip()
    if not topic:
        connection.send_result(msg["id"], {"data": None, "error": "no_topic"})
        return

    future: asyncio.Future[str] = hass.loop.create_future()

    @callback
    def _on_message(mqtt_msg: mqtt.ReceiveMessage) -> None:
        try:
            payload = json.loads(mqtt_msg.payload)
            data = payload.get("IrReceived", {}).get("Data", "")
            if data and not future.done():
                future.set_result(data)
        except Exception:
            pass

    unsub = await mqtt.async_subscribe(hass, topic, _on_message)
    try:
        result = await asyncio.wait_for(future, timeout=30.0)
        connection.send_result(msg["id"], {"data": result})
    except asyncio.TimeoutError:
        connection.send_result(msg["id"], {"data": None, "timeout": True})
    finally:
        unsub()
        if not future.done():
            future.cancel()


# ---------------------------------------------------------------------------
# send_ir  — fire a single IR code for testing
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/send_ir",
    vol.Required("topic"): str,
    vol.Required("protocol"): str,
    vol.Required("bits"): int,
    vol.Required("data"): str,
})
@websocket_api.async_response
async def ws_send_ir(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Publish a single IRSend command via MQTT (for live testing in the panel)."""
    data: str = msg["data"].strip()
    if not data:
        connection.send_error(msg["id"], "no_data", "No IR data provided")
        return
    if not data.lower().startswith("0x"):
        data = f"0x{data}"

    payload = json.dumps({
        "Protocol": msg["protocol"].upper(),
        "Bits": int(msg["bits"]),
        "Data": data,
    })
    await mqtt.async_publish(hass, msg["topic"], payload)
    connection.send_result(msg["id"], {"success": True})


# ---------------------------------------------------------------------------
# delete_entry  — remove a config entry (and its entity) from the panel
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_entry",
    vol.Required("entry_id"): str,
})
@websocket_api.async_response
async def ws_delete_entry(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Remove a tasmota_ir_ready config entry and its associated entity."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if not entry:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return
    await hass.config_entries.async_remove(msg["entry_id"])
    connection.send_result(msg["id"], {"success": True})


# ---------------------------------------------------------------------------
# create_entry  — spin up a new config entry from the panel
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/create_entry",
    vol.Required("device_type"): str,
    vol.Required("name"): str,
    vol.Required("command_topic"): str,
    vol.Optional("vendor"): str,
    vol.Optional("state_topic"): str,
})
@websocket_api.async_response
async def ws_create_entry(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Create a new tasmota_ir_ready config entry from the panel."""
    init_data: dict[str, Any] = {
        "device_type": msg["device_type"],
        "name": msg["name"],
        "command_topic": msg["command_topic"],
    }
    if "vendor" in msg and msg["vendor"]:
        init_data["vendor"] = msg["vendor"]
    if "state_topic" in msg and msg["state_topic"]:
        init_data["state_topic"] = msg["state_topic"]

    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=init_data,
        )
    except Exception as exc:  # noqa: BLE001
        connection.send_error(msg["id"], "create_failed", str(exc))
        return

    flow_type = result.get("type") if isinstance(result, dict) else getattr(result, "type", None)
    if str(flow_type) == "create_entry":
        entry = result.get("result") if isinstance(result, dict) else getattr(result, "result", None)
        connection.send_result(msg["id"], {
            "success": True,
            "entry_id": entry.entry_id if entry else None,
        })
    else:
        reason = result.get("reason", "unknown") if isinstance(result, dict) else getattr(result, "reason", "unknown")
        connection.send_error(msg["id"], "create_failed", f"Flow ended with: {reason}")


# ---------------------------------------------------------------------------
# duplicate_entry  — clone an entry with new connection settings
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/duplicate_entry",
    vol.Required("entry_id"): str,
    vol.Required("overrides"): dict,
})
@websocket_api.async_response
async def ws_duplicate_entry(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Duplicate a config entry with new connection settings."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if not entry:
        connection.send_error(msg["id"], "not_found", "Config entry not found")
        return

    # Merge original options with caller-supplied overrides (new topics, name, etc.)
    all_options: dict[str, Any] = {**entry.data, **entry.options, **msg["overrides"]}

    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=all_options,
        )
    except Exception as exc:  # noqa: BLE001
        connection.send_error(msg["id"], "duplicate_failed", str(exc))
        return

    flow_type = result.get("type") if isinstance(result, dict) else getattr(result, "type", None)
    if str(flow_type) == "create_entry":
        new_entry = result.get("result") if isinstance(result, dict) else getattr(result, "result", None)
        connection.send_result(msg["id"], {
            "success": True,
            "entry_id": new_entry.entry_id if new_entry else None,
        })
    else:
        reason = result.get("reason", "unknown") if isinstance(result, dict) else getattr(result, "reason", "unknown")
        connection.send_error(msg["id"], "duplicate_failed", f"Flow ended with: {reason}")


# ---------------------------------------------------------------------------
# Flipper IRDB — online database browser & converter
# ---------------------------------------------------------------------------

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/flipper_browse",
    vol.Optional("path", default=""): str,
})
@websocket_api.async_response
async def ws_flipper_browse(hass: HomeAssistant, connection, msg: dict) -> None:
    """Browse Flipper IRDB directories and .ir files via the GitHub API.

    path="" lists the real top-level folders of the repo.
    path="TV_sets/Samsung" lists items inside that folder.
    Results are cached in hass.data for the lifetime of the HA session.
    """
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from .flipper_irdb import browse_path

    path: str = msg.get("path", "")

    # Per-path in-memory cache (avoids hammering GitHub API rate limit)
    domain_data = hass.data.setdefault(DOMAIN, {})
    cache: dict[str, list] = domain_data.setdefault("_flipper_cache", {})
    if path in cache:
        connection.send_result(msg["id"], {"items": cache[path]})
        return

    try:
        session = async_get_clientsession(hass)
        items = await browse_path(session, path)
        cache[path] = items
        connection.send_result(msg["id"], {"items": items})
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Flipper IRDB browse failed for %s: %s", path, exc)
        connection.send_error(msg["id"], "browse_failed", str(exc))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/flipper_load",
    vol.Required("path"): str,
    vol.Optional("device_type", default="remote"): str,
})
@websocket_api.async_response
async def ws_flipper_load(hass: HomeAssistant, connection, msg: dict) -> None:
    """Fetch a Flipper IRDB .ir file, convert it and return a Tasmota profile."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from .flipper_irdb import fetch_and_convert

    try:
        session = async_get_clientsession(hass)
        profile = await fetch_and_convert(
            session, msg["path"], msg.get("device_type", "remote")
        )
        connection.send_result(msg["id"], profile)
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Flipper IRDB load failed for %s: %s", msg.get("path"), exc)
        connection.send_error(msg["id"], "load_failed", str(exc))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all WebSocket commands used by the panel."""
    websocket_api.async_register_command(hass, ws_get_entries)
    websocket_api.async_register_command(hass, ws_list_ir_database)
    websocket_api.async_register_command(hass, ws_load_ir_database)
    websocket_api.async_register_command(hass, ws_save_ir_database)
    websocket_api.async_register_command(hass, ws_save_options)
    websocket_api.async_register_command(hass, ws_learn_ir)
    websocket_api.async_register_command(hass, ws_send_ir)
    websocket_api.async_register_command(hass, ws_delete_entry)
    websocket_api.async_register_command(hass, ws_create_entry)
    websocket_api.async_register_command(hass, ws_duplicate_entry)
    websocket_api.async_register_command(hass, ws_flipper_browse)
    websocket_api.async_register_command(hass, ws_flipper_load)
