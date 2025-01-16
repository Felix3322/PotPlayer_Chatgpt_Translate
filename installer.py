import os
import sys
import ctypes
import requests
import locale
import win32com.client

# 定义多语言字符串
LANGUAGE_STRINGS = {
    "en": {
        "admin_required": "This script needs to be run with administrator privileges.",
        "select_directory": "Please select the Translate directory for PotPlayer.",
        "invalid_directory": "No valid directory selected. Exiting installation.",
        "creating_directory": "Creating directory: {}",
        "failed_to_create_directory": "Failed to create directory: {}",
        "download_completed": "File downloaded: {} -> {}",
        "download_failed": "Failed to download {}: {}",
        "installation_complete": "Files have been successfully installed to: {}",
        "choose_option": "Directory not found. Please choose an option:\n1. Manually input directory\n2. Automatically scan all drives\nEnter your choice (1/2): ",
        "default_path_not_found": "Default path not found: {}",
        "scanning_drives": "Scanning all drives, please wait...",
        "found_directory": "Directory found: {}",
        "no_directory_found": "No directory found.",
        "installation_done": "Installation completed. Press Enter to exit.",
        "error_occurred": "An error occurred: {}",
        "enter_directory": "Please enter the full path to the PotPlayer Translate directory:",
    },
    "zh": {
        "admin_required": "此脚本需要以管理员权限运行。",
        "select_directory": "请选择PotPlayer的Translate目录。",
        "invalid_directory": "未选择有效目录，退出安装程序。",
        "creating_directory": "创建目录: {}",
        "failed_to_create_directory": "创建目录失败: {}",
        "download_completed": "文件已成功下载: {} -> {}",
        "download_failed": "下载失败 {}: {}",
        "installation_complete": "文件已成功安装到: {}",
        "choose_option": "目录不存在。请选择操作:\n1. 手动输入目录\n2. 自动扫描硬盘\n输入选项（1/2）：",
        "default_path_not_found": "默认路径未找到: {}",
        "scanning_drives": "正在扫描硬盘，请稍候...",
        "found_directory": "找到目录: {}",
        "no_directory_found": "未找到目录。",
        "installation_done": "安装完成。按回车键退出。",
        "error_occurred": "发生错误: {}",
        "enter_directory": "请输入PotPlayer的Translate目录完整路径：",
    },
}


# 获取系统语言并选择提示语言
def get_language():
    lang_code = locale.getdefaultlocale()[0]
    if lang_code and lang_code.startswith("zh"):
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
        None, "runas", sys.executable, " ".join([f'"{arg}"' for arg in sys.argv]), None, 1
    )
    sys.exit()


# 下载文件函数，带进度显示
def download_file(url, dest_path, strings):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        total_length = response.headers.get('content-length')

        if total_length is None:
            with open(dest_path, 'wb') as file:
                file.write(response.content)
            print(strings["download_completed"].format(url, dest_path))
        else:
            dl = 0
            total_length = int(total_length)
            with open(dest_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        file.write(chunk)
                        dl += len(chunk)
                        done = int(50 * dl / total_length)
                        percent = int(100 * dl / total_length)
                        sys.stdout.write("\r[%s%s] %d%%" % ('=' * done, ' ' * (50 - done), percent))
                        sys.stdout.flush()
            print()  # 换行
            print(strings["download_completed"].format(url, dest_path))
    except Exception as e:
        print(strings["download_failed"].format(url, e))
        sys.exit(1)


# 扫描硬盘函数
def scan_drives(strings):
    drives = [f"{chr(x)}:\\" for x in range(65, 91) if os.path.exists(f"{chr(x)}:\\")]
    for drive in drives:
        potential_path = os.path.join(drive, "Program Files", "DAUM", "PotPlayer", "Extension", "Subtitle", "Translate")
        if os.path.exists(potential_path):
            return potential_path
    return None


# 从安装目录扫描快捷方式获取路径
def get_path_from_installation_dir(strings):
    # 常见的安装路径
    potential_dirs = [
        r"C:\Program Files\DAUM\PotPlayer",
        r"C:\Program Files (x86)\DAUM\PotPlayer"
    ]
    for drive in [f"{chr(x)}:\\" for x in range(65, 91) if os.path.exists(f"{chr(x)}:\\")]:
        potential_dirs.append(os.path.join(drive, "DAUM", "PotPlayer"))

    for dir_path in potential_dirs:
        if os.path.exists(dir_path):
            for lnk_name in ["PotPlayer 64 bit.lnk", "PotPlayer.lnk", "PotPlayer 32 bit.lnk"]:
                lnk_path = os.path.join(dir_path, lnk_name)
                if os.path.exists(lnk_path):
                    potplayer_path = get_path_from_shortcut(lnk_path)
                    if potplayer_path:
                        translate_dir = os.path.join(os.path.dirname(potplayer_path), "Extension", "Subtitle",
                                                     "Translate")
                        if os.path.exists(translate_dir):
                            print(strings["found_directory"].format(translate_dir))
                            return translate_dir
    return None


# 解析快捷方式文件
def get_path_from_shortcut(shortcut_path):
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        return shortcut.TargetPath
    except Exception:
        return None


# 主安装逻辑
def install(strings):
    print("Starting installation...")

    # 优先检测安装目录中的快捷方式
    target_path = get_path_from_installation_dir(strings)

    if not target_path:
        default_path = r"C:\Program Files\DAUM\PotPlayer\Extension\Subtitle\Translate"
        if not os.path.exists(default_path):
            print(strings["default_path_not_found"].format(default_path))
            choice = input(strings["choose_option"]).strip()

            if choice == '2':
                # 自动扫描
                print(strings["scanning_drives"])
                target_path = scan_drives(strings)
                if not target_path:
                    print(strings["no_directory_found"])
                    target_path = input(strings["enter_directory"]).strip()
            else:
                target_path = input(strings["enter_directory"]).strip()

            if not target_path or not os.path.exists(target_path):
                print(strings["invalid_directory"])
                sys.exit(1)
        else:
            target_path = default_path

    print(f"Target Directory: {target_path}")

    # 确保目标目录存在
    if not os.path.exists(target_path):
        try:
            os.makedirs(target_path)
            print(strings["creating_directory"].format(target_path))
        except Exception as e:
            print(strings["failed_to_create_directory"].format(target_path))
            sys.exit(1)

    # 下载文件
    as_file_url = "https://raw.githubusercontent.com/Felix3322/PotPlayer_Chatgpt_Translate/WithoutContextHandling/SubtitleTranslate%20-%20ChatGPT.as"
    ico_file_url = "https://raw.githubusercontent.com/Felix3322/PotPlayer_Chatgpt_Translate/WithoutContextHandling/SubtitleTranslate%20-%20ChatGPT.ico"

    as_file_path = os.path.join(target_path, "SubtitleTranslate - ChatGPT.as")
    ico_file_path = os.path.join(target_path, "SubtitleTranslate - ChatGPT.ico")

    print("Downloading SubtitleTranslate - ChatGPT.as...")
    download_file(as_file_url, as_file_path, strings)

    print("Downloading SubtitleTranslate - ChatGPT.ico...")
    download_file(ico_file_url, ico_file_path, strings)

    print(strings["installation_complete"].format(target_path))


def main():
    lang = get_language()
    strings = LANGUAGE_STRINGS[lang]

    if not is_admin():
        restart_as_admin(strings)

    try:
        install(strings)
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user.")
    except Exception as e:
        print(strings["error_occurred"].format(e))
    input(strings["installation_done"])


if __name__ == "__main__":
    main()
