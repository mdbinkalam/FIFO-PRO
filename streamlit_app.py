import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="FIFO Crypto Report", layout="wide")
page = st.sidebar.radio("Choose Report Type", ["FIFO Report", "USDT Price Summary", "Dashboard View"])
st.title("📊 FIFO Crypto Gain/Loss Report Generator")

uploaded_file = st.file_uploader("Upload your Excel report", type=["xlsx"])
generate = st.button("Generate Report")
debug = st.sidebar.checkbox("Show debug info")

if uploaded_file and generate:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().lower() for col in df.columns]
        st.success("✅ File uploaded successfully!")
        st.write("Preview:", df.head())

        if debug:
            st.write("Detected columns:", df.columns.tolist())

        required_cols = {"date", "type", "coin name", "amount", "price", "net amount"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"Missing required columns: {required_cols - set(df.columns)}")
        else:
            df = df.sort_values(by="date")

            if page == "FIFO Report":
                # Existing FIFO Report logic remains unchanged...
                pass

            elif page == "USDT Price Summary":
                # Existing USDT Price Summary logic remains unchanged...
                pass

            elif page == "Dashboard View":
                df['date'] = pd.to_datetime(df['date']).dt.date
                df['pair'] = df['coin name'].apply(lambda x: 'USDT' if 'USDT' in x.upper() else 'INR')

                st.subheader("📊 Trade Volume by Coin")
                vol_chart = df.groupby('coin name')['amount'].sum().reset_index()
                fig_vol = px.bar(vol_chart, x='coin name', y='amount', title="Total Amount Traded per Coin")
                st.plotly_chart(fig_vol, use_container_width=True)

                st.subheader("📈 Net Amount by Date")
                date_chart = df.groupby('date')['net amount'].sum().reset_index()
                fig_date = px.line(date_chart, x='date', y='net amount', title="Net Amount Over Time")
                st.plotly_chart(fig_date, use_container_width=True)

                st.subheader("💹 Average Price per Coin")
                avg_price_chart = df.groupby('coin name').apply(lambda x: (x['amount'] * x['price']).sum() / x['amount'].sum()).reset_index(name='avg_price')
                fig_price = px.bar(avg_price_chart, x='coin name', y='avg_price', title="Average Trade Price per Coin")
                st.plotly_chart(fig_price, use_container_width=True)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
