# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import zlib
import gzip
import struct
from io import BytesIO

SECTOR = 4096

def modify_entities_mca(region_bytes, modified_chunk_map):
    """
    增量编辑实体区域文件的二进制数据
    :param region_bytes: 原始区域文件二进制数据
    :param modified_chunk_map: 需要修改的区块 {区块索引: NBT数据}
    :return: 修改后的区域文件二进制数据
    """
    # 创建缓冲区并复制时间戳表
    result = bytearray(SECTOR * 2)
    result[SECTOR:SECTOR * 2] = region_bytes[SECTOR:SECTOR * 2]
    # 计算函数引用
    gzip_compress = gzip.compress
    zlib_compress = zlib.compress
    pack_int = struct.pack
    from_bytes = int.from_bytes
    # 初始化位置表
    new_loc = [0] * 1024
    cur_sector = 2
    sector_mask = SECTOR - 1
    # 遍历区块索引
    for index in range(1024):
        header_offset = index * 4
        entry = region_bytes[header_offset:header_offset + 4]
        if len(entry) < 4:
            continue
        offset = (entry[0] << 16) | (entry[1] << 8) | entry[2]
        sectors = entry[3]
        # 跳过空区块
        if offset == 0 or sectors == 0:
            continue
        # 读取区块数据
        data_pos = offset * SECTOR
        # if data_pos + 4 > len(region_bytes):
        #     continue
        length = from_bytes(region_bytes[data_pos:data_pos + 4], 'big')
        # if length <= 0 or length > sectors * SECTOR:
        #     continue
        payload = region_bytes[data_pos + 4:data_pos + 4 + length]
        # 判断区块是否被修改
        if index in modified_chunk_map:
            # 序列化新的NBT数据
            nbt_root = modified_chunk_map[index]
            buf = BytesIO()
            nbt_root.write_file(buffer=buf)
            raw = buf.getvalue()
            # 保持原始压缩格式
            comp = payload[0]
            body = gzip_compress(raw) if comp == 1 else zlib_compress(raw)
            payload = bytes([comp]) + body
            length = len(payload)
        # 计算所需的扇区数量
        total_size = 4 + length
        need = (total_size + sector_mask) >> 12
        if need > 0xFF:
            raise ValueError("chunk too large: needs >255 sectors")
        # 扩展缓冲区
        pos = cur_sector * SECTOR
        result.extend(b"\x00" * (need * SECTOR))
        # 写入数据
        result[pos:pos + 4] = pack_int(">I", length)
        result[pos + 4:pos + 4 + length] = payload
        # 转化位置信息
        new_loc[index] = (cur_sector << 8) | need
        cur_sector += need
    # 写入位置表
    for i, loc in enumerate(new_loc):
        offset = i * 4
        result[offset:offset + 3] = ((loc >> 8) & 0xFFFFFF).to_bytes(3, 'big')
        result[offset + 3] = loc & 0xFF
    return bytes(result)