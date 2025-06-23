import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class MetaMaskInteraction:
    """
    MetaMask 交互类，提供与 MetaMask 浏览器扩展进行交互的所有功能
    """
    
    # MetaMask 扩展的固定元素选择器
    SELECTORS = {
        # 欢迎页面
        'welcome_page': {
            'get_started_button': 'button.onboarding__button',
            'import_wallet_button': '//button[contains(text(), "导入钱包")]',
            'create_wallet_button': '//button[contains(text(), "创建钱包")]',
        },
        
        # 导入钱包页面
        'import_wallet': {
            'input_seed_phrase': '//input[@placeholder="粘贴种子短语"]',
            'password_input': '//input[@id="password"]',
            'confirm_password_input': '//input[@id="confirm-password"]',
            'terms_checkbox': '//div[contains(@class, "check-box")]',
            'import_button': '//button[contains(text(), "导入")]',
        },
        
        # 创建钱包页面
        'create_wallet': {
            'password_input': '//input[@id="create-password"]',
            'confirm_password_input': '//input[@id="confirm-password"]',
            'terms_checkbox': '//div[contains(@class, "check-box")]',
            'create_button': '//button[contains(text(), "创建")]',
            'seed_phrase_revealed': '//div[contains(@class, "reveal-seed-phrase__secret-blocker")]',
            'reveal_seed_phrase_button': '//button[contains(text(), "显示密码短语")]',
            'seed_phrase_text': '//div[contains(@class, "reveal-seed-phrase__secret-words")]',
            'remind_later_button': '//button[contains(text(), "稍后提醒我")]',
        },
        
        # 主页面
        'main_page': {
            'account_menu_button': '//div[contains(@class, "account-menu__icon")]',
            'network_dropdown': '//div[contains(@class, "network-display")]',
            'account_dropdown': '//div[contains(@class, "account-menu__icon")]',
            'settings_button': '//div[contains(text(), "设置")]',
            'lock_button': '//div[contains(text(), "锁定")]',
        },
        
        # 登录页面
        'unlock_page': {
            'password_input': 'input#password',
            'unlock_button': 'button.unlock-page__login-button',
        },
        
        # 交易确认页面
        'confirm_transaction': {
            'confirm_button': '//button[contains(text(), "确认")]',
            'reject_button': '//button[contains(text(), "拒绝")]',
            'gas_fee_link': '//button[contains(text(), "编辑")]',
            'total_amount': '//div[contains(@class, "confirm-page-container-content__total-value")]',
        },
        
        # 添加网络页面
        'add_network': {
            'network_name': '//input[@id="network-name"]',
            'rpc_url': '//input[@id="rpc-url"]',
            'chain_id': '//input[@id="chainId"]',
            'currency_symbol': '//input[@id="currency-symbol"]',
            'block_explorer': '//input[@id="block-explorer-url"]',
            'save_button': '//button[contains(text(), "保存")]',
        },
        
        # 设置页面
        'settings': {
            'networks_tab': '//div[contains(text(), "网络")]',
            'add_network_button': '//button[contains(text(), "添加网络")]',
        },
        
        # 添加代币页面
        'add_token': {
            'custom_token_tab': '//button[contains(text(), "自定义代币")]',
            'token_address': '//input[@id="custom-address"]',
            'token_symbol': '//input[@id="custom-symbol"]',
            'token_decimals': '//input[@id="custom-decimals"]',
            'next_button': '//button[contains(text(), "下一步")]',
            'add_tokens_button': '//button[contains(text(), "添加代币")]',
        }
    }
    
    def __init__(self, extension_path=None, browser_path=None, user_data_dir=None, headless=False):
        """
        初始化 MetaMask 交互类
        
        Args:
            extension_path (str): MetaMask扩展的本地路径
            browser_path (str): Chrome浏览器可执行文件的路径
            user_data_dir (str): Chrome用户数据目录路径
            headless (bool): 是否以无头模式运行浏览器
        """
        self.extension_path = extension_path
        self.browser_path = browser_path
        self.user_data_dir = user_data_dir
        self.driver = None
        self.extension_id = None
        self.headless = headless
        
    def setup_driver(self):
        """
        设置 Chrome 驱动
        """
        chrome_options = Options()
        
        # 设置 Chrome 浏览器路径
        if self.browser_path:
            chrome_options.binary_location = self.browser_path
            
        # 设置用户数据目录
        if self.user_data_dir:
            chrome_options.add_argument(f"user-data-dir={self.user_data_dir}")
        
        # 添加 MetaMask 扩展
        if self.extension_path:
            chrome_options.add_extension(self.extension_path)
        
        # 其他必要设置
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        if self.headless:
            chrome_options.add_argument("--headless=new")  # 新版Selenium中推荐的无头模式语法
            
        # 初始化驱动
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # 找到扩展ID
        if not self.extension_id:
            self.driver.get("chrome://extensions/")
            time.sleep(1)
            
            # 获取扩展ID
            self.extension_id = self._get_metamask_extension_id()
            
        return self.driver
        
    def _get_metamask_extension_id(self):
        """
        获取 MetaMask 扩展的 ID
        """
        self.driver.get("chrome://extensions/")
        time.sleep(2)
        
        # 启用开发者模式以查看扩展ID
        try:
            dev_mode_toggle = self.driver.find_element(By.XPATH, "//div[@class='developer-mode']")
            if dev_mode_toggle:
                dev_mode_toggle.click()
        except:
            pass
            
        time.sleep(1)
        
        # 尝试从页面获取 MetaMask 扩展的 ID
        extensions = self.driver.find_elements(By.XPATH, "//div[@class='extension-id']")
        for extension in extensions:
            ext_id = extension.text.strip()
            if ext_id:
                try:
                    # 测试这个扩展ID是否是MetaMask
                    self.driver.get(f"chrome-extension://{ext_id}/home.html")
                    time.sleep(2)
                    
                    # 检查是否有MetaMask特有的元素
                    if "MetaMask" in self.driver.title or self.driver.find_elements(By.XPATH, "//div[contains(text(), 'MetaMask')]"):
                        return ext_id
                except:
                    continue
        
        # 如果无法自动识别，则返回硬编码的默认ID
        return "nkbihfbeogaeaoehlefnkodbefgpgknn"  # MetaMask的默认扩展ID 

    def open_metamask(self):
        """
        打开 MetaMask 扩展
        """
        if not self.driver:
            self.setup_driver()
            
        if not self.extension_id:
            self.extension_id = self._get_metamask_extension_id()
            
        # 打开MetaMask主页面
        self.driver.get(f"chrome-extension://{self.extension_id}/home.html")
        time.sleep(2)
        return self.driver.current_url
    
    def wait_for_element(self, selector, by=By.XPATH, timeout=10):
        """
        等待元素出现
        
        Args:
            selector (str): CSS 选择器或 XPath
            by: 选择器类型
            timeout (int): 超时时间(秒)
            
        Returns:
            WebElement: 找到的元素
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            print(f"元素未在 {timeout} 秒内找到: {selector}")
            return None
            
    def wait_for_element_clickable(self, selector, by=By.XPATH, timeout=10):
        """
        等待元素可点击
        
        Args:
            selector (str): CSS 选择器或 XPath
            by: 选择器类型
            timeout (int): 超时时间(秒)
            
        Returns:
            WebElement: 找到的元素
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            return element
        except TimeoutException:
            print(f"元素在 {timeout} 秒内不可点击: {selector}")
            return None
    
    def find_element_safe(self, selector, by=By.XPATH):
        """
        安全地查找元素（不抛出异常）
        
        Args:
            selector (str): CSS 选择器或 XPath
            by: 选择器类型
            
        Returns:
            WebElement 或 None
        """
        try:
            return self.driver.find_element(by, selector)
        except NoSuchElementException:
            return None
            
    def click_element_safe(self, selector, by=By.XPATH, timeout=10, retry=3):
        """
        安全地点击元素，具有重试机制
        
        Args:
            selector (str): CSS 选择器或 XPath
            by: 选择器类型
            timeout (int): 等待超时时间
            retry (int): 重试次数
            
        Returns:
            bool: 是否成功点击
        """
        for attempt in range(retry):
            try:
                element = self.wait_for_element_clickable(selector, by, timeout)
                if not element:
                    continue
                    
                # 尝试常规点击
                try:
                    element.click()
                    return True
                except:
                    # 如果常规点击失败，尝试JavaScript点击
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
            except Exception as e:
                print(f"点击失败，尝试 {attempt + 1}/{retry}: {str(e)}")
                time.sleep(1)
                
        return False
        
    def input_text(self, selector, text, by=By.XPATH, clear=True):
        """
        向输入框输入文本
        
        Args:
            selector (str): CSS 选择器或 XPath
            text (str): 要输入的文本
            by: 选择器类型
            clear (bool): 是否先清除输入框
            
        Returns:
            bool: 是否成功输入
        """
        element = self.wait_for_element(selector, by)
        if not element:
            return False
            
        try:
            if clear:
                element.clear()
                
            element.send_keys(text)
            return True
        except Exception as e:
            print(f"输入文本失败: {str(e)}")
            return False
    
    def get_current_page(self):
        """
        获取当前所在的MetaMask页面类型
        
        Returns:
            str: 页面类型标识
        """
        # 检查是否在欢迎页面
        if self.find_element_safe(self.SELECTORS['welcome_page']['get_started_button'], By.CSS_SELECTOR):
            return 'welcome_page'
            
        # 检查是否在解锁页面
        if self.find_element_safe(self.SELECTORS['unlock_page']['password_input'], By.CSS_SELECTOR):
            return 'unlock_page'
            
        # 检查是否在主页面
        if self.find_element_safe(self.SELECTORS['main_page']['account_dropdown'], By.XPATH):
            return 'main_page'
            
        # 检查是否在导入钱包页面
        if self.find_element_safe(self.SELECTORS['import_wallet']['input_seed_phrase'], By.XPATH):
            return 'import_wallet'
            
        # 检查是否在创建钱包页面
        if self.find_element_safe(self.SELECTORS['create_wallet']['password_input'], By.XPATH):
            return 'create_wallet'
            
        # 检查是否在交易确认页面
        if self.find_element_safe(self.SELECTORS['confirm_transaction']['confirm_button'], By.XPATH):
            return 'confirm_transaction'
            
        # 未知页面
        return 'unknown'
        
    def switch_to_tab(self, tab_index=0):
        """
        切换到指定的浏览器标签页
        
        Args:
            tab_index (int): 标签页索引
            
        Returns:
            bool: 是否成功切换
        """
        try:
            windows = self.driver.window_handles
            if tab_index >= len(windows):
                return False
                
            self.driver.switch_to.window(windows[tab_index])
            return True
        except Exception as e:
            print(f"切换标签页失败: {str(e)}")
            return False
            
    def create_new_wallet(self, password):
        """
        创建新钱包
        
        Args:
            password (str): 钱包密码
            
        Returns:
            str: 种子短语，如果失败则返回None
        """
        self.open_metamask()
        
        # 检查当前页面
        current_page = self.get_current_page()
        
        # 如果已经在主页，表示钱包已创建
        if current_page == 'main_page':
            print("钱包已存在")
            return None
            
        # 欢迎页面点击开始
        if current_page == 'welcome_page':
            # 点击"开始使用"按钮
            self.click_element_safe(self.SELECTORS['welcome_page']['get_started_button'], By.CSS_SELECTOR)
            time.sleep(1)
            
            # 点击"创建钱包"按钮
            self.click_element_safe(self.SELECTORS['welcome_page']['create_wallet_button'])
            time.sleep(1)
        
        # 在创建钱包页面输入密码
        if self.get_current_page() == 'create_wallet':
            # 输入密码
            self.input_text(self.SELECTORS['create_wallet']['password_input'], password)
            self.input_text(self.SELECTORS['create_wallet']['confirm_password_input'], password)
            
            # 勾选服务条款
            self.click_element_safe(self.SELECTORS['create_wallet']['terms_checkbox'])
            
            # 点击创建按钮
            self.click_element_safe(self.SELECTORS['create_wallet']['create_button'])
            time.sleep(3)
            
            # 点击显示助记词按钮
            self.click_element_safe(self.SELECTORS['create_wallet']['reveal_seed_phrase_button'])
            time.sleep(1)
            
            # 获取助记词文本
            seed_element = self.wait_for_element(self.SELECTORS['create_wallet']['seed_phrase_text'])
            if seed_element:
                seed_phrase = seed_element.text
                
                # 点击稍后提醒按钮
                self.click_element_safe(self.SELECTORS['create_wallet']['remind_later_button'])
                time.sleep(1)
                
                return seed_phrase
        
        print("创建钱包失败")
        return None
    
    def import_wallet(self, seed_phrase, password):
        """
        导入钱包
        
        Args:
            seed_phrase (str): 种子短语
            password (str): 钱包密码
            
        Returns:
            bool: 是否成功导入
        """
        self.open_metamask()
        
        # 检查当前页面
        current_page = self.get_current_page()
        
        # 如果已经在主页，表示钱包已导入
        if current_page == 'main_page':
            print("钱包已导入")
            return True
            
        # 欢迎页面点击开始
        if current_page == 'welcome_page':
            # 点击"开始使用"按钮
            self.click_element_safe(self.SELECTORS['welcome_page']['get_started_button'], By.CSS_SELECTOR)
            time.sleep(1)
            
            # 点击"导入钱包"按钮
            self.click_element_safe(self.SELECTORS['welcome_page']['import_wallet_button'])
            time.sleep(1)
        
        # 在导入钱包页面输入助记词和密码
        if self.get_current_page() == 'import_wallet':
            # 输入助记词
            self.input_text(self.SELECTORS['import_wallet']['input_seed_phrase'], seed_phrase)
            
            # 输入密码
            self.input_text(self.SELECTORS['import_wallet']['password_input'], password)
            self.input_text(self.SELECTORS['import_wallet']['confirm_password_input'], password)
            
            # 勾选服务条款
            self.click_element_safe(self.SELECTORS['import_wallet']['terms_checkbox'])
            
            # 点击导入按钮
            self.click_element_safe(self.SELECTORS['import_wallet']['import_button'])
            time.sleep(5)
            
            # 检查是否导入成功
            return self.get_current_page() == 'main_page'
        
        print("导入钱包失败")
        return False
        
    def unlock_wallet(self, password):
        """
        解锁钱包
        
        Args:
            password (str): 钱包密码
            
        Returns:
            bool: 是否成功解锁
        """
        self.open_metamask()
        
        # 检查当前页面
        current_page = self.get_current_page()
        
        # 如果已经在主页，表示钱包已解锁
        if current_page == 'main_page':
            print("钱包已解锁")
            return True
            
        # 在解锁页面输入密码
        if current_page == 'unlock_page':
            # 输入密码
            self.input_text(self.SELECTORS['unlock_page']['password_input'], password, By.CSS_SELECTOR)
            
            # 点击解锁按钮
            self.click_element_safe(self.SELECTORS['unlock_page']['unlock_button'], By.CSS_SELECTOR)
            time.sleep(2)
            
            # 检查是否解锁成功
            return self.get_current_page() == 'main_page'
        
        print("解锁钱包失败")
        return False
        
    def lock_wallet(self):
        """
        锁定钱包
        
        Returns:
            bool: 是否成功锁定
        """
        self.open_metamask()
        
        # 检查当前页面
        if self.get_current_page() != 'main_page':
            print("当前不在主页，无法锁定钱包")
            return False
            
        # 点击账户菜单
        self.click_element_safe(self.SELECTORS['main_page']['account_dropdown'])
        time.sleep(1)
        
        # 点击锁定按钮
        self.click_element_safe(self.SELECTORS['main_page']['lock_button'])
        time.sleep(1)
        
        # 检查是否锁定成功
        return self.get_current_page() == 'unlock_page'
        
    def get_wallet_address(self):
        """
        获取钱包地址
        
        Returns:
            str: 钱包地址
        """
        self.open_metamask()
        
        # 检查当前页面
        if self.get_current_page() != 'main_page':
            print("当前不在主页，无法获取钱包地址")
            return None
            
        # 获取钱包地址 (页面上的账户地址复制按钮)
        address_copy_btn = self.find_element_safe('//div[contains(@class, "selected-account__address")]')
        if address_copy_btn:
            # 地址通常在data-clipboard-text属性中
            address = address_copy_btn.get_attribute('data-clipboard-text')
            if not address:
                # 如果没有找到属性，尝试获取显示的文本
                address = address_copy_btn.text
            return address
            
        return None

    def add_network(self, name, rpc_url, chain_id, symbol, explorer_url=None):
        """
        添加自定义网络
        
        Args:
            name (str): 网络名称
            rpc_url (str): RPC URL
            chain_id (str): 链ID
            symbol (str): 货币符号
            explorer_url (str): 区块浏览器URL
            
        Returns:
            bool: 是否成功添加
        """
        self.open_metamask()
        
        # 确保先解锁
        if self.get_current_page() != 'main_page':
            print("当前不在主页，请先解锁钱包")
            return False
            
        # 点击网络下拉菜单
        self.click_element_safe(self.SELECTORS['main_page']['network_dropdown'])
        time.sleep(1)
        
        # 点击设置按钮
        settings_button = self.find_element_safe('//button[contains(@class, "network-display--clickable")]')
        if settings_button:
            settings_button.click()
            time.sleep(1)
        else:
            print("未找到设置按钮")
            return False
            
        # 点击网络标签
        self.click_element_safe(self.SELECTORS['settings']['networks_tab'])
        time.sleep(1)
        
        # 点击添加网络按钮
        self.click_element_safe(self.SELECTORS['settings']['add_network_button'])
        time.sleep(1)
        
        # 输入网络信息
        self.input_text(self.SELECTORS['add_network']['network_name'], name)
        self.input_text(self.SELECTORS['add_network']['rpc_url'], rpc_url)
        self.input_text(self.SELECTORS['add_network']['chain_id'], chain_id)
        self.input_text(self.SELECTORS['add_network']['currency_symbol'], symbol)
        
        if explorer_url:
            self.input_text(self.SELECTORS['add_network']['block_explorer'], explorer_url)
        
        # 点击保存按钮
        save_success = self.click_element_safe(self.SELECTORS['add_network']['save_button'])
        time.sleep(3)
        
        return save_success
        
    def switch_network(self, network_name):
        """
        切换网络
        
        Args:
            network_name (str): 网络名称
            
        Returns:
            bool: 是否成功切换
        """
        self.open_metamask()
        
        # 确保先解锁
        if self.get_current_page() != 'main_page':
            print("当前不在主页，请先解锁钱包")
            return False
            
        # 点击网络下拉菜单
        self.click_element_safe(self.SELECTORS['main_page']['network_dropdown'])
        time.sleep(1)
        
        # 点击指定的网络
        network_element = self.find_element_safe(f'//span[contains(text(), "{network_name}")]')
        if not network_element:
            print(f"未找到网络: {network_name}")
            return False
            
        network_element.click()
        time.sleep(2)
        
        # 验证网络是否切换成功
        self.driver.refresh()
        time.sleep(3)
        
        # 检查当前网络名称
        network_display = self.find_element_safe(self.SELECTORS['main_page']['network_dropdown'])
        if network_display and network_name in network_display.text:
            return True
            
        return False
        
    def add_token(self, token_address, token_symbol=None, token_decimals=None):
        """
        添加代币
        
        Args:
            token_address (str): 代币合约地址
            token_symbol (str): 代币符号（可选，自动获取）
            token_decimals (str): 代币小数位数（可选，自动获取）
            
        Returns:
            bool: 是否成功添加
        """
        self.open_metamask()
        
        # 确保先解锁
        if self.get_current_page() != 'main_page':
            print("当前不在主页，请先解锁钱包")
            return False
            
        # 点击资产标签
        assets_tab = self.find_element_safe('//button[contains(text(), "资产")]')
        if assets_tab:
            assets_tab.click()
            time.sleep(1)
        
        # 点击导入代币按钮
        import_token_button = self.find_element_safe('//button[contains(text(), "导入代币")]')
        if import_token_button:
            import_token_button.click()
            time.sleep(1)
        else:
            print("未找到导入代币按钮")
            return False
            
        # 点击自定义代币标签
        self.click_element_safe(self.SELECTORS['add_token']['custom_token_tab'])
        time.sleep(1)
        
        # 输入代币地址
        self.input_text(self.SELECTORS['add_token']['token_address'], token_address)
        time.sleep(2)  # 等待自动填充
        
        # 如果提供了符号和小数位，则手动填写
        if token_symbol:
            self.input_text(self.SELECTORS['add_token']['token_symbol'], token_symbol)
            
        if token_decimals:
            self.input_text(self.SELECTORS['add_token']['token_decimals'], token_decimals)
        
        # 点击下一步
        self.click_element_safe(self.SELECTORS['add_token']['next_button'])
        time.sleep(1)
        
        # 点击添加代币按钮
        self.click_element_safe(self.SELECTORS['add_token']['add_tokens_button'])
        time.sleep(3)
        
        # 验证代币是否成功添加
        # 这里可以检查资产列表中是否有该代币
        return True
        
    def confirm_transaction(self, gas_adjustment=None):
        """
        确认交易
        
        Args:
            gas_adjustment (str): gas调整方式: 'low', 'medium', 'high'
            
        Returns:
            bool: 是否成功确认
        """
        # 检查是否在交易确认页面
        if self.get_current_page() != 'confirm_transaction':
            print("当前不在交易确认页面")
            return False
            
        # 如果需要调整gas费用
        if gas_adjustment:
            # 点击编辑gas费用
            self.click_element_safe(self.SELECTORS['confirm_transaction']['gas_fee_link'])
            time.sleep(1)
            
            # 根据参数选择相应的gas设置
            gas_option = None
            if gas_adjustment == 'low':
                gas_option = self.find_element_safe('//button[contains(@data-testid, "low")]')
            elif gas_adjustment == 'medium':
                gas_option = self.find_element_safe('//button[contains(@data-testid, "medium")]')
            elif gas_adjustment == 'high':
                gas_option = self.find_element_safe('//button[contains(@data-testid, "high")]')
                
            if gas_option:
                gas_option.click()
                time.sleep(1)
                
            # 点击保存gas设置
            save_button = self.find_element_safe('//button[contains(text(), "保存")]')
            if save_button:
                save_button.click()
                time.sleep(1)
        
        # 点击确认按钮
        confirm_success = self.click_element_safe(self.SELECTORS['confirm_transaction']['confirm_button'])
        time.sleep(5)  # 等待交易提交
        
        return confirm_success
    
    def reject_transaction(self):
        """
        拒绝交易
        
        Returns:
            bool: 是否成功拒绝
        """
        # 检查是否在交易确认页面
        if self.get_current_page() != 'confirm_transaction':
            print("当前不在交易确认页面")
            return False
            
        # 点击拒绝按钮
        reject_success = self.click_element_safe(self.SELECTORS['confirm_transaction']['reject_button'])
        time.sleep(2)  # 等待交易拒绝
        
        return reject_success
    
    def handle_website_connection_request(self, accept=True):
        """
        处理网站连接请求
        
        Args:
            accept (bool): 是否接受连接请求
            
        Returns:
            bool: 是否成功处理
        """
        # 网站连接请求通常出现在新标签页中
        # 尝试查找所有标签页并检查
        windows = self.driver.window_handles
        current_window = self.driver.current_window_handle
        
        for window in windows:
            if window != current_window:
                self.driver.switch_to.window(window)
                
                # 检查是否是MetaMask连接请求页面
                connect_button = self.find_element_safe('//button[contains(text(), "连接")]')
                if connect_button:
                    if accept:
                        # 接受连接
                        connect_button.click()
                    else:
                        # 拒绝连接
                        reject_button = self.find_element_safe('//button[contains(text(), "取消")]')
                        if reject_button:
                            reject_button.click()
                            
                    time.sleep(2)
                    return True
                    
        # 没有找到连接请求页面，切回原来的窗口
        self.driver.switch_to.window(current_window)
        return False
    
    def close_all_tabs_except_main(self):
        """
        关闭除主窗口外的所有标签页
        
        Returns:
            int: 关闭的标签页数量
        """
        if not self.driver:
            return 0
            
        windows = self.driver.window_handles
        if len(windows) <= 1:
            return 0
            
        # 保存MetaMask主页面窗口
        metamask_window = None
        
        for window in windows:
            self.driver.switch_to.window(window)
            if "chrome-extension://" in self.driver.current_url and self.extension_id in self.driver.current_url:
                metamask_window = window
                break
                
        # 关闭其他窗口
        closed_count = 0
        for window in windows:
            if window != metamask_window:
                self.driver.switch_to.window(window)
                self.driver.close()
                closed_count += 1
                
        # 切回MetaMask主窗口
        if metamask_window:
            self.driver.switch_to.window(metamask_window)
            
        return closed_count
        
    def close_driver(self):
        """
        关闭浏览器驱动
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"关闭驱动时出错: {str(e)}")
            finally:
                self.driver = None

    def take_screenshot(self, file_path=None):
        """
        截取当前页面的屏幕截图
        
        Args:
            file_path (str): 保存截图的文件路径，如果不提供则使用时间戳创建
            
        Returns:
            str: 截图文件的路径
        """
        if not self.driver:
            print("驱动未初始化，无法截图")
            return None
            
        if not file_path:
            file_path = f"metamask_screenshot_{int(time.time())}.png"
            
        try:
            self.driver.save_screenshot(file_path)
            print(f"截图已保存至: {file_path}")
            return file_path
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return None 

# 示例用法
if __name__ == "__main__":
    # 指定MetaMask扩展路径
    extension_path = "path/to/metamask.crx"  # 或者解压后的目录
    
    # 创建交互实例
    metamask = MetaMaskInteraction(extension_path=extension_path)
    
    try:
        # 方式1: 创建新钱包
        password = "your_secure_password"
        seed_phrase = metamask.create_new_wallet(password)
        
        if seed_phrase:
            print(f"创建钱包成功! 助记词: {seed_phrase}")
            print("请务必安全保存助记词!")
            
            # 锁定钱包
            metamask.lock_wallet()
            
            # 解锁钱包
            metamask.unlock_wallet(password)
        
        # 方式2: 导入已有钱包
        # seed_phrase = "your twelve word seed phrase here apple banana coconut ..."
        # import_success = metamask.import_wallet(seed_phrase, password)
        # 
        # if import_success:
        #     print("导入钱包成功!")
        
        # 获取钱包地址
        address = metamask.get_wallet_address()
        print(f"钱包地址: {address}")
        
        # 添加自定义网络(以BSC为例)
        network_added = metamask.add_network(
            name="Binance Smart Chain",
            rpc_url="https://bsc-dataseed.binance.org/",
            chain_id="56",
            symbol="BNB",
            explorer_url="https://bscscan.com"
        )
        
        if network_added:
            print("添加网络成功!")
            
            # 切换到刚添加的网络
            network_switched = metamask.switch_network("Binance Smart Chain")
            if network_switched:
                print("切换网络成功!")
        
        # 添加代币(以USDT为例)
        token_added = metamask.add_token(
            token_address="0x55d398326f99059fF775485246999027B3197955"  # BSC上的USDT
        )
        
        if token_added:
            print("添加代币成功!")
            
        # 等待10秒方便查看
        time.sleep(10)
            
    finally:
        # 确保关闭驱动
        metamask.close_driver() 