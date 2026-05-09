# cogs\LifeTracker\src\invoice_crawler.py
import os
import time
import base64
import io
import ddddocr
import PIL.Image
from PIL import Image
from datetime import datetime, timedelta
from config import TW_TZ
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select 
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
class InvoiceCrawler:
    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        self.driver = self._setup_stealth_driver()

    def _setup_stealth_driver(self):
        options = Options()
        # 確保無頭模式開啟
        options.add_argument("--headless=new") 
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 🌟 [新增] 防崩潰終極指令 (解決 GetHandleVerifier 問題)
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.page_load_strategy = 'normal' # 確保網頁完全載入
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        
        download_dir = os.path.abspath(os.path.join(os.getcwd(), "cogs", "LifeTracker", "src", "downloads"))
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        return driver

    def login(self, phone, password):
        """自動登入財政部電子發票平台"""
        target_url = "https://www.einvoice.nat.gov.tw/accounts/login/mw"
        max_retries = 5
        wait = WebDriverWait(self.driver, 10)

        for attempt in range(max_retries):
            try:
                print(f"🔄 開始登入嘗試 ({attempt+1}/{max_retries})...")
                self.driver.get(target_url)
                
                phone_input = wait.until(EC.presence_of_element_located((By.ID, "mobile_phone")))
                phone_input.clear()
                phone_input.send_keys(phone)
                
                pwd_input = self.driver.find_element(By.ID, "password")
                pwd_input.clear()
                pwd_input.send_keys(password)
                
                captcha_img = self.driver.find_element(By.XPATH, "//img[@alt='圖形驗證碼']")
                img_src = captcha_img.get_attribute("src")
                
                base64_data = img_src.split(',')[1]
                raw_img_bytes = base64.b64decode(base64_data)
                
                image = Image.open(io.BytesIO(raw_img_bytes))
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    alpha = image.convert('RGBA').split()[-1]
                    bg = Image.new("RGB", image.size, (255, 255, 255))
                    bg.paste(image, mask=alpha)
                    image = bg
                else:
                    image = image.convert('RGB')
                
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                clean_img_bytes = img_byte_arr.getvalue()
                
                captcha_text = self.ocr.classification(clean_img_bytes)
                print(f"👁️ OCR 辨識出驗證碼: {captcha_text}")
                
                captcha_input = self.driver.find_element(By.ID, "captcha")
                captcha_input.clear()
                captcha_input.send_keys(captcha_text)
                captcha_input.send_keys(Keys.RETURN)
                
                time.sleep(3) 
                
                if len(self.driver.find_elements(By.ID, "mobile_phone")) == 0:
                    print("✅ 登入成功！")
                    return True
                else:
                    print("⚠️ 登入失敗，準備重試...")
                    
            except Exception as e:
                print(f"❌ 錯誤: {e}")
                time.sleep(2)
                
        self.driver.quit()
        return False
    
    def download_csv(self, start_id: str, end_id: str):
        """執行查詢、過濾與下載 CSV 的自動化流程"""
        wait = WebDriverWait(self.driver, 10)
        
        try:
            print(f"📅 準備點擊日曆，區間: {start_id} ~ {end_id}")

            # 🌟 [新增] 給網頁多一點時間載入 Vue 框架，防止 JS 點擊時崩潰
            time.sleep(2) 
            date_input = wait.until(EC.presence_of_element_located((By.ID, "dp-input-searchInvoiceDate")))
            wait.until(EC.element_to_be_clickable((By.ID, "dp-input-searchInvoiceDate")))
            
            # 打開日曆面板
            self.driver.execute_script("arguments[0].click();", date_input)
            time.sleep(1)

            # 找到並點擊起始日
            print(f"🖱️ 點擊設定起始日 ({start_id})...")
            start_element = wait.until(EC.presence_of_element_located((By.ID, start_id)))
            self.driver.execute_script("arguments[0].click();", start_element)
            time.sleep(0.5)
            
            # 找到並點擊結束日
            print(f"🖱️ 點擊設定結束日 ({end_id})...")
            end_element = wait.until(EC.presence_of_element_located((By.ID, end_id)))
            self.driver.execute_script("arguments[0].click();", end_element)
            time.sleep(1)

            # 2. 點擊「查詢」
            print("🔍 點擊查詢按鈕...")
            search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@title='查詢']")))
            self.driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(3) # 等待 API 回傳資料
            
            # 🌟 [新增] 內層 Try-Except，用來應付「查無發票」的狀況
            try:
                # 3. 更改顯示筆數為 100
                print("📄 確認是否有資料並設定顯示筆數為 100 筆...")
                # 使用較短的等待時間 (5秒)，因為如果沒發票，這裡會馬上找不到元件
                short_wait = WebDriverWait(self.driver, 5)
                select_element = short_wait.until(EC.presence_of_element_located((By.ID, "SelectSizes")))
                select = Select(select_element)
                select.select_by_value("100")
                time.sleep(2) 
                
                # 4. 點擊第一頁刷新 (確保同步)
                print("🔄 點擊第一頁刷新...")
                page_one_btn = short_wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='1']")))
                self.driver.execute_script("arguments[0].click();", page_one_btn)
                time.sleep(3) 
                
                # 5. 全選
                print("☑️ 勾選全選...")
                select_all_cb = short_wait.until(EC.presence_of_element_located((By.ID, "invoiceDetailAll")))
                self.driver.execute_script("arguments[0].click();", select_all_cb)
                time.sleep(1)
                
                # 6. 下載 CSV
                print("⬇️ 點擊下載 CSV 檔...")
                download_btn = short_wait.until(
                    lambda d: d.find_element(By.XPATH, "//button[@title='下載CSV檔']") 
                    if not d.find_element(By.XPATH, "//button[@title='下載CSV檔']").get_attribute("disabled") 
                    else False
                )
                self.driver.execute_script("arguments[0].click();", download_btn)
                
                print("🎉 CSV 下載指令已送出！等待檔案下載...")
                time.sleep(5) 
                
            except Exception:
                # 找不到 SelectSizes 或下載按鈕，通常代表畫面顯示「查無資料」
                print("⚠️ 查無資料：該區間沒有發票紀錄，略過下載步驟。")

        except Exception as e:
            print(f"❌ 查詢流程發生錯誤: {e}")
            return False
            
        finally:
            # 🌟 [新增] 無論有沒有發票、甚至發生錯誤，都保證執行安全登出系統
            try:
                print("🚪 任務完成，準備登出系統...")
                logout_btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//a[@title='登出']")))
                self.driver.execute_script("arguments[0].click();", logout_btn)
                time.sleep(2) 
                print("✅ 成功登出，安全下線！")
            except Exception as e:
                print(f"⚠️ 登出時發生異常，可能已經登出或頁面卡住: {e}")
                
        return True

if __name__ == "__main__":
    TEST_PHONE = "" 
    TEST_PWD = ""
    QUERY_PAGE_URL = "https://www.einvoice.nat.gov.tw/portal/btc/mobile/btc502w/detail"
    
    crawler = InvoiceCrawler()
    if crawler.login(TEST_PHONE, TEST_PWD):
        crawler.driver.get(QUERY_PAGE_URL)
        time.sleep(3)
        crawler.download_csv("2024-04-01", "2024-04-07") 
    
    crawler.driver.quit()