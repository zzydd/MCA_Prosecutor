# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

from multiprocessing import Pool
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn
)
import model.config.config as mcap_config
from model.unity_model import unity_path
from mca_tools.get_block_states import get_block_states
from mca import Region

Full_Chunk_Status = mcap_config.CHUNK_FULL_STATUS_List

# 扫描区域文件
def scan_region_mca(region_root_dir, mca_file, target_dict):
    """扫描区域文件，判断是否包含目标方块"""
    # 读取区域文件
    region_file_path = unity_path(f"{region_root_dir}/{mca_file}")
    with open(region_file_path, 'rb') as f:
        region_data = f.read()
    # noinspection PyBroadException
    try:
        region = Region(region_data)
    except:
        return None
    # 将目标方块转化成元组，让比对更快！
    target_blocks = {
        tuple(k.split(":", 1))
        for k in target_dict.keys()
    }
    # 获取子区块高度
    section_top = mcap_config.World_Section_Top
    section_end = mcap_config.World_Section_End
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
            # 遍历 section
            for section_index in range(section_end, section_top):
                # 获取 section 数据
                section = chunk.get_section(section_index)
                if section is None:
                    continue
                # 获取 block_states 数据
                block_states = get_block_states(section)
                if not block_states:
                    continue
                palette = block_states['palette']
                for pe in palette:
                    name = pe['Name'].value
                    ns, bid = name.split(':', 1)
                    # 目标方块判断
                    if (ns, bid) in target_blocks:
                        # 发现目标方块！即刻返回！
                        return mca_file
    # 没找到目标方块
    return None

# 扫描区域文件-多进程启动入口
def _scan_region_mca_multiprocessing(args):
    """扫描区域文件-多进程启动入口"""
    region_root_dir, region_file, target_dict = args
    return scan_region_mca(region_root_dir, region_file, target_dict)

def MCAP_Scan_Blocks_Core(region_root_dir, region_file_list, target_dict, max_processes=1):
    """
    MCA Prosecutor 存档扫描核心
    用于扫描存档文件夹中包含目标方块的区域文件
    :param region_root_dir: [str] 区域文件(存档)根目录
    :param region_file_list: [str list] 要扫描的文件列表
    :param target_dict: [(目标方块 str, 用于替换的方块 str) list] 目标方块元组列表
    :param max_processes: [int] 扫描使用的进程数量
    :return: [str list] 包含目标方块的区域文件列表
    """
    # 初始化
    finished_files = 0 # 已扫描的的文件
    included_files_list = [] # 扫描结果(包含目标方块的区域)
    total_files = len(region_file_list) # 文件总数
    region_root_dir = unity_path(region_root_dir)
    args_list = [(region_root_dir, region_file, target_dict) for region_file in region_file_list] # 参数列表
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
            scan_progress = progress.add_task('[bright_cyan]正在扫描存档数据...', total=total_files)

            # 启动进程池
            for region_file, result in zip(region_file_list,
                                           pool.imap_unordered(_scan_region_mca_multiprocessing, args_list, chunksize=1)):
                # 结果统计
                finished_files += 1
                if result:  # 找到了目标方块
                    included_files_list.append(result)
                else:
                    pass
                # 更新进度条
                progress.update(scan_progress, completed=finished_files)
    # 返回总结果
    return included_files_list