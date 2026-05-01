# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import gzip
from io import BytesIO
from multiprocessing import Pool
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn
)
import mca.nbt as mca_nbt
import mca_tools.mcc_file as mcc_file
import mca_tools.modify_entities as modify_entities
import mca_tools.modify_region as modify_region
import mca_tools.minecraft_old as minecraft_old
import model.config.config as mcap_config
from model.unity_model import unity_path
from mca import Region

Full_Chunk_Status = mcap_config.CHUNK_FULL_STATUS_List


def process_compound_id(container, target_dict, id_keys):
    """
    在一个 TAG_Compound 中尝试处理 id
    返回 "replace" / "remove" / None
    """
    for key in id_keys:
        if key not in container:
            continue
        # 获取原本的旧值
        tag = container[key]
        old_id = tag.value
        try:
            if old_id not in target_dict:
                continue
        except:
            continue
        # 获取对应的新值
        new_id = target_dict[old_id]
        # 判断是否删除
        if new_id is None:
            return "remove"
        # 执行替换
        if isinstance(new_id, int):
            tag.value = new_id # 1.8- 用整数ID
        else:
            container[key] = mca_nbt.TAG_String(new_id)
        return "replace"
    return None

def process_item_compound(compound, target_dict):
    """
    若该 TAG_Compound 是物品，执行替换
    返回 "replace" / "remove" / None
    """
    if not isinstance(compound, mca_nbt.TAG_Compound):
        return None
    # 字段识别关键词
    id_keys = mcap_config.ITEM_COMPOUND_ID_KEYS
    item_keys = mcap_config.ITEM_COMPOUND_ITEM_KEYS
    # 直接物品格式
    action = process_compound_id(compound, target_dict, id_keys)
    if action:
        return action
    # 嵌套物品格式
    for ikey in item_keys:
        if ikey in compound and isinstance(compound[ikey], mca_nbt.TAG_Compound):
            action = process_compound_id(compound[ikey], target_dict, id_keys)
            if action:
                return action
            break
    return None

def replace_items_nbt(root, target_dict):
    """递归扫描 NBT 标签"""
    modified = False
    #【处理 TAG_List】
    if isinstance(root, mca_nbt.TAG_List):
        new_tags = []
        for elem in root:
            # 处理物品标签
            if isinstance(elem, mca_nbt.TAG_Compound):
                action = process_item_compound(elem, target_dict)
                if action == "remove":
                    modified = True
                    continue          # 从列表中删除该 item（正确）
                if action == "replace":
                    modified = True
            # 递归所有子标签
            if isinstance(elem, (mca_nbt.TAG_List, mca_nbt.TAG_Compound)):
                if replace_items_nbt(elem, target_dict):
                    modified = True
            new_tags.append(elem)
        # 若被修改，则写回
        if modified:
            try:
                root.tags = new_tags
            except Exception:
                root.clear()
                for t in new_tags:
                    root.append(t)
        return modified
    #【处理 TAG_Compound】
    if isinstance(root, mca_nbt.TAG_Compound):
        # 遍历 key, val
        for key, val in list(root.items()):
            # 若是 compound 判断是否需要删除
            if isinstance(val, mca_nbt.TAG_Compound):
                action = process_item_compound(val, target_dict)
                if action == "remove":
                    # 若需删除，直接删除字段
                    try:
                        del root[key]
                    except Exception:
                        root.pop(key, None)
                    modified = True
                    continue
                if action == "replace":
                    modified = True
            # 递归处理子标签
            if isinstance(val, (mca_nbt.TAG_List, mca_nbt.TAG_Compound)):
                if replace_items_nbt(val, target_dict):
                    modified = True
        return modified
    #【其他 TAG】
    return False


def processing_chunk(chunk, target_dict):
    # 固定原始字典
    target_dict_raw = target_dict
    # 转换区块对象类型 (不修改，直接转)
    chunk_new = modify_region.NBTBackedEmptyChunk(chunk)
    # 1.8-: 转化替换列表
    if chunk.version < 100:
        target_id_dict = minecraft_old.convert_target_dict(target_dict_raw)
        target_dict = target_dict_raw | target_id_dict
    else:
        target_dict = target_dict_raw

    # 扫描实体方块数据并替换物品
    modified_tile_entities = False
    if chunk.tile_entities:
        modified_tile_entities = False
        for tag in chunk.tile_entities.tags:
            if replace_items_nbt(tag, target_dict):
                modified_tile_entities = True
        if modified_tile_entities:
            chunk_new.tile_entities = chunk.tile_entities

    # 扫描实体数据并替换物品 (仅1.18-)
    modified_entities = False
    if chunk.entities:
        for tag in chunk.entities.tags:
            if replace_items_nbt(tag, target_dict):
                modified_entities = True
        if modified_entities:
            chunk_new.entities = chunk.entities

    return modified_tile_entities, modified_entities, chunk_new


def chunk_generator(region, target_dict):
    """区块生成器，用于批量流式处理 (区域.mca)"""
    # 遍历所有区块
    for chunk_x in range(32):
        for chunk_z in range(32):
            # 读取区块数据
            try:
                chunk = region.get_chunk(chunk_x, chunk_z)
                if not chunk:
                    continue
            except:
                continue
            # 获取区块生成状态
            if chunk.status not in Full_Chunk_Status:
                # 跳过未生成完成的区块
                continue
            # 处理区块
            modified_tile_entities, modified_entities, chunk_new = processing_chunk(chunk, target_dict)
            # 返回生成器
            if modified_tile_entities or modified_entities:
                yield chunk_new


def processing_region_mca(region_root_dir, mca_file, target_dict):
    """在内存中流式处理 区域.mca"""
    # 读取区域文件
    region_file_path = unity_path(f"{region_root_dir}/{mca_file}")
    with open(region_file_path, 'rb') as f:
        region_data = f.read()
    try:
        # 加载区域数据
        region = Region(region_data)
    except:
        return
    # 创建区块生成器
    chunk_iter = chunk_generator(region, target_dict)
    # 流式处理所有区块
    region_data = modify_region.modify_region_bytes_batch(region_data, chunk_iter)
    # 清理无效区块数据
    region_data = modify_region.clean_mca_invalid_bytes(region_data)
    # 保存并写回数据至区域文件
    with open(region_file_path, 'wb') as f:
        f.write(region_data)


def processing_region_mcc(root_dir, file, target_dict):
    # 检查.mcc文件是否合法
    mcc_file_path = unity_path(f"{root_dir}/{file}")
    size_limit = mcap_config.MCC_FILE_SIZE_LIMIT
    invalid_mode = mcap_config.INVALIT_MCC_FILE_Mode
    if not mcc_file.check_mcc_file(mcc_file_path, size_limit, invalid_mode):
        return
    # 从.mcc文件中加载区块
    chunk = mcc_file.load_mcc(mcc_file_path)
    if not chunk:
        return
    # 获取区块生成状态
    if chunk.status not in Full_Chunk_Status:
        return  # 跳过未生成完成的区块
    # 处理区块
    modified_tile_entities, modified_entities, chunk_new = processing_chunk(chunk, target_dict)
    # 写回文件
    if modified_tile_entities or modified_entities:
        mcc_file.save_mcc(mcc_file_path, chunk_new)


def processing_entities_mca(entities_root_dir, mca_file, target_dict):
    """在内存中处理 实体.mca"""
    # 读取区域文件
    entities_file_path = unity_path(f"{entities_root_dir}/{mca_file}")
    with open(entities_file_path, 'rb') as f:
        region_data = f.read()
    try:
        # 加载区域数据
        region = Region(region_data)
    except:
        return
    # 转化替换列表为字典
    modified_chunks = {}
    # 遍历所有区块
    for cx in range(32):
        for cz in range(32):
            try:
                nbt_root = region.chunk_data(cx, cz)
            except Exception:
                continue
            if not nbt_root or "Entities" not in nbt_root:
                continue
            entities = nbt_root["Entities"]
            if not isinstance(entities, mca_nbt.TAG_List):
                continue
            modified = False
            # 遍历所有实体所有NBT
            for ent in entities:
                if isinstance(ent, mca_nbt.TAG_Compound):
                    if replace_items_nbt(ent, target_dict):
                        modified = True
            # 将修改过的区块添加到map
            if modified:
                modified_chunks[cz * 32 + cx] = nbt_root
    # 编辑实体.mca数据
    region_data = modify_entities.modify_entities_mca(region_data, modified_chunks)
    # 清理无效区块数据
    region_data = modify_region.clean_mca_invalid_bytes(region_data)
    # 保存并写回数据至区域文件
    with open(entities_file_path, 'wb') as f:
        f.write(region_data)


def processing_data_file(data_root_dir, data_file, target_dict):
    """在内存中处理 NBT.dat"""
    # 读取.dat文件并加载NBT数据
    try:
        data_file_path = unity_path(f"{data_root_dir}/{data_file}")
        nbt_root = mca_nbt.NBTFile(filename=data_file_path)
    except Exception:
        return
    # 扫描并删除替换物品
    modified = replace_items_nbt(nbt_root, target_dict)
    # 判断是否被编辑
    if not modified:
        return
    # 保存为gzip
    buf = BytesIO()
    nbt_root.write_file(buffer=buf)
    # 写回文件
    with gzip.open(data_file_path, "wb") as f:
        f.write(buf.getvalue())


def _processing_region_mca_multiprocessing(args):
    """处理 区域.mca：多进程启动入口"""
    region_root_dir, region_file, target_dict = args
    processing_region_mca(region_root_dir, region_file, target_dict)

def _processing_region_mcc_multiprocessing(args):
    """处理 区域.mca：多进程启动入口"""
    region_root_dir, region_file, target_dict = args
    processing_region_mcc(region_root_dir, region_file, target_dict)

def _processing_entities_mca_multiprocessing(args):
    """处理 实体.mca：多进程启动入口"""
    entities_root_dir, region_file, target_dict = args
    processing_entities_mca(entities_root_dir, region_file, target_dict)

def _processing_data_file_multiprocessing(args):
    """处理 NBT.dat：多进程启动入口"""
    data_root_dir, region_file, target_dict = args
    processing_data_file(data_root_dir, region_file, target_dict)


def MCAP_Replace_Items_Core(root_dir, file_list, target_dict, max_processes=1, mode=0):
    """
    MCA Prosecutor 存档处理核心
    用于处理存档文件夹中包含目标方块的区域文件
    :param root_dir: [str] 文件目录
    :param file_list: [str list] 要处理的文件列表，必须在 root_dir 中
    :param target_dict: [(目标方块 str, 用于替换的方块 str) list] 目标方块元组列表
    :param max_processes: [int] 处理使用的进程数量
    :param mode: [int] 处理模式，0=区域.mca；1=实体.mca；2=NBT.dat；3=玩家.dat；4=区域.mcc
    """
    # 初始化
    finished_files = 0 # 已处理的的文件
    total_files = len(file_list) # 文件总数
    root_dir = unity_path(root_dir)
    args_list = [(root_dir, region_file, target_dict) for region_file in file_list] # 参数列表
    # 选择处理模式
    if mode == 0:
        progress_function = _processing_region_mca_multiprocessing
        progress_str = "正在处理区域数据..."
    elif mode == 1:
        progress_function = _processing_entities_mca_multiprocessing
        progress_str = "正在处理实体数据..."
    elif mode == 2:
        progress_function = _processing_data_file_multiprocessing
        progress_str = "正在处理数据文件..."
    elif mode == 3:
        progress_function = _processing_data_file_multiprocessing
        progress_str = "正在处理玩家数据..."
    elif mode == 4:
        progress_function = _processing_region_mcc_multiprocessing
        progress_str = "正在处理额外区块..."
    else:
        return
    # 创建线程池
    with Pool(processes=max_processes) as pool:
        # 创建进度条
        with Progress(
                SpinnerColumn(spinner_name="dots", style="bright_yellow"),  # 旋转小组件
                TextColumn("[progress.description]{task.description}"),  # 描述
                BarColumn(),  # 进度条
                TextColumn("[bright_green]{task.percentage:>6.2f}%[/]"),  # 百分比
                TimeRemainingColumn(),  # 剩余时间
                TextColumn("[yellow]{task.completed}/{task.total}[/]"),  # 已完成/总数
        ) as progress:
            main_progress = progress.add_task(f'[bright_cyan]{progress_str}', total=total_files)
            # 启动进程池
            for _ in pool.imap_unordered(progress_function, args_list, chunksize=1):
                # 结果统计
                finished_files += 1
                # 更新进度条
                progress.update(main_progress, completed=finished_files)