/**
 * Tasmota IR Ready — Remote Card v3.0
 *
 * Multi-remote Lovelace card: up to 4 remotes shown as tabs in the header.
 * Full backward compat — single `entity:` config still works unchanged.
 *
 * Single-remote config (legacy — still works):
 *   type:          custom:tasmota-ir-ready-remote-card
 *   entity:        remote.living_room_tv
 *   title:         Living Room TV
 *   card_icon:     📺
 *   hidden_groups: [keypad, colors]
 *   extra_buttons:
 *     - label: Netflix
 *       command: netflix
 *       color:  "#e50914"
 *
 * Multi-remote config (new — up to 4 remotes):
 *   type: custom:tasmota-ir-ready-remote-card
 *   remotes:
 *     - entity:        remote.living_room_tv
 *       title:         Living Room TV
 *       card_icon:     📺
 *     - entity:        remote.soundbar
 *       title:         Soundbar
 *       card_icon:     🔊
 *       hidden_groups: [keypad, colors, channels]
 */

const CARD_VERSION = "3.0.1";
const MAX_REMOTES  = 4;

// ── Button group definitions ──────────────────────────────────────────────────

const GROUP_DEFS = [
  {
    id: "power",
    label: "Power",
    layout: "power",
    buttons: [
      { cmd: "power",     label: "POWER" },
      { cmd: "power_on",  label: "ON"    },
      { cmd: "power_off", label: "OFF"   },
    ],
  },
  {
    id: "volume",
    label: "Volume",
    layout: "row",
    buttons: [
      { cmd: "volume_up",   icon: "mdi:volume-high",   label: "VOL +" },
      { cmd: "mute",        icon: "mdi:volume-mute",   label: "MUTE",  cls: "btn-mute" },
      { cmd: "volume_down", icon: "mdi:volume-medium", label: "VOL −" },
    ],
  },
  {
    id: "channels",
    label: "Channels",
    layout: "row",
    buttons: [
      { cmd: "channel_up",   label: "Ch+" },
      { cmd: "channel_down", label: "Ch−" },
    ],
  },
  {
    id: "nav_aux",
    label: "Navigation Aux",
    layout: "row",
    buttons: [
      { cmd: "home",     icon: "mdi:home",                label: "Home"  },
      { cmd: "menu",     icon: "mdi:menu",                label: "Menu"  },
      { cmd: "back",     icon: "mdi:keyboard-backspace",  label: "Back"  },
      { cmd: "exit",     icon: "mdi:close",               label: "Exit"  },
      { cmd: "info",     icon: "mdi:information-outline", label: "Info"  },
      { cmd: "settings", icon: "mdi:cog",                 label: "Setup" },
    ],
  },
  {
    id: "dpad",
    label: "D-Pad",
    layout: "dpad",
    buttons: [
      { cmd: "up",    icon: "mdi:chevron-up",    pos: "top"    },
      { cmd: "left",  icon: "mdi:chevron-left",  pos: "left"   },
      { cmd: "ok",    label: "OK",               pos: "center" },
      { cmd: "right", icon: "mdi:chevron-right", pos: "right"  },
      { cmd: "down",  icon: "mdi:chevron-down",  pos: "bottom" },
    ],
  },
  {
    id: "colors",
    label: "Color Buttons",
    layout: "row",
    buttons: [
      { cmd: "red",    cls: "btn-color btn-red",    title: "Red"    },
      { cmd: "green",  cls: "btn-color btn-green",  title: "Green"  },
      { cmd: "yellow", cls: "btn-color btn-yellow", title: "Yellow" },
      { cmd: "blue",   cls: "btn-color btn-blue",   title: "Blue"   },
    ],
  },
  {
    id: "keypad",
    label: "Number Keypad",
    layout: "keypad",
    buttons: [
      { cmd: "digit_1", label: "1" }, { cmd: "digit_2", label: "2" }, { cmd: "digit_3", label: "3" },
      { cmd: "digit_4", label: "4" }, { cmd: "digit_5", label: "5" }, { cmd: "digit_6", label: "6" },
      { cmd: "digit_7", label: "7" }, { cmd: "digit_8", label: "8" }, { cmd: "digit_9", label: "9" },
      null,                           { cmd: "digit_0", label: "0" }, null,
    ],
  },
];

const KNOWN_CMDS = new Set([
  "power", "power_on", "power_off",
  "volume_up", "volume_down", "mute",
  "channel_up", "channel_down",
  "up", "down", "left", "right", "ok",
  "back", "home", "menu", "info", "exit", "settings",
  "red", "green", "yellow", "blue",
  "digit_0","digit_1","digit_2","digit_3","digit_4",
  "digit_5","digit_6","digit_7","digit_8","digit_9",
  "source_cycle",
]);

const HOLD_CMDS = new Set([
  "volume_up", "volume_down",
  "channel_up", "channel_down",
  "up", "down", "left", "right",
]);

const CARD_ICONS = [
  { label: "TV",            icon: "📺" },
  { label: "Satellite",     icon: "📡" },
  { label: "Monitor",       icon: "🖥"  },
  { label: "Projector",     icon: "🎬" },
  { label: "Game",          icon: "🎮" },
  { label: "Speaker",       icon: "🔊" },
  { label: "Radio",         icon: "📻" },
  { label: "DVD / Blu-ray", icon: "💿" },
  { label: "Recorder",      icon: "📼" },
  { label: "Remote",        icon: "🎛"  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Normalise any card config into the canonical { remotes: [...] } shape. */
function _normaliseConfig(config) {
  if (Array.isArray(config.remotes) && config.remotes.length) {
    return config.remotes.slice(0, MAX_REMOTES).map(r => ({
      entity:        r.entity        || "",
      title:         r.title         || "",
      card_icon:     r.card_icon     || "",
      hidden_groups: r.hidden_groups || [],
      extra_buttons: r.extra_buttons || [],
      dpad_style:    r.dpad_style    || "dpad",
    }));
  }
  // Legacy single-remote format
  return [{
    entity:        config.entity        || "",
    title:         config.title         || "",
    card_icon:     config.card_icon     || "",
    hidden_groups: config.hidden_groups || [],
    extra_buttons: config.extra_buttons || [],
    dpad_style:    config.dpad_style    || "dpad",
  }];
}

/** Render a button icon. MDI names (mdi:*) become <ha-icon> SVGs; anything
 *  else (emoji, text) is wrapped in a plain span. Using ha-icon guarantees
 *  identical rendering on iOS, Android, and desktop. */
function iconHtml(icon) {
  if (!icon) return "";
  if (icon.startsWith("mdi:")) return `<ha-icon icon="${icon}"></ha-icon>`;
  return `<span class="b-icon">${icon}</span>`;
}

// ── Visual card editor ────────────────────────────────────────────────────────

class TasmotaIrRemoteCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config    = {};
    this._hass      = null;
    this._ready     = false;
    this._editTab   = 0;   // which remote slot is being edited
    this._pickers   = {};  // entity picker elements keyed by index
  }

  setConfig(config) {
    const remotes = _normaliseConfig(config);
    this._config  = { ...config, remotes };
    // Clamp editing tab in case a remote was removed
    if (this._editTab >= remotes.length) this._editTab = remotes.length - 1;
    if (this._ready) this._build();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._ready) this._build();
    // Update all mounted entity pickers
    Object.values(this._pickers).forEach(p => { if (p) p.hass = hass; });
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  _build() {
    this._ready  = true;
    this._pickers = {};
    const remotes = this._config.remotes || [];
    const i       = this._editTab;
    const cur     = remotes[i] || {};
    const hidden  = cur.hidden_groups || [];
    const extra   = cur.extra_buttons || [];

    // ── Remote selector tabs ──────────────────────────────────────────────
    const selectorTabs = remotes.map((r, idx) => {
      const lbl = r.title || `Remote ${idx + 1}`;
      return `<button class="ed-rtab${idx === i ? " active" : ""}" data-rtab="${idx}">${this._esc(lbl)}</button>`;
    }).join("");

    const canAdd    = remotes.length < MAX_REMOTES;
    const canRemove = remotes.length > 1;

    this.innerHTML = `
<style>
  .ed { font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  .ed-section { margin-bottom: 20px; }
  .ed-lbl {
    display: block;
    font-size: 0.78em;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--secondary-text-color);
    margin-bottom: 6px;
  }
  .ed-input {
    width: 100%;
    box-sizing: border-box;
    padding: 9px 11px;
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 8px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    font-size: 0.92em;
    outline: none;
    transition: border-color 0.15s;
  }
  .ed-input:focus { border-color: var(--primary-color, #03a9f4); }
  .ed-divider { border: none; border-top: 1px solid var(--divider-color, rgba(0,0,0,0.1)); margin: 18px 0; }
  .ed-check-row {
    display: flex; align-items: center; gap: 10px;
    padding: 5px 0; font-size: 0.9em; cursor: pointer;
  }
  .ed-check-row input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--primary-color, #03a9f4); cursor: pointer; }
  /* Remote tabs */
  .ed-rtabs {
    display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;
  }
  .ed-rtab {
    padding: 5px 14px;
    border: 1.5px solid var(--divider-color, rgba(0,0,0,0.18));
    border-radius: 16px;
    background: none;
    cursor: pointer;
    font-size: 0.83em;
    font-family: inherit;
    color: var(--secondary-text-color);
    transition: all 0.15s;
    white-space: nowrap;
  }
  .ed-rtab.active {
    background: var(--primary-color, #03a9f4);
    border-color: var(--primary-color, #03a9f4);
    color: #fff;
    font-weight: 600;
  }
  .ed-rtab-actions { display: flex; gap: 8px; margin-top: 6px; }
  .ed-btn-add-remote {
    padding: 5px 14px;
    border: 1.5px dashed var(--primary-color, #03a9f4);
    border-radius: 16px;
    background: none;
    cursor: pointer;
    font-size: 0.83em;
    font-family: inherit;
    color: var(--primary-color, #03a9f4);
    transition: background 0.15s;
  }
  .ed-btn-add-remote:hover { background: rgba(3,169,244,0.08); }
  .ed-btn-rm-remote {
    padding: 5px 12px;
    border: 1.5px solid var(--error-color, #f44336);
    border-radius: 16px;
    background: none;
    cursor: pointer;
    font-size: 0.83em;
    font-family: inherit;
    color: var(--error-color, #f44336);
    transition: background 0.15s;
  }
  .ed-btn-rm-remote:hover { background: rgba(244,67,54,0.08); }
  /* Extra buttons */
  .ed-extra-item {
    display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
    background: var(--secondary-background-color, rgba(0,0,0,0.03));
    border-radius: 8px; padding: 6px 8px;
  }
  .ed-extra-item input {
    flex: 1; padding: 6px 8px;
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 6px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    font-size: 0.85em; min-width: 0; outline: none;
  }
  .ed-extra-item input[data-f="color"] {
    flex: 0 0 36px; padding: 2px; height: 32px; cursor: pointer; border-radius: 4px;
  }
  .ed-btn-rm {
    flex: 0 0 auto; background: none; border: none; cursor: pointer;
    color: var(--error-color, #f44336); font-size: 1.1em;
    padding: 2px 6px; border-radius: 4px; line-height: 1;
  }
  .ed-btn-rm:hover { background: rgba(244,67,54,0.1); }
  .ed-btn-add {
    width: 100%; margin-top: 4px; padding: 8px 14px;
    border: 1.5px dashed var(--primary-color, #03a9f4);
    border-radius: 8px; background: none;
    color: var(--primary-color, #03a9f4);
    cursor: pointer; font-size: 0.88em; font-family: inherit;
    transition: background 0.15s;
  }
  .ed-btn-add:hover { background: rgba(3,169,244,0.08); }
  .ed-extra-header {
    display: grid; grid-template-columns: 1fr 1fr 36px 28px;
    gap: 6px; padding: 0 8px 4px;
    font-size: 0.75em; color: var(--secondary-text-color); font-weight: 500;
  }
  .mdc-field { position: relative; width: 100%; margin-top: 4px; }
  .mdc-field input {
    width: 100%; box-sizing: border-box; height: 56px;
    padding: 20px 16px 6px;
    border: 1px solid var(--outline-color, rgba(128,128,128,0.5));
    border-radius: 4px; background: transparent;
    color: var(--primary-text-color); font-size: 1rem;
    font-family: inherit; outline: none; transition: border-color 0.15s;
    caret-color: var(--primary-color, #03a9f4);
  }
  .mdc-field input:focus { border: 2px solid var(--primary-color, #03a9f4); padding: 20px 15px 6px; }
  .mdc-field label {
    position: absolute; left: 16px; top: 50%;
    transform: translateY(-50%); font-size: 1rem;
    color: var(--secondary-text-color); pointer-events: none;
    transition: top 0.15s, font-size 0.15s, color 0.15s, transform 0.15s;
    padding: 0 2px; background: var(--card-background-color, #fff);
  }
  .mdc-field input:focus ~ label,
  .mdc-field input:not(:placeholder-shown) ~ label {
    top: 0; transform: translateY(-50%); font-size: 0.75rem;
    color: var(--primary-color, #03a9f4);
  }
</style>
<div class="ed">

  <!-- Remote selector -->
  <div class="ed-section">
    <label class="ed-lbl">Remotes (${remotes.length} / ${MAX_REMOTES})</label>
    <div class="ed-rtabs">${selectorTabs}</div>
    <div class="ed-rtab-actions">
      ${canAdd    ? `<button class="ed-btn-add-remote" id="btn-add-remote">＋ Add Remote</button>` : ""}
      ${canRemove ? `<button class="ed-btn-rm-remote"  id="btn-rm-remote">✕ Remove Remote ${i + 1}</button>` : ""}
    </div>
  </div>

  <hr class="ed-divider">

  <!-- Per-remote fields -->
  <div class="ed-section">
    <label class="ed-lbl">Entity — Remote ${i + 1}</label>
    <div id="entity-slot"></div>
  </div>

  <div class="ed-section">
    <label class="ed-lbl">Tab Title (optional)</label>
    <input id="title-inp" class="ed-input" type="text"
           placeholder="e.g. Living Room TV"
           value="${this._esc(cur.title || "")}">
  </div>

  <div class="ed-section">
    <label class="ed-lbl">Tab Icon</label>
    <select id="icon-sel" class="ed-input">
      ${CARD_ICONS.map(o => `<option value="${o.icon}" ${cur.card_icon === o.icon ? "selected" : ""}>${o.icon} ${o.label}</option>`).join("")}
    </select>
  </div>

  <hr class="ed-divider">

  <div class="ed-section">
    <label class="ed-lbl">Hidden Button Groups</label>
    ${GROUP_DEFS.map(g => `
      <label class="ed-check-row">
        <input type="checkbox" data-grp="${g.id}" ${hidden.includes(g.id) ? "checked" : ""}>
        <span>${g.label}</span>
      </label>`).join("")}
  </div>

  <div class="ed-section">
    <label class="ed-lbl">Navigation Style</label>
    <label class="ed-check-row">
      <input type="radio" name="dpad-style" value="dpad"     ${cur.dpad_style !== "touchpad" ? "checked" : ""}>
      <span>D-Pad <small style="color:var(--secondary-text-color)">(directional buttons)</small></span>
    </label>
    <label class="ed-check-row">
      <input type="radio" name="dpad-style" value="touchpad" ${cur.dpad_style === "touchpad"  ? "checked" : ""}>
      <span>Touch Pad <small style="color:var(--secondary-text-color)">(swipe gestures)</small></span>
    </label>
  </div>

  <hr class="ed-divider">

  <div class="ed-section">
    <label class="ed-lbl">Extra Buttons</label>
    <div class="ed-extra-header">
      <span>Label</span><span>Command</span><span>Color</span><span></span>
    </div>
    <div id="extra-list">${extra.map((b, bi) => this._extraHtml(b, bi)).join("")}</div>
    <button class="ed-btn-add" id="btn-add-extra">＋ Add Button</button>
  </div>

</div>`;

    // ── Entity picker ──────────────────────────────────────────────────────
    const picker = document.createElement("ha-selector");
    picker.hass     = this._hass;
    picker.label    = "Entity";
    picker.selector = { entity: { domain: "remote" } };
    picker.value    = cur.entity || "";
    picker.addEventListener("value-changed", e => {
      this._updateCur({ entity: e.detail.value });
    });
    this._pickers[i] = picker;
    this.querySelector("#entity-slot").appendChild(picker);

    // ── Remote tab buttons ─────────────────────────────────────────────────
    this.querySelectorAll("[data-rtab]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._editTab = parseInt(btn.dataset.rtab);
        this._build();
      });
    });

    // ── Add / Remove remote ────────────────────────────────────────────────
    this.querySelector("#btn-add-remote")?.addEventListener("click", () => {
      const remotes = [...(this._config.remotes || [])];
      if (remotes.length >= MAX_REMOTES) return;
      remotes.push({ entity: "", title: "", card_icon: "", hidden_groups: [], extra_buttons: [] });
      this._config = { ...this._config, remotes };
      this._editTab = remotes.length - 1;
      this._emit(this._config);
      this._build();
    });

    this.querySelector("#btn-rm-remote")?.addEventListener("click", () => {
      const remotes = [...(this._config.remotes || [])];
      if (remotes.length <= 1) return;
      remotes.splice(this._editTab, 1);
      if (this._editTab >= remotes.length) this._editTab = remotes.length - 1;
      this._config = { ...this._config, remotes };
      this._emit(this._config);
      this._build();
    });

    // ── Title ──────────────────────────────────────────────────────────────
    this.querySelector("#title-inp").addEventListener("change", e => {
      this._updateCur({ title: e.target.value.trim() });
    });

    // ── Icon picker ────────────────────────────────────────────────────────
    this.querySelector("#icon-sel").addEventListener("change", e => {
      this._updateCur({ card_icon: e.target.value });
    });

    // ── Hidden group checkboxes ────────────────────────────────────────────
    this.querySelectorAll("[data-grp]").forEach(cb => {
      cb.addEventListener("change", () => {
        const hidden = [...this.querySelectorAll("[data-grp]:checked")].map(el => el.dataset.grp);
        this._updateCur({ hidden_groups: hidden });
      });
    });

    // ── Navigation style ───────────────────────────────────────────────────
    this.querySelectorAll("[name=dpad-style]").forEach(radio => {
      radio.addEventListener("change", e => {
        if (e.target.checked) this._updateCur({ dpad_style: e.target.value });
      });
    });

    // ── Extra buttons ──────────────────────────────────────────────────────
    this.querySelector("#btn-add-extra").addEventListener("click", () => {
      const cur    = this._config.remotes[this._editTab];
      const extra  = [...(cur.extra_buttons || []), { label: "", command: "", color: "#607d8b" }];
      this._updateCur({ extra_buttons: extra });
      this._rebuildExtra();
    });
    this._bindExtra();
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  /** Update a field in the currently-editing remote and emit. */
  _updateCur(patch) {
    const remotes = [...(this._config.remotes || [])];
    remotes[this._editTab] = { ...remotes[this._editTab], ...patch };
    this._config = { ...this._config, remotes };
    this._emit(this._config);
    // Refresh the remote-selector tab labels if title changed
    if ("title" in patch) {
      this.querySelectorAll("[data-rtab]").forEach(btn => {
        const idx = parseInt(btn.dataset.rtab);
        const r   = remotes[idx];
        btn.textContent = r.title || `Remote ${idx + 1}`;
      });
    }
  }

  _extraHtml(b, i) {
    return `<div class="ed-extra-item" data-i="${i}">
      <input data-f="label"   placeholder="Label"   value="${this._esc(b.label   || "")}" title="Text shown on the button">
      <input data-f="command" placeholder="Command" value="${this._esc(b.command || "")}" title="Command sent to remote.send_command">
      <input data-f="color"   type="color"          value="${b.color || "#607d8b"}"        title="Button background colour">
      <button class="ed-btn-rm" title="Remove">✕</button>
    </div>`;
  }

  _rebuildExtra() {
    const list = this.querySelector("#extra-list");
    if (!list) return;
    const extra = this._config.remotes[this._editTab]?.extra_buttons || [];
    list.innerHTML = extra.map((b, i) => this._extraHtml(b, i)).join("");
    this._bindExtra();
  }

  _bindExtra() {
    this.querySelectorAll(".ed-extra-item").forEach(row => {
      const idx = parseInt(row.dataset.i);
      const update = () => {
        const cur   = this._config.remotes[this._editTab];
        const extra = [...(cur.extra_buttons || [])];
        extra[idx]  = {
          label:   row.querySelector("[data-f=label]").value.trim(),
          command: row.querySelector("[data-f=command]").value.trim(),
          color:   row.querySelector("[data-f=color]").value,
        };
        this._updateCur({ extra_buttons: extra });
      };
      row.querySelectorAll("input").forEach(inp => inp.addEventListener("change", update));
      row.querySelector(".ed-btn-rm").addEventListener("click", () => {
        const cur   = this._config.remotes[this._editTab];
        const extra = [...(cur.extra_buttons || [])];
        extra.splice(idx, 1);
        this._updateCur({ extra_buttons: extra });
        this._rebuildExtra();
      });
    });
  }

  _emit(config) {
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config },
      bubbles: true,
      composed: true,
    }));
  }

  _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}

if (!customElements.get("tasmota-ir-ready-remote-card-editor")) {
  customElements.define("tasmota-ir-ready-remote-card-editor", TasmotaIrRemoteCardEditor);
}

// ── Card element ──────────────────────────────────────────────────────────────

class TasmotaIrRemoteCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass        = null;
    this._config      = null;
    this._remotes     = [];
    this._activeTab   = 0;
    this._lastKey     = null;
    this._holdTimer   = null;
    this._holdInterval= null;
  }

  // ── Lovelace API ──────────────────────────────────────────────────────────

  static getConfigElement() {
    return document.createElement("tasmota-ir-ready-remote-card-editor");
  }

  static getStubConfig() {
    return {
      remotes: [{ entity: "", hidden_groups: [], extra_buttons: [] }],
    };
  }

  setConfig(config) {
    const remotes = _normaliseConfig(config);
    this._config  = config;
    this._remotes = remotes;
    // Keep active tab in valid range
    if (this._activeTab >= remotes.length) this._activeTab = 0;
    // Never throw here — _renderAll shows an inline "entity not found" state
    // for unconfigured / empty-entity cards without triggering HA's red
    // "configuration error" overlay.
    if (this._hass) this._renderAll();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    // Build a cache key covering all remotes' state + active tab + config
    const stateKey = this._remotes.map(r => {
      const st = hass.states[r.entity];
      const pwrSensor = st?.attributes.power_sensor;
      const pwrState  = pwrSensor ? hass.states[pwrSensor]?.state : null;
      return [
        st?.state,
        JSON.stringify(st?.attributes.configured_commands),
        JSON.stringify(st?.attributes.source_list),
        st?.attributes.source_index,
        pwrState,
      ].join("|");
    }).join("§");

    const cfgKey = this._remotes.map(r =>
      JSON.stringify({ h: r.hidden_groups, e: r.extra_buttons, d: r.dpad_style })
    ).join("§");

    const key = `${stateKey}§§${cfgKey}§§${this._activeTab}`;
    if (key !== this._lastKey) {
      this._lastKey = key;
      this._renderAll();
    }
  }

  getCardSize() { return 9; }

  // ── Command sending ───────────────────────────────────────────────────────

  _send(command) {
    if (!this._hass) return;
    const remote = this._remotes[this._activeTab] || this._remotes[0];
    this._hass.callService("remote", "send_command", {
      entity_id: remote.entity,
      command:   String(command),
    });
  }

  // ── Hold-to-repeat ────────────────────────────────────────────────────────

  _startHold(cmd) {
    this._cancelHold();
    this._holdTimer = setTimeout(() => {
      this._holdInterval = setInterval(() => this._send(cmd), 200);
    }, 300);
  }

  _cancelHold() {
    clearTimeout(this._holdTimer);
    clearInterval(this._holdInterval);
    this._holdTimer    = null;
    this._holdInterval = null;
  }

  // ── Main render ───────────────────────────────────────────────────────────

  _renderAll() {
    const remotes   = this._remotes;
    const multiTab  = remotes.length > 1;
    const active    = remotes[this._activeTab] || remotes[0];
    const st        = this._hass?.states[active.entity];
    const offline   = st?.state === "unavailable";

    if (!st) {
      this.shadowRoot.innerHTML = `${this._css()}
        <ha-card>
          ${multiTab ? this._renderTabBar() : ""}
          <div class="card-err">
            Entity not found: <code>${this._esc(active.entity || "(not set)")}</code>
          </div>
        </ha-card>`;
      if (multiTab) this._wireTabBar();
      return;
    }

    const body = this._renderBody(st, active);

    if (multiTab) {
      this.shadowRoot.innerHTML = `${this._css()}
        <ha-card>
          ${this._renderTabBar()}
          <div class="remote-body${offline ? " is-offline" : ""}">${body}</div>
        </ha-card>`;
      this._wireTabBar();
    } else {
      // Single remote — classic header
      const name = active.title
                   || st.attributes.friendly_name
                   || active.entity;
      this.shadowRoot.innerHTML = `${this._css()}
        <ha-card>
          <div class="card-hdr">
            <div class="hdr-left">
              <span class="card-icon">${active.card_icon || "📺"}</span>
              <span class="card-name">${this._esc(name)}</span>
            </div>
            ${offline
              ? `<span class="badge offline">Unavailable</span>`
              : `<span class="badge online">Online</span>`}
          </div>
          <div class="remote-body${offline ? " is-offline" : ""}">${body}</div>
        </ha-card>`;
    }

    this._wireButtons();
    this._wireTouchpad();
  }

  // ── Tab bar ───────────────────────────────────────────────────────────────

  _renderTabBar() {
    const tabs = this._remotes.map((r, i) => {
      const st      = this._hass?.states[r.entity];
      const offline = st?.state === "unavailable";
      const name    = r.title || st?.attributes.friendly_name || r.entity;
      const icon    = r.card_icon || "📺";
      const dot     = offline ? `<span class="tab-dot"></span>` : "";
      return `<button class="tab-btn${i === this._activeTab ? " active" : ""}" data-tab="${i}" title="${this._esc(name)}">
        <span class="tab-icon">${icon}</span>
        <span class="tab-name">${this._esc(name)}${dot}</span>
      </button>`;
    }).join("");
    return `<div class="tab-bar">${tabs}</div>`;
  }

  _wireTabBar() {
    this.shadowRoot.querySelectorAll("[data-tab]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._activeTab = parseInt(btn.dataset.tab);
        this._lastKey   = null; // force re-render
        this._renderAll();
      });
    });
  }

  // ── Body rendering (per remote) ───────────────────────────────────────────

  _renderBody(entity, remoteConfig) {
    const cmds       = entity.attributes.configured_commands || [];
    const sourceList = entity.attributes.source_list         || [];
    const hidden     = new Set(remoteConfig.hidden_groups    || []);
    const extraBtns  = remoteConfig.extra_buttons            || [];

    // Power sensor: null = no sensor (button stays default red)
    //               true = device on (button turns green)
    //               false = device off (button stays red)
    const pwrSensorId = entity.attributes.power_sensor;
    const powerOn = pwrSensorId
      ? this._hass?.states[pwrSensorId]?.state === "on"
      : null;

    const dpadStyle  = remoteConfig.dpad_style || "dpad";
    const extraCmds  = new Set(extraBtns.map(b => b.command).filter(Boolean));
    const customCmds = cmds.filter(c => !KNOWN_CMDS.has(c) && !sourceList.includes(c) && !extraCmds.has(c));

    const VDC_IDS = new Set(["power", "volume", "channels", "dpad"]);
    let body = "";
    let vdcDone = false;
    for (const g of GROUP_DEFS) {
      if (hidden.has(g.id)) continue;
      if (VDC_IDS.has(g.id)) continue;
      if (!vdcDone && g.id !== "power") {
        body += this._renderVdcZone(cmds, hidden, powerOn, dpadStyle);
        vdcDone = true;
      }
      body += this._groupHtml(g, cmds, powerOn);
    }
    if (!vdcDone) body += this._renderVdcZone(cmds, hidden, powerOn, dpadStyle);

    if (sourceList.length) {
      body += this._sectionLabel("Sources");
      body += `<div class="rmt-row src-row">${
        sourceList.map(s =>
          `<button class="rmt-btn btn-src" data-cmd="${this._esc(s)}" title="${this._esc(s)}">${this._esc(s)}</button>`
        ).join("")
      }</div>`;
    }

    if (extraBtns.filter(b => b.label && b.command).length) {
      body += this._sectionLabel("My Buttons");
      body += `<div class="rmt-row">${
        extraBtns
          .filter(b => b.label && b.command)
          .map(b => {
            const style = b.color ? ` style="--btn-extra-bg:${this._esc(b.color)}"` : "";
            return `<button class="rmt-btn btn-extra" data-cmd="${this._esc(b.command)}"${style} title="${this._esc(b.command)}">${this._esc(b.label)}</button>`;
          }).join("")
      }</div>`;
    }

    if (customCmds.length) {
      body += this._sectionLabel("Custom");
      body += `<div class="rmt-row">${
        customCmds.map(c =>
          `<button class="rmt-btn btn-src" data-cmd="${this._esc(c)}" title="${this._esc(c)}">${this._esc(c)}</button>`
        ).join("")
      }</div>`;
    }

    return body;
  }

  _wireButtons() {
    this.shadowRoot.querySelectorAll("[data-cmd]").forEach(el => {
      const cmd = el.dataset.cmd;
      el.addEventListener("click", () => this._send(cmd));
      if (HOLD_CMDS.has(cmd)) {
        el.addEventListener("pointerdown",   () => this._startHold(cmd));
        el.addEventListener("pointerup",     () => this._cancelHold());
        el.addEventListener("pointercancel", () => this._cancelHold());
        el.addEventListener("pointerleave",  () => this._cancelHold());
      }
    });
  }

  _wireTouchpad() {
    const pad = this.shadowRoot.querySelector("[data-touchpad]");
    if (!pad) return;

    const SWIPE_THRESHOLD = 30; // px — less than this is treated as a tap (ok)

    let startX = 0, startY = 0;

    pad.addEventListener("pointerdown", e => {
      startX = e.clientX;
      startY = e.clientY;
      pad.setPointerCapture(e.pointerId);
      pad.classList.add("tp-pressing");
    });

    pad.addEventListener("pointerup", e => {
      pad.classList.remove("tp-pressing");

      const dx   = e.clientX - startX;
      const dy   = e.clientY - startY;
      const dist = Math.hypot(dx, dy);

      let cmd;
      if (dist < SWIPE_THRESHOLD) {
        cmd = "ok";
      } else {
        // Four-quadrant swipe: pick the dominant axis then sign
        const angle = Math.atan2(dy, dx) * 180 / Math.PI; // −180 … 180
        if (angle > -45 && angle <= 45)   cmd = "right";
        else if (angle > 45 && angle <= 135) cmd = "down";
        else if (angle < -45 && angle >= -135) cmd = "up";
        else                               cmd = "left";
      }

      this._send(cmd);

      // Brief ripple to confirm the gesture
      pad.classList.add("tp-flash");
      setTimeout(() => pad.classList.remove("tp-flash"), 220);
    });

    pad.addEventListener("pointercancel", () => {
      pad.classList.remove("tp-pressing");
    });
  }

  // ── Group renderers ───────────────────────────────────────────────────────

  _groupHtml(group, cmds, powerOn = null) {
    const vis    = group.layout === "dpad" || group.layout === "keypad"
      ? group.buttons
      : group.buttons.filter(b => b && cmds.includes(b.cmd));
    const hasAny = group.buttons.some(b => b && cmds.includes(b.cmd));
    if (!hasAny) return "";
    switch (group.layout) {
      case "power":  return this._renderPower(vis.filter(b => b && cmds.includes(b.cmd)), cmds, powerOn);
      case "dpad":   return this._renderDpad(group.buttons, cmds);
      case "keypad": return this._renderKeypad(group.buttons, cmds);
      default:       return this._renderRow(vis.filter(b => b && cmds.includes(b.cmd)));
    }
  }

  _renderPower(vis, cmds = [], powerOn = null) {
    if (!vis.length) return "";
    const hasCycle = cmds.includes("source_cycle");
    const cycleBtn = hasCycle
      ? `<button class="rmt-btn btn-cycle" data-cmd="source_cycle" title="Cycle Input"><ha-icon icon="mdi:import"></ha-icon></button>`
      : "";
    const rowCls   = hasCycle ? "rmt-row pwr-row" : "rmt-row";
    const pwrCls   = "rmt-btn btn-power-icon" + (powerOn === true ? " btn-power-icon--on" : "");
    if (vis.length === 1 && vis[0].cmd === "power") {
      return `<div class="${rowCls}">
        <button class="${pwrCls}" data-cmd="power" title="Power"><ha-icon icon="mdi:power"></ha-icon></button>
        ${cycleBtn}
      </div>`;
    }
    return `<div class="${rowCls}">${
      vis.map(b => `<button class="rmt-btn btn-power" data-cmd="${b.cmd}">${b.label}</button>`).join("")
    }${cycleBtn}</div>`;
  }

  _renderRow(vis) {
    if (!vis.length) return "";
    return `<div class="rmt-row">${
      vis.map(b => {
        const isColor = b.cls && b.cls.includes("btn-color");
        const inner   = isColor ? "" : b.icon
          ? iconHtml(b.icon)
          : `<span class="b-lbl">${b.label || b.cmd}</span>`;
        const cls   = "rmt-btn" + (b.cls ? " " + b.cls : "") + (HOLD_CMDS.has(b.cmd) ? " hold-capable" : "");
        const title = b.title || b.label || b.cmd;
        return `<button class="${cls}" data-cmd="${b.cmd}" title="${title}">${inner}</button>`;
      }).join("")
    }</div>`;
  }

  _renderDpad(allBtns, cmds) {
    const m = {};
    allBtns.forEach(b => { if (b) m[b.pos] = b; });
    const cell = pos => {
      const b = m[pos];
      if (!b || !cmds.includes(b.cmd)) return `<div class="dpad-void"></div>`;
      const extra = (b.cmd === "ok" ? " dpad-ok" : " dpad-arrow") +
        (HOLD_CMDS.has(b.cmd) ? " hold-capable" : "");
      return `<button class="rmt-btn${extra}" data-cmd="${b.cmd}">${b.icon ? iconHtml(b.icon) : b.label}</button>`;
    };
    return `<div class="dpad-wrap">
      <div class="dpad-row">${cell("top")}</div>
      <div class="dpad-row">${cell("left")}${cell("center")}${cell("right")}</div>
      <div class="dpad-row">${cell("bottom")}</div>
    </div>`;
  }

  _renderKeypad(allBtns, cmds) {
    if (!allBtns.some(b => b && cmds.includes(b.cmd))) return "";
    return `<div class="keypad-grid">${
      allBtns.map(b => {
        if (!b || !cmds.includes(b.cmd)) return `<div></div>`;
        return `<button class="rmt-btn kp-btn" data-cmd="${b.cmd}">${b.label}</button>`;
      }).join("")
    }</div>`;
  }

  _renderVdcZone(cmds, hidden, powerOn = null, dpadStyle = "dpad") {
    const powerGrp = GROUP_DEFS.find(g => g.id === "power");
    const volGrp   = GROUP_DEFS.find(g => g.id === "volume");
    const chGrp    = GROUP_DEFS.find(g => g.id === "channels");
    const dpadGrp  = GROUP_DEFS.find(g => g.id === "dpad");

    const hasPower = !hidden.has("power")    && powerGrp?.buttons.some(b => b && cmds.includes(b.cmd));
    const hasVol   = !hidden.has("volume")   && volGrp?.buttons.some(b  => b && cmds.includes(b.cmd));
    const hasCh    = !hidden.has("channels") && chGrp?.buttons.some(b  => b && cmds.includes(b.cmd));
    const hasDpad  = !hidden.has("dpad")     && dpadGrp?.buttons.some(b => b && cmds.includes(b.cmd));
    const hasCycle = cmds.includes("source_cycle");

    if (!hasPower && !hasVol && !hasCh && !hasDpad && !hasCycle) return "";

    const makeColBtns = btns => btns
      .filter(b => b && cmds.includes(b.cmd))
      .map(b => {
        const cls   = "rmt-btn" + (b.cls ? " " + b.cls : "") + (HOLD_CMDS.has(b.cmd) ? " hold-capable" : "");
        const inner = b.icon
          ? iconHtml(b.icon)
          : `<span class="b-lbl">${b.label || b.cmd}</span>`;
        return `<button class="${cls}" data-cmd="${b.cmd}" title="${b.label || b.cmd}">${inner}</button>`;
      }).join("");

    let pwrHtml = "";
    if (hasPower) {
      const btns   = powerGrp.buttons.filter(b => b && cmds.includes(b.cmd));
      const pwrCls = "rmt-btn btn-power-icon" + (powerOn === true ? " btn-power-icon--on" : "");
      pwrHtml = (btns.length === 1 && btns[0].cmd === "power")
        ? `<button class="${pwrCls}" data-cmd="power" title="Power"><ha-icon icon="mdi:power"></ha-icon></button>`
        : btns.map(b => `<button class="rmt-btn btn-power" data-cmd="${b.cmd}">${b.label}</button>`).join("");
    }
    const cycHtml  = hasCycle ? `<button class="rmt-btn btn-cycle" data-cmd="source_cycle" title="Cycle Input"><ha-icon icon="mdi:import"></ha-icon></button>` : "";
    const volHtml  = hasVol  ? makeColBtns(volGrp.buttons)  : "";
    const chHtml   = hasCh   ? makeColBtns(chGrp.buttons)   : "";
    const dpadHtml = hasDpad
      ? (dpadStyle === "touchpad"
          ? this._renderTouchpad(cmds)
          : this._renderDpad(dpadGrp.buttons, cmds))
      : "";

    const hasHeader = hasPower || hasCycle;

    if (!hasHeader) {
      return `<div class="vdc-zone">
        <div class="vdc-col">${volHtml}</div>
        <div class="vdc-center">${dpadHtml}</div>
        <div class="vdc-col">${chHtml}</div>
      </div>`;
    }

    return `<div class="vdc-grid">
      <div class="vdc-g-hdr">${pwrHtml}</div>
      <div></div>
      <div class="vdc-g-hdr">${cycHtml}</div>
      <div class="vdc-g-col">${volHtml}</div>
      <div class="vdc-g-dpad">${dpadHtml}</div>
      <div class="vdc-g-col">${chHtml}</div>
    </div>`;
  }

  _renderTouchpad(cmds) {
    const has = cmd => cmds.includes(cmd);
    return `<div class="touchpad" data-touchpad>
      ${has("up")    ? `<ha-icon icon="mdi:chevron-up"    class="tp-hint tp-hint-top"></ha-icon>`    : ""}
      ${has("left")  ? `<ha-icon icon="mdi:chevron-left"  class="tp-hint tp-hint-left"></ha-icon>`   : ""}
      ${has("ok")    ? `<div class="tp-center-dot"></div>`                                            : ""}
      ${has("right") ? `<ha-icon icon="mdi:chevron-right" class="tp-hint tp-hint-right"></ha-icon>`  : ""}
      ${has("down")  ? `<ha-icon icon="mdi:chevron-down"  class="tp-hint tp-hint-bottom"></ha-icon>` : ""}
    </div>`;
  }

  _sectionLabel(text) {
    return `<div class="section-lbl"><span>${text}</span></div>`;
  }

  _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // ── Styles ────────────────────────────────────────────────────────────────

  _css() {
    return `<style>
:host { display: block; }
ha-card { overflow: hidden; border-radius: 12px; }

/* ── Error ─────────────────────────────────────────────────── */
.card-err {
  padding: 20px 16px;
  color: var(--error-color, #f44336);
  font-size: 0.9em;
}
.card-err code {
  background: rgba(0,0,0,0.06);
  padding: 1px 5px;
  border-radius: 4px;
}

/* ── Single-remote header ──────────────────────────────────── */
.card-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 12px;
  background: var(--secondary-background-color, rgba(120,120,120,0.08));
  color: var(--primary-text-color);
}
.hdr-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.card-icon { font-size: 1.3em; flex-shrink: 0; }
.card-name {
  font-size: 1.3em;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.badge {
  font-size: 0.68em;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 9px;
  border-radius: 10px;
  flex-shrink: 0;
  text-transform: uppercase;
}
.badge.online  { background: rgba(255,255,255,0.2); }
.badge.offline { background: rgba(244,67,54,0.85); }

/* ── Multi-remote tab bar ──────────────────────────────────── */
.tab-bar {
  display: flex;
  background: var(--secondary-background-color, rgba(120,120,120,0.08));
  border-bottom: 2px solid var(--divider-color, rgba(0,0,0,0.08));
  overflow-x: auto;
  scrollbar-width: none;
}
.tab-bar::-webkit-scrollbar { display: none; }
.tab-btn {
  flex: 1;
  min-width: 0;
  padding: 10px 8px 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-family: inherit;
  color: var(--secondary-text-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  transition: color 0.15s, border-color 0.15s;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
  -webkit-user-select: none;
  position: relative;
}
.tab-btn:hover { color: var(--primary-text-color); }
.tab-btn.active {
  color: var(--primary-color, #03a9f4);
  border-bottom-color: var(--primary-color, #03a9f4);
  font-weight: 600;
}
.tab-icon { font-size: 1.25em; line-height: 1; }
.tab-name {
  font-size: 0.72em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 72px;
}
.tab-dot {
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--error-color, #f44336);
  margin-left: 3px;
  vertical-align: middle;
}

/* ── Body ──────────────────────────────────────────────────── */
.remote-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 14px 20px;
}
.remote-body.is-offline {
  pointer-events: none;
  opacity: 0.4;
}

/* ── Generic button ────────────────────────────────────────── */
.rmt-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-width: 60px;
  min-height: 52px;
  padding: 8px 14px;
  border: none;
  border-radius: 10px;
  background: var(--secondary-background-color, rgba(120,120,120,0.08));
  color: var(--primary-text-color);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.88em;
  line-height: 1.2;
  box-shadow: 0 1px 4px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
  transition: background 0.12s, box-shadow 0.12s, transform 0.08s;
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  position: relative;
  overflow: hidden;
}
.rmt-btn:hover {
  background: var(--secondary-background-color, rgba(120,120,120,0.14));
  box-shadow: 0 2px 6px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.06);
}
.rmt-btn:active {
  background: color-mix(in srgb, var(--primary-color, #03a9f4) 30%, transparent) !important;
  color: var(--primary-color, #03a9f4) !important;
  transform: scale(0.87);
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}
.hold-capable::after {
  content: "";
  position: absolute;
  bottom: 4px; left: 50%;
  transform: translateX(-50%);
  width: 14px; height: 2px;
  border-radius: 1px;
  background: var(--primary-color, #03a9f4);
  opacity: 0.4;
}

.b-icon { font-size: 2em; line-height: 1; }
.b-lbl  { font-size: 1em; letter-spacing: 0.01em; }

/* ── Row ───────────────────────────────────────────────────── */
.rmt-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  width: 100%;
}

/* ── VDC zone ──────────────────────────────────────────────── */
.vdc-zone {
  display: flex;
  align-items: stretch;
  justify-content: center;
  gap: 14px;
  width: 100%;
}
.vdc-col {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: space-between;
  gap: 7px;
  min-width: 64px;
}
.vdc-col .rmt-btn { flex: 1; display: flex; width: 100%; min-height: 44px; }
.vdc-center { flex: 0 0 auto; display: flex; align-items: center; justify-content: center; }

/* ── VDC Grid ──────────────────────────────────────────────── */
.vdc-grid {
  display: grid;
  grid-template-columns: 64px auto 64px;
  column-gap: 14px;
  row-gap: 10px;
  justify-content: center;
  width: 100%;
}
.vdc-g-hdr { display: flex; justify-content: center; align-items: center; }
.vdc-g-hdr .btn-cycle { width: 100%; }
.vdc-g-col {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: space-between;
  gap: 7px;
  align-self: stretch;
}
.vdc-g-col .rmt-btn { flex: 1; display: flex; width: 100%; min-height: 44px; }
.vdc-g-dpad { display: flex; align-items: center; justify-content: center; }

/* ── Power icon ────────────────────────────────────────────── */
.vdc-col .btn-power-icon { flex: 0 0 56px; width: 56px !important; align-self: center; }
.btn-power-icon {
  min-width: 56px !important; min-height: 56px !important;
  width: 56px; height: 56px;
  border-radius: 50% !important;
  background: var(--secondary-background-color, rgba(120,120,120,0.08)) !important;
  color: var(--error-color, #e53935) !important;
  box-shadow: 0 2px 8px rgba(229,57,53,0.25);
}
.btn-power-icon ha-icon { --mdc-icon-size: 28px; }
.btn-power-icon--on {
  color: var(--success-color, #43a047) !important;
  box-shadow: 0 2px 8px rgba(67,160,71,0.35);
}

/* ── Power ─────────────────────────────────────────────────── */
.btn-power {
  background: var(--error-color, #e53935) !important;
  color: #fff !important;
  font-weight: 700;
  font-size: 0.92em;
  box-shadow: 0 2px 6px rgba(229,57,53,0.35);
}

/* ── Mute ──────────────────────────────────────────────────── */
.btn-mute {
  background: var(--secondary-background-color, rgba(120,120,120,0.08)) !important;
  color: var(--primary-text-color) !important;
  box-shadow: none;
}

/* ── OK ────────────────────────────────────────────────────── */
.dpad-ok {
  min-width: 62px !important; min-height: 62px !important;
  border-radius: 50% !important;
  background: var(--secondary-background-color, rgba(120,120,120,0.08)) !important;
  color: var(--primary-text-color) !important;
  font-weight: 700; font-size: 0.95em;
  outline: 2.5px solid var(--primary-color, #03a9f4);
  outline-offset: -2px;
  box-shadow: none;
}

/* ── Color circles ─────────────────────────────────────────── */
.btn-color {
  border-radius: 50% !important;
  min-width: 44px !important; min-height: 44px !important;
  width: 44px; height: 44px;
  padding: 0 !important;
  font-size: 1.4em;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.btn-red    { background: #e53935 !important; color: #fff !important; }
.btn-green  { background: #43a047 !important; color: #fff !important; }
.btn-yellow { background: #fdd835 !important; color: #333 !important; }
.btn-blue   { background: #1e88e5 !important; color: #fff !important; }

/* ── D-pad ─────────────────────────────────────────────────── */
.dpad-wrap { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.dpad-row  { display: flex; align-items: center; justify-content: center; gap: 6px; }
.dpad-void { width: 56px; height: 48px; }
.dpad-arrow {
  min-width: 56px !important; min-height: 48px !important;
  font-size: 1.15em; border-radius: 10px !important;
}

/* ── Keypad ────────────────────────────────────────────────── */
.keypad-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
  width: 75%;
  margin: 0 auto;
}
.kp-btn {
  width: 100%; min-height: 50px !important;
  font-size: 1.2em; font-weight: 600; border-radius: 8px !important;
}

/* ── Touch pad ─────────────────────────────────────────────── */
.touchpad {
  position: relative;
  width: 192px;
  height: 168px;
  border-radius: 18px;
  background: var(--secondary-background-color, rgba(120,120,120,0.08));
  box-shadow: 0 1px 4px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.06);
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s;
}
.touchpad.tp-pressing {
  background: var(--secondary-background-color, rgba(120,120,120,0.14));
}
.touchpad.tp-flash {
  background: color-mix(in srgb, var(--primary-color, #03a9f4) 30%, transparent);
  transition: background 0s;
}
.tp-hint {
  position: absolute;
  --mdc-icon-size: 18px;
  opacity: 0.25;
  color: var(--primary-text-color);
}
.tp-hint-top    { top: 10px;    left: 50%; transform: translateX(-50%); }
.tp-hint-bottom { bottom: 10px; left: 50%; transform: translateX(-50%); }
.tp-hint-left   { left: 10px;  top: 50%;  transform: translateY(-50%); }
.tp-hint-right  { right: 10px; top: 50%;  transform: translateY(-50%); }
.tp-center-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--secondary-text-color, #888);
  opacity: 0.35;
}

/* ── Section label ─────────────────────────────────────────── */
.section-lbl {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.section-lbl::before, .section-lbl::after {
  content: ""; flex: 1; height: 1px;
  background: var(--divider-color, rgba(0,0,0,0.1));
}
.section-lbl span {
  font-size: 0.68em;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
  color: var(--secondary-text-color);
  white-space: nowrap;
}

/* ── Source / Custom / Extra buttons ───────────────────────── */
.rmt-btn ha-icon { --mdc-icon-size: 26px; display: flex; }
.btn-src {
  flex: 1 1 auto; min-width: 66px; max-width: 160px;
  font-size: 0.83em; border-radius: 8px !important;
}
.src-row { flex-wrap: wrap; }
.btn-extra {
  flex: 1 1 auto; min-width: 66px; max-width: 160px;
  font-size: 0.83em; border-radius: 8px !important;
  background: var(--btn-extra-bg, var(--secondary-background-color, rgba(120,120,120,0.08))) !important;
  color: #fff !important;
  font-weight: 500;
}
</style>`;
  }
}

// ── Register ──────────────────────────────────────────────────────────────────

if (!customElements.get("tasmota-ir-ready-remote-card")) {
  customElements.define("tasmota-ir-ready-remote-card", TasmotaIrRemoteCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(c => c.type === "tasmota-ir-ready-remote-card")) {
  window.customCards.push({
    type:        "tasmota-ir-ready-remote-card",
    name:        "Tasmota IR Ready Remote",
    description: "Remote-control card for Tasmota IR Ready - up to 4 remotes as tabs, configurable groups, extra buttons, hold-to-repeat.",
    preview:     false,
    documentationURL: "https://github.com/Hollako/Tasmota-IR-Ready",
  });
}

console.info(
  `%c TASMOTA-IR-REMOTE-CARD %c v${CARD_VERSION} `,
  "background:#03a9f4;color:#fff;padding:2px 5px;border-radius:3px 0 0 3px;font-weight:700",
  "background:#e0e0e0;color:#333;padding:2px 5px;border-radius:0 3px 3px 0"
);
