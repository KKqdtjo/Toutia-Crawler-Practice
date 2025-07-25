# 🕷️ 今日头条评论爬虫 - TouTiao Comment Crawler

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0+-green.svg)](https://selenium-python.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 一个基于Selenium的智能评论爬虫，能够准确识别评论层级关系，突破现代网站动态加载限制

csdn链接：https://blog.csdn.net/2301_80723089/article/details/145677857?fromshare=blogdetail&sharetype=blogdetail&sharerId=145677857&sharerefer=PC&sharesource=2301_80723089&sharefrom=from_link

## 📖 项目简介

本项目是一个专门针对今日头条新闻评论的爬虫工具，解决了现代网站评论数据动态加载的技术难题。通过深度分析DOM结构，实现了准确的评论层级关系识别，为数据分析和研究提供了可靠的数据源。

### ✨ 核心特性

- 🎯 **精准层级识别**：基于DOM结构分析，准确区分主评论和回复评论
- 🔄 **智能内容加载**：自动点击"查看更多"按钮，获取完整评论数据
- 🛡️ **反反爬虫技术**：采用多种策略避免被网站检测和封禁
- 📊 **结构化输出**：生成Excel表格和可视化层级关系报告
- 🔧 **容错机制**：完善的异常处理和文件权限管理
- ⚡ **高效稳定**：智能等待机制，确保数据完整性

## 🚀 快速开始

### 安装ChromeDriver

#### 方法1：自动安装
```bash
pip install webdriver-manager
```

#### 方法2：手动安装
1. 访问 [ChromeDriver官网](https://chromedriver.chromium.org/)
2. 下载对应Chrome版本的驱动
3. 将驱动放入系统PATH或项目目录


## 📁 项目结构

```
TouTiao-Comment-Crawler/
├── final_comment_crawler.py      # 主爬虫程序
├── README.md                      # 项目说明文档
└── output/                        # 输出文件目录
    ├── final_comments.xlsx        # Excel格式评论数据
    └── hierarchy_report.txt       # 层级关系报告
```

## 🔧 核心技术

### 1. 动态内容加载策略

```python
def load_all_comments(self):
    """智能加载所有评论内容"""
    max_attempts = 50
    no_new_comments_count = 0
    
    while attempts < max_attempts and no_new_comments_count < 3:
        # 滚动触发懒加载
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 点击"查看更多回复"按钮
        reply_buttons = self.driver.find_elements(By.CLASS_NAME, "check-more-reply")
        # ... 智能点击逻辑
```

### 2. DOM结构层级识别

```python
def extract_all_comments_with_hierarchy(self):
    """基于DOM结构识别评论层级关系"""
    # 主评论：不在replay-list内的comment-info
    main_comment_elements = self.driver.find_elements(
        By.CSS_SELECTOR, 
        ".comment-info:not(.replay-list .comment-info)"
    )
    
    # 回复评论：在replay-list内的comment-info
    reply_elements = main_comment_elem.find_elements(
        By.CSS_SELECTOR, 
        ".replay-list .comment-info"
    )
```

### 3. 反反爬虫技术

```python
def setup_driver(self):
    """配置反检测浏览器"""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

## 📊 数据输出格式

### Excel表格字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 评论ID | int | 唯一标识符 |
| 用户名 | str | 评论者昵称 |
| 评论内容 | str | 完整评论文字 |
| 是否为回复 | bool | True表示回复评论 |
| 父评论ID | int | 被回复的评论ID |
| 回复对象 | str | 被回复的用户名 |
| 点赞数 | str | 获得的点赞数 |
| 评论时间 | str | 发布时间 |
| 新闻标题 | str | 所属新闻标题 |
| 新闻链接 | str | 新闻原文链接 |

### 层级关系报告示例

```
🔹 主评论 [1] 张三
   内容: 这个新闻很重要，大家要关注...
   点赞: 188 | 时间: 昨天08:52
   └── 共有 4 条回复:
       ├─ [2] 李四: 我同意你的观点
          点赞: 22 | 时间: 昨天10:28
       ├─ [3] 王五: 确实如此
          点赞: 9 | 时间: 昨天14:26
```

## 🛠️ 高级配置

### 自定义参数

```python
class FinalCommentCrawler:
    def __init__(self, news_url, max_comments=100, headless=True):
        self.news_url = news_url
        self.max_comments = max_comments
        self.headless = headless
```

### 代理设置

```python
def setup_proxy(self):
    """配置代理IP"""
    options = Options()
    options.add_argument('--proxy-server=http://proxy_ip:port')
    return webdriver.Chrome(options=options)
```

### 并发爬取

```python
from concurrent.futures import ThreadPoolExecutor

def crawl_multiple_news(news_urls):
    """并发爬取多条新闻"""
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(crawl_single_news, url) for url in news_urls]
        results = [future.result() for future in futures]
    return results
```

## 🔍 技术原理详解

### 为什么普通爬虫获取不到评论？

现代网站大量使用JavaScript动态加载内容：

1. **初始页面**：只包含基础HTML结构
2. **JavaScript执行**：异步请求评论数据
3. **DOM更新**：动态插入评论HTML
4. **用户可见**：完整的评论内容

**解决方案**：使用Selenium模拟真实浏览器，等待JavaScript执行完毕后再抓取数据。

### DOM结构分析

今日头条评论采用嵌套结构：

```html
<div class="comment-info">          <!-- 主评论 -->
    <div class="content">主评论内容</div>
    <div class="replay-list">        <!-- 回复容器 -->
        <div class="comment-info">   <!-- 回复评论 -->
            <div class="content">回复内容</div>
        </div>
    </div>
</div>
```

通过CSS选择器精确识别层级关系，避免了基于文本特征的不可靠判断。

## 📈 性能优化

### 内存管理

```python
def cleanup_resources(self):
    """清理资源"""
    if self.driver:
        self.driver.quit()
    
    # 清理大型数据结构
    self.comments_data.clear()
```

### 速度优化

```python
def optimize_loading(self):
    """优化加载速度"""
    options = Options()
    options.add_argument('--disable-images')      # 禁用图片
    options.add_argument('--disable-javascript')  # 可选：禁用JS
    options.add_argument('--no-sandbox')         # 提高启动速度
```


## 🤝 贡献指南

欢迎提交Issue和Pull Request！


⭐ 如果这个项目对您有帮助，请给个Star支持一下！

**免责声明**：本项目仅供学习和研究使用，请遵守相关法律法规和网站服务条款。使用本工具产生的任何后果由使用者自行承担。
