"""The Tasmota IR Ready component."""
import json
from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE_TYPE,
    DATA_FAN_KEY,
    DATA_HUMIDIFIER_KEY,
    DATA_KEY,
    DATA_MEDIA_KEY,
    DATA_REMOTE_KEY,
    DEVICE_TYPE_CLIMATE,
    DEVICE_TYPE_FAN,
    DEVICE_TYPE_HUB,
    DEVICE_TYPE_HUMIDIFIER,
    DEVICE_TYPE_MEDIA_PLAYER,
    DEVICE_TYPE_REMOTE,
    DOMAIN,
)
from .websocket_api import async_register_websocket_commands

_FRONTEND_SETUP_KEY = f"{DOMAIN}_frontend_setup"

# Read version from manifest once at import time for cache-busting URLs.
try:
    _VERSION = json.loads(
        (Path(__file__).parent / "manifest.json").read_text(encoding="utf-8")
    ).get("version", "1")
except Exception:  # noqa: BLE001
    _VERSION = "1"


async def _async_ensure_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Persist *url* in Lovelace resource storage so the card loads on every dashboard.

    Falls back silently when:
    - the lovelace component isn't available / not yet initialised
    - the dashboard is in YAML mode (resources not writable via storage)
    - any other unexpected error

    When the version in the URL changes (manifest bump), the stored entry is
    updated in-place so old cache-busted URLs don't accumulate.
    """
    try:
        from homeassistant.components.lovelace.resources import (  # noqa: PLC0415
            ResourceStorageCollection,
        )
    except ImportError:
        return

    lovelace = hass.data.get("lovelace")
    if not lovelace:
        return
    resources = getattr(lovelace, "resources", None)
    if not isinstance(resources, ResourceStorageCollection):
        return  # YAML-mode dashboard — user manages resources manually

    await resources.async_load()
    base_url = url.split("?")[0]

    existing = [
        item for item in resources.async_items()
        if item.get("url", "").split("?")[0] == base_url
    ]

    # Remove every stale entry (wrong version or duplicates)
    stale = [item for item in existing if item["url"] != url]
    for item in stale:
        await resources.async_delete_item(item["id"])

    # If at least one correct entry remains, nothing more to do
    if len(existing) - len(stale) > 0:
        return

    # No correct entry exists — create it
    await resources.async_create_item({"res_type": "module", "url": url})


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Register static path, sidebar panel, JS resource, and WebSocket API.

    Guarded by hass.data so it runs at most once per HA session regardless of
    how many config entries trigger async_setup_entry.
    """
    if hass.data.get(_FRONTEND_SETUP_KEY):
        return
    hass.data[_FRONTEND_SETUP_KEY] = True

    www_dir = Path(__file__).parent / "www"

    # Register the static HTTP path that serves the www/ directory.
    # Wrapped in try/except because HA raises ValueError if the path has
    # already been registered (e.g. if async_setup ran before an entry reload).
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(f"/{DOMAIN}_panel", str(www_dir), cache_headers=False)
        ])
    except ValueError:
        pass  # Already registered — harmless, keep going.

    # Persist the card URL in Lovelace resource storage so it loads on every
    # dashboard without any manual resource entry.  The ?v= parameter changes
    # with every release so the browser always fetches the latest file.
    card_url = f"/{DOMAIN}_panel/remote_card.js?v={_VERSION}"
    await _async_ensure_lovelace_resource(hass, card_url)

    try:
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="tasmota-ir-ready-panel",
            sidebar_title="IR Manager",
            sidebar_icon="mdi:remote",
            frontend_url_path="tasmota-ir-ready",
            module_url=f"/{DOMAIN}_panel/panel.js?v={_VERSION}",
            embed_iframe=False,
            require_admin=False,
        )
    except Exception:  # noqa: BLE001
        pass  # Panel already registered — harmless.

    async_register_websocket_commands(hass)


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Called once per HA startup when config entries exist for this domain."""
    await _async_setup_frontend(hass)

    # Remove legacy "hub" entries created by older versions of the integration.
    # These were placeholder entries used to force async_setup to run on first
    # install — they are no longer needed and appear as broken/empty entries
    # in the integrations UI.
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_DEVICE_TYPE) == DEVICE_TYPE_HUB:
            hass.async_create_task(
                hass.config_entries.async_remove(entry.entry_id)
            )

    return True


def _entry_platforms(entry: ConfigEntry) -> list[str]:
    """Return the Home Assistant platforms needed for this entry."""
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_CLIMATE)
    if device_type == DEVICE_TYPE_HUB:
        return []
    if device_type == DEVICE_TYPE_MEDIA_PLAYER:
        return ["media_player"]
    if device_type == DEVICE_TYPE_REMOTE:
        return ["remote"]
    if device_type == DEVICE_TYPE_FAN:
        return ["fan"]
    if device_type == DEVICE_TYPE_HUMIDIFIER:
        return ["humidifier"]
    return ["climate", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tasmota IRHVAC from a config entry.

    Also calls _async_setup_frontend so that the sidebar panel and remote card
    JS are registered even on a first-ever install where async_setup may not
    have been reached before this entry was created.

    Climate is set up first so the entity is stored in hass.data before the
    switch platform tries to look it up.
    """
    await _async_setup_frontend(hass)

    for platform in _entry_platforms(entry):
        await hass.config_entries.async_forward_entry_setups(entry, [platform])
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, _entry_platforms(entry)
    )
    if unload_ok:
        hass.data.get(DATA_KEY, {}).pop(entry.entry_id, None)
        hass.data.get(DATA_MEDIA_KEY, {}).pop(entry.entry_id, None)
        hass.data.get(DATA_REMOTE_KEY, {}).pop(entry.entry_id, None)
        hass.data.get(DATA_FAN_KEY, {}).pop(entry.entry_id, None)
        hass.data.get(DATA_HUMIDIFIER_KEY, {}).pop(entry.entry_id, None)
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
