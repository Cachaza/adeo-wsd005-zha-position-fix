"""Opt-in position interpretation fix for an affected ADEO WSD005 on ZHA.

Normalize only the cached getter ZHA uses to calculate cover position.
The underlying cache, Zigbee read responses and outgoing commands are unchanged.
Percentage targets are deliberately unchanged: their semantics need a separate
physical test. See README.md before configuring this quirk.
"""

from typing import Any

from zigpy.zcl.clusters.closures import WindowCovering
from zhaquirks.builder import QuirkBuilder
from zhaquirks.clusters import CustomCluster


# Set this to YOUR device's permanent IEEE address, in lowercase colon notation.
# None disables matching. Never substitute the temporary Zigbee NWK address.
TARGET_IEEE: str | None = None


class WSD005PositionWindowCovering(CustomCluster, WindowCovering):
    """Present this motor's opening percentage in ZHA's expected ZCL convention."""

    def get(self, key: int | str, default: Any = None) -> Any:
        lift = self.AttributeDefs.current_position_lift_percentage
        if self.find_attribute(key).id != lift.id:
            return super().get(key, default)
        value = super().get(key)
        # 0..100 is the Zigbee percentage range; 255 represents unknown.
        if value is None or not isinstance(value, int) or not 0 <= value <= 100:
            return default
        return 100 - value


QUIRK = (
    QuirkBuilder("Adeo", "WSD005")
    .filter(lambda device: TARGET_IEEE is not None and str(device.ieee) == TARGET_IEEE)
    .replaces(WSD005PositionWindowCovering, endpoint_id=1)
    .skip_configuration()
    .add_to_registry()
)
