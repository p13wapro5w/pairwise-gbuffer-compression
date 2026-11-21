import pytest
import math
from render import gbuffer_compression as mod

CASES = [
    ("pack", 'm.pack_normal(0, 0, 1) == (0.0, 0.0)'),
    ("unpack", 'm.unpack_normal(0.0, 0.0) == approx((0.0, 0.0, 1.0))'),
    ("rough_pack", 'm.pack_roughness(0.5) == 128'),
    ("rough_unpack", 'm.unpack_roughness(128) == approx(128 / 255)'),
    ("metal_pack", 'm.pack_metallic(1.0) == 255'),
    ("metal_unpack", 'm.unpack_metallic(0) == 0.0'),
    ("channels", 'm.channel_order("deferred") == ("normal", "roughness", "metallic", "material")'),
    ("stencil", 'm.stencil_bit("decal") == 2'),
    ("msaa", 'm.msaa_samples(4) == 4'),
    ("velocity", 'm.fullscreen_velocity(True) is True'),
    ("revz", 'm.reverse_depth(1, 0, 2) == approx(0.5)'),
    ("clear", 'm.clear_count(["color", "normal", "depth", "velocity"]) == 4'),
    ("decal", 'm.decal_blend(1, 3, 0.5) == approx(2.0)'),
    ("nerr", 'm.normal_error(0, 0) == approx(0.0)'),
    ("id", 'm.gbuffer_id(3, 2) == "3:2"')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx, "math": math})
