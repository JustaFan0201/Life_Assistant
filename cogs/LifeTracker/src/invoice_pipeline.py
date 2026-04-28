import asyncio
import traceback
from cogs.LifeTracker.utils.EInvoice_Manager import EInvoice_Manager
from cogs.LifeTracker.src.invoice_crawler import InvoiceCrawler
from cogs.LifeTracker.src.invoice_processor import InvoiceProcessor

class InvoicePipeline:
    @staticmethod
    def _run_crawler_sync(phone: str, password: str) -> tuple[bool, str]:
        """
        這是一支阻塞型的同步函數，負責控制 Selenium。
        它將被放在背景執行緒中運行，以免卡死 Discord Bot。
        """
        crawler = None
        try:
            crawler = InvoiceCrawler()
            if not crawler.login(phone, password):
                crawler.driver.quit()
                return False, "載具登入失敗，請確認帳號密碼是否正確。"
            
            # 登入成功後，跳轉到查詢頁面
            QUERY_PAGE_URL = "https://www.einvoice.nat.gov.tw/portal/btc/mobile/btc502w/detail"
            crawler.driver.get(QUERY_PAGE_URL)
            import time; time.sleep(3) 
            
            # 執行下載
            success = crawler.download_csv()
            crawler.driver.quit()
            
            if success:
                return True, "CSV 下載成功"
            else:
                return False, "CSV 下載流程失敗"
                
        except Exception as e:
            if crawler and crawler.driver:
                crawler.driver.quit()
            print("[InvoicePipeline 爬蟲錯誤]")
            traceback.print_exc()
            return False, f"爬蟲發生未預期錯誤: {e}"

    @staticmethod
    async def execute(user_id: int) -> tuple[bool, str]:
        """給按鈕或排程呼叫的非同步主入口"""
        # 1. 取得使用者設定
        config = EInvoice_Manager.get_config(user_id)
        if not config:
            return False, "找不到發票載具設定，請先綁定帳號。"

        # 2. 將爬蟲丟入背景執行緒執行 (不阻塞 Event Loop)
        success, msg = await asyncio.to_thread(
            InvoicePipeline._run_crawler_sync, 
            config['phone_number'], 
            config['password']
        )
        
        if not success:
            return False, msg

        # 3. 呼叫 Processor 進行 AI 分類與資料庫寫入
        try:
            processor = InvoiceProcessor(user_id=user_id)
            await processor.process()
            return True, "昨日發票抓取與 AI 分類已全數完成！"
        except Exception as e:
            print("[InvoicePipeline 處理器錯誤]")
            traceback.print_exc()
            return False, "CSV 處理與 AI 分類時發生錯誤。"