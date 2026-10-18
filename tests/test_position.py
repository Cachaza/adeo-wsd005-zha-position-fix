"""Offline regression checks. No Home Assistant instance or radio is contacted."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import zigpy.device
import zigpy.types as t
from zigpy.zcl.clusters.closures import WindowCovering
from zigpy.zcl import foundation
from zhaquirks.clusters import CustomCluster
from zha.application.platforms.cover import Cover
from zha.application.platforms.cover.const import CoverEntityFeature
from zha.quirks import DEVICE_REGISTRY

import adeo_wsd005_position as quirk


# Synthetic IEEE/NWK examples, unrelated to the original installation.
TEST_IEEE = "00:00:00:00:00:00:00:01"
OTHER_IEEE = "00:00:00:00:00:00:00:02"


@pytest.fixture(autouse=True)
def configured_ieee(monkeypatch):
    monkeypatch.setattr(quirk, "TARGET_IEEE", TEST_IEEE)


def make_device(ieee=TEST_IEEE, model="WSD005", manufacturer="Adeo", nwk=0x1234):
    device = zigpy.device.Device(MagicMock(), t.EUI64.convert(ieee), nwk)
    device.manufacturer = manufacturer
    device.model = model
    endpoint = device.add_endpoint(1)
    endpoint.profile_id = 0x0104
    endpoint.device_type = 0x0202
    # The input/output cluster signature observed on the WSD005.
    for cluster_id in (0, 3, 4, 5, 6, 0x19, 0x102):
        endpoint.add_input_cluster(cluster_id)
    endpoint.add_output_cluster(0x19)
    return device


def resolve_cluster(device):
    return DEVICE_REGISTRY.resolve(device).endpoints[1].in_clusters[0x102]


def ha_position(cluster):
    # Exercise the actual installed ZHA property, not a duplicate conversion.
    entity = MagicMock()
    entity._cluster = cluster
    entity.supported_features = CoverEntityFeature.OPEN
    return Cover.current_cover_position.fget(entity)


@pytest.mark.parametrize("raw", [0, 5, 50, 100])
def test_restored_cache_and_subsequent_updates(raw):
    device = make_device()
    original = device.endpoints[1].in_clusters[0x102]
    original.update_attribute(8, raw)
    cluster = resolve_cluster(device)
    assert isinstance(cluster, quirk.WSD005PositionWindowCovering)
    assert ha_position(cluster) == raw
    assert cluster.get(8) == 100 - raw
    assert cluster.get("current_position_lift_percentage") == 100 - raw
    assert cluster.get_cached_value(8) == raw
    assert original.get(8) == raw
    cluster.update_attribute(8, 100 - raw)
    assert ha_position(cluster) == 100 - raw
    assert cluster.get_cached_value(8) == 100 - raw


def test_missing_unknown_and_unrelated_attributes():
    cluster = resolve_cluster(make_device())
    assert ha_position(cluster) is None
    assert cluster.get(8, "missing") == "missing"
    cluster.update_attribute(8, 255)  # Zigbee unknown percentage sentinel.
    assert ha_position(cluster) is None
    # Observed configuration values and a tilt value must pass through.
    for attribute, value in [(7, 3), (0x17, 20), (9, 0)]:
        cluster.update_attribute(attribute, value)
        assert cluster.get(attribute) == value


@pytest.mark.parametrize("nwk", [0x1234, 0xABCD])
def test_matching_uses_permanent_ieee_not_temporary_network_address(nwk):
    assert isinstance(resolve_cluster(make_device(nwk=nwk)), quirk.WSD005PositionWindowCovering)
    assert not isinstance(
        resolve_cluster(make_device(ieee=OTHER_IEEE, nwk=nwk)),
        quirk.WSD005PositionWindowCovering,
    )


@pytest.mark.parametrize(
    "kwargs",
    [{"ieee": OTHER_IEEE}, {"model": "other"}, {"manufacturer": "other"}],
)
def test_other_devices_are_not_changed(kwargs):
    assert not isinstance(resolve_cluster(make_device(**kwargs)), quirk.WSD005PositionWindowCovering)


def test_unconfigured_quirk_is_disabled(monkeypatch):
    monkeypatch.setattr(quirk, "TARGET_IEEE", None)
    assert not isinstance(resolve_cluster(make_device()), quirk.WSD005PositionWindowCovering)


def test_configuration_is_skipped_and_io_methods_are_inherited():
    assert quirk.QUIRK.zha_device_factory.quirk_definition.skip_configuration
    for method in (
        "command", "write_attributes", "read_attributes",
        "bind", "configure_reporting",
    ):
        assert getattr(quirk.WSD005PositionWindowCovering, method) is getattr(WindowCovering, method)
    # CustomCluster supplies the standard raw-read passthrough when no constants
    # are configured. Verify inheritance here, and actual response behavior below.
    assert quirk.WSD005PositionWindowCovering.read_attributes_raw is CustomCluster.read_attributes_raw
    assert not quirk.WSD005PositionWindowCovering._CONSTANT_ATTRIBUTES


def test_direct_read_response_remains_raw(monkeypatch):
    cluster = resolve_cluster(make_device())
    response = [[foundation.ReadAttributeRecord(
        attrid=8,
        status=foundation.Status.SUCCESS,
        value=foundation.TypeValue(type=foundation.DataTypeId.uint8, value=t.uint8_t(0)),
    )]]
    transport = AsyncMock(return_value=response)
    monkeypatch.setattr(WindowCovering, "read_attributes_raw", transport)
    success, failure = asyncio.run(cluster.read_attributes([8], allow_cache=False))
    assert success == {8: 0}
    assert failure == {}
    transport.assert_awaited_once_with([8], manufacturer=None)
    assert cluster.get_cached_value(8) == 0
    assert cluster.get(8) == 100
    assert ha_position(cluster) == 0
