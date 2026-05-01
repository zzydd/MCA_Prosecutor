# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

"""
批量获取整个区块的 群系biome 生成器对象
"""
from mca import Biome

def stream_biomes(section, offset=2):
    """
    直接从 section 的 biomes NBT 解码并返回 64 个 Biome（4x4x4 单元）。
    返回值：list of 64 mca.Biome（order: cy 0..3, cz 0..3, cx 0..3）。
    offset: 代表点在每个 4x4x4 子格内的偏移 (0..3)，默认 2（中心）。
    """
    if section is None or 'biomes' not in section:
        return None

    biomes_tag = section['biomes']
    raw_palette = biomes_tag.get('palette', [])
    if not raw_palette:
        return None

    # 构造干净 palette（Biome 实例）
    palette = []
    for t in raw_palette:
        try:
            b = Biome.from_name(t.value)
            palette.append(Biome(b.namespace, b.id))
        except Exception as e:
            print(f"[WARN] 生物群系解析异常：{e}")
            palette.append(Biome('minecraft', 'plains'))

    # 无 data => 全 64 个都等于 palette[0]
    if 'data' not in biomes_tag:
        return [palette[0]] * 64

    data = biomes_tag['data']
    bits = max((len(palette) - 1).bit_length(), 1)
    per_state = 64 // bits
    mask = (1 << bits) - 1

    # clamp offset
    if offset < 0:
        offset = 0
    elif offset > 3:
        offset = 3

    out = []
    # 遍历 4x4x4 单元：cy, cz, cx
    for cy in range(4):
        for cz in range(4):
            for cx in range(4):
                # 代表点（局部 0..15）
                x = min(max(cx * 4 + offset, 0), 15)
                y = min(max(cy * 4 + offset, 0), 15)
                z = min(max(cz * 4 + offset, 0), 15)

                # biome_index 在 0..63
                biome_index = (y // 4) * 16 + (z // 4) * 4 + (x // 4)

                state = biome_index // per_state
                if state >= len(data):
                    # data 不足：退化到第一个 palette 项
                    out.append(palette[0])
                    continue

                current = data[state]
                if current < 0:
                    current += 2**64

                shift = (biome_index % per_state) * bits
                current >>= shift
                palette_id = current & mask

                if palette_id >= len(palette):
                    out.append(palette[0])
                else:
                    p = palette[palette_id]
                    out.append(Biome(p.namespace, p.id))

    # out 长度应为 64
    return out
