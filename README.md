# MetaMask 自动化工具

一个用于自动化操作 MetaMask 钱包的工具，支持批量导入钱包、连接网站、处理交互等操作。

## 功能特点

- 批量创建和导入钱包
- 多线程并行处理
- 自动处理 MetaMask 弹窗和交互
- 支持多种网络切换
- 智能错误处理和日志记录

## 安装和配置

1. 克隆仓库：
```bash
git clone <repository_url>
cd Metamask_Auto
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 确保 extensions 目录下有正确版本的 MetaMask 扩展。

## 网站交互函数使用指南

### 1. 窗口管理函数

#### open_and_switch_to_window
用于打开新标签页或切换窗口
```python
# 打开新URL
last_handle = bot.open_and_switch_to_window(driver, url="https://example.com")

# 切换到指定窗口
bot.open_and_switch_to_window(driver, window_handle=last_handle)
```

### 2. MetaMask 交互函数

#### handle_metamask_popup
处理 MetaMask 弹窗（包括下一步和连接按钮）
```python
# 处理弹窗并自动切回主窗口
main_window = driver.current_window_handle
success = bot.handle_metamask_popup(main_window)

# 仅处理弹窗不切回主窗口
success = bot.handle_metamask_popup()
```

#### handle_metamask_notification
处理 MetaMask 通知（包括连接请求和签名请求）
```python
bot.handle_metamask_notification()
```

#### switch_network
切换网络
```python
bot.switch_network(driver, "BSC Mainnet")
```

### 3. 页面交互辅助函数

#### wait_for_element
等待元素出现并返回
```python
# 等待特定元素出现
element = bot.wait_for_element("//button[contains(text(), '连接钱包')]")

# 自定义超时时间
element = bot.wait_for_element("//div[@class='target']", timeout=15)
```

### 4. 最佳实践

1. 窗口切换规范
```python
# 保存主窗口句柄
main_window = driver.current_window_handle

# 执行可能触发新窗口的操作
some_operation()

# 处理弹窗
bot.handle_metamask_popup(main_window)  # 自动切回主窗口

# 验证操作结果
verify_operation()
```

2. 错误处理规范
```python
try:
    # 执行操作
    result = bot.handle_metamask_popup(main_window)
    if not result:
        logger.error("操作失败")
        return False
except Exception as e:
    logger.error(f"发生错误: {str(e)}")
    return False
```

3. 等待时间处理
```python
# 短暂操作等待
time.sleep(2)

# 页面加载等待
time.sleep(5)

# 使用显式等待
element = bot.wait_for_element(xpath, timeout=10)
```

### 5. 注意事项

1. 始终在操作前保存主窗口句柄
2. 使用 try-except 处理所有可能的异常
3. 合理设置等待时间，避免操作过快
4. 验证每个关键操作的结果
5. 使用日志记录重要信息，但避免记录敏感数据

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 推特：https://x.com/KingSmile88
- 微信：yufeng8138 
- DC社区：https://discord.gg/gTQ3uhxCFs

## 使用方法

1. 首先运行 `gen_address.py` 生成账户：
```bash
python src/gen_address.py
```

2. 然后运行主程序：
```bash
python src/main.py
```

## 注意事项

- 请确保已安装 Chrome 浏览器
- 需要正确配置 MetaMask 扩展
- 建议在运行前备份重要数据 
