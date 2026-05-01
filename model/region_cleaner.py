# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from multiprocessing import Pool
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    TimeRemainingColumn,
)
import mca_tools.modify_region as modify_region
import model.config.config as mcap_config
from model.unity_model import unity_path
from mca import Region, EmptyChunk

Full_Chunk_Status = mcap_config.CHUNK_FULL_STATUS_List

# 区块生成器
def chunk_generator(region, tick_threshold:int, cooldown=-1):
    try:
        cooldown = int(cooldown)
        tick_threshold = int(tick_threshold)
    except:
        return
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
            # 删除未完全生成的区块
            if chunk.status not in Full_Chunk_Status:
                yield EmptyChunk(chunk_x, chunk_z, data=False)
            # 获取玩家存在时间
            try:
                inhabited_time = chunk.data['InhabitedTime'].value
            except:
                continue
            # 获取区块修改时间
            try:
                last_update = chunk.data['LastUpdate'].value
            except:
                last_update = 0
            # 判断修改间隔冷却
            if last_update <= cooldown:
                continue
            # 判断玩家活动时间
            if inhabited_time > tick_threshold:
                continue
            # 返回空区块生成器 (删除区块)
            yield EmptyChunk(chunk_x, chunk_z, data=False)

# 识别全空的区域
def is_empty_region(region_bytes):
    return len(region_bytes) >= 4096 and not any(region_bytes[:4096])

#【在内存中流式处理区块】
def processing_region_mca(region_root_dir, mca_file, tick_threshold, cooldown=-1):
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
    chunk_iter =  chunk_generator(region, tick_threshold, cooldown)
    # 流式处理所有区块
    region_data = modify_region.modify_region_bytes_batch(region_data, chunk_iter)
    # 清理无效区块数据
    region_data = modify_region.clean_mca_invalid_bytes(region_data)
    # 识别全空区域
    if is_empty_region(region_data):
        try:
            # 删除全空区域
            os.remove(region_file_path)
            return
        except:
            pass
    # 写回数据至区域文件
    with open(region_file_path, 'wb') as f:
        f.write(region_data)


def _processing_region_mca_multiprocessing(args):
    """处理区域文件-多进程启动入口"""
    region_root_dir, region_file, tick_threshold, cooldown = args
    processing_region_mca(region_root_dir, region_file, tick_threshold, cooldown)

def delete_mca_file_multiprocessing(args):
    root_dir, region_file, _, _ = args
    file_path = unity_path(f"{root_dir}/{region_file}")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass

def MCAP_Region_Cleaner_Core(root_dir, file_list, region_cleaner_args, max_processes=1, mode=0):
    """
    MCA Prosecutor 存档处理核心
    存档瘦身，用于清理那些已加载但没怎么修改过的跑图区块
    :param root_dir: [str] 文件目录，一般是 region 目录
    :param file_list: [str list] 要处理的文件列表，必须在 root_dir 中
    :param region_cleaner_args: 时间参数元组 (时间阈值, 冷却时间, 保存时间)
    :param max_processes: [int] 处理使用的进程数量
    :param mode: [int] 清理模式，0=清理region.mca；1=清理entities.mca, 2=清理poi.mca
    """
    # 初始化
    finished_files = 0 # 已处理的的文件
    total_files = len(file_list) # 文件总数
    tick_threshold, cooldown = region_cleaner_args # 解析参数
    root_dir = unity_path(root_dir)
    args_list = [(root_dir, region_file, tick_threshold, cooldown) for region_file in file_list] # 参数列表
    # 选择处理模式
    if mode == 0:
        progress_function = _processing_region_mca_multiprocessing
        progress_str = "正在清理存档...."
    elif mode == 1:
        progress_function = delete_mca_file_multiprocessing
        progress_str = "清理无效实体...."
    elif mode == 2:
        progress_function = delete_mca_file_multiprocessing
        progress_str = "清理无效兴趣点.."
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

