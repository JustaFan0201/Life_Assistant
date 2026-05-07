from database.db_utils import upsert_mem
from VoiceSensor.ui.modalbtn import ModalButton
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
            pass

        elif action == "DELETE_CATEGORY_MENU":
            from LifeTracker.ui.Button.DeleteCategoryBtn import DeleteCategoryBtn
            view, embed = DeleteCategoryBtn.get_Btn_with_user_id(self.bot, message.author.id)
            await processing_msg.edit(embed=embed, view=view, content="")
        
        elif action == "CHAT":
            # - message* (string)
            # - memory (string)
            msg = data.get("message")
            mem_text = data.get("memory")
            if mem_text:
                upsert_mem(message.author.id, mem_text)
            
            await processing_msg.edit(content=msg)

        else:
            print(f"action: {action} 尚未設置")
        return True

    def get_button_view(self, button):
        view = discord.ui.View(timeout=60)
        view.add_item(button)
        return view