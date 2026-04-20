# cogs/Gmail/ui/View/ContactViews.py
from cogs.BasicDiscordObject import LockableView
from ..Select.ContactSelects import RecipientSelect, ContactManageSelect
from ..Button.ManualInputBtn import ManualInputBtn
from ..Button.EditContactBtn import EditContactBtn
from ..Button.DeleteContactBtn import DeleteContactBtn

class RecipientSelectView(LockableView):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.add_item(RecipientSelect(cog, user_id))
        self.add_item(ManualInputBtn(cog, user_id))

class ContactManageView(LockableView):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.add_item(ContactManageSelect(cog, user_id))

class ContactActionView(LockableView):
    def __init__(self, cog, user_id, nickname):
        super().__init__(timeout=60)
        self.add_item(EditContactBtn(cog, user_id, nickname))
        self.add_item(DeleteContactBtn(cog, user_id, nickname))