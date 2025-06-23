"""
作者信息：
推特：https://x.com/KingSmile88
微信：yufeng8138 
DC社区：https://discord.gg/gTQ3uhxCFs
"""

# import imp
from meta_mask_bot import *
from gen_address import *
from auto_bot import run_one_bot

from faker import Faker
import threading
import random
import string
import sys
import os
from dotenv import load_dotenv
import time
import psutil
import subprocess
import logging
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 设置文件路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_FILE = os.path.join(PROJECT_ROOT, 'bot_accounts.txt')

# 全局变量
thread_num = 2  # 默认线程数
stop_threads = threading.Event()  # 线程停止事件
account_lock = threading.Lock()  # 账户锁
cur_account_idx = 0  # 当前账户索引
accounts = {}  # 账户列表
fake = Faker(locale='en_US')  # 用于生成随机用户名
user_lock = threading.Lock()  # 用户锁
users = {}  # 用户列表
start_idx = 0  # 起始账户索引
end_idx = 0  # 结束账户索引
debug_mode = False  # 调试模式默认关闭
running_threads = []  # 运行中的线程列表

def clear_processes():
    """清理未正常退出的Chrome和Python进程"""
    logger.info("正在清理未正常退出的进程...")
    
    # 获取当前Python进程的PID
    current_pid = os.getpid()
    
    # 清理Chrome进程
    chrome_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
                chrome_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # 清理Python进程（除了当前进程）
    python_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'python' in proc.info['name'].lower() and proc.info['pid'] != current_pid:
                proc.kill()
                python_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    logger.info(f"已清理 {chrome_count} 个Chrome进程和 {python_count} 个Python进程")
    logger.info("进程清理完成")
    time.sleep(3)  # 等待清理完成

def create_wallets():
    """创建新的钱包"""
    logger.info("\n=== 创建新钱包 ===")
    try:
        num = int(input("请输入要创建的钱包数量: "))
        if num <= 0:
            logger.warning("钱包数量必须大于0")
            return False
        
        if os.path.exists(ACCOUNTS_FILE):
            choice = input("bot_accounts.txt 已存在，是否覆盖？(y/n): ")
            if choice.lower() != 'y':
                logger.info("已取消创建钱包")
                return False
        
        accounts = []
        for i in range(num):
            addr, key, mnemonic = create_new_mnemonic_account()
            account = {
                'address': addr,
                'privateKey': key,
                'mnemonic': mnemonic,
                'index': i  # 添加索引字段
            }
            accounts.append(account)
            logger.info(f"已生成钱包 {i+1}/{num}")
        
        # 修改保存逻辑，确保按索引排序
        try:
            with open(ACCOUNTS_FILE, 'w') as f:
                # 按索引排序后再保存
                accounts.sort(key=lambda x: x['index'])
                json.dump(accounts, f, indent=4)
            logger.info(f"\n成功创建并保存 {num} 个钱包")
            return True
        except Exception as e:
            logger.error(f"保存钱包时出错: {str(e)}")
            return False
    except ValueError:
        logger.error("请输入有效的数字")
        return False
    except Exception as e:
        logger.error(f"创建钱包时出错: {str(e)}")
        return False

def restore_account_json(file_path):
    """从文件恢复账户信息"""
    try:
        with open(file_path, 'r') as f:
            accounts = json.load(f)
            # 确保账户按索引排序
            accounts.sort(key=lambda x: x['index'])
            return accounts
    except Exception as e:
        logger.error(f"读取账户文件时出错: {str(e)}")
        return None

def select_wallet_range():
    """选择要使用的钱包范围"""
    global start_idx, end_idx
    logger.info("\n=== 选择钱包范围 ===")
    try:
        if not os.path.exists(ACCOUNTS_FILE):
            logger.warning("未找到钱包文件，请先创建钱包")
            return False
        
        accounts = restore_account_json(ACCOUNTS_FILE)
        if not accounts:
            logger.error("加载钱包失败")
            return False
        
        logger.info(f"当前共有 {len(accounts)} 个钱包")
        start_idx = int(input("请输入起始钱包序号(从0开始): "))
        end_idx = int(input("请输入结束钱包序号: "))
        
        if start_idx < 0 or end_idx >= len(accounts) or start_idx > end_idx:
            logger.error("无效的钱包范围")
            return False
        
        logger.info(f"已选择钱包范围: {start_idx} 到 {end_idx}")
        return True
    except ValueError:
        logger.error("请输入有效的数字")
        return False
    except Exception as e:
        logger.error(f"选择钱包范围时出错: {str(e)}")
        return False

def set_thread_number():
    """设置线程数量"""
    global thread_num
    logger.info("\n=== 设置线程数量 ===")
    try:
        num = int(input("请输入要启动的线程数量: "))
        if num <= 0:
            logger.warning("线程数量必须大于0")
            return False
        thread_num = num
        logger.info(f"已设置线程数量: {thread_num}")
        return True
    except ValueError:
        logger.error("请输入有效的数字")
        return False

def get_account():
    """获取指定范围内的账户"""
    global cur_account_idx, start_idx, end_idx
    global account_lock
    global accounts
    
    try:
        account_lock.acquire()
        if cur_account_idx < start_idx:
            cur_account_idx = start_idx
        
        if cur_account_idx > end_idx:
            logger.info("已完成所有指定账户的操作")
            return None
            
        account = accounts[cur_account_idx]
        logger.info(f"当前使用账户索引: {cur_account_idx}")
        cur_account_idx += 1
        return account
    finally:
        account_lock.release()

def get_user():
    """生成随机用户名"""
    global user_lock
    user_lock.acquire()
    try:
        name = fake.name()
        name = name.replace(' ', '').replace('.', '')
        if len(name) > 18:
            name = name[0:17]
        return name
    finally:
        user_lock.release()

def open_and_switch_to_window(driver, url=None, window_handle=None):
    """
    打开新标签页或切换到指定标签页
    :param driver: WebDriver实例
    :param url: 要打开的URL（如果需要打开新标签页）
    :param window_handle: 要切换到的窗口句柄
    :return: 当前窗口句柄
    """
    try:
        if url:
            # 记录当前窗口句柄
            original_window = driver.current_window_handle
            
            # 打开新标签页
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(url)
            return original_window
        elif window_handle:
            # 切换到指定窗口
            driver.switch_to.window(window_handle)
            return window_handle
        else:
            # 如果都没有指定，切换到最后一个窗口
            driver.switch_to.window(driver.window_handles[-1])
            return driver.window_handles[-1]
    except Exception as e:
        logger.error(f"切换窗口时出错: {str(e)}")
        return None

def run():
    """运行机器人主循环"""
    global stop_threads
    success_count = 0
    fail_count = 0
    
    while not stop_threads.is_set():
        try:
            account = get_account()
            if account is None:
                logger.info(f"当前线程已完成所有账户操作，成功处理: {success_count} 个，失败: {fail_count} 个")
                return
                
            if run_one_bot(account, debug_mode):
                success_count += 1
            else:
                fail_count += 1
                
        except KeyboardInterrupt:
            logger.info("线程收到中断信号，正在退出...")
            return
        except Exception as e:
            logger.error(f"机器人运行出错: {str(e)}")
            fail_count += 1
            time.sleep(5)

def show_menu():
    """显示主菜单"""
    print("\n=== MetaMask 自动化工具 ===")
    print("1. 创建新钱包")
    print("2. 选择钱包范围")
    print("3. 设置线程数量")
    print("4. 启动机器人")
    print("5. 清理进程")
    print("6. 退出程序")
    choice = input("\n请选择操作 (1-6): ")
    return choice

def stop_all_threads():
    """停止所有运行中的线程"""
    global stop_threads, running_threads
    logger.info("\n正在停止所有机器人...")
    stop_threads.set()
    
    for thread in running_threads:
        if thread.is_alive():
            thread.join(timeout=5)
    
    running_threads.clear()
    stop_threads.clear()
    logger.info("所有机器人已停止")

def main():
    """主程序入口"""
    global accounts, debug_mode, start_idx, end_idx, thread_num, running_threads
    
    try:
        while True:
            choice = show_menu()
            
            if choice == '1':
                create_wallets()
            elif choice == '2':
                select_wallet_range()
            elif choice == '3':
                set_thread_number()
            elif choice == '4':
                # 检查必要设置
                if not os.path.exists(ACCOUNTS_FILE):
                    logger.warning("未找到钱包文件，请先创建钱包")
                    continue
                    
                accounts = restore_account_json(ACCOUNTS_FILE)
                if not accounts:
                    logger.error("加载钱包失败")
                    continue
                    
                # 设置调试模式
                debug_choice = input("是否启用调试模式？(y/n): ")
                debug_mode = debug_choice.lower() == 'y'
                
                if debug_mode:
                    thread_num = 1
                    start_idx = 0  # 调试模式下默认使用第一个钱包
                    end_idx = 0
                    logger.info("已启用调试模式，线程数设置为1")
                    logger.info(f"调试模式：使用第一个钱包（索引：{start_idx}）")
                else:
                    if not select_wallet_range():
                        continue
                    
                if start_idx >= len(accounts) or end_idx >= len(accounts):
                    logger.warning("请先选择有效的钱包范围")
                    continue
                
                # 启动机器人
                logger.info("\n正在启动机器人...")
   
                # 重置账户索引
                cur_account_idx = start_idx
                
                # 启动线程
                for i in range(thread_num):
                    thread = threading.Thread(target=run)
                    thread.daemon = True
                    thread.start()
                    running_threads.append(thread)
                    logger.info(f"已启动线程 {i+1}")
                    if debug_mode:
                        time.sleep(5)  # 给浏览器启动留出时间
                        break
                
                try:
                    for thread in running_threads:
                        thread.join()
                except KeyboardInterrupt:
                    stop_all_threads()
                    
            elif choice == '5':
                clear_processes()
            elif choice == '6':
                stop_all_threads()
                logger.info("程序已退出")
                sys.exit(0)
            else:
                logger.warning("无效的选择，请重新输入")
    except KeyboardInterrupt:
        stop_all_threads()
        logger.info("程序已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
