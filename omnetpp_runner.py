import os
import random
import tempfile
import shutil
import time
import subprocess
import sys
from pathlib import Path
import copy
from typing_extensions import overload
from PySide6.QtCore import QTimer, QObject, Signal
import psutil

'''
算力网络仿真程序，基于修改MSYS2的配置实现
'''
class OmnetppRunner(QObject):
    simulation_finished = Signal()
    encountering_errors = Signal()

    @overload
    def __init__(self, omnetppdir:str|Path,projectdir:str|Path,/,commands:list)->None:...
    @overload
    def __init__(self,omnetppdir:str|Path,projectdir:str|Path,/,*commands:str)->None:...

    def __init__(self, omnetppdir:str|Path,projectdir:str|Path,/, *command_args):
        super().__init__()
        if not self._check_valid_dir(omnetppdir):
            raise ValueError("路径错误！")
        def is_subpath_and_relative(path1, path2):
            path1 = Path(path1).resolve()
            path2 = Path(path2).resolve()
            try:
                is_subpath = path1 in path2.parents or path1 == path2
                if is_subpath:
                    # 计算相对路径
                    relative_path = path2.relative_to(path1)
                    return (True, f"./{relative_path}")
                else:
                    return (False, "Path2 is not a subpath of Path1")
            except ValueError:
                return (False, "Path2 is not a subpath of Path1")

        is_subpath, self.relative_path = is_subpath_and_relative(omnetppdir, projectdir)
        if not is_subpath:
            raise ValueError(f"路径错误！{self.relative_path}")
        # print(self.relative_path)
        # 常量定义
        self.OMNETPP_ROOT = omnetppdir
        self.PROJECT_ROOT = projectdir
        self.MSYS2_BASHRC_PATH = (
            self.OMNETPP_ROOT + "\\tools\\win64\\etc\\bash.bashrc"
        )
        self.MARKER_START = "# OMNETPP_COMPUTING_POWER_NETWORK_START"
        self.MARKER_END = "# OMNETPP_COMPUTING_POWER_NETWORK_END"

        if len(command_args) == 1 and isinstance(command_args[0], str) and command_args[0]:
            self.NET_COMMAND = [command_args[0]]
        elif len(command_args) == 1 and isinstance(command_args[0], list) and command_args[0]:
            self.NET_COMMAND = copy.deepcopy([cmd for cmd in command_args[0] if cmd and isinstance(cmd,str)])
        else:
            self.NET_COMMAND = copy.deepcopy([cmd for cmd in command_args if cmd and isinstance(cmd,str)])

        self.NET_COMMAND.append('echo \"算力网络仿真已结束。10s 后将退出\"')
        self.NET_COMMAND.append('sleep 10 && exit;')

        '''
        r"cd ./samples/inet/examples/inet/igmp",
        r"opp_run -u Cmdenv -c IGMPv2 -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../out/clang-release/src/libINET.dll omnetpp.ini",
        '''

        # 备份与文件锁
        self._backup_path = None
        self._lock_file = None
        self.timer = QTimer()

        # 完成标志
        self._finished = False
        # self._process = None
        self._current_test_id = None

    def _generate_lock_name(self, test_id):
        """生成包含实例ID和测试ID的锁文件名"""
        if not test_id:
            raise ValueError(f"测试id错误{test_id}")
        return f"msys2_cpnw_{id(self)}_{test_id}.lock"

    def _acquire_lock(self, test_id):
        """获取文件锁"""
        lock_file = Path(tempfile.gettempdir()) / self._generate_lock_name(test_id)
        try:
            # 检查是否已有同测试ID的锁存在
            if lock_file.exists():
                raise RuntimeError(f"Lock already exists: {lock_file}")
            # 创建新锁
            lock_file.write_text(f"{os.getpid()}:{id(self)}:{test_id}")
            return lock_file

        except Exception as e:
            if lock_file.exists():
                lock_file.unlink()
            raise RuntimeError(f"Failed to acquire lock: {e}")

    def _release_lock(self, test_id):
        """释放指定测试ID的锁"""
        lock_file = Path(tempfile.gettempdir()) / self._generate_lock_name(test_id)
        try:
            if lock_file.exists():
                # 验证锁内容是否匹配当前进程和实例
                content = lock_file.read_text().split(":")
                if len(content) == 3 and content[1] == str(id(self)):
                    lock_file.unlink()
        except Exception as e:
            print(f"Warning: Lock release failed - {e}", file=sys.stderr)

    def _backup_file(self):
        """备份原始文件"""
        timestamp = int(time.time())
        self._backup_path = f"{self.MSYS2_BASHRC_PATH}.bak.{timestamp}"
        try:
            shutil.copy2(self.MSYS2_BASHRC_PATH, self._backup_path)
        except Exception as e:
            raise RuntimeError(f"Backup failed: {e}")

    def _inject_command(self):
        """注入命令到 bash.bashrc"""
        try:
            with open(self.MSYS2_BASHRC_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n{self.MARKER_START}\n")
                print(self.NET_COMMAND)
                for command in self.NET_COMMAND:
                    f.write(f"{command}\n")
                f.write(f"\n\n{self.MARKER_END}\n")
        except Exception as e:
            self._restore_backup()
            raise RuntimeError(f"Command injection failed: {e}")

    def _restore_backup(self):
        """恢复备份文件"""
        if self._backup_path and os.path.exists(self._backup_path):
            try:
                shutil.copy2(self._backup_path, self.MSYS2_BASHRC_PATH)
                os.unlink(self._backup_path)
            except Exception as e:
                print(f"Warning: Restore failed - {e}", file=sys.stderr)

    def run(self):
        """运行仿真并阻塞等待完成"""
        self._current_test_id = random.randint(1, 10000)
        try:
            self._acquire_lock(self._current_test_id)
            self._backup_file()
            self._inject_command()

            # 启动子进程（非阻塞）
            subprocess.Popen(
                [
                    "cmd.exe",
                    "/c",
                    os.path.join(self.OMNETPP_ROOT, "mingwenv.cmd"),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                shell=True
            )
            # 启动定时器检查结果
            print("开始等待")
            self._start_waiting()
        except Exception as e:
            print("错误！")
            self._cleanup_on_error()
            raise e

    def end(self,test_id):
        """运行结束清理"""
        print("开始清理")
        try:
            self._restore_backup()
            self._release_lock(test_id)
        except Exception as e:
            raise e

    def _start_waiting(self):
        """开始等待结果文件"""
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_result_file)
        self._timer.start(500)  # 每500ms检查一次

    def _check_result_file(self):
        """检查结果文件是否存在/窗口是否打开"""
        windows_closed = False
        # 检查mintty是否打开
        import psutil
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                # 检查进程名是否为 mintty.exe
                if proc.info['name'] == 'mintty.exe':
                    exe_path = proc.info['exe'] or ""
                    target_dir = os.path.normcase(self.OMNETPP_ROOT)
                    exe_dir = os.path.normcase(os.path.dirname(exe_path))
                    if target_dir in exe_dir:  # 严格匹配目录
                        windows_closed = False
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        else:
            windows_closed = True
        file_path = Path(self.PROJECT_ROOT) / "results.json"
        # 检查文件是否存在或进程是否已结束
        if file_path.exists() or windows_closed:
            print("文件存在" if file_path.exists() else '')
            print("窗口关闭" if windows_closed else '')
            self._timer.stop()
            self._finished = True
            self.end(self._current_test_id)
            self.deleteLater()
            self.simulation_finished.emit()

    def _cleanup_on_error(self):
        """出错时的清理"""
        print("出错了！")
        if hasattr(self, '_current_test_id') and self._current_test_id:
            self._release_lock(self._current_test_id)
        if hasattr(self, '_backup_path') and self._backup_path:
            self._restore_backup()
        self.encountering_errors.emit()

    def __del__(self):
        """析构时确保清理"""
        print("开始析构！")
        if hasattr(self, '_finished') and not self._finished:
            self._cleanup_on_error()

    def clearCommand(self):
        self.NET_COMMAND = []


    def _check_valid_dir(self, path_dir):
        """
        检测给定目录是否是Windows版OMNeT++ 5.6.2的根目录
        参数:
            dir_path: 要检测的目录路径字符串
        返回:
            bool: 如果是有效的OMNeT++ 5.6.2根目录返回True，否则False
        """
        ve = ValueError
        try:
            path = Path(path_dir)

            # 基本目录检查
            if not path.is_dir():
                raise ve("路径不存在")

            # 检查Windows版特有文件
            required_files = [
                "bin/opp_run.exe",
                "include/omnetpp.h",
                "lib/liboppenvir.a",
                "Makefile.inc"
            ]

            # 检查版本标识文件
            version_files = {
                # "configure.user": "OMNETPP_VERSION=5.6.2",
                "Version": "omnetpp-5.6.2"
            }

            # 检查所有必需文件
            for rel_path in required_files:
                if not (path / rel_path).exists():
                    raise ValueError(f"不存在文件{rel_path}")

            # 检查版本信息
            for version_file, version_str in version_files.items():
                file_path = path / version_file
                if not file_path.exists():
                    raise ve(f"不存在文件{version_file}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    if version_str not in f.read():
                        raise ve(f"版本不对：{version_str}")

            # 检查Windows特有文件
            windows_files = [
                "mingwenv.cmd",
                "bin/opp_makemake.cmd"
            ]
            for rel_path in windows_files:
                if not (path / rel_path).exists():
                    raise ve(f"不存在文件{rel_path}")
            return True
        except Exception as e:
            print(f"检测过程中发生错误: {e}")
            return False

if __name__ == "__main__":
    print("测试")
    from PySide6.QtWidgets import QApplication

    app = QApplication()

    runner = None

    def start_simulation():
        global runner
        runner = OmnetppRunner("C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2",
                               "C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2\\samples\\inet\\examples\\computing_power_network\\simpletest",
                               r"cd ./samples/inet/examples/computing_power_network/mytest",
                               r"opp_run -u Cmdenv -n ../../../src:../..:../../../tutorials:../../../showcases"
                               r" -l ../../../src/INET omnetpp.ini --cmdenv-express-mode=false"
                               )
        runner.run()  # 这会"阻塞"直到仿真完成，但不影响Qt事件循环
    # 启动仿真（非阻塞方式）
    QTimer.singleShot(0, start_simulation)
    sys.exit(app.exec())

'''
opp_run -u Cmdenv -c static -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../out/clang-release/src/libINET.dll omnetpp.ini --cmdenv-express-mode=true
'''
'''
opp_run -u Cmdenv -c static -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../src/INET omnetpp.ini --cmdenv-express-mode=true
'''