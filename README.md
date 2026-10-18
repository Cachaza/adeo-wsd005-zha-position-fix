# ADEO WSD005 position fix for ZHA

A small, opt-in Home Assistant ZHA quirk for an ADEO WSD005 roller shutter motor
that reports its position with the opposite convention to ZHA.

**Scope: reported position and derived state only.** This is a local workaround,
verified on one installation, not a universal fix for every WSD005 or a complete
movement-control driver. It is disabled until you configure your device's IEEE
address. No Home Assistant credentials or installation-specific addresses are
included in this repository.

## The problem

The original motor's RF remote already moved up and down correctly, and its end
limits were configured. When physically closed, Home Assistant nevertheless
displayed it as fully open.

Read-only investigation of endpoint `1`, Window Covering cluster `0x0102`,
attribute `0x0008` (`current_position_lift_percentage`) established:

| Physical position | Raw Zigbee value | ZHA without this quirk | ZHA with this quirk |
| --- | --- | --- | --- |
| Fully closed | `0` | 100% open | 0% open / closed |
| Slightly open | `5` | 95% open | 5% open |

These were observed positions, not assumptions from the UI. The direct device
read agreed with the underlying cached raw value, so refreshing Home Assistant's
state alone did not solve the mismatch.

ZHA normally converts the attribute using `100 - raw`: ZCL uses `0` for open,
whereas Home Assistant uses `0` for closed. On this affected device the raw
attribute already behaved as an opening percentage.

## How it works

The quirk replaces the Window Covering cluster's Python class for one matching
device. Its `get()` method returns `100 - raw` for the lift percentage only. ZHA
then performs its usual conversion, resulting in `100 - (100 - raw) = raw`.

- Matching requires manufacturer `Adeo`, model `WSD005`, and the configured
  permanent IEEE address. It does not match by the temporary NWK address.
- Raw cache values and Zigbee read responses stay intact. Some ZHA diagnostics
  use `get()` and therefore show the normalized value, not the raw device value.
- Missing or invalid percentages, including Zigbee's `255` unknown value, are
  exposed as unknown rather than turned into an invented position.
- All other attributes and outgoing methods are inherited unchanged.
- `skip_configuration()` prevents this quirk from requesting ZHA device
  configuration; it does not disable other Home Assistant startup behavior.
- The endpoint and cluster identifiers remain unchanged. The original
  installation retained its existing entity ID and unique ID after restart.

The quirk does not write a motor-direction attribute, alter end limits, flash
firmware, recalibrate, reset or issue a movement command during matching.

**Movement caveat:** open, close, stop and percentage commands are unchanged and
were not physically tested as part of this fix. Correct reported position does
not establish that percentage targets work correctly. This quirk is not a
replacement for testing movement separately under direct supervision. It also
does not fix reversed RF buttons, bad limits or a genuinely stale device report.

## Verified environment

| Component | Version |
| --- | --- |
| Home Assistant Core | `2026.10.2` |
| ZHA | `2.3.1` |
| zha-quirks | `2.3.0` |
| Device manufacturer / model | `Adeo` / `WSD005` |
| Motor firmware | `0x20230525` |

After activation on the original installation, ZHA reported the quirk as
applied, Home Assistant showed closed / 0%, and a direct read still returned
raw `0`. No related device or quirk errors were found in the startup logs.
Other firmware and ZHA versions have not been established as compatible.

## Installation

### 1. Confirm the same symptom using reads

In **Settings → Devices & services → ZHA**, open your device's information and
copy its permanent **IEEE** address. Do not use its short NWK address.

With the shutter already at a known physical position, use **Manage Zigbee
device** to read endpoint `1`, input cluster `0x0102`, attribute `0x0008`. Use
only attribute reads for diagnosis. Confirm that physical closed corresponds
to raw `0` while Home Assistant reports 100% open. Check the device's history
for updates: an inverted percentage and a stale device report need different
solutions. If the evidence does not match, do not enable this workaround.

### 2. Copy and configure the file

Keep a copy of `configuration.yaml` and any existing custom quirk file before
editing. Download [adeo_wsd005_position.py](adeo_wsd005_position.py) and copy it
into a dedicated custom quirks directory, for example:

```text
/config/custom_zha_quirks/adeo_wsd005_position.py
```

`/config` means Home Assistant Core's configuration directory. A File editor
App may expose the same files under `/homeassistant`; use the path that Core
sees in the YAML configuration below.

In the **installed copy**, replace:

```python
TARGET_IEEE: str | None = None
```

with your own IEEE address as a quoted, lowercase, colon-separated string:

```python
TARGET_IEEE: str | None = "<your-device-ieee>"
```

The angle-bracket text is a placeholder, not an address to copy literally.
Leaving `None` keeps the quirk disabled. Keep your configured copy private;
the repository's default file contains no real device address.

### 3. Point ZHA at the directory

Add this to `configuration.yaml` using the File editor or your normal managed
configuration workflow:

```yaml
zha:
  custom_quirks_path: /config/custom_zha_quirks
```

If a `zha:` block already exists, add the option there instead of duplicating
the block. If `custom_quirks_path` is already configured, put the Python file
in that existing directory and preserve the existing settings. Quirks must be
enabled; do not leave an existing `enable_quirks: false` setting in place.

You do not need to install this project's development dependencies in Home
Assistant or re-pair the motor.

### 4. Validate, then restart when appropriate

Run Home Assistant's configuration check before restarting. Review startup
automations, scripts and any broad cover/group actions that could move the
shutter when entities return or their reported states change. Restart Home
Assistant only when that interruption and possible startup behavior are
acceptable. Installing a quirk does not make the rest of the system read-only.

### 5. Verify without movement

- Confirm ZHA diagnostics report `quirk_applied: true` and identify this module
  (on the verified version: `adeo_wsd005_position:(Adeo / WSD005)`).
- Confirm the original entity ID still exists.
- Read `0x0008` directly again. If raw is still `0`, Home Assistant should now
  show **closed / 0%**.
- Check startup logs for errors related to the motor or this module. The
  generic warning that custom quirks are loaded is expected.

Do not use the normalized number in a diagnostics dump as proof of the raw
Zigbee value. A direct attribute read is the relevant check. Movement testing,
if desired, is a separate step with someone able to observe and stop the motor.

## Rollback

Remove only this Python file from the configured quirks directory. Restore
the YAML option you changed, or remove the new `zha:` block if it contained
only this option and did not exist before. Preserve any other custom quirks.
Validate the configuration and restart when appropriate. No motor reset or
limit recalibration is needed to undo this software interpretation change.

## Development and tests

Use an isolated Python environment; do not run these commands inside Home
Assistant Core's Python environment. The dependency versions below reproduce
the verified ZHA environment. Python must satisfy those dependencies (the
original offline tests used Python 3.12; Core used Python 3.14). This repository's
13 offline test cases have also been run on Python 3.12 and Python 3.14.

```sh
git clone https://github.com/Cachaza/adeo-wsd005-zha-position-fix.git
cd adeo-wsd005-zha-position-fix
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use mock devices and never contact Home Assistant or a radio. They check
matching by IEEE across NWK changes, disabled matching, model/manufacturer
isolation, restored cache and subsequent updates, unknown values, untouched
raw data and attributes, and inherited movement/write methods. Position checks
exercise the installed ZHA cover property instead of duplicating its formula.

## Contributing

Open an issue or pull request with the exact Home Assistant, ZHA, zha-quirks
and motor firmware versions, anonymized device signature, and the raw/physical
position observations. Distinguish real hardware observations from offline
tests. Do not publish tokens, IEEE addresses, network keys or complete private
diagnostic dumps. Do not broaden device matching based only on a model name.

An upstream fix may eventually be a better home for this behavior. This
repository is independent of ADEO, Home Assistant and the Zigpy projects.

## References

- [Home Assistant ZHA documentation](https://www.home-assistant.io/integrations/zha/)
- [ZHA device handlers and custom quirks](https://github.com/zigpy/zha-device-handlers)
- [ZHA 2.3.1 cover implementation](https://github.com/zigpy/zha/blob/2.3.1/zha/application/platforms/cover/__init__.py)
- [WSD005 device information in Zigbee2MQTT](https://www.zigbee2mqtt.io/devices/WSD005.html)
  (a different integration; its options are not ZHA settings)

## License

[MIT](LICENSE).
