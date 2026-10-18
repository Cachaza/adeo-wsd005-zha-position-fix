# Lexman ENKI / ADEO WSD005 — Home Assistant (ZHA)

**Control a Lexman connected roller-shutter motor directly with Home Assistant and ZHA, without an ENKI hub.** Keep the original 433 MHz remote, and optionally fix inverted position reporting with the included opt-in ZHA quirk.

[Español](README.es.md) · [Step-by-step installation](docs/installation.md) · [Troubleshooting](docs/troubleshooting.md) · [How the quirk works](docs/technical-details.md)

> **Tested on one installation, not an official integration.** This guide covers the ADEO `WSD005` Zigbee device, observed with the Lexman ENKI connected replacement roller-shutter motor (product reference **87554450**, 10 Nm / 40 mm). Check the Zigbee manufacturer and model in your own installation; other Lexman motors or firmware may behave differently.

## What works?

| Feature | Result on the verified installation |
| --- | --- |
| Direct pairing to Home Assistant ZHA | ✅ Confirmed; no ENKI gateway |
| Original 433 MHz remote alongside Zigbee | ✅ Confirmed |
| Open / close from Home Assistant | ✅ Confirmed after installation |
| Travel limits set using the remote | ✅ Confirmed |
| Intermediate position (50%) | ✅ Confirmed |
| Correct percentage and closed/open indication | ✅ Confirmed with the quirk on the affected unit |
| STOP from ZHA | Not separately documented as a physical test |
| All firmware variants and other motor models | Not tested |

The manufacturer requires an ENKI gateway **for use with the ENKI application**, not for the direct ZHA setup documented here. This is an independent community integration, not an official ADEO/Home Assistant compatibility guarantee.

## Quick start

1. **Install the motor safely**, following the [manufacturer manual](https://www.manualslib.com/manual/3508550/Lexman-87554450.html). The motor uses mains voltage; electrical wiring and mounting must be done by a competent person with the circuit isolated. Ensure mounting, shaft adapters and shutter attachments are correct.
2. **Pair the original 433 MHz remote** (it does not depend on Zigbee). Select the remote channel, press the **motor-head** button once, then the remote's **pairing** button once. The motor should briefly jog to acknowledge the pairing. See the [manual, p. 119 (English)](https://www.manualslib.com/manual/3508550/Lexman-87554450.html?page=119).
3. **Set and verify both travel limits using the remote** before allowing unattended or Home Assistant movement. Stop if the movement direction is wrong, the shutter binds or a limit fails. See [installation details](docs/installation.md#3-set-and-check-the-travel-limits).
4. **Pair Zigbee with ZHA.** In Home Assistant, open **Settings → Devices & services → ZHA → Add device**. If the Zigbee module is not already joining a network, the manufacturer's pairing/reset procedure is **four quick presses (within 1.5 seconds) of the button on the connected Zigbee module**, not the button on the motor head; the LED should blink blue. **Warning:** this action resets the Zigbee module into pairing mode, so do not repeat it on an already-paired device just to test a button. See [ENKI's product sheet](https://support.enki-home.com/hc/en-us/articles/20527012703890-Lexman-Connected-Replacement-Motor-for-Roller-Shutter-Product-Sheet).
5. **Check the position before automating anything.** Affected devices can show **100% open in ZHA while physically closed**. Do not assume the RF remote or travel limits are wrong. See [the diagnostic steps](docs/troubleshooting.md#home-assistant-says-open-when-the-shutter-is-closed).
6. **Only if your device has that exact symptom**, apply the [opt-in position fix](docs/installation.md#5-optional-install-the-zha-position-fix). Verify state without moving the shutter, then test motion separately under supervision.

**Do not use ZHA's `Inverted` motor-direction control as a substitute for correcting a displayed percentage.** The quirk in this project changes the *reported position interpretation only*, and deliberately does not rewrite open, close, stop or target-position commands.

## Why this quirk exists

On the affected device, a direct Zigbee read of endpoint `1`, Window Covering cluster `0x0102`, lift percentage attribute `0x0008` gave:

| Physical position | Raw Zigbee value | Standard ZHA display | With this quirk |
| --- | --- | --- | --- |
| Closed | `0` | 100% open | 0% open (closed) |
| Slightly open | `5` | 95% open | 5% open |

The device reports an **opening** percentage where ZHA expects the opposite Zigbee convention. This project's [`adeo_wsd005_position.py`](adeo_wsd005_position.py) compensates for the mismatch at the ZHA interpretation layer without changing the raw Zigbee attribute, motor direction or travel limits.

The fix is **disabled by default**. It matches only a configured, specific **permanent device IEEE address**: it must not silently change every `WSD005` on your Zigbee network.

## Verified versions

| Component | Version observed |
| --- | --- |
| Home Assistant Core | `2026.10.2` |
| ZHA | `2.3.1` |
| zha-quirks | `2.3.0` |
| Manufacturer / model | `Adeo` / `WSD005` |
| Firmware | `0x20230525` |

These versions describe **one working installation**, not minimum supported versions or guaranteed compatibility with future releases. The position fix was verified by direct Zigbee reads after a restart; open, close, end limits and the 50% target were subsequently verified physically with the shutter attached.

## Zigbee2MQTT users

[Zigbee2MQTT already has a device page for ADEO WSD005](https://www.zigbee2mqtt.io/devices/WSD005.html), including an `invert_cover` option for the position/state representation. **This repository's Python quirk is for ZHA only**; do not copy it into Zigbee2MQTT, and do not assume identically named options have identical effects in both integrations.

## Documentation and contributing

- [Full hardware / remote / ZHA guide](docs/installation.md)
- [Troubleshooting and safe diagnosis](docs/troubleshooting.md)
- [Technical explanation, quirk installation, rollback and tests](docs/technical-details.md)
- [Guía en español](README.es.md)
- [Official Lexman / ENKI product information](https://support.enki-home.com/hc/en-us/articles/20527012703890-Lexman-Connected-Replacement-Motor-for-Roller-Shutter-Product-Sheet)
- [Home Assistant ZHA documentation](https://www.home-assistant.io/integrations/zha/)

If your hardware or firmware behaves differently, please [open an issue](https://github.com/Cachaza/adeo-wsd005-zha-position-fix/issues) with the model, software versions, a redacted device signature, and **raw values paired with actual observed positions**. Do not publish IEEE addresses, network keys, tokens, home addresses or complete private diagnostics.

This project is independent of ADEO, Lexman, Home Assistant and zigpy. MIT licensed; see [LICENSE](LICENSE).
