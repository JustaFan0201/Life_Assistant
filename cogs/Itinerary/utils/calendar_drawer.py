# cogs\Itinerary\utils\calendar_drawer.py
import calendar
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_month_calendar(year: int, month: int, event_days: list) -> io.BytesIO:
    """生成包含行程標記的月曆圖片，回傳二進位記憶體流"""
    # 設定畫布大小與背景
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='#2B2D31') # 使用 Discord 深色背景色
    ax.axis('off')
    
    cal = calendar.monthcalendar(year, month)
    month_name = f"{year} / {month:02d}"
    
    # 標題 (年份 / 月份)
    plt.text(0.5, 0.95, month_name, ha='center', va='center', fontsize=20, fontweight='bold', color='white', transform=ax.transAxes)
    
    # 星期標籤
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day in enumerate(days_of_week):
        color = '#FF6B6B' if i >= 5 else '#A3A6AA' # 週末用紅色
        plt.text(i/7 + 0.07, 0.82, day, ha='center', va='center', fontsize=12, fontweight='bold', color=color, transform=ax.transAxes)
        
    # 繪製日期網格
    y_start = 0.68
    y_step = 0.13
    for row_idx, week in enumerate(cal):
        for col_idx, day in enumerate(week):
            if day == 0: continue
            
            x = col_idx / 7 + 0.07
            y = y_start - row_idx * y_step
            
            # 💡 如果這天有行程，畫一個圈做標記
            if day in event_days:
                # 畫一個橘色圓形底色
                circle = patches.Circle((x, y), 0.045, color='#E0A04A', transform=ax.transAxes, zorder=1)
                ax.add_patch(circle)
                text_color = 'white'
            else:
                text_color = '#FFFFFF' if col_idx < 5 else '#FFB3B3' # 週末淺紅
                
            plt.text(x, y, str(day), ha='center', va='center', fontsize=12, color=text_color, zorder=2, transform=ax.transAxes)
            
    # 將圖片寫入記憶體
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    buf.seek(0)
    plt.close(fig) # 釋放資源
    return buf