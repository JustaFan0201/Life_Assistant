import asyncio
import traceback
import os
import glob
from cogs.LifeTracker.utils.EInvoice_Manager import EInvoice_Manager
from cogs.LifeTracker.src.invoice_crawler import InvoiceCrawler
from cogs.LifeTracker.src.invoice_processor import InvoiceProcessor

class InvoicePipeline:
    @staticmethod
    def _run_crawler_sync(phone: str, password: str, start_id: str, end_id: str) -> tuple[bool, str]:
        """阻塞型的同步函數，負責控制 Selenium"""
        
        # 🌟 [新增] 執行前先清空 downloads 資料夾，防止讀到上次崩潰殘留的舊 CSV
        download_dir = os.path.abspath(os.path.join(os.getcwd(), "cogs", "LifeTracker", "src", "downloads"))
        if os.path.exists(download_dir):
            for f in glob.glob(os.path.join(download_dir, "*.csv")):
                try: os.remove(f)
                except: pass

        crawler = None
        try:
            crawler = InvoiceCrawler()
            if not crawler.login(phone, password):
                return False, "載具登入失敗，請確認帳號密碼是否正確。"
            
            # 登入成功後，跳轉到查詢頁面
            QUERY_PAGE_URL = "https://www.einvoice.nat.gov.tw/portal/btc/mobile/btc502w/detail"
            crawler.driver.get(QUERY_PAGE_URL)
            import time; time.sleep(3) 
            
            success = crawler.download_csv(start_id, end_id)
            
            if success:
                return True, "CSV 下載成功"
            else:
                return False, "CSV 下載流程失敗"
                
        except Exception as e:
            print("[InvoicePipeline 爬蟲錯誤]")
            traceback.print_exc()
            return False, f"爬蟲發生未預期錯誤: {e}"
        finally:
            # 🌟 [新增] 使用 finally 保證無論如何都會關閉瀏覽器，釋放記憶體
            if crawler and hasattr(crawler, 'driver') and crawler.driver:
                try: crawler.driver.quit()
                except: pass

    @staticmethod
    async def execute(user_id: int) -> tuple[bool, str]:
        """給按鈕或排程呼叫的非同步主入口"""
        config = EInvoice_Manager.get_config(user_id)
        if not config:
            return False, "找不到發票載具設定，請先綁定帳號。"

        start_id, end_id = EInvoice_Manager.calculate_fetch_date_range(config.get('last_fetch_date'))

        # 🌟 [重要修改] 將 > 改為 >=。如果起點等於終點(代表今天已經抓過了)，就直接跳過！
        if start_id >= end_id:
            print(f"✅ 使用者 {user_id} 的發票資料已是最新，跳過爬蟲抓取。")
            return True, "發票資料已是最新，無需重新抓取！"

        success, msg = await asyncio.to_thread(
            InvoicePipeline._run_crawler_sync, 
            config['phone_number'], 
            config['password'],
            start_id,
            end_id
        )
        
        if not success:
            return False, msg

        try:
            processor = InvoiceProcessor(user_id=user_id)
            await processor.process()
            
            EInvoice_Manager.update_last_fetch_date(user_id, end_id)
            return True, f"區間 {start_id} ~ {end_id} 的發票抓取與 AI 分類已全數完成！"
            
        except Exception as e:
            print("[InvoicePipeline 處理器錯誤]")
            traceback.print_exc()
            return False, "CSV 處理與 AI 分類時發生錯誤。"