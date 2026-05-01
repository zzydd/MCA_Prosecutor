# Copyright (C) 2026 ZZYDD
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import re
import sys
import signal
import nbtlib
import colorama
from rich.panel import Panel
from rich.console import Console
from model.unity_model import *
from model.scan_dimensions import scan_dimensions
from model.scan_blocks_core import MCAP_Scan_Blocks_Core
from model.region_cleaner import MCAP_Region_Cleaner_Core
from model.replace_items_core import MCAP_Replace_Items_Core
from model.replace_blocks_core import MCAP_Replace_Blocks_Core
import model.config.config as mcap_config
# 尝试导入图标
try:
    from model.cli_logo import *
except ImportError:
    pass

# 初始化
colorama.init()
Terminal = Console(color_system='auto', style=None)
Project = unity_path(os.path.realpath(sys.argv[0]))
MainPath = unity_path(os.path.dirname(Project))
os.chdir(MainPath)

def cutline(long):
    try:
        long = int(long)
    except:
        long = 0
    return "="*long


def show_logo(cls=0):
    if cls == 1:
        Console().clear()
        if os.name == "nt":
            os.system("cls")
    # 计算偏移
    if Terminal.width <= 40:
        program_logo_lef_space = ""
    elif 40 < Terminal.width < 90:
        program_logo_lef_space = (" " * int((Terminal.width - 40) / 2 + 1))
    else:
        program_logo_lef_space = (" " * int((Terminal.width - 90) / 2 + 1))
    # 程序Logo
    newline = "\n"
    if Terminal.width >= 90:
        program_logo = (rf"{newline}"
        rf"{program_logo_lef_space}[red]   __  ___[green]  _____[bright_blue]   ___      [yellow]   ___                                   __             [/]{newline}"
        rf"{program_logo_lef_space}[red]  /  |/  /[green] / ___/[bright_blue]  / _ |     [yellow]  / _ \  ____ ___   ___ ___  ____ __ __ / /_ ___   ____ [/]{newline}"
        rf"{program_logo_lef_space}[red] / /|_/ / [green]/ /__  [bright_blue] / __ |     [yellow] / ___/ / __// _ \ (_--/ -_)/ __// // // __// _ \ / __/ [/]{newline}"
        rf"{program_logo_lef_space}[red]/_/  /_/  [green]\___/  [bright_blue]/_/ |_|     [yellow]/_/    /_/   \___//___/\__/ \__/ \_,_/ \__/ \___//_/    [/]{newline}"
        rf"{newline}")
    else:
        program_logo = (rf"{newline}"
        rf"{program_logo_lef_space}[red]   __  ___[green]  _____[bright_blue]   ___  [yellow]   ___  [/]{newline}"
        rf"{program_logo_lef_space}[red]  /  |/  /[green] / ___/[bright_blue]  / _ | [yellow]  / _ \ [/]{newline}"
        rf"{program_logo_lef_space}[red] / /|_/ / [green]/ /__  [bright_blue] / __ | [yellow] / ___/ [/]{newline}"
        rf"{program_logo_lef_space}[red]/_/  /_/  [green]\___/  [bright_blue]/_/ |_| [yellow]/_/     [/]{newline}"
        rf"{newline}")
    Terminal.print(Panel(f'{program_logo}', border_style="cyan"), style="bold")


# 获取游戏版本
def get_game_version(data_file):
    data_file = unity_path(data_file)
    nbt_file = nbtlib.load(data_file)
    level_data = nbt_file.get("Data", nbt_file)
    version_data = level_data.get("Version")
    level_name = level_data.get("LevelName", "Unknow-World")
    if version_data:
        version_id = int(version_data.get("Id",0))
        version_name = version_data.get("Name","Unknow")
    else:
        version_id = 0
        version_name = "old (<1.9)"
    return version_id, version_name, level_name

# 检查单人档数据是否存在
def check_single_player_data(data_file):
    data_file = unity_path(data_file)
    nbt_file = nbtlib.load(data_file)
    level_data = nbt_file.get("Data", nbt_file)
    player_data = level_data.get("Player", None)
    if player_data:
        return True
    return False


# 获取文件夹大小
def get_folder_size(path):
    path = unity_path(path)
    return sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(path)
        for filename in filenames
    )


# 容量单位换算
def get_file_size_str(bytes_size):
    if bytes_size < 1024:
        size_str = f"{int(bytes_size)}B"
    elif 1024 <= bytes_size < 1024 * 1024:
        size_str = f"{round(bytes_size / 1024, 3):.2f}KB"
    elif 1024 * 1024 <= bytes_size < 1024 * 1024 * 1024:
        size_str = f"{round(bytes_size / (1024 * 1024), 3):.2f}MB"
    elif 1024 * 1024 * 1024 <= bytes_size < 1024 * 1024 * 1024 * 1024:
        size_str = f"{round(bytes_size / (1024 * 1024 * 1024), 3):.2f}GB"
    else:
        size_str = f"{round(bytes_size / (1024 * 1024 * 1024 * 1024), 4):.3f}TB"
    return size_str


# #【程序描述页】
# def Page_Description():
#     show_logo(1)
#     print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【程序描述】{BRIGHT_MAGENTA}《{cutline(30)}\n")
#     print(f"{BRIGHT_YELLOW}MCA Prosecutor {YELLOW}是一款存档处理工具")
#     print(f"它可以删除和替换存档中指定的物品或者方块")
#     print(f"通过直接读取存档文件来扫描目标方块或物品")
#     print(f"以此确保不会漏掉世界中任何一个方块和容器")
#     print(f"\n{BRIGHT_CYAN}支持的MC存档版本：{BRIGHT_GREEN}1.2.1 ~ 26.1.2+\n")
#     print(f"{GRAY}by: ZZYDD 2026.05.01")
#     print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
#     # 回车继续
#     print(f"{BRIGHT_RED}【警告】执行任何操作前请先备份存档！\n")
#     _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车继续>{BRIGHT_YELLOW}")
#     print(f"{RESET}")


# 【程序描述页】
def Page_Description():
    show_logo(1)
    # 左侧输出列表
    left_lines = [
        "",
        f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【程序描述】{BRIGHT_MAGENTA}《{cutline(30)}\n",
        "",
        f"{BRIGHT_YELLOW}MCA Prosecutor {YELLOW}是一款存档处理工具",
        f"{YELLOW}它可以删除和替换存档中指定的物品或者方块",
        f"{YELLOW}通过直接读取存档文件来扫描目标方块或物品",
        f"{YELLOW}以此确保不会漏掉世界中任何一个方块和容器",
        "",
        f"{BRIGHT_CYAN}支持的MC存档版本：{BRIGHT_GREEN}1.2.1 ~ 26.1.2+",
        "",
        f"{GRAY}by: ZZYDD 2026.05.01", # 这是我的版权信息！禁止修改或删除！
        f"{BRIGHT_MAGENTA}{cutline(76)}",
        ""
    ]
    # 打印左侧内容
    for line in left_lines:
        print(line)
    # 加载图标
    try:
        logo_lines = COLORFUL_LOGO.strip("\n").split("\n")
    except:
        logo_lines = None

    # 计算空格数
    if Terminal.width >= 113:
        right_move = 80
    else:
        right_move = 80 - (113 - Terminal.width)

    # 打印右侧logo
    if logo_lines and Terminal.width >= 100:
        # 向上移动光标
        up_lines = len(left_lines) + 2
        print(f"\033[{up_lines}A", end="")

        for line in logo_lines:
            # 向右移动广播
            print(f"\033[{right_move}C", end="")
            # 使用rich输出单行logo
            Terminal.print(line)
        # 复位光标
        down_lines = max(0, up_lines - len(logo_lines))
        if down_lines > 0:
            # 向下移动光标
            print(f"\033[{down_lines}B", end="")

    # 底部正常输出
    print(f"{BRIGHT_RED}【警告】执行任何操作前请先备份存档！\n")
    try:
        _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车继续>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(f"{RESET}")


#【界面-程序功能】
def Page_Home():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【功能选择】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}【1】{BRIGHT_CYAN}替换方块：{GRAY}删除或替换指定的方块")
        print(f"{YELLOW}【2】{BRIGHT_CYAN}替换物品：{GRAY}删除或替换指定的物品")
        print(f"{YELLOW}【3】{BRIGHT_CYAN}存档清理：{GRAY}删除已生成的跑图区块")
        print(f"{YELLOW}【C】{BRIGHT_CYAN}配置文件：{GRAY}进入配置文件模式")
        print(f"{YELLOW}【H】{BRIGHT_CYAN}程序帮助：{GRAY}显示程序帮助信息")
        print(f"{YELLOW}【E】{BRIGHT_CYAN}退出程序：{GRAY}其余界面返回首页")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        #输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            choice = input(f"{CYAN}【→】{BRIGHT_GREEN}请输入功能序号：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 判断输入
        if choice.upper() == "C":
            return "C"
        elif choice.upper() == "H":
            return "H"
        elif choice.upper() == "E":
            return False
        elif not choice:
            input_error_info = "未输入任何内容"
            continue
        else:
            try:
                choice = int(choice)
            except Exception:
                input_error_info = "输入的内容无效"
                continue
            if not 1 <= choice <= 3:
                input_error_info = "无效的选项"
                continue
            return choice


#【界面-选择存档】
def Page_Select_Save(allowed_version = 0):
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【选择存档】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}输入需要处理的存档路径，请确保存档保版本支持！\n")
        print(f"{YELLOW}支持的MC存档版本：{BRIGHT_GREEN}1.2.1 ~ 26.1.2+")
        if allowed_version:
            print(f"{YELLOW}当前模式数据版本需 {BRIGHT_CYAN}≥{allowed_version}")
        print(f"\n{GRAY}只要新版本没改存档格式，理论上也支持")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        #输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            save_path = input(f"{CYAN}【→】{BRIGHT_GREEN}请输入存档路径：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        if save_path.upper() == "E":
            return False
        # 验证输入
        save_path = unity_path(save_path)
        result_state, result = verify_select_save(save_path, allowed_version)
        if not result_state:
            input_error_info = result
            continue
        # 1.9-: 低版本警告
        if result[3] == 0:
            print(f"{YELLOW}[WARN] 当前选择的存档为 1.9 以前的版本，可能存在兼容问题\n")
            confirm = input(f"{CYAN}【→】{BRIGHT_GREEN}退出请输E，回车继续：{BRIGHT_YELLOW}")
            print(f"{RESET}")
            if confirm.upper() == "E":
                return False
        return result

def verify_select_save(save_path, allowed_version = 0):
    try:
        try:
            allowed_version = int(allowed_version)
        except:
            allowed_version = 0
        # 读取存档信息文件
        save_path = unity_path(save_path)
        level_data_file = f"{save_path}/level.dat"
        # 检查目录是否存在
        if not os.path.isdir(save_path):
            error_info = "存档目录不存在，请检存档查路径"
            return False, error_info
        # 检查存档是否存在
        if not os.path.isfile(level_data_file):
            error_info = "level.dat 文件不存在，请检存档查路径"
            return False, error_info
        # 获取存档信息
        level_version_id, level_version_str, level_name = get_game_version(level_data_file)
        # 比对版本
        if level_version_id < allowed_version:
            error_info = f"不允许的版本！数据版本需 ≥{allowed_version} ；当前 {level_version_str} 数据版本 {level_version_id}；"
            return False, error_info
        return True, (save_path, level_name, level_version_str, level_version_id)
    except Exception as e:
        error_info = f"无法验证存档信息：{e}"
        return False, error_info


#【界面-选择方块】
def Page_Select_Block():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【选择方块】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}请按照下面的格式填写要替换的方块\n")
        print(f"{BRIGHT_GREEN}minecraft:dirt{YELLOW} > {BRIGHT_CYAN}minecraft:air{BRIGHT_RED} ; "
              f"{BRIGHT_GREEN}minecraft:bedrock{YELLOW} > {BRIGHT_CYAN}minecraft:stone\n")
        print(f"{YELLOW}格式说明：{BRIGHT_GREEN}绿色{YELLOW}为目标方块，{BRIGHT_CYAN}蓝色{YELLOW}为替换方块，用 {BRIGHT_YELLOW}> {YELLOW}连接")
        print(f"{YELLOW}          可同时输入多组，每组之间用{BRIGHT_RED} ; {YELLOW}分隔，空格不影响解析")
        print(f"{GRAY}\n颜色仅作为示例，实际输入不会上色\n")
        print(f"{BRIGHT_RED}注意：所有符号必须用英文输入！")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            input_data = input(f"{CYAN}【→】{BRIGHT_GREEN}请按格式输入要替换的方块：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 返回判断
        if input_data.upper()=="E":
            return False
        # 判断格式
        pattern = re.compile(
            r'^\s*'
            r'[a-z0-9_.-]+:[a-z0-9_.\-/]+\s*>\s*[a-z0-9_.-]+:[a-z0-9_.\-/]+'
            r'(?:\s*;\s*[a-z0-9_.-]+:[a-z0-9_.\-/]+\s*>\s*[a-z0-9_.-]+:[a-z0-9_.\-/]+)*'  
            r'\s*$',
            re.IGNORECASE
        )
        if re.match(pattern, input_data):
            input_data = input_data.replace(" ", "")
        else:
            input_error_info = "格式错误，请重新输入！"
            continue
        # 转化输入为目标任务字典
        target_dict = {}
        for group in input_data.split(";"):
            target = group.split(">")
            target_dict[target[0]] = target[1]
        # 返回结果
        return target_dict


#【界面-选择方块】
def Page_Select_Item():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【选择物品】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}请按照下面的格式填写要替换的物品\n")
        print(f"{BRIGHT_GREEN}minecraft:apple{YELLOW} > {BRIGHT_CYAN}None{BRIGHT_RED} ; "
              f"{BRIGHT_GREEN}minecraft:diamond{YELLOW} > {BRIGHT_CYAN}minecraft:stone\n")
        print(f"{YELLOW}格式说明：{BRIGHT_GREEN}绿色{YELLOW}为目标物品，{BRIGHT_CYAN}蓝色{YELLOW}为替换物品，用 {BRIGHT_YELLOW}> {YELLOW}连接")
        print(f"{YELLOW}          替换物品若为{BRIGHT_YELLOW} None {YELLOW}则代表删除")
        print(f"{YELLOW}          可输入多组，每组之间用{BRIGHT_RED} ; {YELLOW}分隔，空格不影响解析")
        print(f"{GRAY}\n颜色仅作为示例，实际输入不会上色\n")
        print(f"{BRIGHT_RED}注意：所有符号必须用英文输入！")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            input_data = input(f"{CYAN}【→】{BRIGHT_GREEN}请按格式输入要替换的物品：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 返回判断
        if input_data.upper()=="E":
            return False
        # 判断格式
        pattern = re.compile(
            r'^\s*'
            r'[a-z0-9_.-]+:[a-z0-9_.\-/]+\s*>\s*(?:none|[a-z0-9_.-]+:[a-z0-9_.\-/]+)'
            r'(?:\s*;\s*[a-z0-9_.-]+:[a-z0-9_.\-/]+\s*>\s*(?:none|[a-z0-9_.-]+:[a-z0-9_.\-/]+))*'
            r'\s*$',
            re.IGNORECASE
        )
        if re.match(pattern, input_data):
            input_data = input_data.replace(" ", "")
        else:
            input_error_info = "格式错误，请重新输入！"
            continue
        # 转化输入为目标任务字典
        target_dict = {}
        for group in input_data.split(";"):
            target = group.split(">")
            target_dict[target[0]] = target[1]
        # 返回结果
        return target_dict


#【界面-选择物品扫描模式】
def Page_Select_Item_Scan_Mode():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【扫描模式】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}【1】{BRIGHT_CYAN}普通扫描：{GRAY}适用原版端，扫描 实体+方块实体+玩家数据")
        print(f"{YELLOW}【2】{BRIGHT_CYAN}全面扫描：{GRAY}适用模组端，扫描 实体+方块实体+玩家数据+数据文件")
        print(f"{YELLOW}【3】{BRIGHT_CYAN}暴力扫描：{GRAY}覆盖更全面，在全面扫描的基础上不限文件类型且包括子目录")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        #输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            choice = input(f"{CYAN}【→】{BRIGHT_GREEN}请输入功能序号：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 判断输入
        if choice.upper() == "E":
            return False
        elif not choice:
            input_error_info = "未输入任何内容"
            continue
        else:
            try:
                choice = int(choice)
            except Exception:
                input_error_info = "输入的内容无效"
                continue
            if not 1 <= choice <= 3:
                input_error_info = "无效的选项"
                continue
            return choice


#【界面-选择区域】
def Page_Select_Area():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【选择区域】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}输入需要处理的坐标范围，此范围将应用至所有维度")
        print(f"{YELLOW}坐标精度为 1区域 (32×32区块 = 512×512方块)")
        print(f"{YELLOW}若输入的坐标与精度无法对齐，将自动向外扩张并对齐")
        print(f"{YELLOW}\n坐标输入格式：{BRIGHT_GREEN}x,z")
        print(f"{YELLOW}处理整个地图：{BRIGHT_YELLOW}all")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        #输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 坐标正则
        coordinate_pattern = re.compile(r'^\s*(-?\d+)\s*,\s*(-?\d+)\s*$')
        # 获取起始坐标
        try:
            coordinate_top  = input(f"{CYAN}【→】{BRIGHT_CYAN}请输入起始坐标：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        if coordinate_top.upper()=="E":
            return False
        if coordinate_top.upper() in ["ALL", "A"]:
            return True
        print(f"{RESET}")
        # 判断起始坐标
        match_top = coordinate_pattern.match(coordinate_top)
        if not match_top:
            input_error_info = "起始坐标格式错误，请检查输入"
            continue
        # 解析起始坐标
        top_x, top_z = map(int, match_top.groups())
        # 获取结束坐标
        coordinate_end = input(f"{CYAN}【→】{BRIGHT_CYAN}请输入结束坐标：{BRIGHT_YELLOW}")
        if coordinate_end.upper()=="E":
            return False
        if coordinate_top.upper() in ["ALL", "A"]:
            return True
        print(f"{RESET}")
        # 判断结束坐标
        match_end = coordinate_pattern.match(coordinate_end)
        if not match_end:
            input_error_info = "结束坐标格式错误，请检查输入"
            continue
        # 解析结束坐标
        end_x, end_z = map(int, match_end.groups())
        # 返回数据
        result_top = (top_x, top_z)
        result_end = (end_x, end_z)
        return result_top, result_end

def Page_Set_Region_Cleaner_tick_threshold():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【存档清理】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f'{YELLOW}设置"跑图区块的"的区块活跃时间识别阈值，单位为 tick (gt)\n')
        print(f"{YELLOW}区块活跃时间代表玩家在该区块的总刻数，多个玩家同处一区块时增长更快")
        print(f'{YELLOW}跑图区块指的是玩家在跑图或者挖矿过程中快速路过的区块')
        print(f"{YELLOW}这些区块通常只是因为路过而被生成，所以删除不会造成太大影响")
        print(f"{YELLOW}阈值越小越安全但是清理的区块也就越少，个人建议设置在 600-3600 之间")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 设置阈值
        try:
            tick_threshold = input(f"{CYAN}【→】{BRIGHT_CYAN}请设置区块活跃时间阈值：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        if tick_threshold.upper()=="E":
            return False
        try:
            tick_threshold = int(tick_threshold)
        except Exception:
            input_error_info = "输入的内容无效"
            continue
        return tick_threshold

def Page_Set_Region_Cleaner_cooldown():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【存档清理】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f'{YELLOW}设置"跑图区块的"的识别冷却时间，单位为 tick (gt)\n')
        print(f'{YELLOW}本参数主要用来跳过那些活跃时间不长，但是刚刚生成或刚被修改的区块')
        print(f'{YELLOW}若区块最后修改时间到游戏保存时的时长小于冷却时间，则会跳过该区块')
        print(f"{YELLOW}阈值越大越安全但是清理的区块也就越少，个人建议设置在 6000-12000 之间")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 设置阈值
        try:
            cooldown = input(f"{CYAN}【→】{BRIGHT_CYAN}请设置冷却时间：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        if cooldown.upper()=="E":
            return False
        try:
            cooldown = int(cooldown)
        except Exception:
            input_error_info = "输入的内容无效"
            continue
        if cooldown < 0:
            input_error_info = "冷却时间不能小于0"
            continue
        return cooldown


#【界面-选设置进程】
def Page_Set_Process():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【进程设置】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}设置用于处理存档的进程数量，进程越多处理越快")
        print(f"{YELLOW}注意：进程数量需小于等于系统的逻辑处理器数量")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            process_use = input(f"{CYAN}【→】{BRIGHT_GREEN}设置进程数量：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 判断输入
        if process_use.upper() == "E":
            return False
        elif not process_use:
            input_error_info = "未输入任何内容"
            continue
        else:
            result_state, result = verify_select_process(process_use)
            if not result_state:
                input_error_info = result
                continue
            else:
                return result

def verify_select_process(process_use):
    # 获取系统逻辑CPU数量
    system_cpus = os.cpu_count()
    # 数据判断
    try:
        process_use = int(process_use)
    except Exception:
        error_info = "输入的内容无效"
        return False, error_info
    # 区间判断
    if 1 <= process_use <= system_cpus:
        return True, process_use
    elif process_use <= 0:
        error_info = "进程数不能小于1"
        return False, error_info
    elif process_use >= system_cpus:
        error_info = f"进程数不能大于系统逻辑CPU数量 ({process_use}/{system_cpus})"
        return False, error_info
    else:
        error_info = "未知的非法区间"
        return False, error_info

#【界面-选择维度】
def Page_Select_Dimensions(save_path):
    input_error_info = ""
    save_path = unity_path(save_path)
    while True:
        # 获取维度列表
        dimension_list = scan_dimensions(save_path)
        # 获取维度列表文本最大长度
        dim_name_max_len = max([len(dim["name"]) for dim in dimension_list]) + 2
        dim_total_max_len = max([len(dim["name"]+dim["path"]) for dim in dimension_list]) + 12 + 4
        if dim_total_max_len >= Terminal.width:
            dim_total_max_len = Terminal.width
        # 计算界面分割线额外长度
        extra_len = dim_total_max_len - 76
        if extra_len <= 0:
            extra_len = 0
        extra_len = int(extra_len)
        extra_half_len = int(extra_len/2)
        #渲染界面
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30 + extra_half_len)}》{BRIGHT_CYAN}【选择维度】{BRIGHT_MAGENTA}《{cutline(30 + extra_half_len)}\n")
        print(f"{YELLOW}输入需要处理的维度索引，同时选择多个维度请用{BRIGHT_YELLOW} , {YELLOW}分割")
        print("")
        # 列出所有维度
        index = 0
        for dimension in dimension_list:
            index = index + 1
            dimension_name = dimension["name"]
            dimension_path = dimension["path"]
            padding_len = dim_name_max_len - len(dimension_name)
            print(f"{BRIGHT_CYAN}【{index:02d}】{BRIGHT_YELLOW}{dimension_name}{GRAY}{'':.<{padding_len}}{WHITE} | {GRAY}{dimension_path}")
        print(f"{BRIGHT_CYAN}【A】 {BRIGHT_YELLOW}所有维度{GRAY}{'':.<{dim_name_max_len-8}}{WHITE} | {GRAY}选择所有列出的维度")
        print(f"\n{BRIGHT_MAGENTA}{cutline(76 + extra_len)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            input_data = input(f"{CYAN}【→】{BRIGHT_GREEN}请选择需要处理的维度：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 返回判断
        if input_data.upper()=="E":
            return False
        # 直接返回全部维度
        if input_data.upper()=="A":
            return dimension_list
        # 判断输入格式是否合法
        pattern = r'^\s*\d*[1-9]\d*\s*(,\s*\d*[1-9]\d*\s*)*$'
        if re.match(pattern, input_data):
            input_data = input_data.replace(" ", "")
        else:
            input_error_info = "格式错误，请重新输入！"
            continue
        # 将输入转化成列表并检查范围
        input_list = input_data.split(",")
        input_list = [int(i)-1 for i in input_list]
        if max(input_list) > len(dimension_list)-1:
            input_error_info = f"无效的索引：{max(input_list)+1}"
            continue
        # 创建选择的维度列表
        dimension_list_choice = [dimension_list[i] for i in input_list]
        return dimension_list_choice #返回结果

#【界面-参数确认】
def Page_Confirm(arges):
    mode, save, dimension_list, area, target_dict, item_mode, process_use = arges
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【参数确认】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        # 输出运行模式
        print(f"{YELLOW}【模式设置】")
        if mode == 1:
            print(f"{BRIGHT_YELLOW}运行模式：{BRIGHT_CYAN}替换方块")
        elif mode ==  2:
            print(f"{BRIGHT_YELLOW}运行模式：{BRIGHT_CYAN}替换物品")
        elif mode ==  3:
            print(f"{BRIGHT_YELLOW}运行模式：{BRIGHT_CYAN}存档清理")
        else:
            print(f"{BRIGHT_YELLOW}运行模式：{BRIGHT_RED}未知模式")
        # 输出物品替换模式
        if item_mode == 0:
            pass
        elif item_mode == 1:
            print(f"{BRIGHT_YELLOW}扫描模式：{BRIGHT_CYAN}普通扫描")
        elif item_mode == 2:
            print(f"{BRIGHT_YELLOW}扫描模式：{BRIGHT_CYAN}全面扫描")
        elif item_mode == 3:
            print(f"{BRIGHT_YELLOW}扫描模式：{BRIGHT_CYAN}暴力扫描")
        else:
            print(f"{BRIGHT_YELLOW}扫描模式：{BRIGHT_RED}未知模式")
        # 输出处理区域
        if area is True:
            print(f"{BRIGHT_YELLOW}处理区域：{BRIGHT_CYAN}整个地图")
        else:
            area_top, area_end = area
            top_x, top_z = area_top
            end_x, end_z = area_end
            print(f"{BRIGHT_YELLOW}处理区域：{BRIGHT_CYAN}{top_x},{top_z}{BRIGHT_YELLOW} > {BRIGHT_GREEN}{end_x},{end_z}")
        # 输出处理进程数
        print(f"{BRIGHT_YELLOW}处理进程：{BRIGHT_CYAN}x{process_use}")
        # 输出存档信息
        save_path, level_name, level_version_str, level_version_id = save
        print(f"\n{YELLOW}【存档信息】")
        print(f"{BRIGHT_YELLOW}存档版本：{BRIGHT_GREEN}{level_version_str}")
        print(f"{BRIGHT_YELLOW}存档名称：{BRIGHT_CYAN}{level_name}")
        print(f"{BRIGHT_YELLOW}存档路径：{CYAN}{save_path}")
        # 输出高级设置
        if mode != 3:
            print("")
            show_global_config()
        # 输出维度列表
        print(f"\n{YELLOW}【已选择的维度】")
        index = 0
        for dim in dimension_list:
            index = index + 1
            dim_name = dim["name"]
            print(f"{BRIGHT_YELLOW} [{index}] {BRIGHT_CYAN}{dim_name}")
        if mode == 3:
            # 输出存档清理信息
            print(f"\n{YELLOW}【存档清理】")
            tick_threshold, cooldown = target_dict
            print(f"{BRIGHT_YELLOW}活跃时间阈值：{BRIGHT_CYAN}{tick_threshold} ticks")
            print(f"{BRIGHT_YELLOW}修改冷却时间：{BRIGHT_CYAN}{cooldown} ticks")
        else:
            # 输出替换列表
            print(f"\n{YELLOW}【替换任务】")
            target_max_len = max(len(k) for k in target_dict.keys()) # 方块字符串最大长度
            index = 0
            for target_key, target_value in target_dict.items():
                index = index + 1
                padding_len = target_max_len - len(target_key)
                print(f"{BRIGHT_YELLOW} [{index}] "
                      f"{BRIGHT_CYAN}{target_key}{'':<{padding_len}}{BRIGHT_YELLOW} >>> {BRIGHT_GREEN}{target_value}")
        # 结尾
        print(f"\n{BRIGHT_MAGENTA}{cutline(76)}\n")

        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 等待确认
        print(f"{WHITE_ON_RED}【警告】操作不可逆！确认执行前请先备份存档！{RESET}\n")
        try:
            confirm = input(f"{CYAN}【→】{BRIGHT_GREEN}是否确认执行({CYAN}Y{BRIGHT_GREEN}/{BRIGHT_RED}N{BRIGHT_GREEN})：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        if confirm.upper() == "E":
            return False
        elif confirm.upper() in ["Y", "YES"]:
            return True
        elif confirm.upper() in ["N", "NO"]:
            return False
        else:
            input_error_info = "输入的选项无效"
            continue

def Page_Config_Mode():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【配置文件】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}【1】{BRIGHT_CYAN}加载配置文件：{GRAY}使用配置文件中的参数")
        print(f"{YELLOW}【2】{BRIGHT_CYAN}创建配置文件：{GRAY}创建或覆盖当前配置文件")
        print(f"{YELLOW}【3】{BRIGHT_CYAN}加载高级参数：{GRAY}仅加载配置文件中的高级参数")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            choice = input(f"{CYAN}【→】{BRIGHT_GREEN}请输入功能序号：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        # 判断输入
        if choice.upper() == "E":
            return False
        elif not choice:
            input_error_info = "未输入任何内容"
            continue
        else:
            try:
                choice = int(choice)
            except Exception:
                input_error_info = "输入的内容无效"
                continue
            if not 1 <= choice <= 3:
                input_error_info = "无效的选项"
                continue
            return choice


def Page_Select_Config():
    input_error_info = ""
    while True:
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【选择配置】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        print(f"{YELLOW}输入配置文件路径，若无配置文件请先返回并创建")
        print(f"{YELLOW}若当前目录下存在 {BRIGHT_YELLOW}mcap_config.toml {YELLOW}回车即可加载")
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        # 输入错误提示
        if input_error_info:
            print(f"{WHITE_ON_RED}[ERROR] {input_error_info}{RESET}\n")
        # 获取输入
        try:
            config_path = input(f"{CYAN}【→】{BRIGHT_CYAN}请输入配置文件路径：{BRIGHT_YELLOW}")
        except EOFError:
            continue
        print(f"{RESET}")
        if config_path.upper() == "E":
            return False
        # 空输入判断
        if config_path=="":
            config_path = "mcap_config.toml"
        # 验证输入
        config_path = unity_path(config_path)
        result_state, result = verify_config_file(config_path)
        if not result_state:
            input_error_info = result
            continue
        else:
            return config_path

def verify_config_file(config_file):
    # 加载配置文件
    try:
        config_file = unity_path(config_file)
        if config_file == "":
            config_file = "mcap_config.toml"
        if not os.path.isfile(config_file):
            return False, "指定的文件不存在"
        config_data = mcap_config.Load_Config_File(config_file)
        if not config_data:
            return False, "配置文件解析失败"
        # 解析配置数据
        config = mcap_config.Load_Config(config_data)
        return True, config
    except Exception as e:
        return False, f"配置文件解析出错：{e}"


# mca文件区域过滤器
def filter_mca_file_area(mca_file_list, area, mcc=False):
    if area is not True:
        # 解析区域坐标
        area_top, area_end = area
        top_x, top_z = area_top
        end_x, end_z = area_end
        if mcc :
            size = 16
        else:
            size = 512
        # 计算区域文件过滤区间
        min_rx = min(top_x, end_x) // size
        max_rx = max(top_x, end_x) // size
        min_rz = min(top_z, end_z) // size
        max_rz = max(top_z, end_z) // size
        # 定义输出列表
        filtered_mca_file_list = []
        # 遍历文件列表
        for mca_file in mca_file_list:
            try:
                _, rx, rz, _ = mca_file.split(".")
                rx, rz = int(rx), int(rz)
            except:
                continue
            if min_rx <= rx <= max_rx and min_rz <= rz <= max_rz:
                filtered_mca_file_list.append(mca_file)
        # 返回文件
        return filtered_mca_file_list
    # 如果为 True 则直接返回整个列表
    return mca_file_list


# 获取文件列表
def get_file_list(root_dir, endswith=None, full_scan=False):
    root_dir = unity_path(root_dir)
    if not os.path.isdir(root_dir):
        return []
    if endswith is None:
        endswith = ""
    if full_scan:
        # 递归扫描
        file_list = [
            os.path.relpath(os.path.join(root, f), root_dir)
            for root, _, files in os.walk(root_dir)
            for f in files
            if f.endswith(endswith)
        ]
    else:
        # 普通扫描
        file_list = [
            f.name
            for f in os.scandir(root_dir)
            if f.is_file() and f.name.endswith(endswith)
        ]
    file_list = [unity_path(p) for p in file_list]
    return file_list


def del_file_list(root_dir, file_list):
    root_dir = unity_path(root_dir)
    for f in file_list:
        file_path = f"{root_dir}\\{f}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(
                    f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {YELLOW}文件{CYAN}{file_path}"
                    f"{YELLOW}删除失败：{BRIGHT_YELLOW}{e}\n"
                )

def show_global_config():
    """显示全局配置"""
    # 判断扫描是否启用
    if mcap_config.SCAN_BEFORE_PROCESSING:
        enable_scan_str = f"{BRIGHT_GREEN}开启"
    else:
        enable_scan_str = f"{BRIGHT_RED}关闭"
    # 判断.mcc扫描模式
    mcc_file_mode = mcap_config.MCC_FILE_MODE
    if mcc_file_mode.lower() == "skip":
        mcc_file_mode_str = f"{YELLOW}跳过"
    elif mcc_file_mode.lower() == "delete":
        mcc_file_mode_str = f"{BRIGHT_RED}删除"
    elif mcc_file_mode.lower() == "handle":
        mcc_file_mode_str = f"{BRIGHT_GREEN}处理"
    else:
        mcc_file_mode_str = f"{YELLOW}未知:{mcc_file_mode}"
    # 判断非法.mcc处理模式
    invalid_mcc_file_mode = mcap_config.INVALIT_MCC_FILE_Mode
    if invalid_mcc_file_mode.lower() == "skip":
        invalid_mcc_file_mode_str = f"{YELLOW}跳过"
    elif invalid_mcc_file_mode.lower() == "delete":
        invalid_mcc_file_mode_str = f"{BRIGHT_RED}删除"
    elif invalid_mcc_file_mode.lower() == "handle":
        invalid_mcc_file_mode_str = f"{BRIGHT_GREEN}处理"
    else:
        invalid_mcc_file_mode_str = f"{YELLOW}未知:{mcc_file_mode}"
    # 显示
    print(f"{YELLOW}【高级设置】")
    print(f"{BRIGHT_YELLOW}处理前扫描: {enable_scan_str}")
    print(f"{BRIGHT_YELLOW}物品ID字段:{'':<3}{CYAN}{mcap_config.ITEM_COMPOUND_ID_KEYS}")
    print(f"{BRIGHT_YELLOW}物品组件字段：{CYAN}{mcap_config.ITEM_COMPOUND_ITEM_KEYS}")
    print(f"\n{YELLOW}【额外区块设置】")
    print(f"{BRIGHT_YELLOW}额外区块处理模式: {mcc_file_mode_str}")
    print(f"{BRIGHT_YELLOW}额外区块超限处理: {invalid_mcc_file_mode_str}")
    print(f"{BRIGHT_YELLOW}额外区块大小阈值: {BRIGHT_CYAN}{mcap_config.MCC_FILE_SIZE_LIMIT}MB")
    print(f"{BRIGHT_YELLOW}额外区块处理进程: {BRIGHT_CYAN}x{mcap_config.MCC_FILE_PROCESS_USE}")
    print(f"\n{YELLOW}【自定义扫描目录】")
    index = 0
    for path in mcap_config.CUSTOM_SCAN_DATA_PATH:
        index += 1
        print(f"{BRIGHT_YELLOW}[{index}]{CYAN}{path}")


#【功能：替换或删除方块】
def Main_Process_Blocks(arges):
    # 解析参数
    mode, save, dimension_list, area, target_dict, item_mode, process_use = arges
    save_path, level_name, level_version_str, level_version_id = save
    # 渲染界面
    show_logo(1)
    start_time = time.time()
    print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【正在处理】{BRIGHT_MAGENTA}《{cutline(30)}\n")
    # 维度处理进度
    dimension_total = len(dimension_list)
    dimension_finished = 0
    # 遍历处理所有维度
    for dimension in dimension_list:
        # 单个维度计数计时
        dim_start_time = time.time()
        dimension_finished += 1
        # 获取维度信息
        dim_name = dimension["name"]
        dim_path = dimension["path"]
        print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}开始处理维度 {BRIGHT_YELLOW}{dim_name} "
              f"{YELLOW}({dimension_finished}/{dimension_total})")
        # 获取文件
        mca_file_root = unity_path(f"{save_path}/{dim_path}/region")
        mca_file_list = get_file_list(mca_file_root, ".mca")
        mcc_file_list = get_file_list(mca_file_root, ".mcc")
        if not mca_file_list:
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}区域目录无数据\n")
            continue
        # 过滤掉处理区域外的文件
        mca_file_list = filter_mca_file_area(mca_file_list, area)
        mcc_file_list = filter_mca_file_area(mcc_file_list, area, True)
        # 启动扫描
        if mcap_config.SCAN_BEFORE_PROCESSING:
            mca_file_list = MCAP_Scan_Blocks_Core(mca_file_root, mca_file_list, target_dict, process_use)
        # 启动替换
        MCAP_Replace_Blocks_Core(mca_file_root, mca_file_list, target_dict, process_use)
        # 处理.mcc
        if mcc_file_list and mcap_config.MCC_FILE_MODE.lower() == "handle":
            mcc_file_process_use = mcap_config.MCC_FILE_PROCESS_USE
            MCAP_Replace_Blocks_Core(mca_file_root, mcc_file_list, target_dict, mcc_file_process_use, 1)
        elif mcap_config.MCC_FILE_MODE.lower() == "delete":
            del_file_list(mca_file_root, mcc_file_list)
        # 单个维度处理完成
        dim_end_time = time.time()
        dim_elapsed_time = dim_end_time - dim_start_time  # 计算耗时
        print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}维度处理完成！耗时：{CYAN}{dim_elapsed_time:.3f}s\n")
    # 全部处理完成
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}全部处理完成！总耗时：{CYAN}{elapsed_time:.3f}s")
    print(f"\n{BRIGHT_MAGENTA}{cutline(76)}\n")
    try:
        _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车返回首页>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(f"{RESET}")


#【功能：替换或删除物品】
def Main_Process_Items(arges):
    # 解析参数
    mode, save, dimension_list, area, target_dict, item_mode, process_use = arges
    save_path, level_name, level_version_str, level_version_id = save
    # 渲染界面
    show_logo(1)
    start_time = time.time()
    print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【正在处理】{BRIGHT_MAGENTA}《{cutline(30)}\n")
    # 维度处理进度
    dimension_total = len(dimension_list)
    dimension_finished = 0
    # 遍历处理所有维度
    if item_mode != 4:
        for dimension in dimension_list:
            # 单个维度计数计时
            dim_start_time = time.time()
            dimension_finished += 1
            # 获取维度信息
            dim_name = dimension["name"]
            dim_path = dimension["path"]
            # 统一路径
            dim_path = unity_path(dim_path)
            save_path = unity_path(save_path)
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}开始处理维度 {BRIGHT_YELLOW}{dim_name} "
                  f"{YELLOW}({dimension_finished}/{dimension_total})")
            # 1.17-：实体和存档一起保存
            if level_version_id < 2681:
                # 处理 .mca
                mca_file_root_list = [
                    (f"{save_path}/{dim_path}/region", 0, "存档")
                ]
            # 1.17+：实体和存档分开保存
            else:
                # 处理 地图.mca + 实体.mca
                mca_file_root_list = [
                    (f"{save_path}/{dim_path}/region", 0, "区域"),
                    (f"{save_path}/{dim_path}/entities", 1, "实体")
                ]
            #【处理.mca】
            for mca_file_root, exec_mode, exec_str in mca_file_root_list:
                mca_file_list = get_file_list(mca_file_root, ".mca")
                mcc_file_list = get_file_list(mca_file_root, ".mcc")
                if not mca_file_list:
                    print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}{exec_str}目录无数据")
                    continue
                # 过滤掉处理区域外的文件
                mca_file_list = filter_mca_file_area(mca_file_list, area)
                mcc_file_list = filter_mca_file_area(mcc_file_list, area, True)
                # 启动扫描和替换
                MCAP_Replace_Items_Core(mca_file_root, mca_file_list, target_dict, process_use, exec_mode)
                # 处理.mcc
                if mcc_file_list and mcap_config.MCC_FILE_MODE.lower() == "handle":
                    mcc_file_process_use = mcap_config.MCC_FILE_PROCESS_USE
                    MCAP_Replace_Items_Core(mca_file_root, mcc_file_list, target_dict, mcc_file_process_use, 4)
                elif mcap_config.MCC_FILE_MODE.lower() == "delete":
                    del_file_list(mca_file_root, mcc_file_list)

            #【处理 NBT.dat】
            if item_mode in [2, 3]:
                data_file_root = f"{save_path}/{dim_path}/data"
                # 获取文件
                if item_mode == 3:
                    # 暴力扫描 (不限文件类型且包括子目录)
                    data_file_list = get_file_list(data_file_root, None, True)
                else:
                    # 普通扫描
                    data_file_list = get_file_list(data_file_root, ".dat")
                if not data_file_list:
                    print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}data目录无数据")
                    continue
                # 启动扫描和替换
                MCAP_Replace_Items_Core(data_file_root, data_file_list, target_dict, process_use, 2)
            # 单个维度处理完成
            dim_end_time = time.time()
            dim_elapsed_time = dim_end_time - dim_start_time  # 计算耗时
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}维度处理完成！耗时：{CYAN}{dim_elapsed_time:.3f}s\n\n")

        #【处理玩家数据】
        print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}开始处理 {BRIGHT_YELLOW}玩家数据")
        player_data_root = f"{save_path}/playerdata" # 玩家数据目录
        # 获取文件列表
        if item_mode == 3:
            # 暴力扫描 (不限文件类型且包括子目录)
            player_data_list = get_file_list(player_data_root, None, True)
        else:
            # 普通扫描
            player_data_list = get_file_list(player_data_root, ".dat")
        if not player_data_list:
            print(f"{GREEN}[WARN] {CYAN}[{get_datetime()}] {YELLOW}无玩家数据")
        else:
            player_data_start_time = time.time() # 开始计时
            MCAP_Replace_Items_Core(player_data_root, player_data_list, target_dict, process_use, 3) # 处理
            # 处理单人档数据
            if check_single_player_data(f"{save_path}/level.dat"):
                MCAP_Replace_Items_Core(save_path, ["level.dat"], target_dict, process_use, 3) # 处理
            player_data_end_time = time.time() # 结束计时
            player_data_elapsed_time = player_data_end_time - player_data_start_time # 计算耗时
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}玩家数据处理完成！耗时：{CYAN}{player_data_elapsed_time:.3f}s\n")

    # 自定义路径处理
    custom_path_list = mcap_config.CUSTOM_SCAN_DATA_PATH
    if custom_path_list:
        custom_path_total = len(custom_path_list)
        custom_path_finished = 0
        for custom_path in custom_path_list:
            custom_path = unity_path(custom_path)
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}开始处理自定义目录{YELLOW} "
                  f"({custom_path_finished}/{custom_path_total}) {BRIGHT_YELLOW}{custom_path}")
            custom_start_time = time.time()
            custom_path_finished += 1
            # 获取文件列表
            if item_mode == 3:
                # 暴力扫描 (不限文件类型且包括子目录)
                custom_data_file_list = get_file_list(custom_path, None, True)
            else:
                # 普通扫描
                custom_data_file_list = get_file_list(custom_path, ".dat")
            if not custom_data_file_list:
                print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}指定的目录中无数据")
                continue
            # 启动扫描和替换
            MCAP_Replace_Items_Core(custom_path, custom_data_file_list, target_dict, process_use, 2)
            # 单个目录处理完成
            custom_end_time = time.time()
            custom_elapsed_time = custom_end_time - custom_start_time  # 计算耗时
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}目录处理完成！耗时：{CYAN}{custom_elapsed_time:.3f}s\n\n")

    # 全部处理完成
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\n{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}全部处理完成！总耗时：{CYAN}{elapsed_time:.3f}s")
    print(f"\n{BRIGHT_MAGENTA}{cutline(76)}\n")
    try:
        _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车返回首页>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(f"{RESET}")

#【功能：替换或删除方块】
def Main_Region_Cleaner(arges):
    # 解析参数
    mode, save, dimension_list, area, region_cleaner_args, item_mode, process_use = arges
    save_path, level_name, level_version_str, level_version_id = save
    # 渲染界面
    show_logo(1)
    start_time = time.time()
    print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【正在清理】{BRIGHT_MAGENTA}《{cutline(30)}\n")
    # 维度处理进度
    dimension_total = len(dimension_list)
    dimension_finished = 0
    # 清理统计信息
    size_before = 0
    file_before = 0
    size_after = 0
    file_after = 0
    # 遍历处理所有维度
    for dimension in dimension_list:
        # 单个维度计数计时
        dim_start_time = time.time()
        dimension_finished += 1
        # 获取维度信息
        dim_name = dimension["name"]
        dim_path = dimension["path"]
        # 统一路径
        dim_path = unity_path(dim_path)
        save_path = unity_path(save_path)
        print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}开始清理维度 {BRIGHT_YELLOW}{dim_name} "
              f"{YELLOW}({dimension_finished}/{dimension_total})")
        # 获取文件
        poi_file_root = f"{save_path}/{dim_path}/poi"
        region_file_root = f"{save_path}/{dim_path}/region"
        entities_file_root = f"{save_path}/{dim_path}/entities"
        poi_file_list = get_file_list(poi_file_root, ".mca")
        region_file_list = get_file_list(region_file_root, ".mca")
        entities_file_list = get_file_list(entities_file_root, ".mca")
        if not region_file_list:
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}区域目录无数据\n")
            continue
        # 统计数据(处理前)
        file_before += len(region_file_list) + len(poi_file_list) + len(entities_file_list)
        size_before += (get_folder_size(region_file_root) +
                        get_folder_size(poi_file_root) +
                        get_folder_size(entities_file_root))
        # 过滤掉处理区域外的文件
        poi_file_list = filter_mca_file_area(poi_file_list, area)
        region_file_list = filter_mca_file_area(region_file_list, area)
        entities_file_list = filter_mca_file_area(entities_file_list, area)
        # 启动清理
        MCAP_Region_Cleaner_Core(region_file_root, region_file_list, region_cleaner_args, process_use)
        # 统计数据(处理后)
        region_file_list_after = get_file_list(region_file_root, ".mca")
        file_after += len(region_file_list_after)
        size_after += get_folder_size(region_file_root)
        region_after_set = set(region_file_list_after)
        # 清理 entities.mca
        if entities_file_list:
            entities_file_list_del = [f for f in entities_file_list if f not in region_after_set]
            MCAP_Region_Cleaner_Core(entities_file_root, entities_file_list_del, region_cleaner_args, process_use, mode=1)
            file_after += len(get_file_list(entities_file_root, ".mca"))
            size_after += get_folder_size(entities_file_root)
        # 清理 poi.mca
        if poi_file_list:
            poi_file_list_del = [f for f in poi_file_list if f not in region_after_set]
            MCAP_Region_Cleaner_Core(poi_file_root, poi_file_list_del, region_cleaner_args, process_use, mode=2)
            file_after += len(get_file_list(poi_file_root, ".mca"))
            size_after += get_folder_size(poi_file_root)
        # 单个维度处理完成
        dim_end_time = time.time()
        dim_elapsed_time = dim_end_time - dim_start_time  # 计算耗时
        print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}维度清理完成！耗时：{CYAN}{dim_elapsed_time:.3f}s\n")
    # 全部处理完成
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {GREEN}全部清理完成！总耗时：{CYAN}{elapsed_time:.3f}s")
    # 输出统计信息
    file_cleaned = int(file_before - file_after)
    size_cleaned = get_file_size_str(size_before - size_after)
    size_before = get_file_size_str(size_before)
    size_after = get_file_size_str(size_after)
    print(f"\n{YELLOW}【统计信息】\n")
    print(f"{BRIGHT_YELLOW}文件个数：清理前 {CYAN}{file_before} {BRIGHT_YELLOW}；清理后 {BRIGHT_GREEN}{file_after}")
    print(f"{BRIGHT_YELLOW}存档大小：清理前 {CYAN}{size_before} {BRIGHT_YELLOW}；清理后 {BRIGHT_GREEN}{size_after}")
    print(f"\n{YELLOW}总计清理：{BRIGHT_CYAN}{file_cleaned} {YELLOW}个文件；共计 {BRIGHT_CYAN}{size_cleaned}")
    print(f"\n{BRIGHT_MAGENTA}{cutline(76)}\n")
    try:
        _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车返回首页>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(f"{RESET}")


# 配置文件模式
def Main_Config_Mode(config_file, enable_confirm = True):
    # 加载配置文件
    print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}配置文件模式")
    # 解析配置数据
    config_file = unity_path(config_file)
    result_state, result = verify_config_file(config_file)
    config = result
    if not result_state:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}{result}\n")
        try:
            _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车返回>{BRIGHT_YELLOW}")
        except EOFError:
            pass
        print(f"{RESET}")
        return False
    print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}配置文件解析成功")
    # 验证并加载配置
    config_state = True

    #【验证模式】
    main_mode = str(config.get("main_mode"))
    if main_mode.lower() == "block":
        select_mode = 1
    elif main_mode.lower() == "item":
        select_mode = 2
    elif main_mode.lower() == "clean":
        select_mode = 3
    else:
        select_mode = None
        config_state = False
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无效的模式：{YELLOW}{main_mode}")

    #【验证存档】
    if select_mode == 3:
        allowed_version = 100
    else:
        allowed_version = 0
    save_path = unity_path(str(config.get("save_path")))
    result_state, result = verify_select_save(save_path, allowed_version)
    if not result_state:
        select_save = None
        config_state = False
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}{result}")
    else:
        select_save = result
        # 验证版本
        if enable_confirm and select_save[3] == 0:
            print(f"{YELLOW}[WARN] 当前选择的存档为 1.9 以前的版本，可能存在兼容问题\n")
            try:
                confirm = input(f"{CYAN}【→】{BRIGHT_GREEN}退出请输E，回车继续：{BRIGHT_YELLOW}")
            except EOFError:
                confirm = ""
            print(f"{RESET}")
            if confirm.upper() == "E":
                return False

    #【验证维度】
    try:
        select_dimensions = []
        dimension_list = list(config.get("dimensions"))
        for dimension in dimension_list:
            if dimension.lower() == "all":
                select_dimensions = scan_dimensions(save_path)
            elif dimension == "minecraft:overworld":
                select_dimensions.append({
                    "name": f"{dimension}",
                    "path": f"."
                })
            elif dimension == "minecraft:the_nether":
                select_dimensions.append({
                    "name": f"{dimension}",
                    "path": f"DIM-1"
                })
            elif dimension == "minecraft:the_end":
                select_dimensions.append({
                    "name": f"{dimension}",
                    "path": f"DIM1"
                })
            else:
                try:
                    dim = dimension.split(":")
                    select_dimensions.append({
                        "name": f"{dimension}",
                        "path": f"dimensions/{dim[0]}/{dim[1]}"
                    })
                except:
                    print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {YELLOW}无法解析维度 {BRIGHT_YELLOW}{dimension}")
                    continue
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无法解析维度列表：{YELLOW}{e}")
        select_dimensions = None
        config_state = False

    #【验证处理区域】
    try:
        top_xz, end_xz = tuple(config.get("select_area"))
        select_top = (int(top_xz[0]), int(top_xz[1]))
        select_end = (int(end_xz[0]), int(end_xz[1]))
        select_area = (select_top, select_end)
        if select_area == ((0,0), (0,0)):
            select_area = True
    except Exception as e:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无法解析区域配置：{YELLOW}{e}")
        select_area = None
        config_state = False

    # 【验证清理设置】
    if select_mode == 3:
        try:
            cleaner_args = config.get("region_cleaner_args")
            cleaner_tick_threshold = int(cleaner_args[0])
            cleaner_cooldown = int(cleaner_args[1])
            if cleaner_cooldown < 0:
                cleaner_cooldown = 6000
                print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {YELLOW}区块清理冷却时间不能小于0；已重置为6000{BRIGHT_YELLOW}")
            target_dict = (cleaner_tick_threshold, cleaner_cooldown)
        except Exception as e:
            target_dict = None
            config_state = False
            print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无法解析清理配置：{YELLOW}{e}")

    # 【验证处理目标】
    else:
        try:
            pattern = re.compile(r'[a-z0-9_.-]+:[a-z0-9_./-]+')
            target_dict = {}
            task_config = dict(config.get("task_config"))
            for key, value in task_config.items():
                if re.match(pattern, key) and re.match(pattern, value):
                    target_dict[key] = value
                elif re.match(pattern, key) and value.lower()=="none":
                    if select_mode == 2:
                        target_dict[key] = None
                    else:
                        target_dict[key] = "minecraft:air"
                else:
                    print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {YELLOW}无效的目标配置 {BRIGHT_YELLOW}{key} > {value}")
        except Exception as e:
            target_dict = None
            config_state = False
            print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无法解析目标配置：{YELLOW}{e}")

    #【验证物品扫描模式】
    if select_mode == 2:
        item_scan_mode = str(config.get("item_scan_mode"))
        if item_scan_mode.lower() == "common":
            select_item_scan_mode = 1
        elif item_scan_mode.lower() == "full":
            select_item_scan_mode = 2
        elif item_scan_mode.lower() == "global":
            select_item_scan_mode = 3
        elif item_scan_mode.lower() == "custom":
            select_item_scan_mode = 4
        else:
            select_item_scan_mode = None
            config_state = False
            print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无效的物品扫描模式：{YELLOW}{item_scan_mode}")
    else:
        select_item_scan_mode = 0

    #【验证进程数量】
    try:
        process_use = config.get("process_use")
        result_state, result = verify_select_process(process_use)
        if not result_state:
            set_process = None
            config_state = False
            print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}{result}")
        else:
            set_process = result
    except Exception as e:
        set_process = None
        config_state = False
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}无法解析进程配置：{YELLOW}{e}")

    #【判断配置是否验证通过】
    if config_state:
        print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}配置加载成功")
        # 构建核心参数
        main_arges = (
            select_mode, select_save,
            select_dimensions, select_area,
            target_dict, select_item_scan_mode, set_process
        )
        # 参数确认
        if enable_confirm:
            confirm_result = Page_Confirm(main_arges)
            if not confirm_result:
                return False
        # 启动处理
        if select_mode == 1:
            Main_Process_Blocks(main_arges)
        elif select_mode == 2:
            Main_Process_Items(main_arges)
        elif select_mode == 3:
            Main_Region_Cleaner(main_arges)
        return True
    else:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}未能加载配置\n")
        try:
            _ = input(f"{CYAN}【→】{BRIGHT_GREEN}回车返回>{BRIGHT_YELLOW}")
        except EOFError:
            pass
        print(f"{RESET}")
        return False

def Main_Set_Global_Config(config_file):
    # 解析配置数据
    config_file = unity_path(config_file)
    result_state, result = verify_config_file(config_file)
    if not result_state:
        print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}{result}")
        try:
            _ = input(f"\n{CYAN}【→】{BRIGHT_GREEN}回车返回>{BRIGHT_YELLOW}")
        except EOFError:
            pass
        print(f"{RESET}")
    print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}配置文件解析成功")
    # 加载全局配置
    if result_state:
        # 渲染界面
        show_logo(1)
        print(f"\n{BRIGHT_MAGENTA}{cutline(30)}》{BRIGHT_CYAN}【高级参数】{BRIGHT_MAGENTA}《{cutline(30)}\n")
        show_global_config()
        print(f"{BRIGHT_MAGENTA}\n{cutline(76)}\n")
        print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}全局变量加载成功")
    else:
        print(f"{BRIGHT_GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}全局变量加载失败")
    # 等待输入
    try:
        _ = input(f"\n{CYAN}【→】{BRIGHT_GREEN}回车返回>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(f"{RESET}")


def Main_Create_Config_File():
    # 创建文件
    def create_config_file():
        result = mcap_config.Create_Config_File()
        if result:
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}成功创建配置文件；{BRIGHT_YELLOW}mcap_config.toml")
        else:
            print(f"{BRIGHT_RED}[ERROR] {CYAN}[{get_datetime()}] {BRIGHT_RED}未能创建配置文件！")
    # 判断文件是否存在
    if os.path.exists("mcap_config.toml"):
        print(f"{YELLOW}[WARN] {CYAN}[{get_datetime()}] {YELLOW}配置文件已存在，是否覆盖？")
        try:
            overwrite = input(f"\n{CYAN}【→】{BRIGHT_GREEN}是否覆盖({CYAN}Y{BRIGHT_GREEN}/{BRIGHT_RED}N{BRIGHT_GREEN})：{BRIGHT_YELLOW}")
        except EOFError:
            overwrite = ""
        print(RESET)
        if overwrite.upper() in ["Y", "YES"]:
            create_config_file()
        else:
            print(f"{GREEN}[INFO] {CYAN}[{get_datetime()}] {BRIGHT_GREEN}操作已取消")
    else:
        create_config_file()
    # 等待输入
    try:
        _ = input(f"\n{CYAN}【→】{BRIGHT_GREEN}回车返回>{BRIGHT_YELLOW}")
    except EOFError:
        pass
    print(RESET)


# noinspection PyUnusedLocal
def Main_Exit(signum=None, frame=None):
    print(f"\n\n{GREEN}[INFO] {CYAN}[{get_datetime()}] {YELLOW}程序退出")
    print(f"{RESET}")
    sys.exit(0)


#【主程序】
if __name__ == '__main__':
    # 设置终端标题
    print("\033]0;MCA Prosecutor\007\n", end="", flush=True)
    Console().clear()
    if os.name == "nt":
        os.system("title MCA Prosecutor")
        os.system("cls")

    # 注册系统事件
    signal.signal(signal.SIGINT, Main_Exit)   # Ctrl+C
    signal.signal(signal.SIGTERM, Main_Exit)  # 终止信号

    # 显示程序说明
    Page_Description()
    while True:
        # 显示主页 (选择功能)
        Select_Mode = Page_Home()
        if not Select_Mode:
            Main_Exit()
        # 配置模式
        if Select_Mode == "C":
            # 选择配置模式
            Config_Mode = Page_Config_Mode()
            if not Config_Mode:
                continue
            # 判断配置模式
            if Config_Mode == 1:
                # 选择配置文件
                Config_File = Page_Select_Config()
                if not Config_File:
                    continue
                # 执行配置模式
                Main_Config_Mode(Config_File)
            elif Config_Mode == 2:
                # 创建配置文件
                Main_Create_Config_File()

            elif Config_Mode == 3:
                # 选择配置文件
                Config_File = Page_Select_Config()
                if not Config_File:
                    continue
                # 加载全局配置
                Main_Set_Global_Config(Config_File)
            # 返回首页
            continue
        # 选择存档
        if Select_Mode == 3:
            allowed_version = 100
        else:
            allowed_version = 0
        Select_Save = Page_Select_Save(allowed_version)
        if not Select_Save:
            continue
        save_path, level_name, level_version_str, level_version_id = Select_Save
        # 选择维度
        Select_Dimensions = Page_Select_Dimensions(save_path)
        if not Select_Dimensions:
            continue
        # 选择处理区域
        Select_Area = Page_Select_Area()
        if not Select_Area:
            continue
        # 选择处理目标
        if Select_Mode == 1: # 替换方块
            # 选择目标方块
            Target_Dict = Page_Select_Block()
            if not Target_Dict:
                continue
            Item_Scan_Mode = 0
        elif Select_Mode == 2: # 替换物品
            # 选择目标物品
            Target_Dict = Page_Select_Item()
            if not Target_Dict:
                continue
            # 选择物品扫描模式
            Item_Scan_Mode = Page_Select_Item_Scan_Mode()
            if not Item_Scan_Mode:
                continue
        elif Select_Mode == 3: # 清理存档
            Target_Dict = {}
            Item_Scan_Mode = 0
            # 设置清理扫描阈值
            Region_Cleaner_tick_threshold = Page_Set_Region_Cleaner_tick_threshold()
            if Region_Cleaner_tick_threshold is False:
                continue
            # 设置冷却时长
            Region_Cleaner_cooldown = Page_Set_Region_Cleaner_cooldown()
            if Region_Cleaner_cooldown is False:
                continue
            # 重定向 Target_Dict 为 region_cleaner_args
            Target_Dict = (Region_Cleaner_tick_threshold, Region_Cleaner_cooldown)
        else:
            continue

        # 设置进程数量
        Set_Process = Page_Set_Process()
        if not Set_Process:
            continue
        # 参数确认页
        Main_Arges = (
            Select_Mode, Select_Save,
            Select_Dimensions, Select_Area,
            Target_Dict, Item_Scan_Mode, Set_Process
        )
        Confirm = Page_Confirm(Main_Arges)
        if not Confirm:
            continue

        # 启动处理
        if Select_Mode == 1:
            Main_Process_Blocks(Main_Arges)
        elif Select_Mode == 2:
            Main_Process_Items(Main_Arges)
        elif Select_Mode == 3:
            Main_Region_Cleaner(Main_Arges)
        else:
            continue
