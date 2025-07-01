import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from matplotlib.font_manager import FontProperties #

# --- 数据准备 ---
# (数据准备部分与原文件相同，此处省略以保持简洁)
# --- 数据准备 ---
# 将上面提供的CSV数据存储为字符串格式
# 注意：大山低脂肪牛乳的部分成分数据缺失，在CSV中留空
csv_data = """
品牌,产品名称,分类,类型,能量(kcal),蛋白质(g),脂肪(g),碳水化合物(g),钙(mg)
明治,おいしい牛乳,全脂牛奶,成分無調整牛乳,137,6.8,7.8,9.9,227
森永,森永のおいしい牛乳,全脂牛奶,成分無調整牛乳,137,6.8,7.8,9.9,227
雪印,雪印メグミルク牛乳,全脂牛奶,成分無調整牛乳,133,6.5,7.6,9.6,227
四叶,特選よつ葉牛乳,全脂牛奶,成分無調整牛乳,140,7.0,8.1,9.7,233
小岩井,小岩井牛乳,全脂牛奶,成分無調整牛乳,137,6.8,7.8,9.9,227
大山,白バラ牛乳,全脂牛奶,成分無調整牛乳,138,6.8,7.8,10.0,228
明治,おいしい低脂肪乳,低脂及其他,加工乳,107,7.4,3.8,10.8,254
森永,おいしい低脂肪牛乳,低脂及其他,低脂肪牛乳,87,7.0,2.0,10.2,234
雪印,すっきりＣa鉄,低脂及其他,乳飲料,75,6.0,1.2,10.1,340
四叶,特選よつ葉低脂肪牛乳,低脂及其他,低脂肪牛乳,95,7.2,2.9,9.9,244
小岩井,小岩井 低脂肪牛乳,低脂及其他,低脂肪牛乳,96,6.8,3.0,10.2,214
大山,白バラ低脂肪牛乳,低脂及其他,低脂肪牛乳,94,,"3.0",,
"""

# 使用io.StringIO将字符串数据读取为Pandas DataFrame
df_牛奶 = pd.read_csv(io.StringIO(csv_data))

# 将数值列的数据类型转换为数字，对于无法转换的（如空值）设置为NaN
for col in ['能量(kcal)', '蛋白质(g)', '脂肪(g)', '碳水化合物(g)', '钙(mg)']:
    df_牛奶[col] = pd.to_numeric(df_牛奶[col], errors='coerce')


# --- 图表绘制 ---

# 【修改1】指定字体文件的确切路径并创建字体属性对象
# 请确保这个路径对于您的运行环境是正确的
try:
    font_path = 'fonts\\LXGWWenKai-Light.ttf' # 假设字体文件在同一目录下
    # 或者提供绝对路径, e.g., font_path = '/path/to/your/fonts/LXGWWenKai-Light.ttf'
    my_font = FontProperties(fname=font_path, size=14)
    title_font = FontProperties(fname=font_path, size=22)
    label_font = FontProperties(fname=font_path, size=14)
    legend_font = FontProperties(fname=font_path, size=12)
    tick_font = FontProperties(fname=font_path, size=12)
except FileNotFoundError:
    print(f"字体文件未找到，请检查路径: {font_path}")
    # 如果找不到字体，则退出或使用默认字体，这里选择退出
    exit()

sns.set_style("whitegrid")
# 【修改2】移除了全局字体设置，保留了负号设置
# plt.rcParams['font.sans-serif'] = ['LXGWWenKai-Light'] # <- 此行已移除
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 创建一个包含两个子图的画布
fig, axes = plt.subplots(2, 1, figsize=(16, 18))
# 【修改3】在所有需要显示文本的地方应用字体属性对象
fig.suptitle('日本常见牛奶品牌营养成分对比 (每200ml)', fontproperties=title_font, y=1.02)

# --- 绘制图表1: 全脂牛奶 (成分無調整牛乳) ---
df_全脂 = df_牛奶[df_牛奶['分类'] == '全脂牛奶'].copy()
df_全脂_长格式 = df_全脂.melt(
    id_vars=['品牌', '产品名称'],
    value_vars=['蛋白质(g)', '脂肪(g)'],
    var_name='营养成分',
    value_name='含量'
)

sns.barplot(data=df_全脂_长格式, x='品牌', y='含量', hue='营养成分', ax=axes[0], palette='viridis')
axes[0].set_title('全脂牛奶：蛋白质与脂肪对比', fontproperties=FontProperties(fname=font_path, size=18))
axes[0].set_xlabel('品牌', fontproperties=label_font)
axes[0].set_ylabel('含量 (克)', fontproperties=label_font)
# 设置刻度标签字体
for label in axes[0].get_xticklabels() + axes[0].get_yticklabels():
    label.set_fontproperties(tick_font)
# 设置图例字体
axes[0].legend(title='营养成分', prop=legend_font)


# --- 绘制图表2: 低脂及其他乳制品 ---
df_低脂 = df_牛奶[df_牛奶['分类'] == '低脂及其他'].copy()
df_低脂['图表标签'] = df_低脂['品牌'] + "\n(" + df_低脂['类型'] + ")"
df_低脂_长格式 = df_低脂.melt(
    id_vars=['图表标签'],
    value_vars=['蛋白质(g)', '脂肪(g)', '钙(mg)'],
    var_name='营养成分',
    value_name='含量'
)

ax2_main = axes[1]
sns.barplot(data=df_低脂_长格式[df_低脂_长格式['营养成分'].isin(['蛋白质(g)', '脂肪(g)'])],
            x='图表标签', y='含量', hue='营养成分', ax=ax2_main, palette='plasma')
ax2_main.set_title('低脂及其他乳制品：蛋白质、脂肪与钙含量对比', fontproperties=FontProperties(fname=font_path, size=18))
ax2_main.set_xlabel('品牌 (产品类型)', fontproperties=label_font)
ax2_main.set_ylabel('蛋白质/脂肪含量 (克)', fontproperties=label_font)
for label in ax2_main.get_xticklabels() + ax2_main.get_yticklabels():
    label.set_fontproperties(tick_font)

ax2_calcium = ax2_main.twinx()
sns.lineplot(data=df_低脂_长格式[df_低脂_长格式['营养成分'] == '钙(mg)'],
             x='图表标签', y='含量', ax=ax2_calcium, color='green', marker='o', label='钙(mg)')
ax2_calcium.set_ylabel('钙含量 (毫克)', fontproperties=label_font, color='green')
for label in ax2_calcium.get_yticklabels():
    label.set_fontproperties(tick_font)
    label.set_color('green')


# 合并图例并设置字体
lines, labels = ax2_main.get_legend_handles_labels()
lines2, labels2 = ax2_calcium.get_legend_handles_labels()
ax2_calcium.legend(lines + lines2, labels + labels2, loc='upper left', prop=legend_font)
ax2_main.get_legend().remove()

# 优化布局并显示图表
plt.tight_layout(rect=[0, 0, 1, 0.98])
plt.show()