# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

"""
用来处理额外区块文件：.mcc
如果区块大小大于 1020KiB 则将数据保存到.mcc文件
同时也意味这该区块包含大量数据，将花费非常多的时间来处理
"""
import os
import zlib
import mca.nbt as nbt
from mca import Chunk
from io import BytesIO
from mca_tools.modify_region import NBTBackedEmptyChunk


def check_mcc_file(file_path, max_size = 1024*1024 * 4, invalid_mode="skip"):
    """检查.mcc文件是否合法"""
    # 检查大小
    if os.path.getsize(file_path) > max_size:
        # 处理模式：直接删除
        if invalid_mode.lower() == "delete":
            try:
                os.remove(file_path)
            except:
                pass
            return False
        # 处理模式：无视风险，继续处理
        elif invalid_mode.lower() == "handle":
            return True
        else:
            return False
    return True


def load_mcc(file_path: str) -> Chunk:
    """ 加 .mcc 文件为 Chunk 对象 """
    with open(file_path, "rb") as f:
        data = f.read()
    nbt_data = nbt.NBTFile(buffer=BytesIO(zlib.decompress(data)))
    chunk = Chunk(nbt_data)
    return chunk


def save_mcc(file_path: str, chunk):
    """ 保存 EmptyChunk 为 .mcc """
    chunk = NBTBackedEmptyChunk(chunk)
    # noinspection PyProtectedMember
    root = chunk._nbt
    buf = BytesIO()
    root.write_file(buffer=buf)
    compressed = zlib.compress(buf.getvalue())
    with open(file_path, "wb") as f:
        f.write(compressed)

