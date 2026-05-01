# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from model.unity_model import *
import model.config.default_config as default_config
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# 定义全局变量
WORLD_HEIGHT_TOP = 320
WORLD_HEIGHT_END = -64
ITEM_COMPOUND_ID_KEYS = [ "id", "Id", "ID",]
ITEM_COMPOUND_ITEM_KEYS = [ "Item", "item", "ITEM",]
CUSTOM_SCAN_DATA_PATH = []
SCAN_BEFORE_PROCESSING = True

MCC_FILE_MODE = "handle"
MCC_FILE_PROCESS_USE = 2
MCC_FILE_SIZE_LIMIT = 4
INVALIT_MCC_FILE_Mode = "skip"


CHUNK_FULL_STATUS_List = ["fullchunk", "full", "minecraft:full", "postprocessed"]
# 计算区块高度
World_Section_Top = int(WORLD_HEIGHT_TOP//16)
World_Section_End = int(WORLD_HEIGHT_END//16)



def Load_Config_File(file_path):
    """加载配置文件"""
    file_path = unity_path(file_path)
    if not os.path.exists(file_path):
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 配置文件加载失败：{YELLOW}文件不存在")
        return False
    try:
        with open(file_path, 'rb') as f:
            config_data = tomllib.load(f)
        return config_data
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 配置文件加载出错：{YELLOW}{e}")
        return False


def load_advanced_config(config_data):
    """加载高级配置项"""
    global WORLD_HEIGHT_TOP
    global WORLD_HEIGHT_END
    global World_Section_Top
    global World_Section_End
    global ITEM_COMPOUND_ID_KEYS
    global ITEM_COMPOUND_ITEM_KEYS
    global CUSTOM_SCAN_DATA_PATH
    global SCAN_BEFORE_PROCESSING
    global MCC_FILE_MODE
    global MCC_FILE_PROCESS_USE
    global MCC_FILE_SIZE_LIMIT
    global INVALIT_MCC_FILE_Mode
    try:
        # 加载配置中
        advanced_config = config_data.get('Advanced', {})
        SCAN_BEFORE_PROCESSING = bool(advanced_config.get('scan_before_processing', True))
        CUSTOM_SCAN_DATA_PATH = list(advanced_config.get('custom_scan_path', []))
        item_compound_key = advanced_config.get('item_compound_key', {})
        WORLD_HEIGHT_TOP = int(advanced_config.get('world_height_top',320))
        WORLD_HEIGHT_END = int(advanced_config.get('world_height_end',-64))
        ITEM_COMPOUND_ID_KEYS = list(item_compound_key.get('id_keys', ['id', 'Id', 'ID']))
        ITEM_COMPOUND_ITEM_KEYS = list(item_compound_key.get('item_keys', ['Item', 'item', 'ITEM']))
        World_Section_Top = int(WORLD_HEIGHT_TOP // 16)
        World_Section_End = int(WORLD_HEIGHT_END // 16)
        mcc_file_config = advanced_config.get('mcc_file', {})
        MCC_FILE_MODE = str(mcc_file_config.get('mcc_file_mode', 'handle'))
        MCC_FILE_PROCESS_USE = int(mcc_file_config.get('mcc_file_process_use', 2))
        MCC_FILE_SIZE_LIMIT = round(float(mcc_file_config.get('mcc_file_size_limit', 4)), 4)
        INVALIT_MCC_FILE_Mode = str(mcc_file_config.get('invalid_mcc_file_mode', 'skip'))
        # 验证配置
        if World_Section_Top <= World_Section_End:
            World_Section_Top = 20
            World_Section_End = -4
            print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 世界最低高度不得大于等于最高高度；已重置")
        if not 1 <= MCC_FILE_PROCESS_USE <= os.cpu_count():
            MCC_FILE_PROCESS_USE = 2
            print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 额外区块处理进程数不得小于1或大于系统逻辑CPU数；已重置")

        return True
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 全局配置加载出错：{YELLOW}{e}")
        return False



def Load_Config(config_data):
    """从配置数据加载配置"""
    try:
        # 读取模式配置
        mode_config = config_data.get('Mode', {})
        main_mode = mode_config.get('Main_Mode', 'block')
        save_path = mode_config.get('Save_Path', '')
        item_scan_mode = mode_config.get('Item_Scan_Mode', 'common')
        process_use = mode_config.get('Process_Use', 4)
        # 读取目标配置
        target_config = config_data.get('Target', {})
        dimensions = target_config.get('Dimensions', [])
        task_config = target_config.get('Task', {})
        select_area = target_config.get('Select_Area', {})
        top_xz = select_area.get('top_xz', [0, 0])
        end_xz = select_area.get('end_xz', [0, 0])
        select_area_tuple = (top_xz, end_xz)
        region_cleaner = target_config.get('Cleaner', {})
        region_cleaner_tick_threshold = region_cleaner.get('tick_threshold', 3600)
        region_cleaner_cooldown = region_cleaner.get('cooldown', 6000)
        region_cleaner_args = (region_cleaner_tick_threshold, region_cleaner_cooldown)

        # 加载高级配置
        if not load_advanced_config(config_data):
            return False
        # 返回配置
        config = {
            "main_mode": main_mode,
            "save_path": save_path,
            "dimensions": dimensions,
            "select_area": select_area_tuple,
            "task_config": task_config,
            "item_scan_mode": item_scan_mode,
            "process_use": process_use,
            "region_cleaner_args": region_cleaner_args
        }
        return config
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 配置加载出错：{YELLOW}{e}")
        return False

def Create_Config_File():
    try:
        with open("mcap_config.toml", "w", encoding="utf-8") as f:
            f.write(default_config.Default_Config_TOML)
        return True
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}[config] 配置创建出错：{YELLOW}{e}")
        return False
