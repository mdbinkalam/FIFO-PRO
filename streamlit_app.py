import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="FIFO Crypto Report", layout="wide")
st.title("📊 Crypto Report Generator")

# Define debug mode globally so it's accessible in both tabs
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
st.session_state.debug_mode = st.sidebar.checkbox("Debug Mode", value=st.session_state.debug_mode)

# Only use two tabs now: FIFO Report and USDT Price Summary
tabs = st.tabs(["FIFO Report", "USDT Price Summary"])

with tabs[0]:
    uploaded_file = st.file_uploader("Upload your Excel report", type=["xlsx"], key="fifo_upload")
    generate = st.button("Generate FIFO Report")

    if uploaded_file and generate:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = [col.strip().lower() for col in df.columns]  # Normalize columns
            st.success("✅ File uploaded successfully!")

            if st.session_state.debug_mode:
                st.write("Preview:", df.head())
                st.write("Detected columns:", df.columns.tolist())

            required_cols = {"date", "type", "coin name", "amount", "price", "net amount"}
            if not required_cols.issubset(set(df.columns)):
                st.error(f"Missing required columns: {required_cols - set(df.columns)}")
            else:
                df = df.sort_values(by="date")
                report_rows = []
                coins = df['coin name'].unique()

                for coin in coins:
                    coin_df = df[df['coin name'] == coin].copy()
                    buys = coin_df[coin_df['type'].str.lower() == 'buy'].copy()
                    sells = coin_df[coin_df['type'].str.lower() == 'sell'].copy()

                    buy_queue = []
                    for _, row in buys.iterrows():
                        buy_queue.append({"date": row["date"], "amount": row["amount"], "price": row["price"]})

                    for _, sell in sells.iterrows():
                        sell_amt = sell["amount"]
                        used_buys = []
                        total_cost = 0
                        original_sell_amt = sell_amt
                        sell_date = sell["date"]
                        sell_price = sell["price"]

                        temp_queue = [b.copy() for b in buy_queue if b["date"] <= sell_date]
                        if sum(b["amount"] for b in temp_queue) < sell_amt:
                            report_rows.append({
                                "Sell Date": sell_date,
                                "Sell Amount": original_sell_amt,
                                "Sell Price": sell_price,
                                "Coin": coin,
                                "Buy Date": "",
                                "Buy Amount Used": "",
                                "Buy Price": "",
                                "Cost Basis": "",
                                "Proceeds": "",
                                "Gain": "",
                                "Error": "Not enough eligible buy amount before this sell"
                            })
                            continue

                        new_queue = []
                        for b in buy_queue:
                            if b["date"] <= sell_date:
                                new_queue.append(b.copy())

                        updated_queue = []
                        while sell_amt > 0 and new_queue:
                            buy = new_queue.pop(0)
                            use_amt = min(sell_amt, buy["amount"])
                            cost = use_amt * buy["price"]
                            used_buys.append((buy["date"], use_amt, buy["price"], cost))
                            total_cost += cost
                            sell_amt -= use_amt
                            if buy["amount"] > use_amt:
                                updated_queue.append({
                                    "date": buy["date"],
                                    "amount": buy["amount"] - use_amt,
                                    "price": buy["price"]
                                })

                        future_buys = [b for b in buy_queue if b["date"] > sell_date]
                        buy_queue = updated_queue + future_buys

                        first = True
                        for bd, amt, prc, cost in used_buys:
                            row = {
                                "Sell Date": sell_date if first else "",
                                "Sell Amount": original_sell_amt if first else "",
                                "Sell Price": sell_price if first else "",
                                "Coin": coin if first else "",
                                "Buy Date": bd,
                                "Buy Amount Used": amt,
                                "Buy Price": prc,
                                "Cost Basis": cost,
                                "Proceeds": original_sell_amt * sell_price if first else "",
                                "Gain": (original_sell_amt * sell_price) - total_cost if first else "",
                                "Error": ""
                            }
                            report_rows.append(row)
                            first = False

                report_df = pd.DataFrame(report_rows)
                st.subheader("📁 FIFO Report")
                st.dataframe(report_df)

                remaining_stock = pd.DataFrame(buy_queue)
                def stock_summary(stock_df):
                    if stock_df.empty:
                        return {"Total Quantity": 0, "Total Value": 0, "Average Price": 0}
                    total_qty = stock_df["amount"].sum()
                    total_val = (stock_df["amount"] * stock_df["price"]).sum()
                    avg_price = total_val / total_qty if total_qty else 0
                    return {"Total Quantity": total_qty, "Total Value": total_val, "Average Price": avg_price}

                summary_df = pd.DataFrame([{"Type": "Closing Stock", **stock_summary(remaining_stock)}])

                st.subheader("📦 Closing Stock Summary")
                st.dataframe(summary_df)

                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    report_df.to_excel(writer, sheet_name="FIFO Report", index=False)
                    summary_df.to_excel(writer, sheet_name="Stock Summary", index=False)
                st.download_button(
                    "👅 Download Report as Excel",
                    data=output.getvalue(),
                    file_name="fifo_with_closing_stock.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Something went wrong: {e}")

with tabs[1]:
    st.warning("USDT Price Summary currently disabled. Coming soon with better handling of average price logic.")
