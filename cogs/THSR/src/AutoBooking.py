from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime, timedelta

# --- 修補 PIL 相容性 ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import ddddocr

# --- 車站代碼設定 ---
BOOKING_STATION_MAP = {
    "南港": "1", "台北": "2", "臺北": "2", "板橋": "3", "桃園": "4", 
    "新竹": "5", "苗栗": "6", "台中": "7", "臺中": "7", "彰化": "8", 
    "雲林": "9", "嘉義": "10", "台南": "11", "臺南": "11", "左營": "12", "高雄": "12"
}

# ==========================================
# [第一階段] 搜尋車次 (含座位偏好)
# ==========================================
def search_trains(start_station, end_station, date_str, time_str, ticket_count=1, seat_prefer="None"):
    """
    執行查詢並回傳車次列表，不自動進入下一步
    :param seat_prefer: "Window"(靠窗), "Aisle"(走道), "None"(無)
    """
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
        home_url = driver.current_url

        # 處理 Cookie
        try:
            wait.until(EC.element_to_be_clickable((By.ID, "cookieAccpetBtn"))).click()
            time.sleep(0.5)
        except: pass

        # --- 1. 填寫基本資訊 ---
        Select(driver.find_element(By.ID, "BookingS1Form_selectStartStation")).select_by_value(start_val)
        Select(driver.find_element(By.ID, "BookingS1Form_selectDestinationStation")).select_by_value(end_val)
        driver.execute_script(f"document.getElementById('toTimeInputField').value = '{date_str}';")
        
        try:
            Select(driver.find_element(By.NAME, "toTimeTable")).select_by_visible_text(time_str)
        except:
            Select(driver.find_element(By.NAME, "toTimeTable")).select_by_index(1)

        Select(driver.find_element(By.NAME, "ticketPanel:rows:0:ticketAmount")).select_by_value(f"{ticket_count}F")

        # --- 2. 選擇座位偏好 (新增功能) ---
        # 高鐵網頁 ID: seatRadio0(無), seatRadio1(靠窗), seatRadio2(走道)
        print(f"💺 正在設定座位偏好: {seat_prefer}")
        try:
            if str(seat_prefer).lower() == "window":
                driver.execute_script("document.getElementById('seatRadio1').click();")
            elif str(seat_prefer).lower() == "aisle":
                driver.execute_script("document.getElementById('seatRadio2').click();")
            else:
                driver.execute_script("document.getElementById('seatRadio0').click();")
        except Exception as e:
            print(f"⚠️ 座位選擇失敗 (可能該時段不開放選位): {e}")

        # --- 3. 驗證碼迴圈 ---
        try:
            ocr = ddddocr.DdddOcr(show_ad=False)
        except:
            ocr = ddddocr.DdddOcr()

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            print(f"\n🔄 第 {attempt} 次嘗試驗證碼...")
            try:
                captcha_img = wait.until(EC.visibility_of_element_located((By.ID, "BookingS1Form_homeCaptcha_passCode")))
                res = ocr.classification(captcha_img.screenshot_as_png)
                print(f"🤖 OCR 結果: {res}")

                if len(res) != 4: raise ValueError("Captcha invalid")

                driver.find_element(By.ID, "securityCode").clear()
                driver.find_element(By.ID, "securityCode").send_keys(res)
                driver.find_element(By.ID, "SubmitButton").click()

                time.sleep(2.5) 
                
                # 判斷是否跳轉到第二階段 (車次列表)
                is_submit_gone = len(driver.find_elements(By.ID, "SubmitButton")) == 0
                if "TrainSelection" in driver.current_url or (is_submit_gone and driver.current_url != home_url):
                    print("✅ 驗證通過，正在解析車次列表...")
                    
                    # ★★★ 呼叫解析函式，抓取所有車次資料 ★★★
                    trains_data = _parse_all_trains(driver)
                    
                    if not trains_data:
                         return {"status": "failed", "msg": "查無車次 (可能已額滿或日期錯誤)", "driver": driver}

                    return {
                        "status": "success", 
                        "msg": f"找到 {len(trains_data)} 班列車", 
                        "trains": trains_data,  # 回傳資料列表，供 Bot 顯示
                        "driver": driver        # 回傳 driver，保持視窗開啟等待選擇
                    }

                # 錯誤處理
                try:
                    err = driver.find_element(By.XPATH, "//div[@id='feedMSG']//span[@class='error']").text
                    if "檢測碼" in err or "驗證碼" in err: raise ValueError("Wrong Captcha")
                    
                    driver.quit() 
                    return {"status": "failed", "msg": f"查詢失敗: {err}"}
                except:
                    raise ValueError("Unknown")

            except Exception:
                if attempt < max_retries:
                    try:
                        # 防呆檢查
                        if len(driver.find_elements(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")) == 0:
                             return {
                                 "status": "success", 
                                 "msg": "已跳轉 (防呆)", 
                                 "trains": _parse_all_trains(driver), 
                                 "driver": driver
                             }
                        driver.find_element(By.ID, "BookingS1Form_homeCaptcha_reCodeLink").click()
                        time.sleep(2)
                    except: break
        
        driver.quit()
        return {"status": "failed", "msg": "驗證碼重試耗盡"}

    except Exception as e:
        if driver: driver.quit()
        return {"status": "error", "msg": str(e)}

def _parse_all_trains(driver):
    """
    [內部函式] 解析頁面上所有車次資訊 (根據你提供的 HTML)
    """
    try:
        wait = WebDriverWait(driver, 10)
        # 等待列表容器載入
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".result-listing")))
        
        # 抓取所有車次項目
        train_elements = driver.find_elements(By.CSS_SELECTOR, "label.result-item")
        trains = []
        
        for el in train_elements:
            try:
                # 從 input 標籤的屬性中抓取最準確的資料
                radio = el.find_element(By.TAG_NAME, "input")
                
                code = radio.get_attribute("QueryCode")          # 車次代碼 (如 657)
                dep_time = radio.get_attribute("QueryDeparture") # 出發時間 (如 15:46)
                arr_time = radio.get_attribute("QueryArrival")   # 抵達時間 (如 17:45)
                duration = radio.get_attribute("QueryEstimatedTime") # 行車時間 (如 1:59)
                
                # 檢查是否有優惠標籤 (例如早鳥)
                discount_info = ""
                try:
                    discount_el = el.find_element(By.CSS_SELECTOR, ".discount p span")
                    discount_info = f"({discount_el.text})"
                except: pass

                trains.append({
                    "code": code,
                    "departure": dep_time,
                    "arrival": arr_time,
                    "duration": duration,
                    "discount": discount_info,
                    "info_str": f"{dep_time} ➜ {arr_time} | 車次 {code} {discount_info}" # 方便顯示用
                })
            except:
                continue
                
        return trains
    except Exception as e:
        print(f"解析車次失敗: {e}")
        return []

# ==========================================
# [第二階段] 選擇特定車次
# ==========================================
def select_train(driver, train_code):
    """
    根據使用者選擇的車次代碼 (train_code) 進行點擊並跳轉
    """
    try:
        wait = WebDriverWait(driver, 10)
        print(f"🎯 正在鎖定車次: {train_code}...")
        
        # 1. 根據車次代碼找到對應的 Radio Button
        # HTML 範例: <input QueryCode="657" ... >
        selector = f"input[QueryCode='{train_code}']"
        try:
            target_radio = driver.find_element(By.CSS_SELECTOR, selector)
        except:
            return {"status": "failed", "msg": f"找不到車次 {train_code}，可能已額滿或過期", "driver": driver}

        # 2. 點擊選擇
        driver.execute_script("arguments[0].click();", target_radio)
        time.sleep(0.5)

        # 3. 點擊送出
        submit_btn = driver.find_element(By.NAME, "SubmitButton")
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # 4. 等待跳轉 (處理彈窗或正常跳轉)
        print("⏳ 正在跳轉至個資頁面...")
        try:
            def find_next_page(d):
                # 情況 A: 出現確認視窗 (btn-custom4)
                if len(d.find_elements(By.ID, "btn-custom4")) > 0: return "modal"
                # 情況 B: 出現身分證輸入框 (idNumber)
                if len(d.find_elements(By.ID, "idNumber")) > 0: return "input"
                return False
            
            wait.until(find_next_page)
            return {"status": "success", "msg": "已選擇車次並跳轉", "driver": driver}
            
        except TimeoutException:
            # 補救措施：檢查網址
            if "wicket:interface=:2" in driver.current_url:
                 return {"status": "success", "msg": "強制判定跳轉成功", "driver": driver}
            raise Exception("跳轉失敗 (Timeout)")

    except Exception as e:
        return {"status": "error", "msg": f"選車失敗: {e}", "driver": driver}

def submit_passenger_info(driver, personal_id, phone="", email="", tgo_id=None, tgo_same_as_pid=False):
    """
    [Step 3] 填寫乘客資訊並送出訂單
    """
    try:
        short_wait = WebDriverWait(driver, 3)
        normal_wait = WebDriverWait(driver, 10)
        
        print("⏳ 進入個資頁面，準備填寫...")

        # 1. 處理一開始的「信用卡優惠/提醒」彈跳視窗
        try:
            modal_btn = short_wait.until(EC.visibility_of_element_located((By.ID, "btn-custom4")))
            print("👀 偵測到提醒視窗，點擊「繼續購票」...")
            modal_btn.click()
            time.sleep(1)
        except:
            print("✅ 無彈跳視窗或已自動關閉")

        # 2. 填寫身分證字號
        print("✍️ 正在填寫身分證...")
        pid_input = normal_wait.until(EC.element_to_be_clickable((By.ID, "idNumber")))
        pid_input.click()
        pid_input.clear()
        pid_input.send_keys(personal_id)
        
        # 3. 填寫手機
        if phone:
            print(f"📱 填寫手機: {phone}")
            p_input = driver.find_element(By.ID, "mobilePhone")
            p_input.clear()
            p_input.send_keys(phone)
            
        # 4. 填寫 Email
        if email:
            print(f"📧 填寫信箱: {email}")
            e_input = driver.find_element(By.ID, "email")
            e_input.clear()
            e_input.send_keys(email)
            
        # 5. 處理 TGo 會員
        if tgo_same_as_pid or tgo_id:
            try:
                tgo_radio = driver.find_element(By.ID, "memberSystemRadio1")
                driver.execute_script("arguments[0].click();", tgo_radio)
                time.sleep(0.5) 

                if tgo_same_as_pid:
                    print("💎 勾選 TGo 會員 (同身分證)")
                    same_id_checkbox = driver.find_element(By.ID, "memberShipCheckBox")
                    if not same_id_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", same_id_checkbox)
                else:
                    print(f"💎 輸入 TGo 會員帳號: {tgo_id}")
                    same_id_checkbox = driver.find_element(By.ID, "memberShipCheckBox")
                    if same_id_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", same_id_checkbox)
                    
                    tgo_input = driver.find_element(By.ID, "msNumber")
                    tgo_input.clear()
                    tgo_input.send_keys(tgo_id)
            except Exception as e:
                print(f"⚠️ TGo 設定失敗: {e}")
        else:
            try:
                non_member_radio = driver.find_element(By.ID, "memberSystemRadio3")
                driver.execute_script("arguments[0].click();", non_member_radio)
            except: pass

        # 6. 勾選同意條款
        try:
            agree_checkbox = driver.find_element(By.NAME, "agree")
            if not agree_checkbox.is_selected():
                driver.execute_script("arguments[0].click();", agree_checkbox)
        except Exception as e:
            print(f"⚠️ 勾選同意條款失敗: {e}")

        # 7. 按下 "完成訂位" (第一次送出)
        print("🚀 準備送出訂單...")
        submit_btn = driver.find_element(By.ID, "isSubmit")
        
        # ⚠️ 正式訂票請取消註解這行：
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # ==========================================
        # ★★★ 8. 處理重複確認視窗 (針對 TGo 會員) ★★★
        # ==========================================
        # 當使用 TGo 時，會跳出 id="step3ConfirmModal"，按鈕是 id="btn-custom2"
        # 當 TGo 資格不符時，會跳出 id="tgoReplyModal"，按鈕是 id="SubmitPassButton"
        
        print("👀 偵測是否有後續確認視窗...")
        time.sleep(1.5) # 給視窗一點時間彈出來

        try:
            # 嘗試尋找並點擊 "btn-custom2" (一般確認資訊視窗)
            confirm_btn_2 = driver.find_elements(By.ID, "btn-custom2")
            if confirm_btn_2 and confirm_btn_2[0].is_displayed():
                print("✅ 偵測到「再次確認資訊」視窗，點擊確定...")
                driver.execute_script("arguments[0].click();", confirm_btn_2[0])
                time.sleep(1) # 等待處理
        except:
            pass

        try:
            # 嘗試尋找並點擊 "SubmitPassButton" (TGo 相關提示視窗)
            confirm_btn_tgo = driver.find_elements(By.ID, "SubmitPassButton")
            if confirm_btn_tgo and confirm_btn_tgo[0].is_displayed():
                print("✅ 偵測到「TGo 注意事項」視窗，點擊確定...")
                driver.execute_script("arguments[0].click();", confirm_btn_tgo[0])
                time.sleep(1)
        except:
            pass

        return {
            "status": "success", 
            "msg": "已填寫個資並完成確認 (流程結束)", 
            "driver": driver
        }

    except Exception as e:
        return {"status": "error", "msg": f"個資填寫失敗: {str(e)}", "driver": driver}
    
def get_booking_result(driver):
    """
    [Step 4] 從完成訂位頁面抓取訂位代號與車票資訊
    """
    try:
        wait = WebDriverWait(driver, 15)
        print("⏳ 正在擷取訂位結果...")
        
        # 1. 等待訂位代號出現 (這是最核心的資訊)
        # HTML: <p class="pnr-code"><span>02915121</span></p>
        pnr_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".pnr-code span")))
        pnr_code = pnr_element.text.strip()
        
        # 2. 抓取付款期限
        try:
            payment_status = driver.find_element(By.CSS_SELECTOR, ".payment-status").text.replace("\n", " ")
        except:
            payment_status = "未付款"

        # 3. 抓取總金額
        try:
            total_price = driver.find_element(By.CSS_SELECTOR, "[id^='setTrainTotalPriceValue']").text
        except:
            total_price = "未知"

        # 4. 抓取車次細節 (可能有多張票，這裡抓第一張當代表)
        train_info = {}
        try:
            train_info["code"] = driver.find_element(By.CSS_SELECTOR, "[id^='setTrainCode']").text
            train_info["dep_time"] = driver.find_element(By.CSS_SELECTOR, "[id^='setTrainDeparture']").text
            train_info["arr_time"] = driver.find_element(By.CSS_SELECTOR, "[id^='setTrainArrival']").text
            train_info["date"] = driver.find_element(By.CSS_SELECTOR, ".ticket-card .date span").text
        except:
            pass

        # 5. 抓取座位資訊 (例如 "5車17E")
        seats = []
        try:
            seat_elements = driver.find_elements(By.CSS_SELECTOR, ".seat-label span")
            for s in seat_elements:
                seats.append(s.text)
        except:
            seats = ["未顯示座位"]

        result_data = {
            "status": "success",
            "pnr": pnr_code, # 訂位代號
            "payment_status": payment_status,
            "price": total_price,
            "train": train_info,
            "seats": seats,
            "driver": driver
        }
        
        print(f"🎉 訂位成功！代號: {pnr_code}")
        return result_data

    except Exception as e:
        # 如果找不到元素，可能是訂票失敗停在錯誤頁面
        return {"status": "error", "msg": f"擷取訂位結果失敗 (可能訂票未完成): {str(e)}", "driver": driver}


if __name__ == "__main__":
    test_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
    print(f"🚀 [Step 1] 搜尋車次 (靠窗)... ({test_date})")
    
    # 1. 搜尋車次 (指定 seat_prefer="Window")
    # 可選值: "Window", "Aisle", "None"
    search_res = search_trains("台北", "左營", test_date, "10:00", seat_prefer="Window")
    
    if search_res["status"] == "success":
        driver = search_res["driver"]
        trains = search_res["trains"]
        
        # 2. 列出車次 (模擬 Bot 介面顯示)
        print(f"\n✅ 查詢成功！共找到 {len(trains)} 班車 (已幫您勾選靠窗)：")
        print("==========================================")
        for i, t in enumerate(trains):
            print(f"[{i+1}] {t['info_str']}")
        print("==========================================")
        
        # 3. 模擬使用者選擇
        # 這裡測試直接選列表中的第一班車
        if len(trains) > 0:
            target_code = trains[0]['code'] 
            # 實際應用時，這裡會由使用者在 Discord 下拉選單中選擇
            
            print(f"\n👉 使用者選擇了: {target_code}")
            
            # 4. 執行選車
            select_res = select_train(driver, target_code)
            
            if select_res["status"] == "success":
                print("✅ 成功跳轉至個資頁面！")
                print("接下來可呼叫 submit_passenger_info 填寫資料。")
            else:
                print(f"❌ 選車失敗: {select_res['msg']}")
        
        input("\n🔴 測試結束，按 Enter 關閉瀏覽器...")
        driver.quit()
    else:
        print(f"❌ 搜尋失敗: {search_res['msg']}")

# --- 測試區塊 (AutoBooking.py 底部) ---
'''if __name__ == "__main__":
    test_date = (datetime.now() + timedelta(days=8)).strftime("%Y/%m/%d")
    print(f"🚀 [Step 1] 開始全流程測試... ({test_date})")
    
    result = search_trains("台北", "左營", test_date, "16:00",seat_prefer="Window")
    
    if result["status"] == "success":
        driver = result["driver"]
        
        print("\n🚀 [Step 3] 進入個資填寫階段...")
        
        # 設定測試資料
        TEST_ID = "D123309733" 
        # TEST_PHONE = "0912345678" # 假設這次不填手機
        TEST_EMAIL = "test@example.com"
        
        res_step3 = submit_passenger_info(driver, personal_id=TEST_ID, email=TEST_EMAIL, tgo_same_as_pid=True)
        
        if res_step3["status"] == "success":
            print("\n🚀 [Step 4] 擷取訂位結果...")
            
            # Step 3: 抓取訂位代號
            final_result = get_booking_result(driver)
            
            if final_result["status"] == "success":
                print("\n==============================")
                print(f"🎫 訂位代號: {final_result['pnr']}")
                print(f"💰 總金額: {final_result['price']}")
                print(f"📅 日期: {final_result['train'].get('date')}")
                print(f"🚄 車次: {final_result['train'].get('code')}")
                print(f"💺 座位: {', '.join(final_result['seats'])}")
                print(f"⚠️ 狀態: {final_result['payment_status']}")
                print("==============================")
            else:
                print(f"❌ 擷取失敗: {final_result['msg']}")
        
        input("\n🔴 測試結束，按 Enter 關閉瀏覽器...")
        driver.quit()
    else:
        print(f"❌ 前置步驟失敗: {result['msg']}")'''