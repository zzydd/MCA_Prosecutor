# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later
Copyright = "Copyright (C) 2026 ZZYDD"

import time
from pathlib import Path

# 获取当前格时间
def get_datetime():
    """获取当前格式化时间（包含毫秒）"""
    return time.strftime('%Y-%m-%d %H:%M:%S')

# 统一文件路径
def unity_path(path):
    """跨平台统一文件路径格式"""
    unity_path = Path(str(path)).as_posix()
    return unity_path


# 颜色封装
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'
GRAY = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
BRIGHT_WHITE = '\033[97m'
RESET = '\033[0m'
WHITE_ON_RED = '\033[1;41;37m '