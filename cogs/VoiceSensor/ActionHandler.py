from database.db_utils import upsert_mem
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
        if action == "OPEN_SYSTEM_START":
            from cogs.System.ui.View.SystemStartView import SystemStartView
            embed, view = SystemStartView.create_start_ui(self.bot)

            await processing_msg.edit(embed=embed, view=view, content="")
        
        elif action == "OPEN_LIFE_ASSISTANT":
            from cogs.System.ui.View.SystemStartView import MainControlView
            embed, view = MainControlView.create_dashboard_ui(self.bot)

            await processing_msg.edit(embed=embed, view=view, content="")
        
        elif action == "OPEN_LIFE_DIARY":
            print(f"id = {message.author.id}")
            from cogs.LifeTracker.ui.View import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, message.author.id)
        
            await processing_msg.edit(embed=embed, view=view, content="")
        
        elif action == "CREATE_CATEGORY_MENU":
            from cogs.LifeTracker.ui.Button.SetupBtn import SetupBtn
            view = self.get_button_view(SetupBtn(self.bot))
            await processing_msg.edit(embed=None, view=view, content="")
            
        elif action == "CREATE_CATEGORY":
            # - category_name* (string) #主類別名稱
            # - fields* (list[string]) #數值類別 像是["金額", "次數"]
            # - subcategories (list[string])
            property_names = ["category_name", "fields", "subcategories"]
            category_name, fields, subcategories = (data.get(x) for x in property_names)
            
            cat_name = category_name.strip()
            fields_list = [f.strip() for f in fields if f.strip()]
            if subcategories:
                subcats_list = [s.strip() for s in subcategories if s.strip()]
               
            from cogs.LifeTracker.utils import LifeTracker_Manager
            success, error_msg = LifeTracker_Manager.create_category(
                user_id=message.author.id,
                username=message.author.name,
                cat_name=cat_name,
                fields_list=fields_list,
                subcats_list=subcats_list
            )
            if not success:
                embed, view, content = None, None, error_msg
            else:
                from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
                embed, view = SetupCategoryModal.create_dashboard(self.bot, message.author.id)
                content = ""

            await processing_msg.edit(embed=embed, view=view, content=content)
            

        elif action == "DELETE_CATEGORY_MENU":
            from cogs.LifeTracker.ui.Button.DeleteCategoryBtn import DeleteCategoryBtn
            btn = DeleteCategoryBtn.get_Btn_with_user_id(self.bot, message.author.id)
            embed, view = btn.create_dashboard()
            await processing_msg.edit(embed=embed, view=view, content="")
            
        elif action == "CHAT":
            # - message* (string)
            # - memory (string)
            msg = data.get("message")
            mem_text = data.get("memory")
            if mem_text:
                upsert_mem(message.author.id, message.author.name, mem_text)
            
            await processing_msg.edit(content=msg)

        else:
            print(f"action: {action} 尚未設置")
        return True

    def get_button_view(self, button):
        view = discord.ui.View(timeout=60)
        view.add_item(button)
        return view