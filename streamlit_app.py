import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="FIFO Crypto Report", layout="wide")
st.title("📊 FIFO Crypto Gain/Loss Report Generator")

uploaded_file = st.file_uploader("Upload your Excel report", type=["xlsx"])
generate = st.button("Generate FIFO Report")

if uploaded_file and generate:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().lower() for col in df.columns]  # Normalize columns
        st.success("✅ File uploaded successfully!")
        st.write("Preview:", df.head())

        # Check required columns
        required_cols = {"date", "level", "amount", "price"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"Missing required columns: {required_cols - set(df.columns)}")
        else:
            buys = df[df['level'].str.lower() == 'buy'].copy().sort_values(by="date")
            sells = df[df['level'].str.lower() == 'sell'].copy().sort_values(by="date")

            if buys.empty or sells.empty:
                st.warning("Could not find both Buy and Sell entries.")
            else:
                report_rows = []
                buy_queue = []

                for _, row in buys.iterrows():
                    buy_queue.append({
                        "date": row["date"],
                        "amount": row["amount"],
                        "price": row["price"]
                    })

                for _, sell in sells.iterrows():
                    sell_amt = sell["amount"]
                    used_buys = []
                    total_cost = 0
                    original_sell_amt = sell_amt

                    temp_queue = [b.copy() for b in buy_queue if b["date"] <= sell["date"]]
                    if sum(b["amount"] for b in temp_queue) < sell_amt:
                        report_rows.append({
                            "Sell Date": sell["date"],
                            "Sell Amount": original_sell_amt,
                            "Sell Price": sell["price"],
                            "Error": "Not enough eligible buy amount before this sell"
                        })
                        continue

                    new_queue = []
                    for b in buy_queue:
                        if b["date"] <= sell["date"]:
                            new_queue.append(b)
                        else:
                            break

                    while sell_amt > 0 and new_queue:
                        buy = new_queue[0]
                        use_amt = min(sell_amt, buy["amount"])
                        cost = use_amt * buy["price"]
                        used_buys.append((buy["date"], use_amt, buy["price"], cost))
                        total_cost += cost
                        sell_amt -= use_amt
                        buy["amount"] -= use_amt
                        if buy["amount"] == 0:
                            new_queue.pop(0)

                    buy_queue = new_queue + [b for b in buy_queue if b["date"] > sell["date"]]

                    for bd, amt, prc, cost in used_buys:
                        report_rows.append({
                            "Sell Date": sell["date"],
                            "Sell Amount": original_sell_amt,
                            "Sell Price": sell["price"],
                            "Buy Date": bd,
                            "Buy Amount Used": amt,
                            "Buy Price": prc,
                            "Cost Basis": cost,
                            "Proceeds": original_sell_amt * sell["price"],
                            "Gain": (original_sell_amt * sell["price"]) - total_cost
                        })

                report_df = pd.DataFrame(report_rows)
                st.subheader("📑 FIFO Report")
                st.dataframe(report_df)

                # Download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    report_df.to_excel(writer, index=False)
                st.download_button(
                    "📥 Download Report as Excel",
                    data=output.getvalue(),
                    file_name="fifo_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"Something went wrong: {e}")
