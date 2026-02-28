from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from datetime import datetime, timedelta
import random

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

# [第一階段] 搜尋車次
def search_trains(start_station, end_station, date_str, time_str, ticket_count=1, seat_prefer="None", train_code=None):
    start_val = BOOKING_STATION_MAP.get(start_station)
    end_val = BOOKING_STATION_MAP.get(end_station)

    if not start_val or not end_val:
        return {"status": "error", "msg": "車站名稱錯誤"}

    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    options.page_load_strategy = 'eager'
    
    # ★★★ 關鍵防擋 1：偽裝正常的 User-Agent (避免送出 HeadlessChrome) ★★★
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    
    if os.environ.get("GOOGLE_CHROME_BIN"):
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    driver = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # ★★★ 關鍵防擋 2：抹除 navigator.webdriver 機器人指紋 ★★★
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        wait = WebDriverWait(driver, 15)

        driver.get("https://irs.thsrc.com.tw/IMINT/")
        home_url = driver.current_url

        try:
            wait.until(EC.element_to_be_clickable((By.ID, "cookieAccpetBtn"))).click()
            time.sleep(0.5)
        except: pass

        # --- 1. 填寫基本資訊 ---
        Select(driver.find_element(By.ID, "BookingS1Form_selectStartStation")).select_by_value(start_val)
        Select(driver.find_element(By.ID, "BookingS1Form_selectDestinationStation")).select_by_value(end_val)
        driver.execute_script(f"document.getElementById('toTimeInputField').value = '{date_str}';")
        
        if train_code:
            print(f"🎯 指定車次搜尋: {train_code}")
            try:
                driver.execute_script("document.querySelector('input[data-target=\"search-by-trainNo\"]').click()")
                time.sleep(0.5)
                driver.find_element(By.NAME, "toTrainIDInputField").send_keys(train_code)
            except Exception as e:
                print(f"⚠️ 切換車次模式失敗: {e}")
        else:
            try:
                Select(driver.find_element(By.NAME, "toTimeTable")).select_by_visible_text(time_str)
            except:
                Select(driver.find_element(By.NAME, "toTimeTable")).select_by_index(1)

        Select(driver.find_element(By.NAME, "ticketPanel:rows:0:ticketAmount")).select_by_value(f"{ticket_count}F")

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

        print("🔧 初始化驗證碼辨識模型...")
        try:
            ocr = ddddocr.DdddOcr(beta=True)
        except TypeError:
            try:
                ocr = ddddocr.DdddOcr(show_ad=False)
            except TypeError:
                ocr = ddddocr.DdddOcr()

        attempt = 0 
        while True:
            attempt += 1
            print(f"\n🔄 第 {attempt} 次嘗試驗證碼...")
            
            try:
                captcha_img = wait.until(EC.visibility_of_element_located((By.ID, "BookingS1Form_homeCaptcha_passCode")))
                res = ocr.classification(captcha_img.screenshot_as_png)
                print(f"🤖 OCR 結果: {res}")

                if len(res) != 4: 
                    raise ValueError("Captcha length invalid")

                security_code = driver.find_element(By.ID, "securityCode")
                security_code.clear()
                security_code.send_keys(res)
                
                driver.find_element(By.ID, "SubmitButton").click()

                time.sleep(2.5) 
                
                current_url = driver.current_url
                page_source = driver.page_source
                
                is_submit_gone = len(driver.find_elements(By.ID, "SubmitButton")) == 0
                
                # 【情況 A：直達個資頁面 (Step 3)】
                # 判斷依據：網址包含 BookingS2Form 且出現身分證輸入框 (idNumber)
                if "BookingS2Form" in current_url or "idNumber" in page_source:
                    print("⚡ 搜尋成功，直達個資頁面 (Direct)")
                    return {
                        "status": "success_direct", 
                        "msg": "已鎖定車次，準備填寫個資", 
                        "trains": [], 
                        "driver": driver # ★★★ 這裡不關閉 driver，回傳給後續使用
                    }

                # 【情況 B：進入選車列表 (Step 2)】
                # 判斷依據：網址包含 TrainSelection
                elif "TrainSelection" in current_url or (is_submit_gone and "IMINT" in current_url and "BookingS2Form" not in current_url):
                    print("✅ 驗證通過，正在解析車次列表...")
                    
                    trains_data = _parse_all_trains(driver)
                    
                    if train_code:
                        has_train = any(t['code'] == train_code for t in trains_data)
                        if not has_train:
                             return {"status": "failed", "msg": f"搜尋結果未見車次 {train_code} (可能已額滿)", "driver": driver}

                    if not trains_data:
                         return {"status": "failed", "msg": "查無車次 (可能已額滿或日期錯誤)", "driver": driver}

                    return {
                        "status": "success", 
                        "msg": f"找到 {len(trains_data)} 班列車 (嘗試了 {attempt} 次)", 
                        "trains": trains_data, 
                        "driver": driver # ★★★ 這裡不關閉 driver
                    }

                # 【情況 C：留在首頁 (失敗/驗證碼錯誤)】
                try:
                    err_element = driver.find_elements(By.XPATH, "//div[@id='feedMSG']//span[@class='error']")
                    if err_element:
                        err_text = err_element[0].text
                        if "檢測碼" in err_text or "驗證碼" in err_text:
                            print(f"❌ 驗證碼錯誤 ({err_text})，準備重試...")
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
                    if len(driver.find_elements(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")) > 0:
                        print("🔄 重新整理驗證碼圖片...")
                        refresh_btn = driver.find_element(By.ID, "BookingS1Form_homeCaptcha_reCodeLink")
                        driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1.5)
                    else:
                        check_data = _parse_all_trains(driver)
                        if check_data:
                            return {
                                "status": "success", 
                                "msg": f"已跳轉 (防呆機制觸發)", 
                                "trains": check_data, 
                                "driver": driver
                            }
                        print("❌ 無法重整驗證碼且無資料")
                        break
                
                except Exception as refresh_error:
                    print(f"❌ 無法重整驗證碼，終止程序: {refresh_error}")
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
        print(f"解析車次失敗: {e}")
        return []

def load_new_trains(driver, direction="later"):
    """
    載入更早或更晚的車次 (極速版：移除 sleep，改用 DOM 變動偵測)
    """
    # 一般等待設為 10 秒
    wait = WebDriverWait(driver, 10)
    # 短等待設為 3 秒 (用於偵測變動)
    short_wait = WebDriverWait(driver, 3)
    
    target_class = "btn-load-earlier" if direction == "earlier" else "btn-load-later"

    try:
        print(f"🔄 [AutoBooking] 正在尋找按鈕 (Class: {target_class})...")
        
        # 1. 快速確認上一波遮罩已消失
        try:
            short_wait.until(EC.invisibility_of_element_located((By.ID, "loadingMask")))
        except: pass 

        # 2. 抓取按鈕 (使用迴圈過濾隱藏的按鈕)
        buttons = driver.find_elements(By.CLASS_NAME, target_class)
        target_btn = None
        for btn in buttons:
            if btn.is_displayed():
                target_btn = btn
                break
        
        if not target_btn:
            print(f"⚠️ 找不到可見的 {target_class} 按鈕")
            return {"status": "failed", "msg": "已無該時段的車次"}

        # --- [優化核心 1]：在點擊前，先抓取「舊資料」的特徵 ---
        # 我們抓列表中的第一個元素。當 AJAX 完成後，這個元素會被移除或替換。
        old_element = None
        try:
            old_element = driver.find_element(By.CSS_SELECTOR, ".result-listing .result-item")
        except:
            pass # 如果原本列表是空的(極少見)，就沒東西可以抓

        # 3. 點擊按鈕
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_btn)
        # 這裡不需要 sleep(0.5)，直接點通常沒問題，或是縮短到 0.1
        time.sleep(0.1) 
        
        print(f"🖱️ 執行 JS Click...")
        driver.execute_script("arguments[0].click();", target_btn)
        
        # --- [優化核心 2]：移除 time.sleep(1.5)，改用智慧等待 ---
        print("⏳ 等待資料極速刷新...")
        
        try:
            # 策略 A: 如果有點到「舊元素」，等待它「過期」(從 DOM 消失)
            # 這代表網頁已經開始重繪表格了，這是最快的反應時間
            if old_element:
                short_wait.until(EC.staleness_of(old_element))
            
            # 策略 B: 雙重保險，確認遮罩消失
            # 只有在遮罩真的出現時才等，不然直接跳過
            wait.until(EC.invisibility_of_element_located((By.ID, "loadingMask")))
            
            # 策略 C: 確認「新元素」出現
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".result-listing .result-item")))

        except TimeoutException:
            # 如果逾時，可能是網頁反應慢，或者其實已經載入好了但我們沒抓到變動
            print("⚠️ DOM 變動偵測逾時 (可能資料已更新或無變化)，嘗試解析...")

        # 4. 解析資料
        new_trains = _parse_all_trains(driver)
        
        if not new_trains:
            return {"status": "failed", "msg": "載入後列表為空"}
            
        print(f"✅ 成功載入 {len(new_trains)} 班車次")
        
        return {
            "status": "success", 
            "msg": f"已載入 {len(new_trains)} 班列車", 
            "trains": new_trains
        }

    except Exception as e:
        print(f"❌ 載入錯誤: {e}")
        return {"status": "error", "msg": str(e)}

def select_train(driver, train_code):
    """
    [單次執行模式] 鎖定特定車次 (train_code)。
    只嘗試一次：如果該車次存在 -> 嘗試購買；如果消失/額滿 -> 立刻回傳失敗，交由 task.py 重啟。
    """
    print(f"🎯 [單次搶票] 正在鎖定車次: {train_code}...")
    
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
        if not target_radio:
            print(f"⏳ 車次 {train_code} 目前無座位/未顯示。")
            return {"status": "failed", "msg": f"車次 {train_code} 目前無座位或未開放", "driver": driver}
            
        print(f"✨ 發現車次 {train_code}！嘗試點擊訂票...")
        
        # 2-1. 點擊選擇
        driver.execute_script("arguments[0].click();", target_radio)
        time.sleep(0.5)

        # 2-2. 點擊送出 (Submit)
        submit_btn = driver.find_element(By.NAME, "SubmitButton")
        driver.execute_script("arguments[0].click();", submit_btn)

        # --- 步驟 3: 檢查結果 (是否成功跳轉到下一頁) ---
        time.sleep(1.5) # 給網頁一點時間反應
        
        try:
            # 檢查是否有「該車次已額滿」的警告視窗
            alert = driver.switch_to.alert
            err_msg = alert.text
            print(f"⚠️ 訂票失敗，高鐵回傳訊息: {err_msg}")
            alert.accept() # 關閉警告視窗
            return {"status": "failed", "msg": f"無法訂票: {err_msg}", "driver": driver}
            
        except NoAlertPresentException:
            # 沒有 Alert，檢查網址或元素看是否跳轉成功到個資頁面
            if "BookingS2Form" in driver.current_url or "idNumber" in driver.page_source or "btn-custom4" in driver.page_source:
                return {"status": "success", "msg": "搶票成功！已跳轉至個資頁面", "driver": driver}
            else:
                return {"status": "failed", "msg": "送出後未成功跳轉至個資頁面", "driver": driver}

    except Exception as e:
        print(f"❌ 選擇車次時發生錯誤: {e}")
        return {"status": "error", "msg": f"選車程序崩潰: {e}", "driver": driver}

def submit_passenger_info(driver, personal_id, phone="", email="", tgo_id=None, tgo_same_as_pid=False):
    """
    [Step 3] 填寫乘客資訊並送出訂單 (支援早鳥實名制)
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

        # 2. 填寫取票人身分證字號 (必填)
        print("✍️ 正在填寫取票人身分證...")
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
                print("🦅 偵測到早鳥實名制欄位，正在填寫乘客身分證...")
                real_name_input.click()
                real_name_input.clear()
                # 這裡假設乘客就是取票人，填入相同的身分證
                real_name_input.send_keys(personal_id)
                time.sleep(0.5)
        except:
            # 找不到代表這張票不需要實名制，直接忽略
            print("ℹ️ 無需填寫早鳥實名資料")

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
        # ★★★ 8. 處理重複確認視窗 (早鳥/TGo) ★★★
        # ==========================================
        
        print("👀 偵測是否有後續確認視窗...")
        time.sleep(1.5) # 給視窗一點時間彈出來

        # 處理一般確認 / 早鳥確認 (都是 btn-custom2)
        try:
            confirm_btn_2 = driver.find_elements(By.ID, "btn-custom2")
            if confirm_btn_2 and confirm_btn_2[0].is_displayed():
                print("✅ 偵測到「再次確認資訊/早鳥確認」視窗，點擊確定...")
                driver.execute_script("arguments[0].click();", confirm_btn_2[0])
                time.sleep(1) 
        except: pass

        # 處理 TGo 提示 (SubmitPassButton)
        try:
            confirm_btn_tgo = driver.find_elements(By.ID, "SubmitPassButton")
            if confirm_btn_tgo and confirm_btn_tgo[0].is_displayed():
                print("✅ 偵測到「TGo 注意事項」視窗，點擊確定...")
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