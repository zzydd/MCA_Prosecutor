# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later

def get_block_states(section):
    """
    从 section 中统一获取 block_states
    返回格式：
    {
        'palette': TAG_List,
        'data': TAG_Long_Array | None
    }
    """
    # 1.18+
    if 'block_states' in section:
        bs = section['block_states']
        return {
            'palette': bs.get('palette'),
            'data': bs.get('data')
        }
    # 1.18-
    if 'Palette' in section:
        return {
            'palette': section['Palette'],
            'data': section.get('BlockStates')
        }
    return None