from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException # 記得引入這個
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime, timedelta

# 修補 PIL
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import ddddocr

BOOKING_STATION_MAP = {
    "南港": "1", "台北": "2", "臺北": "2", "板橋": "3", "桃園": "4", 
    "新竹": "5", "苗栗": "6", "台中": "7", "臺中": "7", "彰化": "8", 
    "雲林": "9", "嘉義": "10", "台南": "11", "臺南": "11", "左營": "12", "高雄": "12"
}

def perform_booking(start_station, end_station, date_str, time_str, ticket_count=1):
    start_val = BOOKING_STATION_MAP.get(start_station)
    end_val = BOOKING_STATION_MAP.get(end_station)

    if not start_val or not end_val:
        return {"status": "error", "msg": "車站名稱錯誤"}

    options = Options()
    # options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    if os.environ.get("GOOGLE_CHROME_BIN"):
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 15)

        driver.get("https://irs.thsrc.com.tw/IMINT/")
        
        # 0. 紀錄首頁網址 (用於比對是否跳轉)
        home_url = driver.current_url

        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "cookieAccpetBtn")))
            cookie_btn.click()
            time.sleep(0.5)
        except:
            pass

        # --- 填寫固定資訊 ---
        Select(driver.find_element(By.ID, "BookingS1Form_selectStartStation")).select_by_value(start_val)
        Select(driver.find_element(By.ID, "BookingS1Form_selectDestinationStation")).select_by_value(end_val)
        driver.execute_script(f"document.getElementById('toTimeInputField').value = '{date_str}';")
        
        try:
            Select(driver.find_element(By.NAME, "toTimeTable")).select_by_visible_text(time_str)
        except:
            Select(driver.find_element(By.NAME, "toTimeTable")).select_by_index(1)

        Select(driver.find_element(By.NAME, "ticketPanel:rows:0:ticketAmount")).select_by_value(f"{ticket_count}F")

        # --- 初始化 OCR ---
        try:
            ocr = ddddocr.DdddOcr(show_ad=False)
        except TypeError:
            ocr = ddddocr.DdddOcr()

        # ==========================================
        # ★★★ 重試迴圈 (邏輯優化版) ★★★
        # ==========================================
        max_retries = 5
        
        for attempt in range(1, max_retries + 1):
            print(f"\n🔄 第 {attempt} 次嘗試驗證碼...")
            
            try:
                captcha_img = wait.until(EC.visibility_of_element_located((By.ID, "BookingS1Form_homeCaptcha_passCode")))
                security_code_input = driver.find_element(By.ID, "securityCode")
                submit_btn = driver.find_element(By.ID, "SubmitButton")

                # 截圖並辨識
                captcha_content = captcha_img.screenshot_as_png
                res = ocr.classification(captcha_content)
                print(f"🤖 OCR 結果: {res}")

                if not res or len(res) != 4:
                    print("⚠️ 驗證碼長度不對，直接刷新...")
                    raise ValueError("Captcha invalid")

                security_code_input.clear()
                security_code_input.send_keys(res)
                submit_btn.click()

                # 等待結果
                time.sleep(2.5) 

                # ★★★ 關鍵修改：更寬鬆的成功判斷 ★★★
                current_url = driver.current_url
                
                # 檢查是否還在首頁 (檢查是否存在 SubmitButton)
                # 如果 SubmitButton 找不到，代表已經跳頁了 (成功)
                is_submit_btn_present = len(driver.find_elements(By.ID, "SubmitButton")) > 0

                # 判斷成功的三個條件：
                # 1. 網址包含 TrainSelection
                # 2. 網址變成了 wicket 介面連結，且找不到 Submit 按鈕 (代表已跳轉)
                # 3. 網址跟原本的首頁網址完全不同
                if "TrainSelection" in current_url or (not is_submit_btn_present and current_url != home_url):
                    return {
                        "status": "success", 
                        "msg": f"✅ 訂票成功！已進入車次選擇頁面 (嘗試次數: {attempt})", 
                        "ocr_code": res,
                        "url": current_url
                    }

                # --- 失敗處理 ---
                # 檢查錯誤訊息
                err_msg = ""
                try:
                    err_elem = driver.find_element(By.XPATH, "//div[@id='feedMSG']//span[@class='error']")
                    if err_elem.is_displayed():
                        err_msg = err_elem.text
                except:
                    pass 

                if err_msg:
                    print(f"❌ 收到錯誤: {err_msg}")
                    if "檢測碼" in err_msg or "驗證碼" in err_msg:
                        raise ValueError("Captcha Wrong") # 觸發重試
                    else:
                        return {"status": "failed", "msg": f"訂票失敗: {err_msg}", "ocr_code": res}
                
                # 沒跳轉也沒報錯，可能是 Unknown State
                print("⚠️ 頁面無反應，嘗試刷新驗證碼...")
                raise ValueError("Unknown State")

            except Exception as e:
                print(f"⚠️ 需要重試: {str(e)[:50]}...")
                
                if attempt < max_retries:
                    try:
                        # ★★★ 二次確認：如果其實已經跳轉了，就不要按刷新 ★★★
                        if len(driver.find_elements(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")) == 0:
                             return {
                                 "status": "success", 
                                 "msg": "✅ 檢測到頁面已跳轉 (無刷新按鈕)", 
                                 "ocr_code": res,
                                 "url": driver.current_url
                             }

                        print("🔄 正在刷新驗證碼圖片...")
                        refresh_btn = driver.find_element(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")
                        refresh_btn.click()
                        time.sleep(2)
                    except Exception as refresh_err:
                        print(f"❌ 無法點擊刷新: {refresh_err}")
                        break
                else:
                    return {"status": "failed", "msg": "已達最大重試次數"}

        return {"status": "failed", "msg": "重試次數耗盡"}

    except Exception as e:
        return {"status": "error", "msg": f"系統錯誤: {str(e)}"}
    
    '''finally:
        if driver:
            driver.quit()'''

if __name__ == "__main__":
    test_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
    print(f"🚀 開始測試訂票... 日期: {test_date}")
    result = perform_booking("台北", "左營", test_date, "10:00")
    print(result)