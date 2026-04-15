### 資料庫遷移功能
生成檔案 類似commit
```bash
alembic revision --autogenerate -m "想要打的留言"
```
更新資料庫 到最新的commit
```bash
alembic upgrade head
```
## Config (可以自訂自己cog的變數)
cogs\LifeTracker\LifeTracker_config.py
讓其他物件可以直接導入全域數值 也可以在config控制
```text
MAX_FIELDS = 3
MAX_SUBCATS = 20
MAX_FIELDS_LENGTH = 8
MAX_SUBCAT_LENGTH = 8
MAX_MAINCAT_LENGTH = 10
MAX_TEXT_LENGTH = 100
MAX_DAY_RANGE = 9999
MIN_DAY_RANGE = 1
MAX_INPUT_VALUE = 1000000
```
## BasicDiscordObject.py 一些ui物件的父類
透過 from cogs.BasicDiscordObject import ObjectYouwant 來導入
```text
class LockableView(ui.View):    # View父類 可以鎖住該View所有按鈕 因為有時候按下按鈕後可能需要等待
                                # 防止使用者在等待時亂按
    async def lock_all(self, interaction: discord.Interaction):
        """立即鎖定所有按鈕並推送到 Discord"""
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = True
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self)
        else:
            await interaction.edit_original_response(view=self)
    async def unlock_all(self):
        """解鎖所有按鈕（僅修改狀態，不主動推送，通常配合後續的 edit 使用）"""
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = False

class SafeButton(ui.Button):    # 按鈕父類 可透過這個按鈕 讓View鎖住其他按鈕
                                # 再透過do_action執行按下後的行為 需要實作do_action
    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, LockableView):
            await self.view.lock_all(interaction)
        
        await self.do_action(interaction)

    async def do_action(self, interaction: discord.Interaction):
        pass

class ValidatedModal(ui.Modal): # 有判斷檢查功能的Modal父類
    """具備自動校驗邏輯的基礎 Modal 父類"""
    async def on_submit(self, interaction: discord.Interaction):    # 使用者填寫完後確認的判斷
                                                                    # 需要實作execute_logic邏輯和on_success discord的UI變化
        error_msg = await self.execute_logic(interaction)
        
        if error_msg:           #錯誤時會傳送訊息 並在3秒後刪除
            await interaction.response.send_message(f"⚠️ {error_msg}", ephemeral=True)
            await asyncio.sleep(3)
            try:
                await interaction.delete_original_response()
            except discord.NotFound:
                pass  
            return
        await self.on_success(interaction)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """
        子類別需實作：呼叫 Manager 方法。
        成功請回傳 None，失敗請回傳 錯誤訊息字串。
        """
        return None

    async def on_success(self, interaction: discord.Interaction):
        """
        子類別需實作：邏輯執行成功後的 UI 處理。
        """
        pass
```
## View (View Structure)
```text
cogs\LifeTracker\ui\View\LifeDashboardView.py
class LifeDashboardView(LockableView):          #放置這個View有哪些按鈕
    def __init__(self, bot, categories=None):
        super().__init__(timeout=None)
        self.bot = bot
        
        if categories:
            self.add_item(CategoryDashboardSelect(self.bot, categories))
        
        self.add_item(SetupBtn(self.bot,row=1))
        self.add_item(DeleteCategoryBtn(self.bot, categories, row=1))
        self.add_item(BackToMainButton(self.bot,row=1))

    @staticmethod
    def create_dashboard(bot, user_id: int):    #撰寫你的View內容
        categories = LifeTrackerDatabaseManager.get_user_categories(user_id)

        embed = discord.Embed(
            title="📔 生活日記",
            description="歡迎使用生活日記！你可以從下方選單快速切換分類，或是建立新分類。",
            color=discord.Color.blue()
        )
        embed.add_field(name="＋ 設定主分類", value="輸入你想記錄的項目來建立新的主分類！", inline=False)
        embed.add_field(name="－ 刪除主分類", value="選擇你想要刪除的分類！", inline=False)
        if categories:
            cat_list_text = "\n".join([f"• **{c.name}** (`{', '.join(c.fields)}`)" for c in categories])
            embed.add_field(name="📂 我的分類清單", value=cat_list_text, inline=False)
        else:
            embed.add_field(name="📂 我的分類清單", value="目前還沒有建立任何分類喔！", inline=False)

        view = LifeDashboardView(bot, categories)
        return embed, view
```
## Btn (Btn Structure)
```text
cogs\LifeTracker\ui\Button\SetupBtn.py
class SetupBtn(ui.Button):
    def __init__(self, bot, label="", emoji="➕", row=1):   # 在__init__定義後 可以讓呼叫的ui帶入自訂的label,emoji, row... if more
        super().__init__(label=label, style=discord.ButtonStyle.green, emoji=emoji, row=row)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
        await interaction.response.send_modal(SetupCategoryModal(self.bot))
```

## Modal (Modal Structure)
```text
class SetupCategoryModal(ValidatedModal):   #透過繼承ValidatedModal的Modal例子 並透過全域Config設定 來控制字數設定
    def __init__(self, bot):
        super().__init__(title="⚙️ 新增自訂紀錄分類")
        self.bot = bot

        self.category_name = ui.TextInput(label=f"主分類名稱(長度限制{MAX_MAINCAT_LENGTH}個字)", placeholder="例如：消費、健身", max_length=MAX_MAINCAT_LENGTH)
        self.add_item(self.category_name)

        self.fields_input = ui.TextInput(
            label=f"需要紀錄的數值 (空白分隔，最多{MAX_FIELDS}個，單個長度限制{MAX_FIELDS_LENGTH}個字)", 
            placeholder="例如：金額 次數", 
            max_length=MAX_TEXT_LENGTH
        )
        self.add_item(self.fields_input)

        self.subcats_input = ui.TextInput(
            label=f"子分類/標籤 (空白分隔，最多{MAX_SUBCATS}個，單個長度限制{MAX_SUBCAT_LENGTH}個字)", 
            placeholder="例如：飲食 通勤 娛樂", 
            required=False, 
            max_length=MAX_TEXT_LENGTH
        )
        self.add_item(self.subcats_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """💡 呼叫 Manager 執行業務邏輯校驗"""
        fields_list = [f.strip() for f in self.fields_input.value.split() if f.strip()]
        subcats_list = [s.strip() for s in self.subcats_input.value.split() if s.strip()]
        cat_name = self.category_name.value.strip()

        # 呼叫 Manager 的靜態方法
        # 注意：我們直接在 validate_logic 執行 create，因為它包含校驗
        success, error_msg = LifeTracker_Manager.create_category(
            user_id=interaction.user.id,
            username=interaction.user.name,
            cat_name=cat_name,
            fields_list=fields_list,
            subcats_list=subcats_list
        )

        if not success:
            return error_msg

        return None

    async def on_success(self, interaction: discord.Interaction):
        """ 資料已在 validate_logic 存入，這裡只負責刷新 UI"""
        try:
            from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            
            embed.title = "✅ 分類建立成功！"
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 畫面更新失敗：{e}", ephemeral=True)
```
## 架構 (Project Structure)

```text
Life_Assistant
├─ config.py                # 配置文件：存放機器人設定與常量 
│                           # 如果要導入api key等信息，可以直接用from config import API_KEY的方式導入
└─ cogs/                    # 功能模組存放區 (Plugins)
    └─ LifeTracker/              # 生活日記模組
        ├─ __init__.py           # 模組入口：載入 Cog 並初始化資料庫
        ├─ LifeTrackerTasks.py   # 核心 Cog：處理每週 AI 總結任務與指令分發
        ├─ LifeTracker_config.py # 這個cog的全域變數 只需要在這裡修改就能直接影響其他檔案
        ├─ ...
        ├─ src/                  # 跟discord.py無關的主邏輯都放在這裡
        │   ├─ __init__.py      
        │   └─ ...
        ├─ utils/                # 工具層：後端邏輯與共同使用的工具
        │   ├─ __init__.py      
        │   ├─ LifeTracker_Manager.py # 把跟資料庫相關的操作都放在這裡
        │   ├─ chart_generator.py     # 動態繪製 Matplotlib 統計圖
        │   └─ ...
        │
        └─ ui/                   # 介面層：遵循 MVC 模式
            ├─ __init__.py      
            ├─ View/             # 視圖層：各級控制面板 (Layouts)
            │   ├─ LifeDashboardView.py       # 模組主入口：分類選擇與概覽
            │   ├─ ManageSubcatView.py        # 子分類 (標籤) 管理主視圖
            │   └─ ...
            │
            ├─ Select/           # 選擇組件：下拉選單邏輯 (Controllers)
            │   ├─ CategoryDashboardSelect.py # 主介面分類切換
            │   ├─ DeleteSubcatSelect.py      # 選擇欲刪除的標籤
            │   └─ ...
            │
            ├─ Button/           # 按鈕組件：封裝互動行為 (Actions)
            │   ├─ SetupBtn.py             # 初始化設定
            │   ├─ FillRecordBtn.py        # 進入數據填充流程
            │   └─ ...
            │
            └─ Modal/            # 視窗層：表單輸入介面 (Forms)
                ├─ SetupCategoryModal.py    # 初始建立分類 (定義欄位)
                ├─ DynamicLogModal.py       # 根據分類欄位動態生成
                └─ ...
```
    


