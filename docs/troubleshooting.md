# Troubleshooting Lexman / ADEO WSD005 in Home Assistant

[Back to README](../README.md) · [Installation guide](installation.md) · [Technical details](technical-details.md)

**Start with observation and read-only diagnostics.** Do not use an UP/DOWN/ZHA test to investigate a misreported percentage until physical limits and motor direction are known safe. The connected Zigbee module, motor head and 433 MHz remote each have different controls.

## Home Assistant says open when the shutter is closed

This is the case the [opt-in quirk](../adeo_wsd005_position.py) is designed to address.

1. Confirm the shutter's physical position **by looking at it**. Leave it still during the following reads.
2. From ZHA's device-management/cluster tools, inspect **endpoint `1` → input cluster `0x0102` (Window Covering) → attribute `0x0008`** (`current_position_lift_percentage`).
3. Compare the **raw** device value with Home Assistant's cover entity position:

   | Physical observation | Raw Zigbee | ZHA unmodified | Affected device with quirk |
   | --- | --- | --- | --- |
   | Closed | `0` | 100% open | 0% open |
   | Slight opening | `5` | 95% open | 5% open |

4. If your reads **match this pattern**, follow [the opt-in workaround](installation.md#5-optional-install-the-zha-position-fix). Verify without movement after restarting.
5. If they **do not match**, do not install the workaround. The value could be stale, missing, different on your firmware, or your device might already use the expected convention.

**Do not simply switch on `Inverted` in ZHA**: that setting can change motor direction rather than just fixing the displayed position. Use an interpretation fix only after evidence of reversed percentages.

## The device is paired but the percentage does not update

- Compare a direct Zigbee read to what is currently cached and shown in Home Assistant.
- Check the ZHA device availability, recent events, signal and logs.
- A stale raw value is a **different failure** from the reproducible `0 → 100%` inversion.
- Do not repeatedly reset/re-pair or change travel limits to fix a stale status. Investigate reporting and connectivity first.
- If the value is unknown (for example, Zigbee `255`), this quirk intentionally does **not** invent a percentage.

## The 433 MHz remote does not respond

- Confirm the battery / shipping pull-tab, selected remote channel, and correct remote for this product.
- Use the **motor-head button + remote pairing button** procedure from the [manufacturer manual, p. 119](https://www.manualslib.com/manual/3508550/Lexman-87554450.html?page=119). Do not confuse the motor-head button with the Zigbee module button.
- Look for the expected acknowledgement (a short motor jog). If there is no acknowledgement, stop and recheck the exact product model and manual.
- The remote does **not** require an ENKI gateway or a functional ZHA connection.

## ZHA cannot discover the device

- Ensure ZHA is running, permit joining in Home Assistant, and check the coordinator and Zigbee connectivity.
- For **initial pairing only**, use the manufacturer-documented sequence: **four fast presses (within 1.5 s)** on the *connected Zigbee module*'s central button, then look for its rapidly blinking blue indicator.
- **Warning:** ENKI calls this a **reset into pairing mode**. It may remove an existing network pairing; do not do it casually if already paired.
- Check that ZHA detects `Adeo` / `WSD005`. Similar-looking models are not necessarily compatible with this workaround.

## Movement direction or travel limits are wrong

This is a **mechanical/control issue**, not the percentage-display bug.

- Stop commanding the motor if it moves unexpectedly or runs past a stop.
- Follow the exact Lexman motor/remote manual for direction and limit programming. Make sure the shutter and attachments are properly installed.
- Do not solve it by changing the quirk's maths. The quirk intentionally does not affect motor direction or stored end limits.
- If movement could jam the curtain or break attachments, isolate power and have the mechanism inspected before further motion.

## Opening at 50% actually opens to the wrong position

A correct reported percentage **does not prove** that a `set_cover_position` command uses the desired convention. This quirk changes the *getter*, not the outgoing Zigbee target. In the original installation a 50% command was physically verified as correct; your firmware may differ.

- Do not change motor direction, limits or quirk code based on the displayed position alone.
- Check actual motion only **after** limits and direction are safe, with a person present and power isolation available.
- Record the actual physical position, requested position and new raw attribute value before reporting a compatibility issue.

## Quirk is not applied after restart

- In your installed `adeo_wsd005_position.py`, `TARGET_IEEE` must contain **your device's permanent IEEE**, not `None` or its NWK address.
- The Zigbee manufacturer and model must be exactly `Adeo` / `WSD005` on the verified implementation.
- Check `zha: custom_quirks_path` points to the directory **as seen by Home Assistant Core**. Don't duplicate `zha:` keys or overwrite an existing custom-quirks configuration.
- Validate configuration and inspect startup logs. A generic custom-quirks warning is expected; import/match errors are not.
- Check `quirk_applied: true` and the module identifier. If the entity disappeared or changed ID, investigate before restoring automations.

## Zigbee2MQTT users

Zigbee2MQTT has [native WSD005 support](https://www.zigbee2mqtt.io/devices/WSD005.html) and an `invert_cover` option. **Do not install a Python ZHA quirk in Zigbee2MQTT.** Also do not treat the Zigbee2MQTT option as the same as ZHA's `Inverted` switch.

## Reporting an issue

Please include (without secrets): exact product reference, Zigbee manufacturer/model and firmware, Home Assistant/ZHA/zha-quirks versions, whether the RF remote works, physical position with direct attribute reads, expected/actual ZHA position and which operations you have **actually** tested.

Do not share your IEEE address, Zigbee network key, credentials, access tokens, precise home location or full unredacted Home Assistant diagnostics.
