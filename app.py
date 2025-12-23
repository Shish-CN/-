import streamlit as st
import yfinance as yf
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="纺锤体建仓法", layout="wide", page_icon="💎")

# 自定义CSS美化
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 30px;
    }
    .metric-box {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
    }
    .price-level {
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
        color: white;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="main-header"><h1>💎 纺锤体建仓法 - 精准狙击版</h1><p>V3.2 Web版</p></div>', unsafe_allow_html=True)

# 侧边栏输入
with st.sidebar:
    st.header("⚙️ 参数设置")
    ticker = st.text_input("股票代码 (如 NVDA, AAPL)", value="NVDA").upper()
    user_pe = st.number_input("保守 Forward PE 锚点", min_value=1.0, max_value=200.0, value=45.0, step=1.0)
    
    st.header("📊 VIX 恐慌指数设置")
    vix_input = st.selectbox("VIX数据源", ["实时获取", "手动输入"])
    if vix_input == "手动输入":
        vix_value = st.slider("VIX值", min_value=10.0, max_value=50.0, value=20.0, step=0.1)
    else:
        vix_value = None
    
    if st.button("🚀 开始计算", type="primary"):
        st.session_state.calculate = True

# 恐慌系数计算函数
def calculate_coefficient(vix):
    if vix is None: return 0.90
    if vix <= 15: return 0.96
    if vix <= 20: return 0.92
    if vix <= 25: return 0.88
    if vix <= 30: return 0.84
    return 0.80

# 获取股票数据
@st.cache_data(ttl=300)  # 缓存5分钟
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d", interval="1m")
        return info, hist
    except:
        return None, None

# 主计算函数
def calculate_strategy(ticker, user_pe, vix_value):
    try:
        # 获取数据
        info, hist = get_stock_data(ticker)
        if not info:
            st.error("无法获取股票数据，请检查代码")
            return
        
        # 获取当前价格
        current_price = info.get('currentPrice', 0)
        if current_price == 0 and hist is not None and not hist.empty:
            current_price = hist['Close'].iloc[-1]
        
        # 获取EPS
        eps_fwd = info.get('forwardEps')
        eps_trail = info.get('trailingEps')
        eps_used = eps_fwd if eps_fwd and eps_fwd > 0 else eps_trail
        eps_type = 'Forward Non-GAAP' if eps_fwd else '历史Trailing GAAP'
        
        if not eps_used:
            st.error("无法获取EPS数据")
            return
        
        # 计算实际PE
        current_actual_pe = current_price / eps_used
        
        # 如果未手动输入VIX，尝试获取实时VIX
        if vix_value is None:
            try:
                vix_ticker = yf.Ticker('^VIX')
                vix_hist = vix_ticker.history(period="1d", interval="1m")
                if not vix_hist.empty:
                    vix_value = vix_hist['Close'].iloc[-1]
                else:
                    vix_value = 20.0  # 默认值
            except:
                vix_value = 20.0
        
        # 计算恐慌系数
        panic_coeff = calculate_coefficient(vix_value)
        
        # 计算三个价格点位
        price_head = eps_used * user_pe
        price_tail = price_head * panic_coeff
        price_mid = (price_head + price_tail) / 2
        
        # 挂单区间
        BANDWIDTH = 0.015
        head_low, head_high = price_head * (1 - BANDWIDTH), price_head * (1 + BANDWIDTH)
        mid_low, mid_high = price_mid * (1 - BANDWIDTH), price_mid * (1 + BANDWIDTH)
        tail_low, tail_high = price_tail * (1 - BANDWIDTH), price_tail * (1 + BANDWIDTH)
        
        # 返回结果
        return {
            'current_price': current_price,
            'eps_used': eps_used,
            'eps_type': eps_type,
            'current_actual_pe': current_actual_pe,
            'vix': vix_value,
            'panic_coeff': panic_coeff,
            'price_head': price_head,
            'price_tail': price_tail,
            'price_mid': price_mid,
            'head_range': (head_low, head_high),
            'mid_range': (mid_low, mid_high),
            'tail_range': (tail_low, tail_high)
        }
        
    except Exception as e:
        st.error(f"计算错误: {e}")
        return None

# 显示结果
if 'calculate' in st.session_state and st.session_state.calculate:
    with st.spinner("正在计算..."):
        result = calculate_strategy(ticker, user_pe, vix_value)
        
    if result:
        # 数据仪表盘
        st.header("📊 数据仪表盘")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("当前价格", f"${result['current_price']:.2f}")
        with col2:
            st.metric("当前实际PE", f"{result['current_actual_pe']:.2f}x")
        with col3:
            st.metric("VIX指数", f"{result['vix']:.2f}")
        with col4:
            st.metric("恐慌系数", f"{result['panic_coeff']:.3f}")
        
        # 价格水平显示
        st.header("🎯 精准挂单区间")
        
        # 第一档
        with st.container():
            st.markdown(f"""
            <div class="price-level" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <h3>🔵 第一档：锤头 (${result['price_head']:.2f})</h3>
                <p><strong>挂单区间</strong>: ${result['head_range'][0]:.2f} ~ ${result['head_range'][1]:.2f}</p>
                <p><strong>建议仓位</strong>: 15%-20%</p>
                <p>初次建仓/观察仓</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 第二档
        with st.container():
            st.markdown(f"""
            <div class="price-level" style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);">
                <h3>🟢 第二档：锤身 (${result['price_mid']:.2f})</h3>
                <p><strong>挂单区间</strong>: ${result['mid_range'][0]:.2f} ~ ${result['mid_range'][1]:.2f}</p>
                <p><strong>建议仓位</strong>: 30%</p>
                <p>主力加仓/核心仓</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 第三档
        with st.container():
            st.markdown(f"""
            <div class="price-level" style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);">
                <h3>🔴 第三档：锤尾 (${result['price_tail']:.2f})</h3>
                <p><strong>挂单区间</strong>: ${result['tail_range'][0]:.2f} ~ ${result['tail_range'][1]:.2f}</p>
                <p><strong>建议仓位</strong>: 30%-35%</p>
                <p>极限抄底/满仓</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 可视化图表
        st.header("📈 价格位置可视化")
        
        # 创建价格区间图
        fig = go.Figure()
        
        # 添加价格点
        price_points = [
            ('锤尾', result['price_tail'], '#ff416c'),
            ('锤身', result['price_mid'], '#4CAF50'),
            ('锤头', result['price_head'], '#667eea'),
            ('当前价', result['current_price'], '#FFD700')
        ]
        
        for name, price, color in price_points:
            fig.add_trace(go.Scatter(
                x=[name],
                y=[price],
                mode='markers',
                marker=dict(size=15, color=color),
                name=name,
                hovertext=f"${price:.2f}",
                hoverinfo="text"
            ))
        
        # 添加区间带
        ranges = [
            ('锤尾区间', result['tail_range'][0], result['tail_range'][1], 'rgba(255, 65, 108, 0.2)'),
            ('锤身区间', result['mid_range'][0], result['mid_range'][1], 'rgba(76, 175, 80, 0.2)'),
            ('锤头区间', result['head_range'][0], result['head_range'][1], 'rgba(102, 126, 234, 0.2)')
        ]
        
        for name, low, high, color in ranges:
            fig.add_trace(go.Scatter(
                x=[name, name],
                y=[low, high],
                mode='lines',
                line=dict(width=0),
                fillcolor=color,
                fill='toself',
                showlegend=False
            ))
        
        fig.update_layout(
            title='纺锤体价格区间分布',
            yaxis_title='价格 ($)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 决策建议
        st.header("💡 决策建议")
        
        if result['current_price'] > result['head_range'][1]:
            st.warning("⛔️ 当前价格处于溢价区，建议等待回落")
        elif result['current_price'] < result['tail_range'][0]:
            st.success("🚀 当前价格处于极度折价区，建议执行P3档位买入")
        else:
            # 计算位置比例
            if result['price_head'] != result['price_tail']:
                pos_ratio = (result['current_price'] - result['price_tail']) / (result['price_head'] - result['price_tail'])
            else:
                pos_ratio = 1.0
            
            if pos_ratio > 0.66:
                st.info("✅ 处于【锤头区】，可建立底仓")
            elif pos_ratio > 0.33:
                st.info("✅ 处于【锤身区】，应加大力度加仓")
            else:
                st.info("✅ 处于【锤尾区】，接近极限底，安全垫高")

# 部署说明
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 部署到GitHub Pages")
st.sidebar.code("""
1. 创建 requirements.txt:
   streamlit
   yfinance
   numpy
   plotly
   
2. 部署到 Streamlit Cloud:
   - 上传到 GitHub
   - 访问 streamlit.io/cloud
   - 连接仓库，自动部署
""")