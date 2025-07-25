# 今日头条最终版评论爬虫 - 基于DOM结构识别回复关系
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FinalCommentCrawler:
    def __init__(self, news_url):
        """初始化爬虫"""
        self.news_url = news_url
        self.driver = None
        self.comments_data = []
        self.comment_id_counter = 1
        
    def setup_driver(self):
        """设置浏览器驱动"""
        options = Options()
        # 使用headless模式提高效率
        options.add_argument("--headless")  
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # 禁用CSP警告日志
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--log-level=3")  # 只显示严重错误
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def wait_and_find_comments_button(self):
        """等待并查找评论按钮"""
        print("正在查找评论按钮...")
        
        selectors = [
            "side-drawer-btn",
            "comment-btn", 
            "show-comment",
            "[class*='comment']",
            "[class*='drawer']",
            "button[class*='comment']",
            "div[class*='comment']",
        ]
        
        for selector in selectors:
            try:
                if selector.startswith("["):
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = self.driver.find_elements(By.CLASS_NAME, selector)
                
                for element in elements:
                    text = element.text.lower()
                    if any(keyword in text for keyword in ['评论', 'comment', '查看', '全部']):
                        print(f"找到评论按钮: {element.text}")
                        return element
            except:
                continue
                
        return None
    
    def scroll_and_wait_for_comments(self):
        """滚动页面并等待评论区加载"""
        print("滚动页面并等待评论区加载...")
        
        for i in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"滚动第 {i+1} 次")
            
        time.sleep(5)
    
    def click_show_all_comments(self):
        """点击查看全部评论按钮"""
        try:
            self.scroll_and_wait_for_comments()
            comment_btn = self.wait_and_find_comments_button()
            
            if comment_btn:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", comment_btn)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", comment_btn)
                time.sleep(5)
                print("已点击查看全部评论")
                return True
            else:
                print("未找到评论按钮")
                return False
                
        except Exception as e:
            print(f"点击评论按钮时出错: {e}")
            return False
    
    def load_all_comments(self):
        """加载所有评论，包括回复"""
        print("开始加载所有评论...")
        max_attempts = 50
        attempts = 0
        no_new_comments_count = 0
        
        while attempts < max_attempts and no_new_comments_count < 3:
            try:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 查找并点击所有"查看更多回复"按钮
                reply_buttons = self.driver.find_elements(By.CLASS_NAME, "check-more-reply")
                clicked_any = False
                
                for button in reply_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(2)
                            print(f"点击了查看更多回复按钮: {button.text}")
                            clicked_any = True
                    except:
                        continue
                
                # 查找并点击"更多"或"加载更多"按钮
                more_selectors = ["[class*='more']", "[class*='load']"]
                for selector in more_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                text = button.text.lower()
                                if any(keyword in text for keyword in ['更多', 'more', '加载', 'load']):
                                    self.driver.execute_script("arguments[0].click();", button)
                                    time.sleep(2)
                                    print(f"点击了加载更多按钮: {button.text}")
                                    clicked_any = True
                    except:
                        continue
                
                if not clicked_any:
                    no_new_comments_count += 1
                    print(f"没有找到更多按钮 ({no_new_comments_count}/3)")
                else:
                    no_new_comments_count = 0
                    
                attempts += 1
                
            except Exception as e:
                print(f"加载更多评论时出错: {e}")
                break
                
        print(f"完成评论加载，共尝试 {attempts} 次")
    
    def extract_all_comments_with_hierarchy(self):
        """提取所有评论，基于DOM结构识别层级关系"""
        comments = []
        print("开始提取所有评论数据（基于DOM结构识别层级）...")
        
        time.sleep(3)
        
        # 查找所有主评论元素（不在replay-list内的comment-info）
        main_comment_elements = self.driver.find_elements(By.CSS_SELECTOR, ".comment-info:not(.replay-list .comment-info)")
        print(f"找到 {len(main_comment_elements)} 个主评论元素")
        
        for main_comment_elem in main_comment_elements:
            try:
                # 提取主评论
                main_comment_data = self.extract_single_comment(main_comment_elem, is_reply=False)
                if main_comment_data:
                    main_comment_id = main_comment_data['评论ID']
                    comments.append(main_comment_data)
                    
                    # 查找该主评论下的所有回复
                    reply_elements = main_comment_elem.find_elements(By.CSS_SELECTOR, ".replay-list .comment-info")
                    print(f"在主评论 {main_comment_id} 下找到 {len(reply_elements)} 个回复")
                    
                    for reply_elem in reply_elements:
                        try:
                            reply_data = self.extract_single_comment(reply_elem, is_reply=True, parent_id=main_comment_id, parent_username=main_comment_data['用户名'])
                            if reply_data:
                                comments.append(reply_data)
                        except Exception as e:
                            print(f"提取回复时出错: {e}")
                            continue
                            
            except Exception as e:
                print(f"提取主评论时出错: {e}")
                continue
        
        return comments
    
    def extract_single_comment(self, comment_elem, is_reply=False, parent_id=None, parent_username=None):
        """提取单条评论的详细信息"""
        try:
            comment_data = {
                '评论ID': self.comment_id_counter,
                '是否为回复': is_reply,
                '父评论ID': parent_id if is_reply else None,
                '回复对象': parent_username if is_reply else None
            }
            self.comment_id_counter += 1
            
            # 提取用户名
            try:
                username_elem = comment_elem.find_element(By.CLASS_NAME, "name")
                comment_data['用户名'] = username_elem.text.strip()
            except:
                comment_data['用户名'] = f'用户{self.comment_id_counter}'
            
            # 提取评论内容
            try:
                content_elem = comment_elem.find_element(By.CLASS_NAME, "content")
                content = content_elem.text.strip()
                comment_data['评论内容'] = content
            except:
                comment_data['评论内容'] = '无内容'
            
            # 提取点赞数
            try:
                like_elem = comment_elem.find_element(By.CLASS_NAME, "ttp-comment-like")
                like_span = like_elem.find_element(By.TAG_NAME, "span")
                like_text = like_span.text.strip()
                comment_data['点赞数'] = like_text if like_text.isdigit() else '0'
            except:
                comment_data['点赞数'] = '0'
            
            # 提取时间
            try:
                time_elem = comment_elem.find_element(By.CLASS_NAME, "time")
                comment_data['评论时间'] = time_elem.text.strip()
            except:
                comment_data['评论时间'] = '未知时间'
            
            comment_type = "回复" if is_reply else "主评论"
            print(f"提取{comment_type} {comment_data['评论ID']}: {comment_data['用户名']} - {comment_data['评论内容'][:30]}...")
            
            return comment_data
            
        except Exception as e:
            print(f"提取评论详情时出错: {e}")
            return None
    
    def crawl_all_comments(self):
        """爬取所有评论的主函数"""
        print("开始爬取所有评论...")
        print(f"新闻URL: {self.news_url}")
        
        self.setup_driver()
        
        try:
            # 访问新闻页面
            print("正在访问新闻页面...")
            self.driver.get(self.news_url)
            time.sleep(5)
            
            # 获取新闻标题
            try:
                title = self.driver.find_element(By.TAG_NAME, "h1").text
                print(f"新闻标题: {title}")
            except:
                title = "未知标题"
            
            # 点击查看全部评论
            if self.click_show_all_comments():
                # 加载所有评论
                self.load_all_comments()
                
                # 提取所有评论（基于DOM结构）
                comments = self.extract_all_comments_with_hierarchy()
                
                # 为每条评论添加新闻信息
                for comment in comments:
                    comment['新闻标题'] = title
                    comment['新闻链接'] = self.news_url
                    self.comments_data.append(comment)
                
                print(f"成功提取 {len(comments)} 条评论")
            else:
                print("无法加载评论")
                
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_excel(self, filename="final_comments.xlsx"):
        """保存数据到Excel文件"""
        if self.comments_data:
            df = pd.DataFrame(self.comments_data)
            
            # 重新排列列的顺序
            columns_order = [
                '评论ID', '用户名', '评论内容', '是否为回复', 
                '父评论ID', '回复对象', '点赞数', '评论时间', '新闻标题', '新闻链接'
            ]
            
            # 确保所有列都存在
            for col in columns_order:
                if col not in df.columns:
                    df[col] = None
            
            df = df[columns_order]
            df.to_excel(filename, index=False)
            
            print(f"\n数据已保存到 {filename}")
            print(f"共爬取 {len(self.comments_data)} 条评论")
            
            # 统计信息
            main_comments = len([c for c in self.comments_data if not c['是否为回复']])
            reply_comments = len([c for c in self.comments_data if c['是否为回复']])
            
            print(f"其中主评论: {main_comments} 条")
            print(f"回复评论: {reply_comments} 条")
            
        else:
            print("没有数据可保存")
    
    def generate_hierarchy_report(self, filename="hierarchy_report.txt"):
        """生成层级关系报告"""
        if not self.comments_data:
            return
            
        print("正在生成层级关系报告...")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== 评论层级关系报告 ===\n\n")
            
            # 按评论ID排序
            sorted_comments = sorted(self.comments_data, key=lambda x: x['评论ID'])
            
            # 创建主评论到回复的映射
            main_comments = [c for c in sorted_comments if not c['是否为回复']]
            
            for main_comment in main_comments:
                f.write(f"🔹 主评论 [{main_comment['评论ID']}] {main_comment['用户名']}\n")
                f.write(f"   内容: {main_comment['评论内容'][:80]}...\n")
                f.write(f"   点赞: {main_comment['点赞数']} | 时间: {main_comment['评论时间']}\n")
                
                # 找到该主评论的所有回复
                replies = [c for c in sorted_comments if c.get('父评论ID') == main_comment['评论ID']]
                
                if replies:
                    f.write(f"   └── 共有 {len(replies)} 条回复:\n")
                    for reply in replies:
                        f.write(f"       ├─ [{reply['评论ID']}] {reply['用户名']}: {reply['评论内容'][:60]}...\n")
                        f.write(f"          点赞: {reply['点赞数']} | 时间: {reply['评论时间']}\n")
                else:
                    f.write("   └── 暂无回复\n")
                
                f.write("\n" + "="*80 + "\n\n")
        
        print(f"层级关系报告已保存到 {filename}")

def main():
    # 新闻URL
    NEWS_URL = "https://www.toutiao.com/article/7529907917705708084/?channel=&source=search_tab&wid=1753361536453"
    
    # 创建爬虫实例
    crawler = FinalCommentCrawler(NEWS_URL)
    
    # 开始爬取
    crawler.crawl_all_comments()
    
    # 保存数据
    crawler.save_to_excel("final_comments.xlsx")
    
    # 生成层级关系报告
    crawler.generate_hierarchy_report("hierarchy_report.txt")

if __name__ == "__main__":
    main() 