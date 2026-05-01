# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from model.unity_model import unity_path

def scan_dimensions(save_path):
    """
    扫描获取存档中的所有维度及其目录
    :param save_path: 存档根目录
    :return: 维度信息字典列表 [{"name":"spacename:id"; path:"relative_path"}]
    """
    # 维度列表
    dimension_list = []
    save_path = unity_path(save_path)
    # 主世界
    overworld_path = f"{save_path}/region"
    if os.path.exists(overworld_path):
        dimension_list.append({
            "name": f"minecraft:overworld",
            "path": f"."
        })
    # 下界
    overworld_path = f"{save_path}/DIM-1/region"
    if os.path.exists(overworld_path):
        dimension_list.append({
            "name": f"minecraft:the_nether",
            "path": f"DIM-1"
        })
    # 末地
    overworld_path = f"{save_path}/DIM1/region"
    if os.path.exists(overworld_path):
        dimension_list.append({
            "name": f"minecraft:the_end",
            "path": f"DIM1"
        })

    # 其他维度
    dimensions_root = f"{save_path}/dimensions"
    # 扫描根目录
    if not os.path.isdir(dimensions_root):
        return dimension_list
    # 获取命名空间
    for namespace in os.listdir(dimensions_root):
        namespace_path = f"{dimensions_root}/{namespace}"
        # 扫描命名空间根目录
        if not os.path.isdir(namespace_path):
            continue
        # 获取维度名称
        for dimension_id in os.listdir(namespace_path):
            dimension_path = f"{namespace_path}/{dimension_id}"
            # 扫描维度名称根目录
            if not os.path.isdir(dimension_path):
                continue
            # 添加维度字典至列表
            dimension_list.append({
                "name": f"{namespace}:{dimension_id}",
                "path": f"dimensions/{namespace}/{dimension_id}"
            })
    # 返回数据
    return dimension_list
