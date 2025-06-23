"""
作者信息：
推特：https://x.com/KingSmile88
微信：yufeng8138 
DC社区：https://discord.gg/gTQ3uhxCFs
"""

from meta_mask_bot import *
import logging
import time
from selenium.webdriver.support.ui import WebDriverWait

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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

def run_one_bot(account, debug_mode=False):
    """
    运行单个机器人实例
    :param account: 账户信息字典
    :param debug_mode: 是否启用调试模式
    :return: 是否成功运行
    """
    url = "https://app.quackai.ai/quackipedia?inviterCode=0cgb35&"
    try:
        bot = MetaMaskBot(account['address'], account['mnemonic'], '12345678')
        bot.debug_mode = debug_mode  # 设置调试模式
        open_and_switch_to_window(bot.driver, url)
        
        # 等待页面完全加载
        if debug_mode:
            logger.info("等待页面完全加载...")
        WebDriverWait(bot.driver, 20).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(5)  # 额外等待时间，确保动态内容加载完成
        
        # 调试模式下不自动关闭浏览器
        if not debug_mode:
            bot.driver.quit()
            logger.info("浏览器已关闭")
        else:
            logger.info("\n调试模式：浏览器窗口保持打开状态")
            logger.info("请手动关闭浏览器窗口或按 Ctrl+C 退出程序")
            while True:
                time.sleep(1)
                
        logger.info(f"账户 {account['address']} 处理成功")
        return True
        
    except Exception as e:
        logger.error(f"\n处理账户 {account['address']} 时出错: {str(e)}")
        if debug_mode:
            import traceback
            traceback.print_exc()
        return False 