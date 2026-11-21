"""G-Buffer 压缩与布局约定。

本模块集中定义延迟/前向管线的 G-Buffer 编码规则，避免各 pass 各自为政：

* 法线使用八面体编码（两个分量即可重建单位向量），解码后重新归一化，
  补偿 8bit 量化带来的长度误差；
* 粗糙度、金属度统一量化为 8bit，通道顺序由布局表唯一定义；
* 模板位按用途分区，描边、贴花、透明裁剪、材质 id 互不覆盖；
* MSAA 样本数、速度缓冲、反向 Z、清屏附件、贴花混合均走统一入口。
"""

import math

# 通道布局：延迟与前向使用各自的表，禁止共用一套解释。
LAYOUTS = {
    # 延迟光照：法线 + 粗糙度 + 金属度 + 材质 id
    "deferred": ("normal", "roughness", "metallic", "material"),
    # 前向透明：材质 id 提前，粗糙度/金属度顺序与延迟表不同
    "forward": ("normal", "material", "roughness", "metallic"),
}

# 模板位分区：每个用途独占一位，避免后处理读到被覆盖的材质 id。
STENCIL_BITS = {
    "outline": 1 << 0,      # 1  描边
    "decal": 1 << 1,        # 2  贴花
    "alpha_clip": 1 << 2,   # 4  透明裁剪
    "material_id": 1 << 3,  # 8  材质 id
}

# 合法 MSAA 级别；0/1 均表示不做多重采样。
MSAA_LEVELS = (1, 2, 4, 8, 16)

# 8bit 量化满量程。
_QUANT_MAX = 255


def _clamp01(value):
    return 0.0 if value < 0.0 else (1.0 if value > 1.0 else float(value))


def _sign(value):
    """三值符号函数，0 映射为 0，避免八面体折叠时产生错误象限。"""
    if value > 0.0:
        return 1.0
    if value < 0.0:
        return -1.0
    return 0.0


def pack_normal(x, y, z):
    """八面体编码。

    输入单位向量，输出 (u, v) ∈ [-1, 1]²。八面体编码只需要两个分量，
    相比三通道 8bit 存储节省 1/3 带宽，且解码后可精确还原单位长度。
    """
    l1 = abs(x) + abs(y) + abs(z)
    if l1 <= 0.0:
        # 退化输入（零向量）映射到 +Z 的法线。
        return (0.0, 0.0)

    x = float(x) / l1
    y = float(y) / l1

    if z < 0.0:
        old_x = x
        x = (1.0 - abs(y)) * _sign(old_x)
        y = (1.0 - abs(old_x)) * _sign(y)

    return (x, y)


def unpack_normal(u, v):
    """八面体解码。

    解码后重新归一化，作为 8bit 量化误差的补偿，保证返回值是单位向量；
    这正是光照方向不再因 |n| != 1 而偏移的关键。
    """
    u = float(u)
    v = float(v)

    z = 1.0 - (abs(u) + abs(v))
    if z < 0.0:
        old_u = u
        u = (1.0 - abs(v)) * _sign(old_u)
        v = (1.0 - abs(old_u)) * _sign(v)

    length = math.sqrt(u * u + v * v + z * z)
    if length <= 0.0:
        return (0.0, 0.0, 1.0)

    return (u / length, v / length, z / length)


def pack_roughness(value):
    """粗糙度量化到 8bit（四舍五入，带边界钳制）。"""
    return int(math.floor(_clamp01(float(value)) * _QUANT_MAX + 0.5))


def unpack_roughness(byte):
    """粗糙度还原到 [0, 1]。"""
    return int(byte) / _QUANT_MAX


def pack_metallic(value):
    """金属度量化到 8bit（四舍五入，带边界钳制）。"""
    return int(math.floor(_clamp01(float(value)) * _QUANT_MAX + 0.5))


def unpack_metallic(byte):
    """金属度还原到 [0, 1]。"""
    return int(byte) / _QUANT_MAX


def channel_order(layout):
    """通道布局。

    延迟光照与前向透明使用分表定义，任何 pass 都必须按此表解释通道，
    杜绝采样时通道顺序写反导致粗糙度/金属度互换。
    """
    try:
        return LAYOUTS[layout]
    except KeyError:
        raise ValueError("unknown gbuffer layout: %r" % (layout,))


def stencil_bit(kind):
    """模板位分区。

    每个用途独占一位：描边与透明裁剪不再共用，材质 id 不会被后处理覆盖。
    """
    try:
        return STENCIL_BITS[kind]
    except KeyError:
        raise ValueError("unknown stencil usage: %r" % (kind,))


def msaa_samples(level):
    """MSAA 样本数。

    G-Buffer 按样本存储，返回实际采样数；0 视为关闭多重采样。
    """
    level = int(level)
    if level == 0:
        return 1
    if level not in MSAA_LEVELS:
        raise ValueError("unsupported MSAA level: %r" % (level,))
    return level


def fullscreen_velocity(enabled):
    """全屏速度标记。

    开启后静态场景也写入速度缓冲，相机移动时全屏速度均有效，
    时域效果不再错位。
    """
    return bool(enabled)


def reverse_depth(z, near, far):
    """反向深度。

    将线性视空间深度映射到 [0, 1]，近平面为 1、远平面为 0，
    让浮点精度集中到远处，缓解 z-fighting 与贴花闪烁。
    """
    z = float(z)
    near = float(near)
    far = float(far)

    if far == near:
        raise ValueError("near and far planes must differ")

    value = (far - z) / (far - near)
    return _clamp01(value)


def clear_count(attachments):
    """清屏附件数。

    颜色、法线、深度、速度等所有附件都必须在每帧清除，
    未绘制区域不能残留上一帧的数据。
    """
    if attachments is None:
        raise ValueError("attachments must not be None")
    return len(attachments)


def decal_blend(base, decal, alpha):
    """贴花混合。

    按 alpha 在基础材质与贴花材质之间插值，而不是直接覆盖，
    避免贴花把金属度等属性清成零。
    """
    alpha = _clamp01(float(alpha))
    return float(base) * (1.0 - alpha) + float(decal) * alpha


def normal_error(u, v):
    """法线误差。

    返回解码法线偏离单位长度的绝对误差；八面体解码后的归一化会把该误差
    压到浮点精度量级。
    """
    x, y, z = unpack_normal(u, v)
    length = math.sqrt(x * x + y * y + z * z)
    return abs(length - 1.0)


def gbuffer_id(seed, index):
    """G-Buffer id。

    以 ``seed:index`` 形式生成稳定的标识，便于测试与调试定位。
    """
    return "%d:%d" % (int(seed), int(index))
