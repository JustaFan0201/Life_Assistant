from database.db_utils import upsert_mem
from cogs.LifeTracker.utils import LifeTracker_Manager
import discord
from datetime import datetime
from config import TW_TZ
from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
from cogs.Gmail.utils import EmailDatabaseManager
from cogs.Stock.utils import StockManager
from cogs.Stock.ui.View.StockDashboardView import StockDashboardView
            
            
class ActionHandler:
    def __init__(self, bot):
        self.bot = bot

    async def handle_actions(self, message, processing_msg, actions):
        embed, view, content, attachments = None, None, "", []
        for step in actions:
            pack = await self.execute_action(message, step)
            if not pack:
                content = "在AI分析意圖時，發生不可預期錯誤。"
            else:
                embed, view, content, attachments = pack
        await processing_msg.edit(embed=embed, view=view, content=content, attachments=attachments)
        
    
    async def execute_action(self, message, step):

        action = step.get("action")
        data = step.get("data", {})
        print(f"action = {action}")
        # # ❗1️⃣ 缺資料 → 進 UI flow
        # if missing:
        #     return await self.handle_missing(
        #         message, processing_msg, action, data, missing
        #     )

        # 🟢 2️⃣ 正常執行
        embed, view, content, attachments = None, None, "", []

        if action == "OPEN_SYSTEM_START":
            from cogs.System.ui.View.SystemStartView import SystemStartView
            embed, view = SystemStartView.create_start_ui(self.bot)

        elif action == "OPEN_LIFE_ASSISTANT":
            from cogs.System.ui.View.SystemStartView import MainControlView
            embed, view = MainControlView.create_dashboard_ui(self.bot)
        
        elif action == "OPEN_LIFE_DIARY":
            from cogs.LifeTracker.ui.View import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, message.author.id)
        
        elif action == "CREATE_CATEGORY_EMPTY":
            from cogs.LifeTracker.ui.Button.SetupBtn import SetupBtn
            view = ActionHandler.get_button_view(SetupBtn(self.bot))
            
        elif action == "CREATE_CATEGORY_WITH_DATA":
            # - category_name* (string) #主類別名稱
            # - fields* (list[string]) #數值類別 像是["金額", "次數"]
            # - subcategories (list[string])
            property_names = ["category_name", "fields", "subcategories"]
            category_name, fields, subcategories = (data.get(x) for x in property_names)
            
            cat_name = category_name.strip()
            fields_list = [f.strip() for f in fields if f.strip()]
            if subcategories:
                subcats_list = [s.strip() for s in subcategories if s.strip()]
               
            success, error_msg = LifeTracker_Manager.create_category(
                user_id=message.author.id,
                username=message.author.name,
                cat_name=cat_name,
                fields_list=fields_list,
                subcats_list=subcats_list
            )
            if not success:
                content = error_msg
            else:
                from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
                embed, view = SetupCategoryModal.create_dashboard(self.bot, message.author.id)
            
        elif action == "DELETE_CATEGORY":
            # - category_name #主類別名稱
            name = data.get("category_name").strip()
            if name:
                if LifeTracker_Manager.delete_category(category_name=name):
                    from cogs.LifeTracker.ui.Select.DeleteCategorySelect import DeleteCategorySelect
                    embed, view = DeleteCategorySelect.create_dashboard(self.bot, message.author.id)
                else:
                    cats = LifeTracker_Manager.get_deletable_categories(user_id=message.author.id)
                    if cats:
                        content = f"刪除錯誤 {name} 並不存在或不可刪除\n目前可刪除目錄:\n" + "\n".join([f" - {cat.name}" for cat in cats])
                    else:
                        content = f"刪除錯誤 {name} 並不存在或不可刪除\n目前無刪除目錄"
            else:
                from cogs.LifeTracker.ui.Button.DeleteCategoryBtn import DeleteCategoryBtn
                btn = DeleteCategoryBtn.get_Btn_with_user_id(self.bot, message.author.id)
                embed, view = btn.create_dashboard()

        elif action == "CREATE_ITINERARY_EMPTY":
            from cogs.Itinerary.ui.View.ItineraryAddView import ItineraryAddView
            embed, view = ItineraryAddView.create_ui()
        
        elif action == "CREATE_ITINERARY_WITH_DATA":
            # - description* (str) #行程內容
            # - year* (int)
            # - month* (int)
            # - day* (int)
            # - hour* (int)
            # - minute (int)
            # - is_private (int) #1:私人通知 0:頻道通知
            property_names = ["description", "year", "month", "day", "hour", "minute", "is_private"]
            description, year, month, day, hour, minute, is_private = (data.get(x) for x in property_names)
            if not minute: minute=0
            if is_private is None: is_private=1
            year, month, day, hour = int(year), int(month), int(day), int(hour)
            event_time = datetime(year, month, day, hour, minute, tzinfo=TW_TZ)
            clean_time = event_time.replace(tzinfo=None, second=0, microsecond=0)
            from cogs.Itinerary.utils.calendar_manager import CalendarDatabaseManager
            from cogs.Itinerary.itinerary_cog import Itinerary
            success, report = CalendarDatabaseManager.add_event(
                user_id=message.author.id,
                user_name=message.author.name,
                event_time=clean_time, 
                description=description,
                is_private= (is_private == 1)
            )

            if not success:
                content = report
            else:
                embed, view, file = Itinerary.create_itinerary_dashboard_ui(message.author.id)
                embed.title = "✅ 行程新增成功！"
                embed.color = discord.Color.green()
                attachments = [file]
        
        elif action == "DELETE_ITINERARY":
            from cogs.Itinerary.ui.View.ItineraryDeleteView import ItineraryDeleteView
            embed, view = ItineraryDeleteView.create_ui(message.author.id)
        
        elif action == "VIEW_ITINERARY":
            from cogs.Itinerary.ui.View.ItineraryDashboardView import ItineraryDashboardView
            embed, view, file = ItineraryDashboardView.create_ui(message.author.id)
            attachments = [file]

        elif action == "GMAIL_HOME":
            embed, view = GmailDashboardView.create_ui(message.author.id)
        
        elif action == "CREATE_GMAIL_CATEGORY_EMPTY":
            from cogs.Gmail.ui.Button.AddCategoryBtn import AddCategoryBtn
            view = ActionHandler.get_button_view(AddCategoryBtn(message.author.id))

        elif action == "CREATE_GMAIL_CATEGORY_WITH_DATA":
            # - category_name* (string) #分類名稱
            # - description* (string) #給 AI 的分類判斷提示詞
            category_name = data.get("category_name")
            description = data.get("description")
            from cogs.Gmail.ui.Modal.AddCategoryModal import AddCategoryModal
            success, msg = AddCategoryModal.add_and_check(message.author.id, category_name, description)
            
            if not success:
                content = msg
            else:
                embed, view = GmailDashboardView.create_ui(message.author.id)
                if msg:
                    embed.description = f"🎉 **{msg}**\n\n{embed.description}"
        
        elif action == "DELETE_GMAIL_CATEGORY":
            # - category_name
            category_name = data.get("category_name")
            categories = EmailDatabaseManager.get_user_categories(message.author.id)
            if not categories:
                content = "目前沒有可刪除的GMAIL分類"
            elif category_name:
                success = EmailDatabaseManager.delete_category(category_name=category_name)
                if success:
                    content = f"GMAIL分類({category_name})以成功刪除"
                else:
                    print(categories)
                    content = f"刪除錯誤 {category_name} 並不存在或不可刪除\n目前可刪除目錄:\n" + "\n".join([f' - {cat["name"]}' for cat in categories])
            else:
                from cogs.Gmail.ui.View.DeleteCategoryView import DeleteCategoryView
                embed, view = DeleteCategoryView.create_ui(message.author.id, categories) 
            
        elif action == "SET_GMAIL_ACCOUNT_EMPTY":
            from cogs.Gmail.ui.Button.SetupMailBtn import SetupMailBtn
            view = ActionHandler.get_button_view(SetupMailBtn())

        elif action == "SET_GMAIL_ACCOUNT_WITH_DATA":
            # - gmail_address* (string) #Gmail地址
            # - app_password* (string) #Google 應用程式密碼（16位）
            gmail_address, app_password = data.get("gmail_address"), data.get("app_password")
            from cogs.Gmail.utils import EmailTools
            clean_address = EmailTools()._extract_pure_email(gmail_address)
            report = EmailDatabaseManager.save_user_config(message.author.id, message.author.name, clean_address, app_password)    
            if "❌" in report:
                content = report
            else:
                content = "GMAIL已成功連結"
        
        elif action == "GMAIL_SETUP_GUIDE":
            from cogs.Gmail.ui.View.HelpView import HelpView
            view = HelpView(message.author.id)
            embed = view.generate_embed()

        elif action == "STOCK_MONITOR_HOME":
            embed, view = StockDashboardView.create_dashboard(self.bot, message.author.id)

        elif action == "STOCK_PROFIT_DETAIL":
            stocks = StockManager.get_user_stocks(message.author.id)
            if not stocks:
                content = "⚠️ 你的監控清單目前是空的。"
            else:
                from cogs.Stock.ui.View.StockListView import StockListView
                embed, view = await StockListView.create_ui(self.bot, message.author.id, message.author.name)

        elif action == "ADD_STOCK_MONITOR_EMPTY":
            from cogs.Stock.ui.Button.StockAddBtn import StockAddBtn
            view = ActionHandler.get_button_view(StockAddBtn(self.bot))
            
        elif action == "ADD_STOCK_MONITOR_WITH_DATA":
            # - stock_code* (string) #股票代碼
            # - share_quantity* (int) #持股數量
            # - total_cost* (float) #總投入成本(含手續費)
            # - rise_alert_percent (int) #漲幅預警(%)
            # - fall_alert_percent (int) #跌幅預警(%)
            from cogs.Stock.ui.Modal.StockAddModal import StockAddModal
            error_msg = await StockAddModal.check(
                data.get("stock_code"),
                data.get("share_quantity"),
                data.get("total_cost"),
                data.get("rise_alert_percent"),
                data.get("fall_alert_percent"),
                message.author.id,
                message.author.name
            )
            if error_msg:
                content = error_msg
            else:
                embed, view = StockDashboardView.create_dashboard(self.bot, message.author.id)
                embed.title = "✅ 新增成功！"
                
        elif action == "REMOVE_STOCK_MONITOR":
            # - stock_code (string) #股票代碼
            stock_code = data.get("stock_code")
            stocks = StockManager.get_user_stocks(message.author.id)
            if not stocks:
                content = "您目前沒有監控任何股票，無法執行刪除操作！"
            elif not stock_code:
                from cogs.Stock.ui.View.StockDeleteView import StockDeleteView
                embed, view = StockDeleteView.create_ui(self.bot, message.author.id)
            else:
                from cogs.Stock.ui.Select.StockDeleteSelect import StockDeleteSelect
                embed, view = StockDeleteSelect.create_dashboard(self.bot, message.author.id, stock_code)
            
        elif action == "QUICK_STOCK_QUERY":
            # - stock_code (string) #股票代碼
            stock_code = data.get("stock_code")
            if not stock_code:
                from cogs.Stock.ui.Button.StockQueryBtn import StockQueryBtn
                view = ActionHandler.get_button_view(StockQueryBtn(self.bot))
            else:
                from cogs.Stock.ui.Modal.StockQueryModal import StockQueryModal
                embed, view = await StockQueryModal.create_dashboard(self.bot, message.author.id, stock_code)

        elif action == "CHAT":
            # - message* (string)
            # - memory (string)
            content = data.get("message")
            mem_text = data.get("memory")
            if mem_text:
                upsert_mem(message.author.id, message.author.name, mem_text)

        else:
            print(f"action: {action} 尚未設置")
            return None
        
        return embed, view, content, attachments
    

    @staticmethod
    def get_button_view(button):
        view = discord.ui.View(timeout=60)
        view.add_item(button)
        return view