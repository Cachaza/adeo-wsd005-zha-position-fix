# Installing a Lexman / ADEO WSD005 with Home Assistant ZHA

[Back to README](../README.md) · [Español](../README.es.md) · [Troubleshooting](troubleshooting.md)

This walkthrough covers the Lexman ENKI connected replacement shutter motor corresponding to product reference **87554450** on the [manufacturer's product sheet](https://support.enki-home.com/hc/en-us/articles/20527012703890-Lexman-Connected-Replacement-Motor-for-Roller-Shutter-Product-Sheet). The paired Zigbee device in the tested installation identifies itself as **`Adeo` / `WSD005`**.

**Read before starting:** The motor is mains-powered (230 V AC), and a moving shutter can damage its attachments, motor or housing. Electrical installation, motor mounting, limit setting and repairs must follow the actual product manual. Isolate power before touching wiring, the shaft or attachments; use a competent installer if needed. Stop immediately if motion is unexpected or the tube/shutter is obstructed. Never place hands in moving parts.

## 1. Check your hardware

You need:

- The correct motor, shaft adapters, manufacturer-approved support and shutter attachments. Verify the actual product reference: other Lexman motors can have different size, torque, radio module and pairing procedure.
- The included **433 MHz RF remote** (its own CR2032 battery). This is separate from Zigbee.
- A running Home Assistant installation with a supported Zigbee coordinator and the **ZHA** integration. This guide does **not** require an ENKI hub.
- Safe physical access to the shutter and a means of isolating its power for commissioning.

The official page identifies reference `87554450` as a 10 Nm, 40 mm shaft motor and confirms **Zigbee 3.0** plus a separate **433 MHz remote**. Other variants are outside the verified scope.

## 2. Pair the original 433 MHz remote

Follow the [manufacturer's remote-control procedure (English manual, p. 119)](https://www.manualslib.com/manual/3508550/Lexman-87554450.html?page=119), not a generic Somfy or Tuya procedure:

1. Check the remote's battery / remove its shipping insulation tab. Select the desired remote channel.
2. Press the **button on the motor head once**.
3. Press the **small pairing button on the RF remote once** (not its up/down/stop keys).
4. The motor should acknowledge with a brief jog/vibration.
5. Check that the remote controls the **expected direction** before setting end limits.

The **motor-head button**, **RF remote pairing button**, and **separate connected Zigbee module button** are different controls. Do not mix up their sequences.

You do not need an ENKI gateway to use the RF remote. If the remote is already paired and works, **skip pairing** rather than repeating button sequences.

## 3. Set and check the travel limits

The Lexman remote saves upper and lower limits in the motor. The procedure illustrated on the [Spanish manual, p. 29](https://www.manualslib.es/manual/913385/Lexman-87554450.html?page=29) uses the remote's small pairing button and directional keys:

1. **Before adjusting limits**, verify actual UP and DOWN direction. If reversed, consult the manufacturer's direction configuration; do not compensate by guessing from Home Assistant.
2. Carefully bring the shutter to the desired **lower** stop. Press the remote **pairing** button **twice**, followed by the **DOWN** key once. Check for the motor's acknowledgement.
3. Carefully bring it to the desired **upper** stop without forcing the mechanism. Press the remote **pairing** button **twice**, followed by the **UP** key once. Check for acknowledgement.
4. Check both stops and the shutter's movement with the RF remote while watching the mechanism.

If a stop fails, **do not proceed to Home Assistant controls or automation**. Fix the physical installation/limits first. The [next manual page](https://www.manualslib.es/manual/913385/Lexman-87554450.html?page=30) also contains *deletion* and *direction change* sequences: do not experiment with those while troubleshooting a percentage display issue.

## 4. Add the Zigbee module directly to ZHA

1. In Home Assistant, open **Settings → Devices & services → ZHA → Add device** (the UI wording/location may vary by Home Assistant version).
2. Put the **connected Zigbee module** into join mode if it is not already joining. The [manufacturer's product support](https://support.enki-home.com/hc/en-us/articles/20527012703890-Lexman-Connected-Replacement-Motor-for-Roller-Shutter-Product-Sheet) specifies **four rapid presses within 1.5 seconds of the *central button on the connected module***. Its indicator should blink rapidly blue.
3. Wait for ZHA to discover the device. Confirm the manufacturer/model shown by ZHA: the tested unit reports `Adeo` / `WSD005`.
4. Rename the entity as desired, but keep track of its original `entity_id` for debugging.

**Important:** ADEO describes that four-press sequence as a **module reset back into pairing mode**. It can disrupt an existing Zigbee pairing. It is appropriate when deliberately onboarding/re-pairing, **not** when the device is already working in ZHA. This is not the same as setting a travel limit and should not intentionally alter travel limits, but don't rely on undocumented reset side effects.

After joining, **first examine the reported position without sending any movement command**.

## 5. Optional: install the ZHA position fix

Only install this when a real physical position and a read-only Zigbee attribute read demonstrate the inversion described in [troubleshooting](troubleshooting.md#home-assistant-says-open-when-the-shutter-is-closed).

On the tested device, **fully closed → raw `0` from Window Covering `0x0102`, attribute `0x0008` → ZHA incorrectly showing 100% open**. The quirk corrects interpretation; it is **not** a motor direction or calibration fix.

1. Back up your Home Assistant configuration and any existing custom-quirk files.
2. Copy [`adeo_wsd005_position.py`](../adeo_wsd005_position.py) into a custom ZHA quirks directory, e.g. `/config/custom_zha_quirks/adeo_wsd005_position.py`.
3. In the installed copy of the file, change the default disabled setting:

   ```python
   TARGET_IEEE: str | None = None
   ```

   to your **own permanent IEEE address** (illustrative, not real):

   ```python
   TARGET_IEEE: str | None = "aa:bb:cc:dd:ee:ff:00:11"
   ```

   The temporary Zigbee NWK address is not suitable. Keep the customized file private.
4. Add this to **the existing** `zha:` block in `configuration.yaml`, or create the block if none exists:

   ```yaml
   zha:
     custom_quirks_path: /config/custom_zha_quirks
   ```

   If another custom quirks directory is already configured, put the file there instead. Do **not** duplicate the `zha:` key. Leave ZHA quirks enabled.
5. Run Home Assistant's configuration validation. Before restarting, check startup automations, scripts and cover groups: unrelated startup behavior **can** move a shutter. Restart only when it is safe to interrupt Home Assistant.
6. Without moving the shutter, verify `quirk_applied: true` and the quirk identifier `adeo_wsd005_position`, confirm the original entity still exists, and read `0x0008` directly again. A **raw `0` with Home Assistant showing closed / 0%** is the expected observation.
7. Review ZHA logs for device-specific errors. ZHA may log a **generic warning about custom quirks**, which is expected; don't confuse it with a failure.

**The quirk only changes ZHA's position interpretation.** It leaves open/close/stop and percentage target commands untouched. Always test those under direct supervision before allowing automations; reported percentages alone cannot establish safe movement behavior.

## 6. Supervised validation before automation

Only when the RF remote, physical limits, and reported position all behave correctly:

- Ensure the curtain is properly attached to the shaft and the upper/lower path is clear. Have a reliable way to stop/isolating motor power.
- Observe a controlled **OPEN** command, then **CLOSE**, checking actual direction and travel stops.
- Observe a controlled **intermediate target**, such as 50%, to ensure the real opening fraction matches what Home Assistant displays.
- Test **STOP** independently if you intend to rely on it.
- Verify that remote operation remains correct after Zigbee commissioning.
- Only then add groups, scheduled actions, voice assistants or automations.

**Observed on the original installation:** After the quirk was active, the owner confirmed physical opening/closing, correct travel limits and a 50% target with the shutter attached. This is a real-world check of that single unit, not a guarantee of every WSD005 firmware.

## 7. Revert or update later

See [rollback and detailed compatibility notes](technical-details.md#rollback). Deleting this specific quirk and reverting its ZHA path entry (if the path was added solely for it) requires validation and a Home Assistant restart; it does **not** require a motor reset or new limits.

After updates to ZHA / zha-quirks / Home Assistant, confirm both reported position and supervised commands again before relying on unattended automations.

## Source links

- [Official ENKI / Lexman 87554450 product sheet](https://support.enki-home.com/hc/en-us/articles/20527012703890-Lexman-Connected-Replacement-Motor-for-Roller-Shutter-Product-Sheet)
- [Lexman 87554450 manufacturer's manual (English pages)](https://www.manualslib.com/manual/3508550/Lexman-87554450.html)
- [Home Assistant ZHA integration](https://www.home-assistant.io/integrations/zha/)
- [WSD005 in Zigbee2MQTT (separate integration)](https://www.zigbee2mqtt.io/devices/WSD005.html)
