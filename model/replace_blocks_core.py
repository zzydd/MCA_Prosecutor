# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

from multiprocessing import Pool
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn,
)
import mca.nbt as mca_nbt
import mca_tools.mcc_file as mcc_file
import mca_tools.modify_region as modify_region
import mca_tools.minecraft_old as minecraft_old
import model.config.config as mcap_config
from model.unity_model import unity_path
from mca_tools.get_block_states import get_block_states
from mca import Region, EmptyChunk

Full_Chunk_Status = mcap_config.CHUNK_FULL_STATUS_List


# 收集方块种类
def scan_palette_blocks(sections):
    """
    从所有 section 的 palette 中收扫描所有存在的方块类型名称
    返回 set[str]，例如 {"minecraft:stone", "minecraft:air"}
    """
    names = set()
    # 遍历 section
    for section in sections:
        if not section:
            continue
        # 获取 block_states
        block_states = get_block_states(section)
        if not block_states:
            continue
        # 获取 palette
        palette = block_states.get("palette")
        if not palette:
            continue
        # 遍历方块
        for p in palette:
            try:
                names.add(p["Name"].value)
            except KeyError:
                pass
    return names

# 替换方块
def replace_block(section, target_dict):
    # 获取 palette
    block_states = get_block_states(section)
    if not block_states:
        return section
    palette = block_states['palette']
    # 查找并替换所有匹配的方块
    for block_entry in palette:
        block_name = block_entry['Name'].value
        if block_name in target_dict:
            # 替换方块
            block_entry['Name'] = mca_nbt.TAG_String(target_dict[block_name])
            # 删除属性
            if 'Properties' in block_entry:
                del block_entry['Properties']
    # 返回结果
    return section


# 处理单个区块
def processing_chunk(chunk, target_dict):
    # 获取子区块高度
    section_top = mcap_config.World_Section_Top
    section_end = mcap_config.World_Section_End
    # 创建新区块对象
    chunk_new = EmptyChunk(chunk.x, chunk.z, chunk.version, chunk.status, chunk.data)
    modified_sections = []
    # 遍历区块中的 section
    for section_index in range(section_end, section_top):
        try:
            # 读取 section 数据
            section = chunk.get_section(section_index)
            if section is None:
                continue
            # 替换方块
            if chunk.version < 1451:
                # 1.13-
                section_replace = minecraft_old.replace_block(section, target_dict)
            else:
                # 1.13+
                section_replace = replace_block(section, target_dict)
            # 转化section数据
            section_new = modify_region.NBTBackedEmptySection(section_replace)
            # 添加到新区块对象
            chunk_new.add_section(section_new)
            modified_sections.append(section_replace)
        except KeyError:
            modified_sections.append(None)
            continue
    # 处理实体方块数据
    if chunk.tile_entities:
        if chunk.version < 1451:
            # 1.13- 直接复制
            chunk_new.tile_entities = chunk.tile_entities
        else:
            # 1.13+ 删除数据
            existing_blocks = scan_palette_blocks(modified_sections)
            # 过滤并替换实体方块数据
            new_tile_entities = mca_nbt.TAG_List(type=mca_nbt.TAG_Compound, name=chunk.tile_entities.name)
            new_tile_entities.tags = [
                te for te in chunk.tile_entities.tags
                if te.get("id") and te.get("id").value in existing_blocks
            ]
            # 检查tags列表是否为空
            if new_tile_entities.tags:
                chunk_new.tile_entities = new_tile_entities

    # 复制实体数据 (仅 1.18-)
    if chunk.entities:
        chunk_new.entities = chunk.entities
    return chunk_new


# 区块生成器
def chunk_generator(region, target_dict):
    # 遍历所有区块
    for chunk_x in range(32):
        for chunk_z in range(32):
            # 读取区块数据
            try:
                chunk = region.get_chunk(chunk_x, chunk_z)
            except:
                continue
            if not chunk:
                continue
            # 获取区块生成状态
            if chunk.status not in Full_Chunk_Status:
                continue # 跳过未生成完成的区块
            # 处理区块
            chunk_new = processing_chunk(chunk, target_dict)
            # 生成修改后的区块
            yield chunk_new


#【在内存中流式处理区块】(高效!)
def processing_region_mca(region_root_dir, mca_file, target_dict):
    # 读取区域文件
    region_file_path = unity_path(f"{region_root_dir}/{mca_file}")
    with open(region_file_path, 'rb') as f:
        region_data = f.read()
    # noinspection PyBroadException
    try:
        # 加载区域数据
        region = Region(region_data)
    except:
        return
    # 创建区块生成器
    chunk_iter =  chunk_generator(region, target_dict)
    # 流式处理所有区块
    region_data = modify_region.modify_region_bytes_batch(region_data, chunk_iter)
    # 清理无效区块数据
    region_data = modify_region.clean_mca_invalid_bytes(region_data)
    # 保存并写回数据至区域文件
    with open(region_file_path, 'wb') as f:
        f.write(region_data)

#【处理额外区块文件】
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
    chunk_new = processing_chunk(chunk, target_dict)
    # 写入新区块
    mcc_file.save_mcc(mcc_file_path, chunk_new)


def _processing_region_mca_multiprocessing(args):
    """处理区域文件-多进程启动入口"""
    region_root_dir, region_file, target_dict = args
    processing_region_mca(region_root_dir, region_file, target_dict)

def _processing_region_mcc_multiprocessing(args):
    """处理区域文件-多进程启动入口"""
    region_root_dir, region_file, target_dict = args
    processing_region_mcc(region_root_dir, region_file, target_dict)


def MCAP_Replace_Blocks_Core(root_dir, file_list, target_dict, max_processes=1, mode=0):
    """
    MCA Prosecutor 存档处理核心
    用于替换存档中的方块
    :param root_dir: [str] 文件目录，一般是 region 目录
    :param file_list: [str list] 要处理的文件列表，必须在 root_dir 中
    :param target_dict: [(目标方块 str, 用于替换的方块 str) list] 目标方块元组列表
    :param max_processes: [int] 处理使用的进程数量
    :param mode: [int] 处理模式，0=处理.mca文件；1=处理.mcc文件
    """
    # 初始化
    finished_files = 0 # 已处理的的文件
    total_files = len(file_list) # 文件总数
    root_dir = unity_path(root_dir)
    args_list = [(root_dir, region_file, target_dict) for region_file in file_list] # 参数列表
    # 选择处理模式
    if mode == 0: # 处理.mca
        progress_function = _processing_region_mca_multiprocessing
        progress_str = "正在处理区域数据..."
    elif mode == 1: # 处理.mcc
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
