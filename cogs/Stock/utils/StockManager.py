from database.models import UserStockWatch, User
from database import SessionLocal
from cogs.Stock.stock_config import TOTAL_SELL_COST_RATE

class StockManager:
    @staticmethod
    def get_user_stocks(user_id):
        """獲取使用者的所有監控股票"""
        with SessionLocal() as session:
            user = session.query(User).filter_by(discord_id=user_id).first()
            return user.stocks if user else []

    @staticmethod
    def add_stock(user_id, username, data: dict):
        """新增或更新股票監控"""
        with SessionLocal() as session:
            user = session.query(User).filter_by(discord_id=user_id).first()
            if not user:
                user = User(discord_id=user_id, username=username)
                session.add(user)
                session.flush()

            watch = session.query(UserStockWatch).filter_by(
                user_id=user_id, stock_symbol=data['symbol']
            ).first()

            if watch:
                watch.shares = data['shares']
                watch.total_cost = data['total_cost']
                watch.buy_price = data['buy_price']
                watch.target_up = data['up']
                watch.target_down = data['down']
            else:
                session.add(UserStockWatch(
                    user_id=user_id, 
                    stock_symbol=data['symbol'],
                    stock_name=data['name'],
                    shares=data['shares'],
                    total_cost=data['total_cost'],
                    buy_price=data['buy_price'],
                    target_up=data['up'],
                    target_down=data['down']
                ))
            session.commit()
            return True

    @staticmethod
    def calculate_profit(price, shares, total_cost):
        """計算精確損益邏輯"""
        if not (shares and total_cost): return None
        
        current_value = price * shares
        raw_profit = current_value - total_cost
        est_sell_cost = current_value * TOTAL_SELL_COST_RATE
        net_profit = raw_profit - est_sell_cost
        roi = (net_profit / total_cost) * 100
        return {
            "net_profit": int(net_profit),
            "roi": roi,
            "avg_price": total_cost / shares
        }

    @staticmethod
    def delete_stock(user_id, symbol):
        """刪除指定股票監控"""
        try:
            with SessionLocal() as session:
                from database.models import UserStockWatch
                watch = session.query(UserStockWatch).filter_by(
                    user_id=user_id, 
                    stock_symbol=symbol
                ).first()
                
                if watch:
                    name = watch.stock_name
                    session.delete(watch)
                    session.commit()
                    return True, name
                return False, "找不到該股票紀錄"
        except Exception as e:
            return False, str(e)
        
    @staticmethod
    def get_alert_watches():
        """獲取所有設定了漲跌幅預警的股票紀錄"""
        from database import SessionLocal
        with SessionLocal() as session:
            from database.models import UserStockWatch
            watches = session.query(UserStockWatch).filter(
                (UserStockWatch.target_up.isnot(None)) | 
                (UserStockWatch.target_down.isnot(None))
            ).all()
            
            # 🌟 轉換為字典回傳，避免 Session 關閉後發生 DetachedInstanceError
            return [{
                "user_id": w.user_id,
                "stock_symbol": w.stock_symbol,
                "target_up": w.target_up,
                "target_down": w.target_down,
                "last_notified_price": w.last_notified_price,
            } for w in watches]

    @staticmethod
    def update_notified_price(user_id: int, symbol: str, price: float):
        """更新股票的最後通知價格"""
        from database import SessionLocal
        with SessionLocal() as session:
            from database.models import UserStockWatch
            watch = session.query(UserStockWatch).filter_by(
                user_id=user_id, stock_symbol=symbol
            ).first()
            if watch:
                watch.last_notified_price = price
                session.commit()