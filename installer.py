import os
import sys
import ctypes
import requests
import locale
from tkinter import Tk, filedialog

# 定义多语言支持
LANGUAGE_STRINGS = {
    "en": {
        "default_path_not_found": "Default path not found: {}",
        "choose_option": "Directory not found. Please choose an option:\n1. Manually select a directory\n2. Automatically scan all drives\nEnter your choice (1/2): ",
        "scanning_drives": "Scanning all drives, please wait...",
        "found_directory": "Directory found: {}",
        "no_directory_found": "No directory found.",
        "select_directory": "Please select the Translate directory for PotPlayer",
        "invalid_directory": "No valid directory selected. Exiting installation.",
        "creating_directory": "Creating directory: {}",
        "failed_to_create_directory": "Failed to create directory: {}",
        "download_completed": "File downloaded: {} -> {}",
        "download_failed": "Failed to download {}: {}",
        "installation_complete": "Files have been successfully installed to: {}",
        "admin_required": "This script needs to be run with administrator privileges. Please restart the script as an administrator.",
    },
    "zh": {
        "default_path_not_found": "默认路径未找到: {}",
        "choose_option": "目录不存在。请选择操作:\n1. 手动选择目录\n2. 自动扫描硬盘\n输入选项（1/2）：",
        "scanning_drives": "正在扫描硬盘，请稍候...",
        "found_directory": "找到目录: {}",
        "no_directory_found": "未找到目录。",
        "select_directory": "请选择PotPlayer的Translate目录",
        "invalid_directory": "未选择有效目录，退出安装程序。",
        "creating_directory": "创建目录: {}",
        "failed_to_create_directory": "创建目录失败: {}",
        "download_completed": "文件已成功下载: {} -> {}",
        "download_failed": "下载失败 {}: {}",
        "installation_complete": "文件已成功安装到: {}",
        "admin_required": "此脚本需要以管理员权限运行。请以管理员权限重新启动此脚本。",
    },
}


# 获取系统语言并选择提示语言
def get_language():
    lang_code = locale.getdefaultlocale()[0]
    if lang_code.startswith("zh"):
        return "zh"
    else:
        return "en"


# 检测是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


# 提升到管理员权限
def restart_as_admin(strings):
    print(strings["admin_required"])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()


# 下载文件函数
def download_file(url, dest_path, strings):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(strings["download_completed"].format(url, dest_path))
    except Exception as e:
        print(strings["download_failed"].format(url, e))
        exit(1)


# 扫描硬盘函数
def scan_drives(strings):
    drives = [f"{chr(x)}:\\" for x in range(65, 91) if os.path.exists(f"{chr(x)}:\\")]
    for drive in drives:
        potential_path = os.path.join(drive, "Program Files", "DAUM", "PotPlayer", "Extension", "Subtitle", "Translate")
        if os.path.exists(potential_path):
            return potential_path
    return None


# 手动选择目录
def manual_directory_selection(strings):
    Tk().withdraw()  # 隐藏Tkinter主窗口
    selected_dir = filedialog.askdirectory(title=strings["select_directory"])
    return selected_dir if selected_dir else None


# 主函数
def main():
    # 获取语言设置
    lang = get_language()
    strings = LANGUAGE_STRINGS[lang]

    # 检测是否以管理员权限运行
    if not is_admin():
        restart_as_admin(strings)

    # 默认目录
    default_path = r"C:\Program Files\DAUM\PotPlayer\Extension\Subtitle\Translate"

    # 下载链接
    as_file_url = "https://raw.githubusercontent.com/Felix3322/PotPlayer_Chatgpt_Translate/WithoutContextHandling/SubtitleTranslate%20-%20ChatGPT.as"
    ico_file_url = "https://raw.githubusercontent.com/Felix3322/PotPlayer_Chatgpt_Translate/WithoutContextHandling/SubtitleTranslate%20-%20ChatGPT.ico"

    # 检测默认路径
    if not os.path.exists(default_path):
        print(strings["default_path_not_found"].format(default_path))
        choice = input(strings["choose_option"]).strip()

        if choice == '2':
            # 自动扫描
            print(strings["scanning_drives"])
            found_path = scan_drives(strings)
            if found_path:
                print(strings["found_directory"].format(found_path))
                target_path = found_path
            else:
                print(strings["no_directory_found"])
                target_path = manual_directory_selection(strings)
        else:
            # 手动选择目录
            target_path = manual_directory_selection(strings)

        if not target_path:
            print(strings["invalid_directory"])
            return
    else:
        target_path = default_path

    # 确保目标目录存在
    if not os.path.exists(target_path):
        try:
            os.makedirs(target_path)
            print(strings["creating_directory"].format(target_path))
        except Exception as e:
            print(strings["failed_to_create_directory"].format(target_path))
            exit(1)

    # 下载文件
    as_file_path = os.path.join(target_path, "SubtitleTranslate - ChatGPT.as")
    ico_file_path = os.path.join(target_path, "SubtitleTranslate - ChatGPT.ico")

    download_file(as_file_url, as_file_path, strings)
    download_file(ico_file_url, ico_file_path, strings)

    print(strings["installation_complete"].format(target_path))


if __name__ == "__main__":
    main()
    input("Done. Press enter to close the window.")
