# coding=UTF-8
"""
作者信息：
推特：https://x.com/KingSmile88
微信：yufeng8138 
DC社区：https://discord.gg/gTQ3uhxCFs
"""

import time
import json
import random
import platform
import datetime
import threading
import os
import logging
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# MetaMask 扩展相关配置
METAMASK_EXTENSION_ID = os.getenv('METAMASK_EXTENSION_ID', 'jofoggdnjloolkiihcihdlchcagmlbkc')
METAMASK_EXTENSION_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extensions', '12.16.0_0')

# 设置 bot_file 目录路径（统一使用项目根目录下的 bot_file 文件夹）
BOT_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_file')
data_path_prefix = os.path.join(BOT_FILE_DIR, 'Chrome_')

# 确保 bot_file 目录存在
os.makedirs(BOT_FILE_DIR, exist_ok=True)

# 全局变量
chromes = {}  # 存储Chrome实例的字典
scroll_pages_num = 30  # 滚动页面次数

def open_and_switch_to_window(driver, url):
    """打开新窗口并切换到该窗口"""
    last_handle = driver.current_window_handle
    logger.info('正在打开新标签页')
    driver.execute_script("window.open('', '_blank');")
    time.sleep(1)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(1)
    driver.get(url)
    time.sleep(1)
    return last_handle

class MetamaskUtil:
    """MetaMask 工具类，用于处理 MetaMask 相关的操作"""
    def __init__(self):
        """初始化 MetaMask 工具类"""
        self.home_url = f'chrome-extension://{METAMASK_EXTENSION_ID}/home.html'

    def launch_chrome(self, data_path):
        """启动 Chrome 浏览器并配置 MetaMask 扩展"""
        try:
            options = uc.ChromeOptions()
            options.add_argument(f'--user-data-dir={data_path}')
            
            # 添加 MetaMask 扩展
            if not os.path.exists(METAMASK_EXTENSION_PATH):
                raise FileNotFoundError(f"未找到 MetaMask 扩展: {METAMASK_EXTENSION_PATH}")
            options.add_argument(f'--load-extension={METAMASK_EXTENSION_PATH}')
            
            # 其他配置
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-notifications')
            
            logger.info('正在使用 undetected-chromedriver 启动 Chrome...')
            logger.info(f'MetaMask 扩展路径: {METAMASK_EXTENSION_PATH}')
            logger.info(f'用户数据目录: {data_path}')
            
            # 设置 ChromeDriver 路径
            service = Service(ChromeDriverManager().install())
            
            # 设置 undetected_chromedriver 的配置
            driver = uc.Chrome(
                options=options,
                service=service,
                suppress_welcome=True,
                use_subprocess=True,
            )
            
            # 应用 stealth 设置
            stealth(driver,
                languages=["zh-CN", "zh"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            return driver
        except Exception as e:
            logger.error(f"启动 Chrome 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def init_metamask(self, driver, secret, password):
        """初始化 MetaMask 钱包"""
        logger.info("正在初始化 MetaMask...")
        
        try:
            # 等待 MetaMask 扩展加载
            logger.info("等待 MetaMask 扩展加载...")
            time.sleep(5)  # 增加初始等待时间
            
            # 使用 open_and_switch_to_window 打开并切换到 MetaMask 主页
            logger.info(f"导航到 MetaMask 主页...")
            last_handle = open_and_switch_to_window(driver, self.home_url)
            time.sleep(3)
            
            # 检查是否需要解锁
            try:
                logger.info("检查是否需要解锁...")
                # 等待密码输入框出现
                password_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))
                )
                if password_input:
                    logger.info("找到密码输入框，正在解锁...")
                    # 清除可能存在的内容并输入密码
                    password_input.clear()
                    password_input.send_keys(password)
                    time.sleep(1)
                    
                    # 点击登录按钮
                    login_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "登录") or contains(text(), "解锁")]'))
                    )
                    driver.execute_script("arguments[0].click();", login_button)
                    time.sleep(3)
                    
                    # 等待页面加载完成
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                    
                    logger.info("成功解锁钱包")
                    return
                    
            except Exception as e:
                # logger.info(f"未找到解锁界面或解锁失败: {str(e)}")
                logger.info(f"未找到解锁界面或解锁失败: ")
                
                logger.info("继续导入流程")
            
            # 开始导入钱包流程
            logger.info("开始导入钱包流程...")
            
            try:
                # 记录当前页面信息
                logger.info(f"当前页面 URL: {driver.current_url}")
                logger.info("当前页面标题: " + driver.title)
                
                # 尝试定位使用条款复选框
                try:
                    logger.info("尝试定位使用条款复选框...")
                    checkbox = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="checkbox"]'))
                    )
                    if not checkbox.is_selected():
                        checkbox.click()
                        time.sleep(1)
                except Exception as e:
                    logger.info(f"未找到使用条款复选框或已选中: {str(e)}")
                
                # 尝试多种方式定位导入钱包按钮
                logger.info("尝试定位导入钱包按钮...")
                import_button = None
                
                # 方法1：通过文本内容
                try:
                    import_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//button[text()="导入现有钱包"]'))
                    )
                except:
                    logger.info("方法1未找到按钮，尝试方法2...")
                
                # 方法2：通过部分文本
                if not import_button:
                    try:
                        import_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "导入现有")]//ancestor::button'))
                        )
                    except:
                        logger.info("方法2未找到按钮，尝试方法3...")
                
                # 方法3：通过class名称（需要根据实际情况调整）
                if not import_button:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, 'button')
                        for button in buttons:
                            if '导入' in button.text or '现有' in button.text:
                                import_button = button
                                break
                    except:
                        logger.info("方法3未找到按钮")
                
                if import_button:
                    logger.info(f"找到导入按钮，文本内容: {import_button.text}")
                    # 使用 JavaScript 点击按钮
                    driver.execute_script("arguments[0].click();", import_button)
                    time.sleep(3)
                    
                    # 使用 open_and_switch_to_window 切换到新标签页
                    last_handle = open_and_switch_to_window(driver, driver.current_url)
                    time.sleep(2)
                else:
                    # 如果还是找不到按钮，保存页面信息以供调试
                    logger.error("未能找到导入钱包按钮")
                    logger.info("页面内容:")
                    logger.info(driver.page_source)
                    raise Exception("未能找到导入钱包按钮")
                
                # 处理数据收集页面
                logger.info("处理数据收集页面...")
                try:
                    # 等待页面加载
                    time.sleep(2)
                    
                    # 尝试定位"不，谢谢"按钮
                    decline_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "不，谢谢")]'))
                    )
                    logger.info("找到'不，谢谢'按钮")
                    driver.execute_script("arguments[0].click();", decline_button)
                    time.sleep(2)
                except Exception as e:
                    logger.info(f"未找到'不，谢谢'按钮，尝试其他方式: {str(e)}")
                    try:
                        # 尝试通过按钮顺序定位（通常"不，谢谢"是左边的按钮）
                        buttons = driver.find_elements(By.TAG_NAME, 'button')
                        if len(buttons) >= 2:
                            logger.info("通过按钮顺序定位'不，谢谢'按钮")
                            driver.execute_script("arguments[0].click();", buttons[0])
                            time.sleep(2)
                    except Exception as e:
                        logger.error(f"处理数据收集页面失败: {str(e)}")
                
                # 等待页面加载完成
                logger.info("等待页面加载完成...")
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                time.sleep(2)
                
                # 输入助记词
                logger.info("正在输入助记词...")
                try:
                    # 确保在正确的标签页
                    handles = driver.window_handles
                    driver.switch_to.window(handles[-1])
                    
                    # 首先等待助记词输入区域加载
                    logger.info("等待助记词输入区域加载...")
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'import-srp__srp'))
                    )
                    time.sleep(1)
                    
                    # 查找所有助记词输入框
                    input_fields = driver.find_elements(By.CLASS_NAME, 'import-srp__srp-word')
                    
                    if input_fields:
                        logger.info(f"找到 {len(input_fields)} 个助记词输入框")
                        words = secret.strip().split()
                        
                        if len(words) != len(input_fields):
                            raise Exception(f"助记词数量 ({len(words)}) 与输入框数量 ({len(input_fields)}) 不匹配")
                        
                        # 逐个输入助记词
                        for i, (word, field) in enumerate(zip(words, input_fields)):
                            # 不在日志中显示具体的助记词
                            logger.info(f"正在输入第 {i+1} 个助记词...")
                            # 找到输入框元素
                            input_element = field.find_element(By.TAG_NAME, 'input')
                            # 清除可能存在的内容
                            input_element.clear()
                            # 使用send_keys模拟真实输入
                            input_element.send_keys(word)
                            # 等待一下确保输入完成
                            time.sleep(0.5)
                            # 验证输入是否成功，但不输出具体内容
                            actual_value = input_element.get_attribute('value')
                            if actual_value != word:
                                logger.error(f"第 {i+1} 个助记词输入验证失败")
                                raise Exception("助记词输入验证失败")
                    else:
                        raise Exception("未找到助记词输入框")
                    
                    # 等待一下确保所有输入都已完成
                    time.sleep(2)
                    
                    # 点击"确认私钥助记词"按钮
                    logger.info("点击确认私钥助记词按钮...")
                    try:
                        confirm_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "确认私钥助记词") or contains(text(), "Confirm Secret Recovery Phrase")]'))
                        )
                        driver.execute_script("arguments[0].click();", confirm_button)
                        time.sleep(2)
                        
                        # 确保切换到新打开的标签页
                        handles = driver.window_handles
                        if len(handles) > 1:
                            driver.switch_to.window(handles[-1])
                            time.sleep(2)
                        
                        # 等待进入密码设置页面
                        logger.info("等待进入密码设置页面...")
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))
                        )
                    except Exception as e:
                        logger.error(f"点击确认私钥助记词按钮失败: {str(e)}")
                        # 保存当前页面信息以供调试
                        logger.info("当前页面内容:")
                        logger.info(driver.page_source)
                        raise Exception("无法进入密码设置页面，请检查助记词是否输入正确")
                    
                except Exception as e:
                    logger.error(f"输入助记词失败: {str(e)}")
                    # 保存当前页面信息以供调试
                    logger.info("当前页面内容:")
                    logger.info(driver.page_source)
                    raise e
                
                # 设置密码
                logger.info("正在设置密码...")
                try:
                    # 确保在正确的标签页
                    handles = driver.window_handles
                    driver.switch_to.window(handles[-1])
                    
                    password_inputs = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, '//input[@type="password"]'))
                    )
                    if len(password_inputs) < 2:
                        raise Exception(f"未找到足够的密码输入框，当前只有 {len(password_inputs)} 个")
                    
                    # 输入两次密码
                    for input_box in password_inputs:
                        input_box.clear()  # 清除可能的现有输入
                        input_box.send_keys(password)
                        time.sleep(0.5)
                    
                    # 同意条款（如果有）
                    try:
                        checkboxes = driver.find_elements(By.XPATH, '//input[@type="checkbox"]')
                        for checkbox in checkboxes:
                            if not checkbox.is_selected():
                                driver.execute_script("arguments[0].click();", checkbox)
                                time.sleep(0.5)
                    except:
                        logger.info("未找到需要勾选的条款复选框")
                    
                    # 点击导入/确认按钮
                    logger.info("点击导入/确认按钮...")
                    confirm_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            '//button[contains(text(), "导入") or contains(text(), "Import") or contains(text(), "创建") or contains(text(), "Create")]'
                        ))
                    )
                    driver.execute_script("arguments[0].click();", confirm_button)
                    time.sleep(5)
                    
                    # 确保切换到新打开的标签页
                    handles = driver.window_handles
                    if len(handles) > 1:
                        driver.switch_to.window(handles[-1])
                        time.sleep(2)
                    
                    # 处理"您的钱包已准备就绪"界面
                    logger.info("处理钱包准备就绪界面...")
                    try:
                        ready_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "完成")]'))
                        )
                        driver.execute_script("arguments[0].click();", ready_button)
                        time.sleep(2)
                    except Exception as e:
                        logger.warning(f"未找到钱包准备就绪界面的完成按钮: {str(e)}")
                    
                    # 处理"MetaMask安装完成"界面（固定扩展程序步骤）
                    logger.info("处理安装完成界面...")
                    try:
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "下一步")]'))
                        )
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                    except Exception as e:
                        logger.warning(f"未找到安装完成界面的下一步按钮: {str(e)}")
                    
                    # 处理最终完成界面
                    logger.info("处理最终完成界面...")
                    try:
                        final_done_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "完成")]'))
                        )
                        driver.execute_script("arguments[0].click();", final_done_button)
                        time.sleep(2)
                        logger.info("钱包导入成功")
                    except Exception as e:
                        logger.error(f"未找到最终完成界面的完成按钮: {str(e)}")
                        raise Exception("钱包导入失败")
                    
                except Exception as e:
                    logger.error(f"设置密码失败: {str(e)}")
                    raise e
                
                logger.info("MetaMask 初始化完成")
                
            except Exception as e:
                logger.error(f"导入流程出错: {str(e)}")
                # 保存页面截图和源码
                try:
                    screenshot_path = os.path.join(BOT_FILE_DIR, f'error_screenshot_{int(time.time())}.png')
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"错误截图已保存至: {screenshot_path}")
                    
                    source_path = os.path.join(BOT_FILE_DIR, f'error_source_{int(time.time())}.html')
                    with open(source_path, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    logger.info(f"页面源码已保存至: {source_path}")
                except:
                    pass
                raise e
            
        except Exception as e:
            logger.error(f"MetaMask 初始化过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def handle_website_interaction(self, driver, action_type=None):
        """统一处理网站交互（连接和签名）
        
        Args:
            driver: WebDriver实例
            action_type: 指定操作类型，可以是 'connect' 或 'sign'，如果为 None 则都尝试
            
        Returns:
            str: 'connect' 或 'sign' 表示执行的操作，None 表示没有操作执行
        """
        last_handle = driver.current_window_handle
        driver.get(self.home_url)
        time.sleep(2)
        
        try:
            if action_type in [None, 'connect']:
                # 检查连接请求
                conn_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//button[text()="下一步"]'))
                )
                if conn_btn:
                    conn_btn[0].click()
                    WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[text()="连接"]'))
                    ).click()
                    logger.info('网站已连接到 MetaMask')
                    return 'connect'
            
            if action_type in [None, 'sign']:
                # 检查签名请求
                sign_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//button[text()="签名"]'))
                )
                if sign_btn:
                    sign_btn[0].click()
                    logger.info('签名已确认')
                    return 'sign'
            
            return None
            
        except Exception as e:
            logger.error(f"处理网站交互时出错: {str(e)}")
            return None
            
        finally:
            driver.switch_to.window(last_handle)

    def switch_network(self, driver, network_name):
        """切换网络
        
        Args:
            driver: WebDriver 实例
            network_name: 网络名称，如 'Ethereum Mainnet', 'BSC Mainnet', 'Polygon Mainnet' 等
        """
        try:
            logger.info(f"正在切换到网络: {network_name}")
            
            # 点击网络切换按钮
            network_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "network-display")]'))
            )
            network_button.click()
            time.sleep(2)
            
            # 点击添加网络按钮（如果需要）
            try:
                add_network_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "添加网络") or contains(text(), "Add network")]'))
                )
                add_network_button.click()
                time.sleep(2)
                
                # 添加常用网络配置
                networks = {
                    'BSC Mainnet': {
                        'network_name': 'BNB Smart Chain',
                        'rpc_url': 'https://bsc-dataseed.binance.org/',
                        'chain_id': '56',
                        'currency_symbol': 'BNB',
                        'block_explorer': 'https://bscscan.com/'
                    },
                    'Polygon Mainnet': {
                        'network_name': 'Polygon Mainnet',
                        'rpc_url': 'https://polygon-rpc.com',
                        'chain_id': '137',
                        'currency_symbol': 'MATIC',
                        'block_explorer': 'https://polygonscan.com/'
                    }
                }
                
                if network_name in networks:
                    network_config = networks[network_name]
                    # 填写网络信息
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="网络名称"]'))
                    ).send_keys(network_config['network_name'])
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="RPC URL"]'))
                    ).send_keys(network_config['rpc_url'])
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="链 ID"]'))
                    ).send_keys(network_config['chain_id'])
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="货币符号"]'))
                    ).send_keys(network_config['currency_symbol'])
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="区块浏览器 URL"]'))
                    ).send_keys(network_config['block_explorer'])
                    
                    # 保存网络
                    save_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "保存") or contains(text(), "Save")]'))
                    )
                    save_button.click()
                    time.sleep(2)
                    
                    # 切换到新网络
                    switch_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "切换网络") or contains(text(), "Switch network")]'))
                    )
                    switch_button.click()
                    time.sleep(2)
                else:
                    # 直接点击已有网络
                    network_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f'//div[contains(text(), "{network_name}")]'))
                    )
                    network_option.click()
                    time.sleep(2)
            
            except Exception as e:
                logger.info(f"网络 {network_name} 已存在，直接切换")
                # 直接点击已有网络
                network_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f'//div[contains(text(), "{network_name}")]'))
                )
                network_option.click()
                time.sleep(2)
            
            logger.info(f"已成功切换到网络: {network_name}")
            
        except Exception as e:
            logger.error(f"切换网络时出错: {str(e)}")
            raise e

class MetaMaskBot:
    """MetaMask 机器人主类"""
    def __init__(self, file_id, mnemonic, password):
        """初始化 MetaMask 机器人"""
        logger.info('正在初始化机器人')
        self.mnemonic = mnemonic
        self.password = password
        self.running = True
        self.metamask = MetamaskUtil()
        self.debug_mode = False  # 添加调试模式属性
        self.init_chrome(file_id)

    def init_chrome(self, file_id):
        """初始化 Chrome 浏览器"""
        global chromes
        data_path = data_path_prefix + str(file_id)
        logger.info('正在为机器人启动 Chrome')
        self.driver = self.metamask.launch_chrome(data_path)
        chromes[file_id] = self.driver
        self.metamask.init_metamask(self.driver, self.mnemonic, self.password)

    def wait_for_element(self, xpath, timeout=10):
        """等待元素出现并返回
        
        Args:
            xpath: 元素的XPath表达式
            timeout: 等待超时时间（秒）
            
        Returns:
            找到的元素，如果超时则返回None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except Exception as e:
            logger.warning(f"等待元素超时: {xpath}")
            return None

    def switch_to_metamask_window(self, return_to_original=True):
        """统一的窗口切换处理函数
        
        Args:
            return_to_original: 是否在操作后返回原始窗口
            
        Returns:
            tuple: (original_handle, success)
            - original_handle: 原始窗口句柄
            - success: 切换是否成功
        """
        try:
            original_handle = self.driver.current_window_handle
            handles = self.driver.window_handles
            self.driver.switch_to.window(handles[-1])
            time.sleep(2)
            
            if return_to_original:
                self.driver.switch_to.window(original_handle)
            
            return original_handle, True
        except Exception as e:
            logger.error(f"切换MetaMask窗口时出错: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return None, False

    def handle_metamask_notification(self):
        """处理MetaMask通知"""
        try:
            original_handle, success = self.switch_to_metamask_window(return_to_original=False)
            if not success:
                return False
            
            # 处理连接请求
            if self._handle_connection_request():
                logger.info('已处理MetaMask连接请求')
            
            # 处理签名请求
            if self._handle_signature_request():
                logger.info('已处理MetaMask签名请求')
            
            # 切回主窗口
            self.driver.switch_to.window(original_handle)
            return True
            
        except Exception as e:
            logger.error(f"处理MetaMask通知时出错: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

    def _handle_connection_request(self):
        """处理连接请求的内部函数"""
        try:
            next_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="下一步"]'))
            )
            next_button.click()
            time.sleep(1)
            
            connect_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="连接"]'))
            )
            connect_button.click()
            return True
        except:
            return False

    def _handle_signature_request(self):
        """处理签名请求的内部函数"""
        try:
            sign_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="签名"]'))
            )
            sign_button.click()
            return True
        except:
            return False

    def handle_metamask_popup(self, original_window):
        """处理MetaMask弹窗"""
        try:
            time.sleep(3)
            _, success = self.switch_to_metamask_window(return_to_original=False)
            if not success:
                return False
            
            # 检查是否是网络添加页面
            if self._handle_network_approval():
                logger.info("网络添加/切换成功")
            else:
                # 尝试处理连接请求
                if self._handle_connection_request():
                    logger.info("连接请求处理成功")
                else:
                    logger.error("未找到预期的按钮")
                    if self.debug_mode:
                        logger.info("当前页面内容:")
                        logger.info(self.driver.page_source)
                    return False
            
            # 切换回原始窗口
            self.driver.switch_to.window(original_window)
            self.driver.refresh()
            return True
            
        except Exception as e:
            logger.error(f"处理MetaMask弹窗时出错: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

    def _handle_network_approval(self):
        """处理网络添加/切换的内部函数"""
        try:
            # 查找批准按钮
            approve_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '批准')]"))
            )
            if approve_button:
                logger.info("找到网络添加页面的批准按钮")
                approve_button.click()
                time.sleep(2)
                
                # 检查是否需要切换网络
                try:
                    switch_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '切换网络')]"))
                    )
                    if switch_button:
                        logger.info("找到切换网络按钮")
                        switch_button.click()
                        time.sleep(2)
                except:
                    logger.info("未找到切换网络按钮，继续执行")
                return True
        except:
            return False
