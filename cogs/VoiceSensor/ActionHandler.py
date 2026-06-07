from database.db_utils import upsert_mem, name_to_id
from cogs.LifeTracker.utils import LifeTrackerManager
import discord
from datetime import datetime
from config import TW_TZ
from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
from cogs.Gmail.utils import EmailDatabaseManager
from cogs.Stock.utils import StockManager
from cogs.Stock.ui.View.StockDashboardView import StockDashboardView
import asyncio
from database.models import TrackerCategory, TrackerSubCategory

DEBUG = False
  
class ActionHandler:
    def __init__(self, bot):
        self.bot = bot

    async def enrich_actions_context(self, message, text, result, memory, *, ALL=False):
        if DEBUG:
            self.channel = message.channel
        more_content_parts = []
        needs_parts = {}
        if result:
            actions = result.get("actions", [])
            for step in actions:
                action = step.get("action")
                # Gmail 分類相關
                if action in [
                    "DELETE_GMAIL_CATEGORY",
                    "VIEW_GMAIL_CATEGORY_CONTENT"
                ]:
                    needs_parts["Gmail"] = True
                    
                # LifeTracker 分類相關
                elif action in ["DELETE_CATEGORY"]:
                    needs_parts["LifeTracker_del_cat"] = True

                elif action in [
                    "VIEW_DIARY_CATEGORY",
                    "CREATE_DIARY_RECORD_EMPTY",
                    "CREATE_DIARY_SUBCATEGORY",
                    "MODIFY_DIARY_SUBCATEGORY_EMPTY",
                ]:
                    needs_parts["LifeTracker_cat"] = True
                elif action in [
                    "DELETE_DIARY_SUBCATEGORY",
                    "MODIFY_DIARY_SUBCATEGORY_WITH_DATA"
                ]:
                    needs_parts["LifeTracker_subcat"] = True
                elif action in [
                    "CREATE_DIARY_RECORD_WITH_DATA"
                ]:
                    needs_parts["LifeTracker_subcat_field"] = True
                
                # 股票分類相關
                elif action in [
                    "REMOVE_STOCK_MONITOR"
                ]:
                    needs_parts['Stock'] = True

        if ALL or needs_parts.get("Stock"):
            stocks = StockManager.get_user_stocks(message.author.id)
            stock_details = [f'name:{s.stock_name} code/symbol{s.stock_symbol}:' for s in stocks]
            more_content_parts.append(ActionHandler.list_text_format("目前股票監控", stock_details, indent=1))

        if ALL or needs_parts.get("Gmail"):
            categories = EmailDatabaseManager.get_user_categories(message.author.id)
            names = [c["name"] for c in categories]
            more_content_parts.append(ActionHandler.list_text_format(" Gmail 分類", names))
        
        if ALL or needs_parts.get("LifeTracker_del_cat"):
            cats = LifeTrackerManager.get_deletable_categories(user_id=message.author.id)
            names = [c.name for c in cats]
            more_content_parts.append(ActionHandler.list_text_format("生活日記可刪除主分類", names))
        
        # only trigger one
        if ALL or needs_parts.get("LifeTracker_subcat_field"):
            texts = []
            cats = LifeTrackerManager.get_user_categories(user_id=message.author.id)
            ids = [c.id for c in cats]
            for id in ids:
                cat_info, subcats_info = LifeTrackerManager.get_category_details(id)
                sub_names = [c['name'] for c in subcats_info]
                texts.append(ActionHandler.list_text_format(f" {cat_info['name']} 標籤名稱", sub_names, indent=1))
                texts.append(ActionHandler.list_text_format(f" {cat_info['name']} 數值類別", cat_info['fields'], indent=1))
            more_content_parts.append('\n'.join(texts))
        elif needs_parts.get("LifeTracker_subcat"):
            texts = []
            cats = LifeTrackerManager.get_user_categories(user_id=message.author.id)
            ids = [c.id for c in cats]
            for id in ids:
                cat_info, subcats_info = LifeTrackerManager.get_category_details(id)
                sub_names = [c['name'] for c in subcats_info]
                texts.append(ActionHandler.list_text_format(f" {cat_info['name']} 目前的標籤名稱", sub_names))
            more_content_parts.append('\n'.join(texts))
        elif needs_parts.get("LifeTracker_cat"):
            cats = LifeTrackerManager.get_user_categories(user_id=message.author.id)
            names = [c.name for c in cats]
            more_content_parts.append(ActionHandler.list_text_format("生活日記主分類", names))

        if not more_content_parts:
            return result
        more_content = "\n\n".join(more_content_parts)
        print("===== 額外上下文 =====")
        print(more_content)
        if DEBUG:
            await self.channel.send("===== 額外上下文 =====\n" + more_content + '\n')
            if result:
                import json
                await self.channel.send("原json:\n" + json.dumps(result, ensure_ascii=False) + '\n')

        from cogs.VoiceSensor.utils import AiAnalyzer
        new_result = await AiAnalyzer.parse_ui_action(
            text=text,
            memory=memory,
            more_content=more_content
        )

        return new_result
        
    async def handle_actions(self, message, processing_msg, result):
        if DEBUG:
            import json
            await self.channel.send("json:\n" + json.dumps(result, ensure_ascii=False) + '\n')
        
        actions = result.get("actions", [])
        if not actions:
            return await processing_msg.edit(content="❌ 無法解析操作")

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

        action_handlers = {
            # 1. 系統主選單模組
            "OPEN_SYSTEM_START": self._handle_system_start,
            "OPEN_LIFE_ASSISTANT": self._handle_life_assistant,
            
            # 2. 記帳生活追蹤模組
            "OPEN_LIFE_DIARY": self._handle_life_diary,
            "CREATE_CATEGORY_EMPTY": self._handle_create_category_empty,
            "CREATE_CATEGORY_WITH_DATA": self._handle_create_category_with_data,
            "DELETE_CATEGORY": self._handle_delete_category,
            "VIEW_DIARY_CATEGORY": self._handle_view_diary_category,
            "CREATE_DIARY_RECORD_EMPTY": self._handle_create_diary_record_empty,
            "CREATE_DIARY_RECORD_WITH_DATA": self._handle_create_diary_record_with_data,
            "CREATE_DIARY_SUBCATEGORY": self._handle_create_diary_subcategory,
            "DELETE_DIARY_SUBCATEGORY": self._handle_delete_diary_subcategory,
            "MODIFY_DIARY_SUBCATEGORY_EMPTY": self._handle_modify_diary_subcategory_empty,
            "MODIFY_DIARY_SUBCATEGORY_WITH_DATA": self._handle_modify_diary_subcategory_with_data,
            # 3. 行事曆行程模組
            "CREATE_ITINERARY_EMPTY": self._handle_create_itinerary_empty,
            "CREATE_ITINERARY_WITH_DATA": self._handle_create_itinerary_with_data,
            "DELETE_ITINERARY": self._handle_delete_itinerary,
            "VIEW_ITINERARY": self._handle_view_itinerary,
            
            # 4. Gmail 連結模組
            "GMAIL_HOME": self._handle_gmail_home,
            "CREATE_GMAIL_CATEGORY_EMPTY": self._handle_create_gmail_category_empty,
            "CREATE_GMAIL_CATEGORY_WITH_DATA": self._handle_create_gmail_category_with_data,
            "DELETE_GMAIL_CATEGORY": self._handle_delete_gmail_category,
            "VIEW_GMAIL_CATEGORY": self._handle_view_gmail_category,
            "VIEW_GMAIL_CATEGORY_CONTENT": self._handle_view_gmail_category_content,
            "SET_GMAIL_ACCOUNT_EMPTY": self._handle_set_gmail_account_empty,
            "SET_GMAIL_ACCOUNT_WITH_DATA": self._handle_set_gmail_account_with_data,
            "GMAIL_SETUP_GUIDE": self._handle_gmail_setup_guide,
            
            # 5. 股市監控模組
            "STOCK_MONITOR_HOME": self._handle_stock_monitor_home,
            "STOCK_PROFIT_DETAIL": self._handle_stock_profit_detail,
            "ADD_STOCK_MONITOR_EMPTY": self._handle_add_stock_monitor_empty,
            "ADD_STOCK_MONITOR_WITH_DATA": self._handle_add_stock_monitor_with_data,
            "REMOVE_STOCK_MONITOR": self._handle_remove_stock_monitor,
            "QUICK_STOCK_QUERY": self._handle_quick_stock_query,
            
            # 6. 大模型聊天模組
            "CHAT": self._handle_chat
        }

        handler = action_handlers.get(action)
        
        if handler:
            # 執行對應的獨立處置器並回傳
            return await handler(message, data)
            
        # Default fallback (原本的 else 區塊)
        print(f"action: {action} 尚未設置")
        return None


    # --- 1. 系統控制選單 ---
    async def _handle_system_start(self, message, data):

        await asyncio.sleep(0)
        from cogs.System.ui.View.SystemStartView import SystemStartView
        embed, view = SystemStartView.create_start_ui(self.bot)
        return embed, view, "", []

    async def _handle_life_assistant(self, message, data):

        await asyncio.sleep(0)
        from cogs.System.ui.View.SystemStartView import MainControlView
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        return embed, view, "", []

    # --- 2. 記帳模組 ---
    async def _handle_life_diary(self, message, data):
        await asyncio.sleep(0)
        from cogs.LifeTracker.ui.View import LifeDashboardView
        embed, view = LifeDashboardView.create_dashboard(self.bot, message.author.id)
        return embed, view, "", []

    async def _handle_create_category_empty(self, message, data):
        await asyncio.sleep(0)
        from cogs.LifeTracker.ui.Button.SetupBtn import SetupBtn
        view = ActionHandler.get_button_view(SetupBtn(self.bot))
        return None, view, "", []

    async def _handle_create_category_with_data(self, message, data):
        await asyncio.sleep(0)
        embed, view, content = None, None, ""
        property_names = ["category_name", "fields", "subcategories"]
        category_name, fields, subcategories = (data.get(x) for x in property_names)
        
        cat_name = category_name.strip()
        fields_list = [f.strip() for f in fields if f.strip()]
        subcats_list = [s.strip() for s in subcategories if s.strip()] if subcategories else []
           
        success, error_msg = LifeTrackerManager.create_category(
            user_id=message.author.id, username=message.author.name,
            cat_name=cat_name, fields_list=fields_list, subcats_list=subcats_list
        )
        if not success:
            content = error_msg
        else:
            from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
            embed, view = SetupCategoryModal.create_dashboard(self.bot, message.author.id)
        return embed, view, content, []

    async def _handle_delete_category(self, message, data):
        await asyncio.sleep(0)
        embed, view, content = None, None, ""
        name = data.get("category_name", "").strip()
        if name:
            if LifeTrackerManager.delete_category(category_name=name):
                from cogs.LifeTracker.ui.Select.DeleteCategorySelect import DeleteCategorySelect
                embed, view = DeleteCategorySelect.create_dashboard(self.bot, message.author.id)
            else:
                cats = LifeTrackerManager.get_deletable_categories(user_id=message.author.id)
                content = f"刪除錯誤 {name} 並不存在或不可刪除\n目前可刪除目錄:\n" + "\n".join([f" - {cat.name}" for cat in cats]) if cats else f"刪除錯誤 {name} 並不存在或不可刪除\n目前無刪除目錄"
        else:
            from cogs.LifeTracker.ui.Button.DeleteCategoryBtn import DeleteCategoryBtn
            btn = DeleteCategoryBtn.get_Btn_with_user_id(self.bot, message.author.id)
            embed, view = btn.create_dashboard()
        return embed, view, content, []

    async def _handle_view_diary_category(self, message, data):
        from cogs.LifeTracker.ui.View import CategoryDetailView
        category_name = data.get('category_name')
        if category_name is None:
            return await self._handle_life_diary(message, data)
            
        try: 
            cat_result = name_to_id(TrackerCategory, category_name)
            category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
        except NameError as err_msg: 
            return None, None, err_msg, []
            
        embed, view, chart_file = await CategoryDetailView.create_ui(self.bot, category_id)
        return embed, view, "", ([chart_file] if chart_file else [])

    async def _handle_create_diary_record_empty(self, message, data):
        await asyncio.sleep(0)
        category_name = data.get('category_name')
        
        try: 
            cat_result = name_to_id(TrackerCategory, category_name)
            category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
        except NameError as err_msg: 
            return None, None, err_msg, []
        
        from cogs.LifeTracker.ui.View.LogRecordView import LogRecordView
        cat_info, subcats_info = LifeTrackerManager.get_category_details(category_id)
        if not cat_info:
            return None, None, "❌ 發生錯誤：找不到該分類資訊", []
            
        view_tmp = LogRecordView(self.bot, category_id, cat_info, subcats_info)
        embed, view = view_tmp.build_ui()
        return embed, view, "", []
        
    async def _handle_create_diary_record_with_data(self, message, data):
        category_name = data.get('category_name')
        subcategory_name = data.get('subcategory_name')
        from database.db import SessionLocal
        with SessionLocal() as db:
            try:
                cat_result = name_to_id(TrackerCategory, category_name, db=db)
                category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
                
                subcat_result = name_to_id(TrackerSubCategory, subcategory_name, db=db)
                subcat_id = subcat_result.id if hasattr(subcat_result, 'id') else subcat_result
            except NameError as err_msg: 
                return None, None, err_msg, []
        fields_and_values = data.get('fields_and_values')
        note = data.get('note')
        record_time = data.get('record_time')
        success, error_msg = LifeTrackerManager.add_life_record(
            user_id=message.author.id,
            category_id=category_id,
            subcat_id=subcat_id,
            values_dict=fields_and_values,
            note=note,
            record_time_str=record_time
        )
        if not success:
            return None, None, error_msg, []
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        embed, view, chart_file = await CategoryDetailView.create_ui(self.bot, category_id, page=0)
        attachments = [chart_file] if chart_file else []
        return embed, view, "", attachments

    async def _handle_create_diary_subcategory(self, message, data):
        category_name = data.get('category_name')
        subcategories = data.get('subcategories')
        
        try:
            cat_result = name_to_id(TrackerCategory, category_name)
            category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
        except NameError as err_msg:
            return None, None, err_msg, []

        if subcategories is None:
            from cogs.LifeTracker.ui.Button.AddSubCategoryBtn import AddSubCategoryBtn
            view = ActionHandler.get_button_view(AddSubCategoryBtn(self.bot, category_name=category_name))
            return None, view, "", []

        subcats_list = [s.strip() for s in subcategories if s.strip()] if subcategories else []
        
        # 🌟 修正這裡：使用 Keyword Arguments 傳遞參數
        success, error_msg = LifeTrackerManager.add_subcategory(
            category_id=category_id, 
            subcat_names_list=subcats_list
        )
        
        if not success:
            return None, None, error_msg, []
            
        from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
        embed, view = await ManageSubcatView.create_ui(self.bot, category_id)
        embed.title = "✅ 標籤新增成功！"
        embed.color = discord.Color.green()
        return embed, view, "", []

    async def _handle_delete_diary_subcategory(self, message, data):
        await asyncio.sleep(0)  
        category_name = data.get('category_name')
        subcategory_name = data.get('subcategory_name')
        
        try: 
            cat_result = name_to_id(TrackerCategory, category_name)
            category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
        except NameError as err_msg: 
            return None, None, err_msg, []
        
        if subcategory_name is None:
            from cogs.LifeTracker.ui.Button import ToggleDeleteBtn
            _, subcats_info = LifeTrackerManager.get_category_details(category_id)
            if not subcats_info:
                return None, None, f"目前 {category_name} 沒有任何標籤喔！", []
            view = ActionHandler.get_button_view(ToggleDeleteBtn(self.bot, category_id, subcats_info))
            return None, view, "", []
            
        suc = LifeTrackerManager.delete_subcategory(subcat_name=subcategory_name)
        
        if suc:
            return None, None, f"✅ 從 {category_name} 刪除 {subcategory_name} 成功", []
        return None, None, f"❌ 從 {category_name} 刪除 {subcategory_name} 失敗。\n{subcategory_name} 可能不存在。", []
        
    async def _handle_modify_diary_subcategory_empty(self, message, data):
        await asyncio.sleep(0)
        category_name = data.get('category_name')
        
        try: 
            cat_result = name_to_id(TrackerCategory, category_name)
            category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
        except NameError as err_msg: 
            return None, None, err_msg, []
        
        _, subcats_info = LifeTrackerManager.get_category_details(category_id)
        if not subcats_info:
            return None, None, f"目前 {category_name} 沒有任何標籤喔！", []
        from cogs.LifeTracker.ui.Button import EditModeBtn
        view = ActionHandler.get_button_view(EditModeBtn(self.bot, category_id))
        return None, view, "", []
    
    async def _handle_modify_diary_subcategory_with_data(self, message, data):
        category_name = data.get('category_name')
        subcategory_name = data.get('subcategory_name')
        from database.db import SessionLocal
        
        with SessionLocal() as db:
            try:
                cat_result = name_to_id(TrackerCategory, category_name, db=db)
                category_id = cat_result.id if hasattr(cat_result, 'id') else cat_result
                
                subcat_result = name_to_id(TrackerSubCategory, subcategory_name, db=db)
                subcat_id = subcat_result.id if hasattr(subcat_result, 'id') else subcat_result
            except NameError as err_msg: 
                return None, None, err_msg, []
        
        new_subcategory_name = data.get('new_subcategory_name')
        success, error_msg = LifeTrackerManager.update_subcategory_name(category_id, subcat_id, new_subcategory_name)
        if not success:
            return None, None, error_msg, []
            
        from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
        embed, view = await ManageSubcatView.create_ui(self.bot, category_id)
        embed.title = "✅ 標籤名稱已更新"
        embed.color = discord.Color.green()
        return embed, view, "", []
        
        
    # --- 3. 行事曆模組 ---
    async def _handle_create_itinerary_empty(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Itinerary.ui.View.ItineraryAddView import ItineraryAddView
        embed, view = ItineraryAddView.create_ui()
        return embed, view, "", []

    async def _handle_create_itinerary_with_data(self, message, data):
        
        await asyncio.sleep(0)
        attachments = []
        property_names = ["description", "year", "month", "day", "hour", "minute", "is_private"]
        description, year, month, day, hour, minute, is_private = (data.get(x) for x in property_names)
        
        minute = minute or 0
        is_private = 1 if is_private is None else is_private
        event_time = datetime(int(year), int(month), int(day), int(hour), minute, tzinfo=TW_TZ)
        clean_time = event_time.replace(tzinfo=None, second=0, microsecond=0)
        
        from cogs.Itinerary.utils.calendar_manager import CalendarDatabaseManager
        from cogs.Itinerary.itinerary_cog import Itinerary
        success, report = CalendarDatabaseManager.add_event(
            user_id=message.author.id, user_name=message.author.name,
            event_time=clean_time, description=description, is_private=(is_private == 1)
        )
        if not success:
            content = report
            embed, view = None, None
        else:
            embed, view, file = Itinerary.create_itinerary_dashboard_ui(message.author.id)
            embed.title = "✅ 行程新增成功！"
            embed.color = discord.Color.green()
            attachments = [file]
            content = ""
        return embed, view, content, attachments

    async def _handle_delete_itinerary(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Itinerary.ui.View.ItineraryDeleteView import ItineraryDeleteView
        embed, view = ItineraryDeleteView.create_ui(message.author.id)
        return embed, view, "", []

    async def _handle_view_itinerary(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Itinerary.ui.View.ItineraryDashboardView import ItineraryDashboardView
        embed, view, file = ItineraryDashboardView.create_ui(message.author.id)
        return embed, view, "", [file]

    # --- 4. Gmail 模組 ---
    async def _handle_gmail_home(self, message, data):
        
        await asyncio.sleep(0)
        embed, view = GmailDashboardView.create_ui(message.author.id)
        return embed, view, "", []

    async def _handle_create_gmail_category_empty(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Gmail.ui.Button.AddCategoryBtn import AddCategoryBtn
        view = ActionHandler.get_button_view(AddCategoryBtn(message.author.id))
        return None, view, "", []

    async def _handle_create_gmail_category_with_data(self, message, data):
        
        await asyncio.sleep(0)
        embed, view, content = None, None, ""
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
        return embed, view, content, []

    async def _handle_delete_gmail_category(self, message, data):
        
        await asyncio.sleep(0)
        embed, view, content = None, None, ""
        category_name = data.get("category_name")
        categories = EmailDatabaseManager.get_user_categories(message.author.id)
        
        if not categories:
            content = "目前沒有可刪除的GMAIL分類"
        elif category_name:
            if EmailDatabaseManager.delete_category(category_name=category_name):
                content = f"GMAIL分類({category_name})以成功刪除"
            else:
                content = f"刪除錯誤 {category_name} 並不存在或不可刪除\n目前可刪除目錄:\n" + "\n".join([f' - {cat["name"]}' for cat in categories])
        else:
            from cogs.Gmail.ui.View.DeleteCategoryView import DeleteCategoryView
            embed, view = DeleteCategoryView.create_ui(message.author.id, categories)
        return embed, view, content, []

    async def _handle_view_gmail_category(self, message, data):
        categories = EmailDatabaseManager.get_user_categories(message.author.id)
        name_list = [c["name"] for c in categories]
        return None, None, ActionHandler.list_text_format(" Gmail 分類", name_list), []
    
    async def _handle_view_gmail_category_content(self, message, data):
        await asyncio.sleep(0)
        category_name = data.get("category_name")
        categories = EmailDatabaseManager.get_user_categories(message.author.id)
        category_id = [c['id']for c in categories if c['name']==category_name]
        if not category_id:
            return None, f"{category_name} 分類不存在", "", []
        category_id = category_id[0]
        emails = EmailDatabaseManager.get_category_emails(category_id)
        from cogs.Gmail.ui.View.CategoryEmailPagerView import CategoryEmailPagerView
        pager_view = CategoryEmailPagerView(message.author.id, category_name, emails)
        return pager_view.generate_embed(), pager_view, "", []
        
    async def _handle_set_gmail_account_empty(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Gmail.ui.Button.SetupMailBtn import SetupMailBtn
        view = ActionHandler.get_button_view(SetupMailBtn())
        return None, view, "", []

    async def _handle_set_gmail_account_with_data(self, message, data):
        
        await asyncio.sleep(0)
        gmail_address, app_password = data.get("gmail_address"), data.get("app_password")
        from cogs.Gmail.utils import EmailTools
        clean_address = EmailTools()._extract_pure_email(gmail_address)
        report = EmailDatabaseManager.save_user_config(message.author.id, message.author.name, clean_address, app_password)    
        content = report if "❌" in report else "GMAIL已成功連結"
        return None, None, content, []

    async def _handle_gmail_setup_guide(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Gmail.ui.View.HelpView import HelpView
        view = HelpView(message.author.id)
        embed = view.generate_embed()
        return embed, view, "", []

    # --- 5. 股市模組 ---
    async def _handle_stock_monitor_home(self, message, data):
        
        await asyncio.sleep(0)
        embed, view = StockDashboardView.create_dashboard(self.bot, message.author.id)
        return embed, view, "", []

    async def _handle_stock_profit_detail(self, message, data):
        
        embed, view, content = None, None, ""
        stocks = StockManager.get_user_stocks(message.author.id)
        if not stocks:
            content = "⚠️ 你的監控清單目前是空的。"
        else:
            from cogs.Stock.ui.View.StockListView import StockListView
            embed, view = await StockListView.create_ui(self.bot, message.author.id, message.author.name)
        return embed, view, content, []

    async def _handle_add_stock_monitor_empty(self, message, data):
        
        await asyncio.sleep(0)
        from cogs.Stock.ui.Button.StockAddBtn import StockAddBtn
        view = ActionHandler.get_button_view(StockAddBtn(self.bot))
        return None, view, "", []

    async def _handle_add_stock_monitor_with_data(self, message, data):
        
        embed, view, content = None, None, ""
        from cogs.Stock.ui.Modal.StockAddModal import StockAddModal
        error_msg = await StockAddModal.check(
            data.get("stock_code"), data.get("share_quantity"), data.get("total_cost"),
            data.get("rise_alert_percent"), data.get("fall_alert_percent"),
            message.author.id, message.author.name
        )
        if error_msg:
            content = error_msg
        else:
            embed, view = StockDashboardView.create_dashboard(self.bot, message.author.id)
            embed.title = "✅ 新增成功！"
        return embed, view, content, []

    async def _handle_remove_stock_monitor(self, message, data):
        
        await asyncio.sleep(0)
        embed, view, content = None, None, ""
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
        return embed, view, content, []

    async def _handle_quick_stock_query(self, message, data):
        
        embed, view = None, None
        stock_code = data.get("stock_code")
        if not stock_code:
            from cogs.Stock.ui.Button.StockQueryBtn import StockQueryBtn
            view = ActionHandler.get_button_view(StockQueryBtn(self.bot))
        else:
            from cogs.Stock.ui.Modal.StockQueryModal import StockQueryModal
            embed, view = await StockQueryModal.create_dashboard(self.bot, message.author.id, stock_code)
        return embed, view, "", []

    # --- 6. AI 聊天記憶模組 ---
    async def _handle_chat(self, message, data):
        
        await asyncio.sleep(0)
        content = data.get("message", "")
        mem_text = data.get("memory")
        if mem_text:
            upsert_mem(message.author.id, message.author.name, mem_text)
        return None, None, content, []

    @staticmethod
    def get_button_view(button):
        view = discord.ui.View(timeout=60)
        view.add_item(button)
        return view
    
    @staticmethod
    def list_text_format(cat_name, list, indent=0):
        if not indent and not list:
            return f"目前的{cat_name}內是空的。"
        return f"目前的{cat_name}有：\n" + "\n".join(f'{" "*2*indent}- {x}' for x in list)
