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

def get_thsr_schedule(start_station, end_station, search_date=None, search_time="10:30"):
    """
    執行 Selenium 爬蟲並回傳結構化資料 List[Dict]
    """
    
    if not search_date:
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    start_val = STATION_MAP.get(start_station)
    end_val = STATION_MAP.get(end_station)

    if not start_val or not end_val:
        return {"error": "找不到指定的車站名稱"}

    # --- 瀏覽器設定 ---
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=800,600") 
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
        wait = WebDriverWait(driver, 15) # 稍微延長等待上限

        driver.get("https://www.thsrc.com.tw/ArticleContent/a3b630bb-1066-4352-a1ef-58c7b4e8ef7c")
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
            if(t) {{ t.value = 'tot-1'; t.dispatchEvent(new Event('change')); }}
            
            var d = document.getElementById('Departdate03');
            if(d) {{ d.value = '{search_date}'; d.dispatchEvent(new Event('change')); }}
            
            var ot = document.getElementById('outWardTime');
            if(ot) {{ ot.value = '{search_time}'; ot.dispatchEvent(new Event('change')); }}
        """
        driver.execute_script(js_script)

        # 點擊查詢
        search_btn = driver.find_element(By.ID, "start-search")
        driver.execute_script("arguments[0].click();", search_btn)

        # 等待結果
        try:
            # 等待第一列出現
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
            
            # 【關鍵修正】 Render 的 CPU 很慢，0.5秒可能只夠它畫出 4 行
            # 加長到 1.5 秒，確保 DOM 裡的表格渲染完全
            time.sleep(1.5) 
            
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
                
                discount_els = row.find_elements(By.CSS_SELECTOR, ".toffer-text")
                discount_str = ", ".join([el.text.strip() for el in discount_els if el.text.strip()]) or "無優惠"
                
                schedule_data.append({
                    "id": train_id,
                    "dep": dep_time,
                    "arr": arr_time,
                    "duration": duration,
                    "discount": discount_str
                })
                
                # 【關鍵修正】將上限提高到 10，讓 View 有更多資料顯示
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