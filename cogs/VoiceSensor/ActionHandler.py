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
            return True

        elif action == "OPEN_LIFE_ASSISTANT":
            from cogs.System.ui.View.SystemStartView import MainControlView
            embed, view = MainControlView.create_dashboard_ui(self.bot)

            await processing_msg.edit(embed=embed, view=view, content="")
            return True

        elif action == "OPEN_LIFE_DIARY":
            print(f"id = {message.author.id}")
            from cogs.LifeTracker.ui.View import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, message.author.id)
        
            await processing_msg.edit(embed=embed, view=view, content="")
            return True

        elif action == "CREATE_CATEGORY":
            return await self.handle_create_category(message, data)

        elif action == "DELETE_CATEGORY_MENU":
            return await self.handle_delete_menu(message, processing_msg)

        else:
            print(f"action: {action} 尚未設置")
        return True
    
