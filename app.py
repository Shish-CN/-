# app.py - 简化版确保能部署
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="纺锤体建仓法", layout="wide")

# 标题
st.title("💎 纺锤体建仓法 - 精准狙击版")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("参数设置")
    ticker = st.text_input("股票代码", value="AAPL").upper()
    user_pe = st.number_input("保守 Forward PE", value=25.0, min_value=1.0, max_value=100.0)
    vix_value = st.slider("VIX指数 (或使用实时)", min_value=10.0, max_value=50.0, value=20.0)
    
    if st.button("开始计算", type="primary"):
        st.session_state['calculate'] = True

# 恐慌系数计算
def calculate_coefficient(vix):
    if vix <= 15: return 0.96
    if vix <= 20: return 0.92
    if vix <= 25: return 0.88
    if vix <= 30: return 0.84
    return 0.80

# 计算函数
def calculate_strategy(ticker, user_pe, vix_value):
    try:
        # 获取股票数据（简化处理，避免复杂API调用）
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 使用更可靠的价格获取方式
        current_price = info.get('regularMarketPrice') or info.get('currentPrice') or 100
        
        # 获取EPS
        eps = info.get('forwardEps') or info.get('trailingEps') or 5.0
        
        # 计算
        panic_coeff = calculate_coefficient(vix_value)
        price_head = eps * user_pe
        price_tail = price_head * panic_coeff
        price_mid = (price_head + price_tail) / 2
        
        return {
            'current_price': current_price,
            'eps': eps,
            'vix': vix_value,
            'panic_coeff': panic_coeff,
            'price_head': price_head,
            'price_tail': price_tail,
            'price_mid': price_mid
        }
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        # 返回示例数据
        return {
            'current_price': 150,
            'eps': 5.0,
            'vix': vix_value,
            'panic_coeff': calculate_coefficient(vix_value),
            'price_head': 5.0 * user_pe,
            'price_tail': 5.0 * user_pe * calculate_coefficient(vix_value),
            'price_mid': (5.0 * user_pe + 5.0 * user_pe * calculate_coefficient(vix_value)) / 2
        }

# 显示结果
if st.session_state.get('calculate', False):
    with st.spinner("计算中..."):
        result = calculate_strategy(ticker, user_pe, vix_value)
    
    # 显示结果
    st.header("📊 计算结果")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前价格", f"${result['current_price']:.2f}")
    with col2:
        st.metric("VIX指数", f"{result['vix']:.2f}")
    with col3:
        st.metric("恐慌系数", f"{result['panic_coeff']:.3f}")
    
    st.markdown("---")
    
    st.subheader("🎯 三档价格点位")
    st.info(f"🔵 **锤头价**: ${result['price_head']:.2f} (锚定价)")
    st.success(f"🟢 **锤身价**: ${result['price_mid']:.2f} (加仓位)")
    st.error(f"🔴 **锤尾价**: ${result['price_tail']:.2f} (极限位)")
    
    st.markdown("---")
    st.subheader("📈 价格位置分析")
    
    # 简单分析
    current = result['current_price']
    head = result['price_head']
    tail = result['price_tail']
    
    if current > head:
        st.warning("⚠️ 当前价格高于锤头价，建议等待回调")
    elif current < tail:
        st.success("🚀 当前价格低于锤尾价，强烈建议买入")
    elif current > (head + tail) / 2:
        st.info("📊 当前价格在锤头区，可建立观察仓")
    else:
        st.info("📊 当前价格在锤尾区，安全边际较高")

# 部署说明
with st.expander("💡 使用说明"):
    st.markdown("""
    1. **输入股票代码**：如 AAPL, NVDA, TSLA
    2. **设置保守PE**：参考行业平均或历史PE
    3. **调整VIX**：实时VIX约15-25，恐慌时可达30+
    4. **查看计算结果**：系统自动计算三档买入价格
    """)

st.markdown("---")
st.caption("纺锤体建仓法 V3.2 | 数据来源: Yahoo Finance")
