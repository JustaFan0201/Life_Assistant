from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import prettytable as pt
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
    執行 Selenium 爬蟲並回傳格式化後的表格字串
    """
    
    # 若無指定日期，預設明天
    if not search_date:
        search_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")

    start_val = STATION_MAP.get(start_station)
    end_val = STATION_MAP.get(end_station)

    if not start_val or not end_val:
        return "❌ 錯誤：找不到指定的車站名稱，請確認輸入。"

    # --- 瀏覽器設定 ---
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 【優化 1】調小視窗大小 (不用畫那麼多像素，省 CPU)
    options.add_argument("--window-size=1280,720") 
    
    # 【優化 2】禁止載入圖片 (最有效的加速！省流量也省時間)
    options.add_argument("--blink-settings=imagesEnabled=false")
    
    # 【優化 3】設定網頁載入策略 (重要)
    # 'normal': 等所有資源(含圖片、廣告)載入才開始 (預設，最慢)
    # 'eager': HTML 解析完就開始，不藉圖片 (推薦)
    options.page_load_strategy = 'eager'
    if os.environ.get("GOOGLE_CHROME_BIN"):
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    # 使用 webdriver_manager 自動下載對應版本的 driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    result_text = ""

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)

        # 進入特定頁面
        driver.get("https://www.thsrc.com.tw/ArticleContent/a3b630bb-1066-4352-a1ef-58c7b4e8ef7c")

        # 關閉 Cookie 視窗
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "swal2-confirm")))
            cookie_btn.click()
            time.sleep(0.5)
        except: pass

        # --- 注入 JS 設定參數 ---
        def set_val(dom_id, val):
            if val is None: return
            script = f"""
                var el = document.getElementById('{dom_id}');
                if(el){{
                    el.value = '{val}';
                    el.dispatchEvent(new Event('change'));
                    el.dispatchEvent(new Event('blur')); 
                }}
            """
            driver.execute_script(script)
            time.sleep(0.1)

        set_val("select_location01", start_val)
        set_val("select_location02", end_val)
        set_val("typesofticket", 'tot-1') # 預設單程
        set_val("Departdate03", search_date)
        set_val("outWardTime", search_time)

        # 點擊查詢
        search_btn = driver.find_element(By.ID, "start-search")
        driver.execute_script("arguments[0].click();", search_btn)

        # 等待結果
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ttab-01 .tr-row")))
            time.sleep(1.5)
        except:
            return "⚠️ 查詢逾時：找不到班次資料 (可能是日期過遠或無該時段班次)。"

        # 抓取資料
        rows = driver.find_elements(By.CSS_SELECTOR, "#ttab-01 .tr-row")
        output_data = []

        for row in rows:
            try:
                text = row.text.strip()
                if not text: continue 

                train_id = row.find_element(By.CSS_SELECTOR, ".train").text
                dep_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(1) .font-16r").text
                arr_time = row.find_element(By.CSS_SELECTOR, ".tr-td:nth-child(3) .font-16r").text
                duration = row.find_element(By.CSS_SELECTOR, ".traffic-time").text
                
                # 優惠資訊
                discount_els = row.find_elements(By.CSS_SELECTOR, ".toffer-text")
                discounts = [el.text.strip() for el in discount_els if el.text.strip()]
                discount_str = ", ".join(discounts) if discounts else "-"

                # 備註
                all_tds = row.find_elements(By.CSS_SELECTOR, ".tr-td")
                note_str = all_tds[-1].text.strip() if all_tds else ""

                if dep_time >= search_time:
                    output_data.append([train_id, dep_time, arr_time, duration, discount_str, note_str])
                
                if len(output_data) >= 5: break
                
            except Exception:
                continue

        if output_data:
            tb = pt.PrettyTable()
            
            # 設定欄位名稱
            tb.field_names = ['車次', '出發', '抵達', '時長', '優惠', '備註']
            
            # 1. 設定對齊方式 (置中)
            tb.align = "c" 
            
            # 2. 增加內距 (Padding)
            tb.padding_width = 1 
            
            for d in output_data:
                # d 依序是 [車次, 出發, 抵達, 時長, 優惠, 備註]
                
                # 資料清理邏輯：
                # 確保 d[4] 和 d[5] 即使是 None 或 空字串 也能被處理
                raw_discount = d[4] if d[4] else "-"
                raw_note = d[5] if d[5] else "-"
                
                # 視覺優化：如果值是 "-" (代表無資料)，顯示為 " -- " 看起來比較寬
                discount = raw_discount if raw_discount != "-" else " -- "
                note = raw_note if raw_note != "-" else " -- "
                
                tb.add_row([
                    f"{d[0]}",    # 車次
                    f"{d[1]}",    # 出發
                    f"{d[2]}",    # 抵達
                    f"{d[3]}",    # 時長
                    discount,     # 優惠 (已處理)
                    note          # 備註 (已處理)
                ])

            # 4. 加上標題與裝飾
            title_text = f"🚄 **{start_station} ➔ {end_station}**"
            time_text = f"📅 **{search_date}** (查詢 {search_time} 後)"
            
            # 組合最終字串
            result_text = f"{title_text}\n{time_text}\n```\n{tb.get_string()}\n```"
            
    except Exception as e:
        result_text = f"❌ 發生內部錯誤: {str(e)}"
    
    finally:
        if driver:
            driver.quit()
    
    return result_text