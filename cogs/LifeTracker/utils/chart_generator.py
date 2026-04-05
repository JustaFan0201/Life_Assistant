import discord
import io
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import time
from config import FONT_PATH
if os.path.exists(FONT_PATH):
    custom_font = fm.FontProperties(fname=FONT_PATH)
    fe = fm.FontEntry(fname=FONT_PATH, name='CustomFont')
    fm.fontManager.ttflist.insert(0, fe)
    plt.rcParams['font.family'] = fe.name
else:
    print(f"⚠️ 警告：找不到字體檔案於 {FONT_PATH}，將使用系統預設字體。")

def generate_donut_chart(category_name: str, stats_data: dict, target_field: str = "") -> discord.File:
    """生成甜甜圈圖並回傳 Discord File 物件"""
    if not stats_data:
        return None

    raw_labels = list(stats_data.keys())
    sizes = list(stats_data.values())
    
    # 計算總計
    total = sum(sizes)
    
    # 圓餅圖上的文字：標籤 + 百分比
    combined_labels = [f"{label}\n{size/total*100:.1f}%" for label, size in zip(raw_labels, sizes)]

    # 將圖片寬度拉長 (7x4)
    fig = plt.figure(figsize=(7, 4)) # 改用 plt.figure()
    fig.patch.set_alpha(0.0)
    
    # 這裡不要用 plt.subplots()
    # 我們手動加一個 Axes，座標為 [左, 下, 寬, 高]
    # 我們讓寬度佔畫布的一半 (0.5)，高度全開 (1)，並且左貼齊 (0)
    ax = fig.add_axes([0, 0, 0.5, 1]) 
    ax.patch.set_alpha(0.0)

    # 繪製圓餅圖 ( labeldistance 往內縮一點到 0.75)
    wedges, texts = ax.pie(
        sizes, 
        labels=combined_labels, 
        labeldistance=0.75,  
        startangle=140,
        textprops={
            'color': "white", 
            'fontsize': 14, 
            'fontweight': 'bold',
            'ha': 'center',       
            'va': 'center'        
        },
        # 移除 edgecolor='none'，因為 pie 本身沒 edgecolor 
        wedgeprops=dict(width=0.45) 
    )

    center_text = f"{target_field}\n總計: {total}"
    ax.text(0, 0, center_text, ha='center', va='center', fontsize=18, fontweight='bold', color='white')
    
    legend_labels = [f"{label}: {size}" for label, size in zip(raw_labels, sizes)]
    
    legend = ax.legend(
        wedges, 
        legend_labels,
        title=f"{category_name} - {target_field}", 
        loc="center left",         
        bbox_to_anchor=(1.0, 0.5), 
        frameon=False,             
        labelcolor='white',        
        fontsize=15
    )
    
    # 讓圖例的標題也變成白色跟粗體
    if legend.get_title():
        legend.get_title().set_color("white")
        legend.get_title().set_fontweight("bold")
        legend.get_title().set_fontsize(16)

    # 確保畫出來是正圓
    ax.axis('equal')  

    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    timestamp = int(time.time() * 1000) 
    return discord.File(buf, filename=f"chart_{timestamp}.png")