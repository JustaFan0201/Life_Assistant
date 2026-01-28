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
    "全票": "", 
    "早鳥": "e1b4c4d9-98d7-4c8c-9834-e1d2528750f1",
    "大學生": "68d9fc7b-7330-44c2-962a-74bc47d2ee8a",
}

def get_thsr_schedule(start_station, end_station, search_date=None, search_time="10:30", ticket_type="全票", trip_type="單程"):
    """
    執行 Selenium 爬蟲並回傳結構化資料 List[Dict]
    """
    
    if not search_date:
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    start_val = STATION_MAP.get(start_station)
    end_val = STATION_MAP.get(end_station)
    
    # 取得優惠代碼
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
    options.add_argument("--window-size=1920,1080") # 解析度調大
    options.page_load_strategy = 'eager'
    
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

            // 設定優惠票種 (使用 jQuery selectpicker)
            if (typeof $ !== 'undefined') {{
                if ('{discount_val}' !== '') {{
                    $('#offer').selectpicker('val', '{discount_val}');
                }} else {{
                    $('#offer').selectpicker('val', []);
                }}
            }}
        """
        driver.execute_script(js_script)

        # 點擊查詢
        search_btn = driver.find_element(By.ID, "start-search")
        driver.execute_script("arguments[0].click();", search_btn)

        # 等待結果載入 (等待第一筆資料出現)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
            # 重要：稍微等待 JS 渲染優惠資訊 (因為是異步載入)
            time.sleep(1.5) 
        except:
            return {"error": "查詢逾時或查無班次"}

        # 抓取資料
        rows = driver.find_elements(By.CSS_SELECTOR, "#ttab-01 .tr-row")
        schedule_data = []

        for row in rows:
            try:
                # 排除空行
                if not row.text.strip(): continue 

                train_id = row.find_element(By.CSS_SELECTOR, ".train").text
                dep_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(1) .font-16r").text
                
                # 過濾舊班次 (只顯示查詢時間之後的)
                if dep_time < search_time: continue

                arr_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(3) .font-16r").text
                duration = row.find_element(By.CSS_SELECTOR, ".traffic-time").text
                
                # ★★★ 關鍵修改：抓取優惠資訊 ★★★
                # 策略 1: 嘗試抓取手機版隱藏欄位 (.xs-ticket-info)，這裡通常有完整文字如 "早鳥價65折起"
                discount_str = ""
                try:
                    xs_info = row.find_element(By.CSS_SELECTOR, ".xs-ticket-info").get_attribute("innerText").strip()
                    if xs_info:
                        # 去除 "適用優惠:" 前綴
                        discount_str = xs_info.replace("適用優惠:", "").strip()
                except: pass

                # 策略 2: 如果手機版沒抓到，抓取桌機版欄位 (.toffer-text)
                if not discount_str:
                    discount_els = row.find_elements(By.CSS_SELECTOR, ".toffer-text")
                    # 過濾空字串
                    discount_list = [el.text.strip() for el in discount_els if el.text.strip()]
                    if discount_list:
                        discount_str = ", ".join(discount_list)
                    else:
                        discount_str = "無優惠" # 真的完全沒字就是原價

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