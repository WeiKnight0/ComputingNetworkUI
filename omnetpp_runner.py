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

'''
算力网络仿真程序，基于修改MSYS2的配置实现
'''
class OmnetppRunner:
    @overload
    def __init__(self, omnetppdir:str|Path,projectdir:str|Path,/,commands:list)->None:...
    @overload
    def __init__(self,omnetppdir:str|Path,projectdir:str|Path,/,*commands:str)->None:...

    def __init__(self, omnetppdir:str|Path,projectdir:str|Path,/, *command_args):
        # self.omnetpp_dir=dir

        # self.OMNETPP_ROOT = "C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2"
        if not self.__check_valid_dir(omnetppdir):
            raise ValueError("路径错误！")
        print(omnetppdir, projectdir)
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
        print(self.relative_path)
        # 常量定义
        self.OMNETPP_ROOT = omnetppdir
        self.PROJECT_ROOT = projectdir
        self.MSYS2_BASHRC_PATH = (
            self.OMNETPP_ROOT + "\\tools\\win64\\etc\\bash.bashrc"
        )  # 根据实际路径修改
        self.MARKER_START = "# OMNETPP_COMPUTING_POWER_NETWORK_START"
        self.MARKER_END = "# OMNETPP_COMPUTING_POWER_NETWORK_END"
        # self.NET_COMMAND = []

        # error
        if len(command_args) == 1 and isinstance(command_args[0], list) and command_args[0]:
            self.NET_COMMAND = [command_args[0]]
        else:
            self.NET_COMMAND = copy.deepcopy([cmd for cmd in command_args if cmd and isinstance(cmd,str)])

        '''
        r"cd ./samples/inet/examples/inet/igmp",
        r"opp_run -u Cmdenv -c IGMPv2 -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../out/clang-release/src/libINET.dll omnetpp.ini",
        '''

        # 备份与文件锁
        self.__backup_path = None
        self.__lock_file = None

    def __generate_lock_name(self, test_id):
        """生成包含实例ID和测试ID的锁文件名"""
        if not test_id:
            raise ValueError(f"测试id错误{test_id}")
        return f"msys2_cpnw_{id(self)}_{test_id}.lock"

    def __acquire_lock(self, test_id):
        """获取文件锁"""
        lock_file = Path(tempfile.gettempdir()) / self.__generate_lock_name(test_id)
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

    def __release_lock(self, test_id):
        """释放指定测试ID的锁"""
        lock_file = Path(tempfile.gettempdir()) / self.__generate_lock_name(test_id)
        try:
            if lock_file.exists():
                # 验证锁内容是否匹配当前进程和实例
                content = lock_file.read_text().split(":")
                if len(content) == 3 and content[1] == str(id(self)):
                    lock_file.unlink()
        except Exception as e:
            print(f"Warning: Lock release failed - {e}", file=sys.stderr)

    def __del__(self):
        """析构时删除该实例创建的所有锁"""
        self.__restore_backup()
        lock_pattern = f"msys2_cpnw_{id(self)}_*.lock"
        for lock_file in Path(tempfile.gettempdir()).glob(lock_pattern):
            try:
                lock_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete lock {lock_file}: {e}", file=sys.stderr)

    def __backup_file(self):
        """备份原始文件"""
        timestamp = int(time.time())
        self.__backup_path = f"{self.MSYS2_BASHRC_PATH}.bak.{timestamp}"
        try:
            shutil.copy2(self.MSYS2_BASHRC_PATH, self.__backup_path)
        except Exception as e:
            raise RuntimeError(f"Backup failed: {e}")

    def __inject_command(self):
        """注入命令到 bash.bashrc"""
        try:
            with open(self.MSYS2_BASHRC_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n{self.MARKER_START}\n")
                for command in self.NET_COMMAND:
                    f.write(f"{command}\n")
                f.write(f"\n\n{self.MARKER_END}\n")
        except Exception as e:
            self.__restore_backup()
            raise RuntimeError(f"Command injection failed: {e}")

    def __restore_backup(self):
        """恢复备份文件"""

        if self.__backup_path and os.path.exists(self.__backup_path):
            try:
                shutil.copy2(self.__backup_path, self.MSYS2_BASHRC_PATH)
                os.unlink(self.__backup_path)
            except Exception as e:
                print(f"Warning: Restore failed - {e}", file=sys.stderr)

    def run(self):
        """运行入口"""
        test_id = random.randint(1, 10000)
        try:
            self.__acquire_lock(test_id)
            self.__backup_file()
            self.__inject_command()

            # 通过预定义的.cmd文件启动MSYS2（阻塞等待）
            subprocess.run(
                [
                    "cmd.exe",
                    "/c",
                    os.path.join(self.OMNETPP_ROOT, "mingwenv.cmd"),
                ],  # 替换为实际路径
                check=True,
                # creationflags=subprocess.CREATE_NO_WINDOW,  # 隐藏CMD窗口
            )
            self.__wait()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            raise e
        finally:
            self.end(test_id)

    def end(self,test_id):
        """运行结束清理"""
        try:
            self.__restore_backup()
            self.__release_lock(test_id)
        except Exception as e:
            raise e

    def __wait(self):
        while not (Path(self.PROJECT_ROOT)/"results.json").exists():
            pass

    def clearCommand(self):
        self.NET_COMMAND = []

    @staticmethod
    def __check_valid_dir(dir):
        """
        检测给定目录是否是Windows版OMNeT++ 5.6.2的根目录
        参数:
            dir_path: 要检测的目录路径字符串
        返回:
            bool: 如果是有效的OMNeT++ 5.6.2根目录返回True，否则False
        """
        ve = ValueError
        try:
            path = Path(dir)

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
                    raise ValueError(f"不存在文件{str(path / rel_path)}")

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
    # 使用方法示例
    try:
        # runner = OmnetppRunner("C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2",
        #                        r"cd /c/users/WeiKnight/Documents/omnetpp-5.6.2/samples/inet/examples/inet/igmp",
        #                        r"opp_run -u Cmdenv -c IGMPv2 -n ../../../src:../..:../../../tutorials:../../../showcases -l ../../../out/clang-release/src/libINET.dll omnetpp.ini"
        #                        )
        runner = OmnetppRunner("C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2",
                               "C:\\Users\\WeiKnight\\Documents\\omnetpp-5.6.2\\samples\\inet\\examples\\computing_power_network\\simpletest",
                               r"cd ./samples/inet/examples/computing_power_network/simpletest",
                               r"opp_run -u Cmdenv -c static -n ../../../src:../..:../../../tutorials:../../../showcases"
                               r" -l ../../../out/clang-release/src/libINET.dll omnetpp.ini --cmdenv-express-mode=true")
        runner.run()
    except Exception as e:
        print(e)