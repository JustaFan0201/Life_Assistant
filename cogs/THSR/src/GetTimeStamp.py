# cogs/THSR/src/GetTimeStamp.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
from datetime import datetime, timedelta
import os

# ... (保留原本的 STATION_MAP 和 DISCOUNT_MAP) ...
# 車站代碼表
STATION_MAP = {
    "南港": "NanGang", "台北": "TaiPei", "板橋": "BanQiao", "桃園": "TaoYuan",
    "新竹": "XinZhu", "苗栗": "MiaoLi", "台中": "TaiZhong", "彰化": "ZhangHua",
    "雲林": "YunLin", "嘉義": "JiaYi", "台南": "TaiNan", "左營": "ZuoYing"
}

# 票種優惠代碼表
DISCOUNT_MAP = {
    "全票": "", 
    "早鳥": "e1b4c4d9-98d7-4c8c-9834-e1d2528750f1",
    "大學生": "68d9fc7b-7330-44c2-962a-74bc47d2ee8a",
}

def get_thsr_schedule(start_station, end_station, search_date=None, search_time="10:30", ticket_type="全票", trip_type="單程"):
    """
    執行 Selenium 爬蟲並回傳結構化資料 List[Dict]
    回傳的字典中包含 'driver'，以便後續翻頁使用
    """
    
    if not search_date:
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    start_val = STATION_MAP.get(start_station)
    end_val = STATION_MAP.get(end_station)
    discount_val = DISCOUNT_MAP.get(ticket_type, "")
    trip_val = 'tot-2' if trip_type == "來回" else 'tot-1'

    if not start_val or not end_val:
        return {"error": "找不到指定的車站名稱"}

    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.page_load_strategy = 'eager'
    
    if os.environ.get("GOOGLE_CHROME_BIN"):
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        driver.get("https://www.thsrc.com.tw/ArticleContent/a3b630bb-1066-4352-a1ef-58c7b4e8ef7c")
        
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "swal2-confirm")))
            cookie_btn.click()
            time.sleep(0.5)
        except: pass

        # 注入 JS 設定參數
        js_script = f"""
            var s = document.getElementById('select_location01');
            if(s) {{ s.value = '{start_val}'; s.dispatchEvent(new Event('change')); }}
            var e = document.getElementById('select_location02');
            if(e) {{ e.value = '{end_val}'; e.dispatchEvent(new Event('change')); }}
            var t = document.getElementById('typesofticket');
            if(t) {{ t.value = '{trip_val}'; t.dispatchEvent(new Event('change')); }}
            var d = document.getElementById('Departdate03');
            if(d) {{ d.value = '{search_date}'; d.dispatchEvent(new Event('change')); }}
            var ot = document.getElementById('outWardTime');
            if(ot) {{ ot.value = '{search_time}'; ot.dispatchEvent(new Event('change')); }}
            if (typeof $ !== 'undefined') {{
                if ('{discount_val}' !== '') {{
                    $('#offer').selectpicker('val', '{discount_val}');
                }} else {{
                    $('#offer').selectpicker('val', []);
                }}
            }}
        """
        driver.execute_script(js_script)

        search_btn = driver.find_element(By.ID, "start-search")
        driver.execute_script("arguments[0].click();", search_btn)

        # 等待結果載入
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
            time.sleep(1.5) 
        except:
            driver.quit()
            return {"error": "查詢逾時或查無班次"}

        # 解析資料
        schedule_data = _parse_schedule_table(driver)

        return {
            "status": "success",
            "start": start_station,
            "end": end_station,
            "date": search_date,
            "data": schedule_data,
            "driver": driver # ★★★ 關鍵：回傳 driver
        }

    except Exception as e:
        if driver: driver.quit()
        return {"error": str(e)}

def load_more_schedule(driver, direction="later"):
    """
    [新增] 一般查詢的翻頁功能
    """
    wait = WebDriverWait(driver, 10)
    
    # 根據 HTML 結構，我們用 CSS Selector 來抓按鈕
    # 較早班次: 包含 "較早" 文字的按鈕
    # 較晚班次: 包含 "較晚" 文字的按鈕
    
    try:
        print(f"🔄 正在載入{direction}班次...")
        
        # 1. 尋找按鈕 (使用 XPath 根據文字內容找)
        xpath = ""
        if direction == "earlier":
            xpath = "//a[contains(@name, 'changePage') and contains(., '較早')]"
        else:
            xpath = "//a[contains(@name, 'changePage') and contains(., '較晚')]"
            
        try:
            # 檢查是否存在可見的按鈕
            btn = driver.find_element(By.XPATH, xpath)
            if not btn.is_displayed():
                return {"status": "failed", "msg": "已無更多班次"}
        except NoSuchElementException:
            return {"status": "failed", "msg": "找不到翻頁按鈕"}

        # 2. 抓取舊資料特徵 (用於等待更新)
        old_first_row = None
        try:
            old_first_row = driver.find_element(By.CSS_SELECTOR, "#ttab-01 .tr-row")
        except: pass

        # 3. 點擊按鈕
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        
        # 4. 等待更新
        try:
            if old_first_row:
                wait.until(EC.staleness_of(old_first_row))
            else:
                time.sleep(2) # 保底等待
            
            # 再次確認新資料出現
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
        except TimeoutException:
            pass # 可能載入太快或太慢，嘗試直接解析

        # 5. 解析新資料
        new_data = _parse_schedule_table(driver)
        
        if not new_data:
            return {"status": "failed", "msg": "載入後無資料"}
            
        return {
            "status": "success",
            "data": new_data
        }

    except Exception as e:
        print(f"翻頁錯誤: {e}")
        return {"status": "error", "msg": str(e)}

def _parse_schedule_table(driver):
    """
    [內部函式] 解析時刻表
    """
    rows = driver.find_elements(By.CSS_SELECTOR, "#ttab-01 .tr-row")
    data = []
    
    # 找出當前選擇的日期 (用來過濾過期班次)
    # 這裡簡化處理，因為翻頁後可能跨日，我們主要依賴網頁顯示的順序
    
    for row in rows:
        try:
            if not row.text.strip(): continue 

            train_id = row.find_element(By.CSS_SELECTOR, ".train").text
            dep_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(1) .font-16r").text
            arr_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(3) .font-16r").text
            duration = row.find_element(By.CSS_SELECTOR, ".traffic-time").text
            
            discount_str = ""
            try:
                xs_info = row.find_element(By.CSS_SELECTOR, ".xs-ticket-info").get_attribute("innerText").strip()
                if xs_info:
                    discount_str = xs_info.replace("適用優惠:", "").strip()
            except: pass

            if not discount_str:
                discount_els = row.find_elements(By.CSS_SELECTOR, ".toffer-text")
                discount_list = [el.text.strip() for el in discount_els if el.text.strip()]
                if discount_list:
                    discount_str = ", ".join(discount_list)
                else:
                    discount_str = "無優惠"

            data.append({
                "id": train_id,
                "dep": dep_time,
                "arr": arr_time,
                "duration": duration,
                "discount": discount_str
            })
            
            if len(data) >= 10: break
            
        except Exception:
            continue
            
    return data