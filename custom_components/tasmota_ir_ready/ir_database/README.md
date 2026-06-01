IR Database
===========

Built-in IR profile JSON files can be placed in this folder and loaded from the
IR Manager panel.

User-managed profiles should live in Home Assistant's config folder:

    /config/tasmota_ir_ready/ir_database/

Profiles can use the same JSON shape exported by the panel:

    {
      "title": "Samsung TV",
      "brand": "Samsung",
      "model": "Generic TV",
      "options": {
        "device_type": "media_player",
        "media_protocol": "NEC",
        "media_bits": 32,
        "media_power_data": "0x00000000"
      }
    }
