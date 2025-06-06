import yfinance as yf  # 導入 yfinance 套件，用於獲取股票資料
import pandas as pd  # 導入 pandas 套件，用於資料處理和分析
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# 設定頁面標題
st.set_page_config(page_title="ETF近期整理", layout="wide")
st.title("台灣熱門ETF近期表現整理")

# ETF簡介（可擴充）
etf_info = {
    '0050.TW': '元大台灣50，追蹤台灣50指數，季配息。',
    '0056.TW': '元大高股息，追蹤台灣高股息指數，季配息。',
    '00878.TW': '國泰永續高股息，追蹤MSCI台灣ESG永續高股息精選30指數，月配息。',
    '006208.TW': '富邦台50，追蹤台灣50指數，半年配息。',
    '00692.TW': '富邦公司治理，追蹤台灣公司治理100指數，半年配息。',
}

# 讓使用者自訂ETF清單
all_etfs = list(etf_info.keys())
def_etfs = ['0050.TW', '0056.TW', '00878.TW']
etf_symbols = st.sidebar.multiselect('選擇ETF', all_etfs, default=def_etfs)

# 預設查詢區間（近一個月）
def_date = datetime.now() - timedelta(days=31)
def_start_date = def_date.date()
def_end_date = datetime.now().date()

# 下載ETF資料（近一個月）
etf_data = {}
with st.spinner('正在獲取ETF資料...'):
    for symbol in etf_symbols:
        etf = yf.Ticker(symbol)
        hist = etf.history(start=def_start_date, end=def_end_date)
        if not hist.empty:
            etf_data[symbol] = hist

# 整理資料
df_month = pd.DataFrame({k: v['Close'] for k, v in etf_data.items()})
df_vol = pd.DataFrame({k: v['Volume'] for k, v in etf_data.items()})
df_7d = df_month.tail(7)
df_3d = df_month.tail(3)

# 馬卡龍色系
macaron_colors = [
    '#AEEEEE',  # 粉藍
    '#B7F0B1',  # 粉綠
    '#FFFACD',  # 粉黃
    '#FFDAB9',  # 粉橘
    '#E6E6FA',  # 粉紫
    '#FFB6C1',  # 粉紅
]

# ETF簡介
st.sidebar.markdown('---')
st.sidebar.subheader('ETF簡介')
for symbol in etf_symbols:
    st.sidebar.markdown(f"**{symbol}**：{etf_info.get(symbol, '暫無資料')}")

# 使用 tabs 方式顯示三種表格與圖表
labels = ["自訂義日期區間", "近一個月", "近7天", "近3天"]
tabs = st.tabs(labels)

# Helper function for summary and ranking

def get_summary(df):
    summary = []
    for symbol in df.columns:
        if not df[symbol].empty:
            start_price = df[symbol].iloc[0]
            end_price = df[symbol].iloc[-1]
            change_pct = (end_price - start_price) / start_price * 100
            summary.append({
                'symbol': symbol,
                'start': start_price,
                'end': end_price,
                'change_pct': change_pct
            })
    return summary

# tab0: 自訂義日期區間
def show_tab(df, df_vol, title):
    st.subheader(f"{title}ETF收盤價")
    st.dataframe(df)
    fig_price = go.Figure()
    for idx, symbol in enumerate(df.columns):
        fig_price.add_trace(go.Scatter(x=df.index, y=df[symbol], mode='lines+markers', name=symbol, line=dict(color=macaron_colors[idx % len(macaron_colors)])))
    fig_price.update_layout(title=f'{title}ETF收盤價走勢', xaxis_title='日期', yaxis_title='收盤價', template='plotly_white')
    st.plotly_chart(fig_price, use_container_width=True)
    # 成交量
    st.subheader(f"{title}ETF成交量")
    fig_vol = go.Figure()
    for idx, symbol in enumerate(df_vol.columns):
        fig_vol.add_trace(go.Bar(x=df_vol.index, y=df_vol[symbol], name=symbol, marker_color=macaron_colors[idx % len(macaron_colors)]))
    fig_vol.update_layout(barmode='group', title=f'{title}ETF成交量', xaxis_title='日期', yaxis_title='成交量', template='plotly_white')
    st.plotly_chart(fig_vol, use_container_width=True)
    # 漲跌幅排行
    summary = get_summary(df)
    if summary:
        st.subheader(f"{title}ETF漲跌幅排行")
        df_rank = pd.DataFrame(summary).sort_values('change_pct', ascending=False)
        fig_rank = px.bar(df_rank, x='symbol', y='change_pct', color='symbol', color_discrete_sequence=macaron_colors, text='change_pct')
        fig_rank.update_layout(title=f'{title}ETF漲跌幅排行', xaxis_title='ETF', yaxis_title='漲跌幅(%)', template='plotly_white', showlegend=False)
        st.plotly_chart(fig_rank, use_container_width=True)

with tabs[0]:
    st.subheader("自訂義日期區間ETF收盤價")
    col1, col2 = st.columns(2)
    custom_start = col1.date_input('開始日期', def_start_date, key='custom_start')
    custom_end = col2.date_input('結束日期', def_end_date, key='custom_end')
    custom_data = {}
    custom_vol = {}
    with st.spinner('正在獲取自訂區間ETF資料...'):
        for symbol in etf_symbols:
            etf = yf.Ticker(symbol)
            hist = etf.history(start=custom_start, end=custom_end)
            if not hist.empty:
                custom_data[symbol] = hist['Close']
                custom_vol[symbol] = hist['Volume']
    if custom_data:
        df_custom = pd.DataFrame(custom_data)
        df_custom_vol = pd.DataFrame(custom_vol)
        show_tab(df_custom, df_custom_vol, "自訂義日期區間")
    else:
        st.info('此區間無資料，請重新選擇日期。')

with tabs[1]:
    show_tab(df_month, df_vol, "近一個月")

with tabs[2]:
    show_tab(df_7d, df_vol.tail(7), "近7天")

with tabs[3]:
    show_tab(df_3d, df_vol.tail(3), "近3天")

# ====== 右側ETF總結與推薦 ======
st.sidebar.markdown('---')
st.sidebar.header("ETF總結與買入建議")

# 排序找最佳/最差ETF
if get_summary(df_month):
    best = max(get_summary(df_month), key=lambda x: x['change_pct'])
    worst = min(get_summary(df_month), key=lambda x: x['change_pct'])
    st.sidebar.markdown(f"**近一個月表現最佳ETF：** {best['symbol']}（{best['change_pct']:.2f}%）")
    st.sidebar.markdown(f"**近一個月表現最差ETF：** {worst['symbol']}（{worst['change_pct']:.2f}%）")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**各ETF近一個月漲跌幅：**")
    for etf in get_summary(df_month):
        st.sidebar.markdown(f"- {etf['symbol']}：{etf['change_pct']:.2f}%")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**買入建議：**")
    for etf in get_summary(df_month):
        if etf['change_pct'] > 2:
            advice = "建議觀察高點，分批買入"
        elif etf['change_pct'] > 0:
            advice = "可考慮分批布局"
        else:
            advice = "建議暫緩，觀察反彈訊號"
        st.sidebar.markdown(f"- {etf['symbol']}：{advice}")

# ====== 資料下載功能 ======
st.markdown('---')
st.subheader('下載資料')
st.download_button('下載近一個月收盤價 (CSV)', df_month.to_csv().encode('utf-8'), file_name='etf_month.csv', mime='text/csv')
st.download_button('下載近一個月成交量 (CSV)', df_vol.to_csv().encode('utf-8'), file_name='etf_volume.csv', mime='text/csv')

# ====== 參考資料來源 ======
st.markdown('---')
st.markdown('**股價資料來源：** [Yahoo! Finance](https://tw.finance.yahoo.com/)')

# 顯示更新時間
st.text(f"最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


