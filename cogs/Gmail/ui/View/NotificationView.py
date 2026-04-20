# cogs/Gmail/ui/View/NotificationView.py
from cogs.BasicDiscordObject import LockableView
from ..Button.ReplyNotificationBtn import ReplyNotificationBtn

class NewEmailNotificationView(LockableView):
    def __init__(self, cog, email_info, target_user_id):
        super().__init__(timeout=None)
        self.add_item(ReplyNotificationBtn(cog, email_info, target_user_id))