from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime, timedelta
import random

# --- 修補 PIL 相容性 ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import ddddocr
if os.getenv("RENDER"):
    Test=False
else:
    Test=True

# --- 車站代碼設定 ---
BOOKING_STATION_MAP = {
    "南港": "1", "台北": "2", "臺北": "2", "板橋": "3", "桃園": "4", 
    "新竹": "5", "苗栗": "6", "台中": "7", "臺中": "7", "彰化": "8", 
    "雲林": "9", "嘉義": "10", "台南": "11", "臺南": "11", "左營": "12", "高雄": "12"
}

# [第一階段] 搜尋車次
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
    options.add_argument("--headless=new") 
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

        # 高鐵網頁 ID: seatRadio0(無), seatRadio1(靠窗), seatRadio2(走道)
        if Test: print(f"💺 正在設定座位偏好: {seat_prefer}")
        try:
            if str(seat_prefer).lower() == "window":
                driver.execute_script("document.getElementById('seatRadio1').click();")
            elif str(seat_prefer).lower() == "aisle":
                driver.execute_script("document.getElementById('seatRadio2').click();")
            else:
                driver.execute_script("document.getElementById('seatRadio0').click();")
        except Exception as e:
            if Test: print(f"⚠️ 座位選擇失敗 (可能該時段不開放選位): {e}")

        try:
            ocr = ddddocr.DdddOcr(show_ad=False)
        except:
            ocr = ddddocr.DdddOcr()

        attempt = 0 
        while True:
            attempt += 1
            if Test: print(f"\n🔄 第 {attempt} 次嘗試驗證碼...")
            
            try:
                # 等待驗證碼圖片出現
                captcha_img = wait.until(EC.visibility_of_element_located((By.ID, "BookingS1Form_homeCaptcha_passCode")))
                
                # 辨識
                res = ocr.classification(captcha_img.screenshot_as_png)
                if Test: print(f"🤖 OCR 結果: {res}")

                # 基本長度檢查，不對就直接觸發重整
                if len(res) != 4: 
                    raise ValueError("Captcha length invalid")

                # 填寫並送出
                security_code = driver.find_element(By.ID, "securityCode")
                security_code.clear()
                security_code.send_keys(res)
                
                driver.find_element(By.ID, "SubmitButton").click()

                time.sleep(2.5) 
                
                # --- 判斷是否成功 (跳轉到第二階段) ---
                # 檢查 SubmitButton 是否消失，或者 URL 是否改變
                is_submit_gone = len(driver.find_elements(By.ID, "SubmitButton")) == 0
                
                if "TrainSelection" in driver.current_url or (is_submit_gone and driver.current_url != "https://irs.thsrc.com.tw/IMINT/"):
                    if Test: print("✅ 驗證通過，正在解析車次列表...")
                    
                    trains_data = _parse_all_trains(driver)
                    
                    if not trains_data:
                         return {"status": "failed", "msg": "查無車次 (可能已額滿或日期錯誤)", "driver": driver}

                    return {
                        "status": "success", 
                        "msg": f"找到 {len(trains_data)} 班列車 (嘗試了 {attempt} 次)", 
                        "trains": trains_data, 
                        "driver": driver 
                    }

                try:
                    err_element = driver.find_elements(By.XPATH, "//div[@id='feedMSG']//span[@class='error']")
                    if err_element:
                        err_text = err_element[0].text
                        if "檢測碼" in err_text or "驗證碼" in err_text:
                            if Test: print(f"❌ 驗證碼錯誤 ({err_text})，準備重試...")
                            raise ValueError("Wrong Captcha")
                        else:
                            driver.quit()
                            return {"status": "failed", "msg": f"查詢失敗: {err_text}"}
                    else:
                        raise ValueError("Unknown status, retrying...")
                except Exception as e:
                    raise ValueError(f"Check failed: {e}")

            except Exception:
                try:
                    if len(driver.find_elements(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")) == 0:
                        check_data = _parse_all_trains(driver)
                        if check_data:
                            return {
                                "status": "success", 
                                "msg": f"已跳轉 (防呆機制觸發)", 
                                "trains": check_data, 
                                "driver": driver
                            }
                    
                    if Test: print("🔄 重新整理驗證碼圖片...")
                    refresh_btn = driver.find_element(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")
                    driver.execute_script("arguments[0].click();", refresh_btn)
                    time.sleep(1.5) # 等待新圖片載入
                
                except Exception as refresh_error:
                    if Test: print(f"❌ 無法重整驗證碼，終止程序: {refresh_error}")
                    break
        
        driver.quit()
        return {"status": "failed", "msg": "驗證流程異常終止"}

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
        if Test: print(f"解析車次失敗: {e}")
        return []


def select_train(driver, train_code):
    """
    [搶票模式] 鎖定特定車次 (train_code)。
    如果該車次存在 -> 嘗試購買。
    如果該車次消失/額滿 -> 重新整理頁面，持續監控直到買到為止。
    """
    wait = WebDriverWait(driver, 10)
    
    # 設定重試間隔 (秒)，太快會被鎖 IP
    REFRESH_INTERVAL = 5  
    
    print(f"🎯 [搶票模式啟動] 正在鎖定車次: {train_code}...")
    start_time = time.time()
    MAX_DURATION = 1800 # 30分鐘

    while True:
        if time.time() - start_time > MAX_DURATION:
             return {"status": "failed", "msg": "搶票超時 (30分鐘)，自動停止", "driver": driver}
        try:
            # --- 步驟 1: 尋找車次按鈕 ---
            selector = f"input[QueryCode='{train_code}']"
            target_radio = None
            
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    target_radio = elements[0]
            except:
                pass

            # --- 步驟 2: 判斷是否找到車次 ---
            if target_radio:
                print(f"✨ 發現車次 {train_code}！嘗試點擊訂票...")
                
                # 2-1. 點擊選擇
                driver.execute_script("arguments[0].click();", target_radio)
                time.sleep(0.5)

                # 2-2. 點擊送出 (Submit)
                submit_btn = driver.find_element(By.NAME, "SubmitButton")
                driver.execute_script("arguments[0].click();", submit_btn)

                # 2-3. 檢查結果 (是否成功跳轉到下一頁)
                try:
                    # 等待一下，看看有沒有 Alert (例如：該車次已額滿)
                    time.sleep(1)
                    try:
                        alert = driver.switch_to.alert
                        err_msg = alert.text
                        print(f"⚠️ 訂票失敗，高鐵回傳訊息: {err_msg}")
                        alert.accept() # 關閉警告視窗
                        # 繼續迴圈 (重新整理再試)
                    except NoAlertPresentException:
                        # 沒有 Alert，檢查網址或元素看是否跳轉成功
                        if "BookingS2Form" not in driver.current_url and ("idNumber" in driver.page_source or "btn-custom4" in driver.page_source):
                            return {"status": "success", "msg": "搶票成功！已跳轉至個資頁面", "driver": driver}
                except Exception as e:
                    print(f"⚠️ 判斷跳轉時發生錯誤: {e}")

            else:
                print(f"⏳ 車次 {train_code} 目前無座位/未顯示，繼續監控中...")

            # --- 步驟 3: 重新整理頁面 (Refresh) ---
            # 隨機延遲，模擬人類行為並避免被鎖
            sleep_time = REFRESH_INTERVAL + random.uniform(0, 2)
            print(f"🔄 {sleep_time:.1f} 秒後重新整理...")
            time.sleep(sleep_time)

            try:
                driver.refresh()
                # 重新整理後，通常會有「確認重新提交表單」的 Alert
                # 我們需要等待並接受它，不然程式會卡住
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert.accept()
                print("✅ 已確認表單重送")
                
                # 等待頁面載入完成 (等待表格出現)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table_simple")))

            except TimeoutException:
                # 沒跳出 Alert 可能只是單純重新整理，或是頁面載入慢，繼續執行
                pass
            except NoAlertPresentException:
                pass

        except Exception as e:
            print(f"❌ 搶票迴圈發生未預期錯誤: {e}")
            # 發生錯誤時不要立刻死掉，休息一下再試 (增加容錯率)
            time.sleep(5)
            try:
                driver.refresh()
            except:
                return {"status": "error", "msg": f"搶票程式崩潰: {e}", "driver": driver}

def submit_passenger_info(driver, personal_id, phone="", email="", tgo_id=None, tgo_same_as_pid=False):
    """
    [Step 3] 填寫乘客資訊並送出訂單 (支援早鳥實名制)
    """
    try:
        short_wait = WebDriverWait(driver, 3)
        normal_wait = WebDriverWait(driver, 10)
        
        if Test: print("⏳ 進入個資頁面，準備填寫...")

        # 1. 處理一開始的「信用卡優惠/提醒」彈跳視窗
        try:
            modal_btn = short_wait.until(EC.visibility_of_element_located((By.ID, "btn-custom4")))
            if Test: print("👀 偵測到提醒視窗，點擊「繼續購票」...")
            modal_btn.click()
            time.sleep(1)
        except:
            if Test: print("✅ 無彈跳視窗或已自動關閉")

        # 2. 填寫取票人身分證字號 (必填)
        if Test: print("✍️ 正在填寫取票人身分證...")
        pid_input = normal_wait.until(EC.element_to_be_clickable((By.ID, "idNumber")))
        pid_input.click()
        pid_input.clear()
        pid_input.send_keys(personal_id)
        
        # ==========================================
        # ★★★ 新增：偵測並填寫早鳥實名制欄位 ★★★
        # ==========================================
        # 早鳥票會多出一個欄位要求輸入「乘客」的身分證
        try:
            # 嘗試尋找 class 包含 passengerDataIdNumber 的輸入框
            # 這裡我們假設只有一位乘客 (ticket_count=1)，所以直接找第一個
            # 如果有多位乘客，這裡需要用 find_elements 並跑迴圈
            
            # 使用 CSS Selector 尋找屬性 name 包含 passengerDataIdNumber 的 input
            real_name_input = driver.find_element(By.CSS_SELECTOR, "input[name*='passengerDataIdNumber']")
            
            if real_name_input.is_displayed():
                if Test: print("🦅 偵測到早鳥實名制欄位，正在填寫乘客身分證...")
                real_name_input.click()
                real_name_input.clear()
                # 這裡假設乘客就是取票人，填入相同的身分證
                real_name_input.send_keys(personal_id)
                time.sleep(0.5)
        except:
            # 找不到代表這張票不需要實名制，直接忽略
            if Test: print("ℹ️ 無需填寫早鳥實名資料")

        # 3. 填寫手機
        if phone:
            if Test: print(f"📱 填寫手機: {phone}")
            p_input = driver.find_element(By.ID, "mobilePhone")
            p_input.clear()
            p_input.send_keys(phone)
            
        # 4. 填寫 Email
        if email:
            if Test: print(f"📧 填寫信箱: {email}")
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
                    if Test: print("💎 勾選 TGo 會員 (同身分證)")
                    same_id_checkbox = driver.find_element(By.ID, "memberShipCheckBox")
                    if not same_id_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", same_id_checkbox)
                else:
                    if Test: print(f"💎 輸入 TGo 會員帳號: {tgo_id}")
                    same_id_checkbox = driver.find_element(By.ID, "memberShipCheckBox")
                    if same_id_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", same_id_checkbox)
                    
                    tgo_input = driver.find_element(By.ID, "msNumber")
                    tgo_input.clear()
                    tgo_input.send_keys(tgo_id)
            except Exception as e:
                if Test: print(f"⚠️ TGo 設定失敗: {e}")
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
            if Test: print(f"⚠️ 勾選同意條款失敗: {e}")

        # 7. 按下 "完成訂位" (第一次送出)
        if Test: print("🚀 準備送出訂單...")
        submit_btn = driver.find_element(By.ID, "isSubmit")
        
        # ⚠️ 正式訂票請取消註解這行：
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # ==========================================
        # ★★★ 8. 處理重複確認視窗 (早鳥/TGo) ★★★
        # ==========================================
        
        if Test: print("👀 偵測是否有後續確認視窗...")
        time.sleep(1.5) # 給視窗一點時間彈出來

        # 處理一般確認 / 早鳥確認 (都是 btn-custom2)
        try:
            confirm_btn_2 = driver.find_elements(By.ID, "btn-custom2")
            if confirm_btn_2 and confirm_btn_2[0].is_displayed():
                if Test: print("✅ 偵測到「再次確認資訊/早鳥確認」視窗，點擊確定...")
                driver.execute_script("arguments[0].click();", confirm_btn_2[0])
                time.sleep(1) 
        except: pass

        # 處理 TGo 提示 (SubmitPassButton)
        try:
            confirm_btn_tgo = driver.find_elements(By.ID, "SubmitPassButton")
            if confirm_btn_tgo and confirm_btn_tgo[0].is_displayed():
                if Test: print("✅ 偵測到「TGo 注意事項」視窗，點擊確定...")
                driver.execute_script("arguments[0].click();", confirm_btn_tgo[0])
                time.sleep(1)
        except: pass

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
        if Test: print("⏳ 正在擷取訂位結果...")
        
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
        
        if Test: print(f"🎉 訂位成功！代號: {pnr_code}")
        return result_data

    except Exception as e:
        # 如果找不到元素，可能是訂票失敗停在錯誤頁面
        return {"status": "error", "msg": f"擷取訂位結果失敗 (可能訂票未完成): {str(e)}", "driver": driver}

