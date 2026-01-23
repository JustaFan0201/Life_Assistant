from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
import os

# 車站代碼表
STATION_MAP = {
    "南港": "NanGang", "台北": "TaiPei", "板橋": "BanQiao", "桃園": "TaoYuan",
    "新竹": "XinZhu", "苗栗": "MiaoLi", "台中": "TaiZhong", "彰化": "ZhangHua",
    "雲林": "YunLin", "嘉義": "JiaYi", "台南": "TaiNan", "左營": "ZuoYing"
}

# 票種優惠代碼表
DISCOUNT_MAP = {
    "全票": "", # 空值代表不選優惠
    "早鳥": "e1b4c4d9-98d7-4c8c-9834-e1d2528750f1",
    "大學生": "68d9fc7b-7330-44c2-962a-74bc47d2ee8a",
    # "少年": "d380e2a7-dbbd-471c-93b1-4e08a65438aa", # 如有需要可自行擴充
}

def get_thsr_schedule(start_station, end_station, search_date=None, search_time="10:30", ticket_type="全票", trip_type="單程"):
    """
    執行 Selenium 爬蟲並回傳結構化資料 List[Dict]
    :param ticket_type: "全票", "大學生", "早鳥"
    :param trip_type: "單程", "來回"
    """
    
    if not search_date:
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    start_val = STATION_MAP.get(start_station)
    end_val = STATION_MAP.get(end_station)
    
    # 取得優惠代碼 (預設為空字串)
    discount_val = DISCOUNT_MAP.get(ticket_type, "")

    # 取得行程代碼 (單程 tot-1, 來回 tot-2)
    trip_val = 'tot-2' if trip_type == "來回" else 'tot-1'

    if not start_val or not end_val:
        return {"error": "找不到指定的車站名稱"}

    # --- 瀏覽器設定 ---
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=800,600") # 解析度稍微調大，避免 RWD 隱藏元素
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.page_load_strategy = 'eager'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    
    if os.environ.get("GOOGLE_CHROME_BIN"):
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        driver.get("https://www.thsrc.com.tw/ArticleContent/a3b630bb-1066-4352-a1ef-58c7b4e8ef7c")
        
        # 處理 Cookie 同意視窗
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "swal2-confirm")))
            cookie_btn.click()
            time.sleep(0.5)
        except: pass

        # --- 注入 JS 設定參數 ---
        # ★★★ 關鍵修正：針對 #offer 使用 jQuery 的 selectpicker 方法 ★★★
        # 因為原始網頁載入了 jQuery，我們可以直接利用它來操作複雜的下拉選單
        js_script = f"""
            // 1. 設定起訖站
            var s = document.getElementById('select_location01');
            if(s) {{ s.value = '{start_val}'; s.dispatchEvent(new Event('change')); }}
            
            var e = document.getElementById('select_location02');
            if(e) {{ e.value = '{end_val}'; e.dispatchEvent(new Event('change')); }}
            
            // 2. 設定單程/來回
            var t = document.getElementById('typesofticket');
            if(t) {{ t.value = '{trip_val}'; t.dispatchEvent(new Event('change')); }}
            
            // 3. 設定日期時間
            var d = document.getElementById('Departdate03');
            if(d) {{ d.value = '{search_date}'; d.dispatchEvent(new Event('change')); }}
            
            var ot = document.getElementById('outWardTime');
            if(ot) {{ ot.value = '{search_time}'; ot.dispatchEvent(new Event('change')); }}

            // 4. ★ 設定優惠票種 (使用 jQuery selectpicker) ★
            // 如果 discount_val 有值，就選該 UUID，否則清空 (全票)
            if (typeof $ !== 'undefined') {{
                if ('{discount_val}' !== '') {{
                    $('#offer').selectpicker('val', '{discount_val}');
                }} else {{
                    $('#offer').selectpicker('val', []); // 全票時清空選擇
                }}
            }}
        """
        driver.execute_script(js_script)

        # 點擊查詢
        search_btn = driver.find_element(By.ID, "start-search")
        driver.execute_script("arguments[0].click();", search_btn)

        # 等待結果
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
            time.sleep(1.5) # 給予渲染緩衝時間
        except:
            return {"error": "查詢逾時或查無班次"}

        # 抓取資料
        rows = driver.find_elements(By.CSS_SELECTOR, "#ttab-01 .tr-row")
        schedule_data = []

        for row in rows:
            try:
                text = row.text.strip()
                if not text: continue 

                train_id = row.find_element(By.CSS_SELECTOR, ".train").text
                dep_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(1) .font-16r").text
                
                # 過濾舊班次
                if dep_time < search_time: continue

                arr_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(3) .font-16r").text
                duration = row.find_element(By.CSS_SELECTOR, ".traffic-time").text
                
                # 抓取優惠文字
                discount_els = row.find_elements(By.CSS_SELECTOR, ".toffer-text")
                discount_str = ", ".join([el.text.strip() for el in discount_els if el.text.strip()]) or "無優惠"
                
                schedule_data.append({
                    "id": train_id,
                    "dep": dep_time,
                    "arr": arr_time,
                    "duration": duration,
                    "discount": discount_str
                })
                
                if len(schedule_data) >= 10: break
                
            except Exception:
                continue
        
        return {
            "status": "success",
            "start": start_station,
            "end": end_station,
            "date": search_date,
            "data": schedule_data
        }

    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if driver:
            driver.quit()