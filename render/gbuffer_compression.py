import math

def pack_normal(x, y, z):
    """八面体编码。"""
    raise NotImplementedError("TODO: pack_normal")

def unpack_normal(u, v):
    """八面体解码。"""
    raise NotImplementedError("TODO: unpack_normal")

def pack_roughness(value):
    """粗糙度量化。"""
    raise NotImplementedError("TODO: pack_roughness")

def unpack_roughness(byte):
    """粗糙度还原。"""
    raise NotImplementedError("TODO: unpack_roughness")

def pack_metallic(value):
    """金属度量化。"""
    raise NotImplementedError("TODO: pack_metallic")

def unpack_metallic(byte):
    """金属度还原。"""
    raise NotImplementedError("TODO: unpack_metallic")

def channel_order(layout):
    """通道布局。"""
    raise NotImplementedError("TODO: channel_order")

def stencil_bit(kind):
    """模板位分区。"""
    raise NotImplementedError("TODO: stencil_bit")

def msaa_samples(level):
    """MSAA 样本数。"""
    raise NotImplementedError("TODO: msaa_samples")

def fullscreen_velocity(enabled):
    """全屏速度标记。"""
    raise NotImplementedError("TODO: fullscreen_velocity")

def reverse_depth(z, near, far):
    """反向深度。"""
    raise NotImplementedError("TODO: reverse_depth")

def clear_count(attachments):
    """清屏附件数。"""
    raise NotImplementedError("TODO: clear_count")

def decal_blend(base, decal, alpha):
    """贴花混合。"""
    raise NotImplementedError("TODO: decal_blend")

def normal_error(u, v):
    """法线误差。"""
    raise NotImplementedError("TODO: normal_error")

def gbuffer_id(seed, index):
    """G-Buffer id。"""
    raise NotImplementedError("TODO: gbuffer_id")
