[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Tasmota IR Ready

Home Assistant integration for controlling IR devices via Tasmota-compatible IR transceiver hardware. Supports **air conditioners** (climate), **media players** (TVs, AV receivers), **fans**, **humidifiers**, and **generic IR remotes**.

## Supported Device Types

- **Climate** - Full AC control using Tasmota's `IRHVAC` command with bidirectional state sync
- **Media Player** - TV and AV receiver control via Tasmota's `IRSend` command
- **Fan** - IR-controlled fans with speed presets, oscillation and direction
- **Humidifier** - IR-controlled humidifiers with modes and humidity setpoint tracking
- **Remote** - Generic IR remote with named button commands via `IRSend`

## Hardware

Use a Tasmota-compatible IR transmitter/receiver device that supports the `IRHVAC` and `IRSend` commands.

<p align="center">
  <img src="https://raw.githubusercontent.com/Hollako/Tasmota-IR-Ready/master/images/tasmota_homeassistant_irhub.png?v=2" alt="Tasmota IR with Home Assistant" width="480">
</p>

Tasmota configuration looks like this:

<p align="center">
  <img src="https://raw.githubusercontent.com/Hollako/Tasmota-IR-Ready/master/images/tasmota_config.jpeg" alt="Tasmota configuration" width="360">
</p>

## Installation

### HACS

1. Add this repository as a custom HACS integration repository.
2. Install `Tasmota-IR-Ready` from HACS.
3. Restart Home Assistant.

### Manual

1. Download this repository.
2. Copy `custom_components/tasmota_ir_ready` into your Home Assistant `custom_components` folder.
3. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Tasmota IR Ready**.
4. Choose your **Device Type**: Climate, Media Player, Fan, Humidifier, or Remote.
5. Fill in the required fields for your chosen device type.

After the integration is created, open **Configure** on the integration entry to adjust options.

---

## IR Manager Panel

<p align="center">
  <img src="https://raw.githubusercontent.com/Hollako/Tasmota-IR-Ready/master/images/config_panel.png" alt="IR Manager panel" width="100%">
</p>

The integration adds an **IR Manager** panel to your Home Assistant sidebar. It is the central tool for capturing, testing, and organising IR codes before filling them into your device configuration.

### Learning IR codes

1. Open the IR Manager panel.
2. Select your Tasmota device's telemetry topic (e.g. `tele/<device>/RESULT`).
3. Click **Learn** and point your original remote at the Tasmota IR receiver.
4. Press the button you want to capture - the hex code appears automatically within 30 seconds.
5. Copy the code into the relevant field of your device configuration.

### Testing IR codes

Use the **Send** function to transmit any hex code on demand directly from the panel, without saving it first. Useful for verifying a captured code actually works before configuring it.

### IR Database

The panel includes a built-in IR profile database and supports user-managed profiles:

- **Built-in profiles** - ready-to-use hex code sets for common devices, stored inside the integration
- **Custom profiles** - place your own JSON profiles in `/config/tasmota_ir_ready/ir_database/` and they appear alongside the built-in ones
- **Export** - save a configured device's full IR code set as a reusable profile

Profile format:

```json
{
  "title": "Samsung TV",
  "brand": "Samsung",
  "model": "Generic TV",
  "options": {
    "device_type": "media_player",
    "media_protocol": "NEC",
    "media_bits": 32,
    "media_power_data": "0xE0E040BF"
  }
}
```

### Flipper Zero IRDB import

The panel can browse and import profiles directly from the [Flipper Zero IRDB](https://github.com/UberGuidoZ/Flipper-IRDB) repository on GitHub. Parsed signals (NEC, NECext, Samsung32, SIRC/SONY, RC5, LG) are converted automatically to Tasmota hex codes. Raw timing signals are skipped.

---

## Climate (Air Conditioner)

Controls air conditioners using Tasmota's `IRHVAC` command. Supports full bidirectional state sync - when you use the original AC remote, Tasmota's IR receiver reports the change back to Home Assistant.

### Verifying AC compatibility

Open the Tasmota console, point your AC remote at the IR receiver, and press a button. If everything is configured correctly, you should see a line like this:

```javascript
{'IrReceived': {'Protocol': 'FUJITSU_AC', 'Bits': 128, 'Data': '0x0x1463001010FE09304013003008002025', 'Repeat': 0, 'IRHVAC': {'Vendor': 'FUJITSU_AC', 'Model': 1, 'Power': 'On', 'Mode': 'fan_only', 'Celsius': 'On', 'Temp': 20, 'FanSpeed': 'Auto', 'SwingV': 'Off', 'SwingH': 'Off', 'Quiet': 'Off', 'Turbo': 'Off', 'Econo': 'Off', 'Light': 'Off', 'Filter': 'Off', 'Clean': 'Off', 'Beep': 'Off', 'Sleep': -1}}}
```

If `Vendor` is not `Unknown` and you see the `IRHVAC` key, the integration can control your AC.

### Connection & Sensors

- **MQTT Command Topic** - topic to publish IRHVAC commands
- **MQTT State Topic** - topic to receive state updates from Tasmota
- `state_topic_2`: optional second state topic (useful to subscribe to both `tele/.../RESULT` and `stat/.../RESULT`)
- `availability_topic`: optional Tasmota LWT topic (auto-derived from the command topic if left blank)
- `temperature_sensor`: optional current-temperature sensor
- `humidity_sensor`: optional current-humidity sensor
- `power_sensor`: optional entity reflecting the AC physical power state

### AC Capabilities

Use your original AC remote and the Tasmota console to discover the values your AC supports. Cycle through all modes, fan speeds, swing positions, and feature buttons, then select only the values your AC actually reports.

**HVAC modes:**

- `heat`
- `cool`
- `heat_cool`
- `auto`
- `dry`
- `fan_only`
- `auto_fan_only`
- `fan_only_auto`

**Fan speeds:** Home Assistant standard values and Tasmota IRHVAC values. If your AC reports `min`, `medium`, and `max`, select those. Home Assistant displays `min` as `low` and `max` as `high` so climate card icons work correctly, while the integration still sends `min` and `max` to Tasmota.

**Swing options:**

- `off`
- `both`
- `vertical`
- `horizontal`
- `highest`
- `high`
- `middle`
- `low`
- `lowest`
- `left max`
- `left`
- `horizontal middle`
- `right`
- `right max`
- `wide`

`vertical`, `horizontal`, and `both` are automatic swing modes. Fixed vane positions send exact `SwingV` or `SwingH` values to Tasmota. `horizontal middle` is displayed separately to avoid conflicting with vertical `middle`, but sends `SwingH: middle` to Tasmota.

### Feature Switches

Optional switch entities for AC-specific functions:

- `SwingV`
- `SwingH`
- `Quiet`
- `Turbo`
- `Econo`
- `Light`
- `Filter`
- `Clean`
- `Beep`
- `Sleep`

Only enable switches for features your AC and Tasmota protocol support.

---

## Media Player

Controls TVs and AV receivers using Tasmota's `IRSend` command. You configure hex IR codes for each button - learned directly from your remote using the IR Manager panel.

**Supported controls:**

- Power on / off / toggle
- Volume up / down / mute
- Play / pause / play-pause toggle / stop
- Next track / previous track
- Source selection (up to 6 sources)

**Source selection modes:**

- **Direct** - each source has its own unique IR code; selecting a source sends that code immediately
- **Cycle** - a single IR code cycles through inputs; the integration tracks the current position and presses the button the right number of times to reach the target source

**Optional sensors:**

- `power_sensor` - external binary sensor entity reflecting the TV/device physical power state; keeps HA in sync when the device is controlled by the original remote or another means

---

## Fan

Controls IR-controlled fans using Tasmota's `IRSend` command. Configure hex IR codes for each function directly from your remote using the IR Manager panel.

**Supported controls:**

- Power on / off / toggle
- Speed presets - up to 6 named speed levels (e.g. Low, Medium, High)
- Oscillation - toggle, dedicated on code, and dedicated off code
- Direction - forward and reverse

**Optional sensors:**

- `power_sensor` - external binary sensor entity reflecting the fan's physical power state; keeps HA in sync when the fan is controlled by other means

The availability topic is auto-derived from the command topic (`tele/<device>/LWT`) or can be set explicitly.

---

## Humidifier

Controls IR-controlled humidifiers using Tasmota's `IRSend` command. All state is optimistic since IR devices cannot report back - target humidity and on/off state are tracked entirely in Home Assistant.

**Supported controls:**

- Power on / off / toggle
- Modes - up to 6 named operating modes (e.g. Auto, Sleep, Boost)
- Target humidity - stored optimistically in HA (no IR code sent when changing the setpoint)

**Humidity range:**

Configure `min_humidity`, `max_humidity`, and `humidity_step` to match your device's capabilities. These are exposed as HA capability attributes so the humidifier card slider behaves correctly.

**Action states** (derived automatically):

- **Humidifying** - device is on and working toward the target (or no sensor data available)
- **Idle** - device is on but current humidity has reached the target
- **Off** - device is off

**Optional sensors:**

- `humidity_sensor` - external HA sensor for current humidity (updates the current humidity attribute in real time)
- `power_sensor` - external binary sensor reflecting physical power state

The availability topic is auto-derived from the command topic (`tele/<device>/LWT`) or can be set explicitly.

---

## Remote

Generic IR remote entity that sends named commands via `remote.send_command`. Use it with automations, scripts, the built-in **Tasmota IR Ready Remote Card** (see below), or the [Universal Remote Card](https://github.com/Nerwyn/universal-remote-card).

**Built-in command names:**

`power`, `power_on`, `power_off`, `volume_up`, `volume_down`, `mute`, `digit_0`–`digit_9`, `up`, `down`, `left`, `right`, `ok`, `back`, `home`, `menu`, `info`, `exit`, `channel_up`, `channel_down`, `red`, `green`, `yellow`, `blue`

**Aliases:** `center` / `enter` / `select` / `dpad_center` → `ok`, `return` → `back`, `ch_up` / `ch_down`, `vol_up` / `vol_down`

**Source modes** - both can be active simultaneously on the same remote:

- **Direct** - each source button sends its own dedicated IR code immediately
- **Cycle** - a single cycle IR code steps through inputs; the integration tracks the current position and presses the button the right number of times to reach the target. A dedicated cycle button appears on the card

**Custom commands** - add extra IR codes from the integration's Configure panel. They appear automatically on the card with the name you gave them.

---

## Dashboard

- **Climate** - thermostat card, tile card, or any climate-compatible card
- **Media Player** - media control card or mini media player card
- **Remote** - use the built-in Tasmota IR Ready Remote Card (below), the [Universal Remote Card](https://github.com/Nerwyn/universal-remote-card), or any button card calling `remote.send_command`

When the original AC remote is used, a Tasmota IR receiver updates the climate state in Home Assistant automatically.

---

## Tasmota IR Ready Remote Card

<p align="center">
  <img src="https://raw.githubusercontent.com/Hollako/Tasmota-IR-Ready/master/images/remote_card.png" alt="Tasmota IR Ready Remote Card" width="360">
</p>

A custom Lovelace card included with the integration. It reads the remote entity's configured commands and renders the appropriate buttons automatically. The card registers itself when the integration loads — no Lovelace resource entry needed.

### Multi-remote tabs

A single card can display up to **4 remotes** as tabs in the header. Each tab has its own icon, title, hidden groups, and extra buttons. Switching tabs instantly shows that remote's controls and routes all commands to its entity. An offline indicator dot appears on tabs whose entity is unavailable.

**Multi-remote config:**

```yaml
type: custom:tasmota-ir-ready-remote-card
remotes:
  - entity: remote.living_room_tv
    title: Living Room TV
    card_icon: 📺
  - entity: remote.soundbar
    title: Soundbar
    card_icon: 🔊
    hidden_groups: [keypad, colors, channels]
  - entity: remote.bedroom_tv
    title: Bedroom TV
    card_icon: 🖥
```
### Configuration

#### Top-level keys

| Key | Description |
|-----|-------------|
| `remotes` | List of up to 4 remote objects (see per-remote keys below). When present, the card shows a tab bar. |
| `entity` | *(Legacy single-remote)* Remote entity ID. Ignored when `remotes` is set. |
| `title` | *(Legacy single-remote)* Card title override. |
| `card_icon` | *(Legacy single-remote)* Header icon emoji. |
| `hidden_groups` | *(Legacy single-remote)* Button groups to hide. |
| `extra_buttons` | *(Legacy single-remote)* Additional custom buttons. |

#### Per-remote keys (inside `remotes:`)

| Key | Required | Description |
|-----|----------|-------------|
| `entity` | ✓ | Remote entity ID (`remote.*`) |
| `title` | | Tab label (defaults to the entity friendly name) |
| `card_icon` | | Emoji icon shown on the tab. Choices: 📺 TV · 📡 Satellite · 🖥 Monitor · 🎬 Projector · 🎮 Game · 🔊 Speaker · 📻 Radio · 💿 DVD · 📼 Recorder · 🎛 Remote |
| `hidden_groups` | | List of button group IDs to hide: `power`, `volume`, `channels`, `dpad`, `keypad`, `colors`, `nav_aux`, `colors` |
| `extra_buttons` | | List of additional custom buttons (see below) |
| `dpad_style` | | Navigation style in the VDC zone: `dpad` (default, four directional buttons) or `touchpad` (swipe surface: tap for OK, swipe for directions) |

### Extra buttons

```yaml
extra_buttons:
  - label: Netflix
    command: netflix
    color: "#e50914"
  - label: YouTube
    command: youtube
    color: "#ff0000"
```

### Power button state

When a `power_sensor` is configured on the remote entity (via **Configure** on the integration entry), the power button reflects the sensor state in real time:

- **Green** - the sensor is `on` (device is powered)
- **Red** (default appearance) - the sensor is `off` or unavailable (device is off)

If no `power_sensor` is assigned, the power button stays in its default style with no colour change.

### Navigation style

The D-pad in the VDC zone can be switched to a **touch pad** per remote using the `dpad_style` option:

| Style | Description |
|-------|-------------|
| `dpad` | Four directional buttons + OK button (default) |
| `touchpad` | Single swipe surface - tap anywhere for OK, swipe in any direction to send up/down/left/right |

The touch pad flashes the theme's accent colour on each interaction and shows faint directional hints at its edges. Change the style from the **Visual editor** or add `dpad_style: touchpad` directly in YAML.

### Layout

The card is divided into sections that appear only when the corresponding commands are configured on the entity:

- **Header row** - power button (left) and cycle-input button (right), column-aligned above the VDC zone
- **VDC zone** - Volume column | D-pad / Touch pad center | Channel column
- **Number keypad** - 1–9 + 0
- **Navigation** - back, home, menu, info, exit, settings
- **Color buttons** - red, green, yellow, blue
- **Sources** - one button per source; direct sources send their IR code immediately, cycle sources use the cycle logic
- **My Buttons** - card-level extra buttons
- **Custom** - any additional commands discovered from the entity but not in any built-in group

### Interaction

- **Tap** - sends one IR command
- **Hold** - repeats automatically for `volume_up`, `volume_down`, `channel_up`, `channel_down`, `up`, `down`, `left`, `right` (starts after 300 ms, repeats every 200 ms)
- **Swipe** *(touch pad style only)* - swipe up / down / left / right to send the corresponding directional command; a short tap anywhere on the surface sends OK

### Visual editor

All options are configurable through the Lovelace card editor - click the pencil icon on the card to open it. The editor supports adding and removing remotes, switching between them to edit each one independently, and configuring the entity, tab icon, title, hidden groups, and extra buttons per remote.

---

## Credits

Inspired by:
1. [Tasmota-IRHVAC](https://github.com/hristo-atanasov/Tasmota-IRHVAC) by hristo-atanasov
2. [SmartIR](https://github.com/smartHomeHub/SmartIR) by smartHomeHub
