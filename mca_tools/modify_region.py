# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import zlib
import math
import struct
import mca.nbt as mca_nbt
from io import BytesIO
from mca import EmptySection, EmptyChunk

# 文件定义
SECTOR = 4096 # 扇区大小
HEADER_SECTORS = 2 # 文件头扇区
HEADER_SIZE = SECTOR * HEADER_SECTORS # 文件头大小

# section类型转换
class NBTBackedEmptySection(EmptySection):
    """
    将 section NBT直接转为 EmptySection
    chunk.get_section(i) >>> EmptySection
    继承自EmptySection，直接用EmptySection来保存section，避免构建EmptySection
    """
    def __init__(self, section_nbt):
        y = section_nbt['Y'].value
        super().__init__(y)
        self._nbt = section_nbt
    def save(self):
        if self._nbt is not None:
            # 返回原始 NBT
            return self._nbt
        return super().save()

# chunk类型转换
class NBTBackedEmptyChunk(EmptyChunk):
    """
    将 Chunk NBT 直接转为 EmptyChunk
    region.get_chunk(x, z) >>> EmptyChunk
    与 NBTBackedEmptySection 类似
    """
    def __init__(self, chunk):
        super().__init__(chunk.x, chunk.z, chunk.version, chunk.status, chunk.data)
        # 注意：这里必须是 TAG_Compound
        self._nbt = chunk.data
    def save(self):
        # 1.18-
        if self.version < 2844:
            root = mca_nbt.NBTFile()
            root.tags.append(mca_nbt.TAG_Int(name='DataVersion', value=self.version))
            root.tags.append(self._nbt)
            return root
        # 1.18+
        else:
            return self._nbt


def _idx(cx:int, cz:int)->int:
    # 计算区块坐标
    return (cx & 31) + (cz & 31) * 32

def _chunk_bytes_from_chunk(empty_chunk) -> bytes:
    """
    获取区块对象二进制数据
    :param empty_chunk: EmptyChunk
    :return: 区块二进制数据
    """
    # 获取 NBT 对象
    nbt_obj = empty_chunk.save()
    # 序列化为原始 NBT 字节
    buf = BytesIO()
    nbt_obj.write_file(buffer=buf)
    raw_nbt = buf.getvalue()
    # 使用 zlib 压缩并包装成 Region 格式
    # 格式: [4字节-长度][1字节-压缩类型][压缩数据]
    compressed = zlib.compress(raw_nbt)
    payload = bytes([2]) + compressed  # 类型2表示zlib压缩
    return len(payload).to_bytes(4, 'big') + payload

#【编辑区块】
def modify_chunk(region_path, chunk_new) -> None:
    """
    增量编辑指定区块
    :param region_path: [str] 区域文件路径
    :param chunk_new: [EmptyChunk] 新的区块对象
    :return None，直接编辑文件，不返回数据
    """
    # 获取区块二进制数据
    new_bytes = _chunk_bytes_from_chunk(chunk_new)
    need = (len(new_bytes) + SECTOR - 1) // SECTOR
    if need <= 0:
        need = 1
    if need > 0xFF:
        raise ValueError("chunk too large: needs >255 sectors")
    # 获取坐标
    idx = _idx(chunk_new.x, chunk_new.z)
    header_pos = idx * 4
    # 打开文件
    with open(region_path, "r+b") as f:
        # 移动到文件末尾
        f.seek(0, 2)
        file_end = f.tell()
        # 确保 header 空间足够
        if file_end < HEADER_SIZE:
            f.write(b'\x00' * (HEADER_SIZE - file_end))
            file_end = HEADER_SIZE
        # 计算文件末尾位置
        aligned_end = (file_end + SECTOR - 1) // SECTOR * SECTOR
        # 对齐扇区
        if aligned_end > file_end:
            f.write(b'\x00' * (aligned_end - file_end))
        # 计算新区块的扇区偏移
        new_off = aligned_end // SECTOR
        # 追加写入数据
        f.write(new_bytes)
        # 对齐扇区
        bytes_written = len(new_bytes)
        total_bytes_needed = need * SECTOR
        if total_bytes_needed > bytes_written:
            f.write(b'\x00' * (total_bytes_needed - bytes_written))
        # 更新 header
        f.seek(header_pos)
        header_val = (new_off << 8) | (need & 0xFF)
        f.write(struct.pack('>I', header_val))

#【编辑区域二进制数据】
def modify_region_bytes(region_bytes: bytes, new_chunk) -> bytes:
    """
    在区域文件二进制数据中直接增量编辑指定区块
    :param region_bytes: [bytes] 区域文件二进制数据
    :param new_chunk: [EmptyChunk] 新的区块对象
    :return: [bytes] 编辑好的区域文件二进制数据
    """
    # 读取区域数据
    rb = bytearray(region_bytes)
    if len(rb) < HEADER_SIZE:
        rb.extend(b'\x00' * (HEADER_SIZE - len(rb)))
    header, sectors = rb[:HEADER_SIZE], rb[HEADER_SIZE:]
    # 获取区块坐标
    cx = new_chunk.x
    cz = new_chunk.z
    # 计算坐标
    i = _idx(cx, cz)
    # 新区块数据
    new_bytes = _chunk_bytes_from_chunk(new_chunk)
    need = math.ceil(len(new_bytes) / SECTOR)
    # 添加至结尾
    pos = len(sectors) // SECTOR
    sectors.extend(b'\x00' * (need * SECTOR))
    start = pos * SECTOR
    sectors[start:start+len(new_bytes)] = new_bytes
    # 更新 header
    new_off = pos + HEADER_SECTORS
    struct.pack_into('>I', header, i*4, (new_off << 8) | need)
    struct.pack_into('>I', header, 4096 + i*4, int(time.time()))
    # 返回数据
    return bytes(header + sectors)

#【批量编辑区域二进制数据】
def modify_region_bytes_batch(region_bytes: bytes, chunk_generator) -> bytes:
    """
    在区域文件二进制数据中直接增量编辑指定区块，批量处理版
    :param region_bytes: [bytes] 区域文件二进制数据
    :param chunk_generator: [iter] 需要处理的区块生成器
    :return: [bytes] 编辑好的区域文件二进制数据
    """
    rb = bytearray(region_bytes)
    # 确保 header 存在
    if len(rb) < HEADER_SIZE:
        rb.extend(b'\x00' * (HEADER_SIZE - len(rb)))
    # 保证按扇区对齐
    if len(rb) % SECTOR != 0:
        rb.extend(b'\x00' * (SECTOR - (len(rb) % SECTOR)))

    for new_chunk in chunk_generator:
        if new_chunk is None:
            continue
        cx = new_chunk.x
        cz = new_chunk.z
        i = _idx(cx, cz)
        header_pos = i * 4
        # 识别需要删除的区块
        if new_chunk.data is False:
            # 删除区块数据
            struct.pack_into('>I', rb, header_pos, 0)
            struct.pack_into('>I', rb, SECTOR + header_pos, 0)
            continue
        # 读取区块二进制数据
        new_bytes = _chunk_bytes_from_chunk(new_chunk)
        need = (len(new_bytes) + SECTOR - 1) // SECTOR
        if need <= 0:
            need = 1
        # 检查 need 是否能存入 header 的 1 字节（0-255）
        if need > 0xFF:
            raise ValueError(f"chunk too large: needs {need} sectors (>255)")
        # 追加到文件末尾（不复用）
        new_off = len(rb) // SECTOR  # 绝对扇区索引
        new_loc = (new_off << 8) | (need & 0xFF)
        struct.pack_into('>I', rb, header_pos, new_loc)
        # append 数据并按扇区填充
        rb.extend(new_bytes)
        remaining_bytes = need * SECTOR - len(new_bytes)
        if remaining_bytes > 0:
            rb.extend(b'\x00' * remaining_bytes)
    # 最终保证扇区对齐（通常已经对齐）
    if len(rb) % SECTOR != 0:
        rb.extend(b'\x00' * (SECTOR - (len(rb) % SECTOR)))
    return bytes(rb)

#【清理存档中的无效数据】
def clean_mca_invalid_bytes(region_bytes: bytes) -> bytes:
    """
    清理区域文件中的僵尸区块数据
    上面的区域文件编辑函数都是增量编辑，仅将新数据追加在末尾，所以会导致存档变大
    本函数的作用是读取有效数据并合并成新的区域文件，删除那些无效的数据。(拼好档，划掉)
    另外呢，这个函数虽说在 modify_region 中，但对于 entities.mca 同样有效
    :param region_bytes: 区域文件二进制数据
    :return: 清理完后的区域文件二进制数据
    """
    # 读取旧区域数据
    rb = bytearray(region_bytes)
    if len(rb) < HEADER_SIZE:
        return region_bytes
    old_header = rb[:HEADER_SIZE]
    old_body   = rb[HEADER_SIZE:]
    # 创建新区域数据
    new_header = bytearray(b'\x00' * HEADER_SIZE)
    new_body   = bytearray()
    # 遍历读取每个区块
    for i in range(1024):
        # 从 header 中读取数据位置
        loc = struct.unpack_from('>I', old_header, i * 4)[0]
        off, cnt = loc >> 8, loc & 0xFF
        if off == 0 or cnt == 0:
            continue
        # 计算区块数据起始和结束位置
        start = (off - HEADER_SECTORS) * SECTOR
        end   = start + cnt * SECTOR
        if start < 0 or end > len(old_body):
            continue  # 数据损坏，跳过
        # 读取区块数据
        chunk_bytes = bytes(old_body[start:end])
        if len(chunk_bytes) < 5:
            continue
        length = int.from_bytes(chunk_bytes[:4], 'big')
        if length + 4 > len(chunk_bytes):
            continue
        chunk_bytes = chunk_bytes[:length + 4]
        # 对齐并写入新区域数据
        pos = len(new_body) // SECTOR
        need = (len(chunk_bytes) + SECTOR - 1) // SECTOR
        new_body.extend(b'\x00' * (need * SECTOR))
        new_body[pos * SECTOR:pos * SECTOR + len(chunk_bytes)] = chunk_bytes
        # 更新 header 偏移和长度
        new_off = pos + HEADER_SECTORS
        struct.pack_into('>I', new_header, i * 4, (new_off << 8) | need)
        # 复制或创建时间戳
        ts = struct.unpack_from('>I', old_header, SECTOR + i * 4)[0]
        if ts == 0:
            ts = int(time.time())
        struct.pack_into('>I', new_header, SECTOR + i * 4, ts)
    # 返回结果
    return bytes(new_header + new_body)
