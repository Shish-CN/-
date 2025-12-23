import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="纺锤体建仓法", layout="wide")

st.title("💎 纺锤体建仓法 V3.2")
st.markdown("---")

# 输入区域
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("股票代码", value="AAPL", help="例如：AAPL, NVDA, TSLA")
with col2:
    user_pe = st.number_input("保守Forward PE", value=25.0, min_value=1.0, max_value=100.0)

vix_value = st.slider("VIX恐慌指数", min_value=10.0, max_value=50.0, value=20.0, step=0.1)

if st.button("🚀 开始计算", type="primary"):
    # 恐慌系数计算函数
    def calculate_coefficient(vix):
        if vix <= 15: return 0.96
        if vix <= 20: return 0.92
        if vix <= 25: return 0.88
        if vix <= 30: return 0.84
        return 0.80
    
    try:
        # 获取股票数据（简单版本）
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        
        if len(hist) > 0:
            current_price = hist['Close'].iloc[-1]
        else:
            current_price = 150  # 默认值
        
        # 获取EPS
        info = stock.info
        eps = info.get('forwardEps') or info.get('trailingEps') or 5.0
        
        # 计算恐慌系数
        panic_coeff = calculate_coefficient(vix_value)
        
        # 计算三个价格点位
        price_head = eps * user_pe
        price_tail = price_head * panic_coeff
        price_mid = (price_head + price_tail) / 2
        
        # 显示结果
        st.success("✅ 计算完成！")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("当前价格", f"${current_price:.2f}")
        with col2:
            st.metric("锤头价", f"${price_head:.2f}")
        with col3:
            st.metric("恐慌系数", f"{panic_coeff:.3f}")
        
        st.markdown("---")
        
        # 价格区间
        st.subheader("🎯 买入价格区间")
        st.info(f"""
        **第一档（锤头）**: ${price_head:.2f}
        - 仓位: 15-20%
        - 说明: 初次建仓/观察仓
        """)
        
        st.warning(f"""
        **第二档（锤身）**: ${price_mid:.2f}
        - 仓位: 30%
        - 说明: 主力加仓位
        """)
        
        st.error(f"""
        **第三档（锤尾）**: ${price_tail:.2f}
        - 仓位: 30-35%
        - 说明: 极限抄底位
        """)
        
        # 决策建议
        st.markdown("---")
        st.subheader("💡 决策建议")
        
        if current_price > price_head:
            st.warning("⏳ 当前价格偏高，建议等待回调")
        elif current_price < price_tail:
            st.success("🚀 价格已到极限位，建议买入")
        else:
            st.info("📊 价格在合理区间，可分批建仓")
            
    except Exception as e:
        st.error(f"❌ 发生错误: {str(e)}")
        st.info("请检查股票代码是否正确，或稍后重试")

# 底部信息
st.markdown("---")
st.caption("数据来源: Yahoo Finance | 更新时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
