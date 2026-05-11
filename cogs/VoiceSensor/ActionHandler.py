from database.db_utils import upsert_mem
from cogs.LifeTracker.utils import LifeTracker_Manager
import discord


class ActionHandler:
    def __init__(self, bot):
        print("test1")
        self.bot = bot

    async def handle_actions(self, message, processing_msg, actions):
        print("test2")
        for step in actions:
            await self.execute_action(message, processing_msg, step)
    
    
    async def execute_action(self, message, processing_msg, step):

        action = step.get("action")
        data = step.get("data", {})
        missing = step.get("missing_fields", [])
        print(f"action = {action}")
        # # ❗1️⃣ 缺資料 → 進 UI flow
        # if missing:
        #     return await self.handle_missing(
        #         message, processing_msg, action, data, missing
        #     )

        # 🟢 2️⃣ 正常執行
        embed, view, content = None, None, ""

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
            view = self.get_button_view(SetupBtn(self.bot))
            
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
            
        elif action == "CHAT":
            # - message* (string)
            # - memory (string)
            content = data.get("message")
            mem_text = data.get("memory")
            if mem_text:
                upsert_mem(message.author.id, message.author.name, mem_text)

        else:
            print(f"action: {action} 尚未設置")
            return False
        
        await processing_msg.edit(embed=embed, view=view, content=content)
        return True


    def get_button_view(self, button):
        view = discord.ui.View(timeout=60)
        view.add_item(button)
        return view