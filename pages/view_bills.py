import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="View Bills",
    page_icon="📊",
    layout="wide"
)

st.title("📊 View Bills")

def get_bills():
    conn = sqlite3.connect('bills.db')
    query = """
        SELECT 
            invoice_number,
            company_name,
            total_cost,
            bill_date
        FROM bills
        ORDER BY bill_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Get the data
df = get_bills()

# Convert bill_date to datetime
df['bill_date'] = pd.to_datetime(df['bill_date'])

# Modify the filtered_df assignment to just use the original df
filtered_df = df.copy()

# Show total amount
total_amount = filtered_df['total_cost'].sum()
st.metric("Total Amount", f"₹{total_amount:,.2f}")

# Display the data
st.dataframe(
    filtered_df,
    column_config={
        "total_cost": st.column_config.NumberColumn(
            "Total Cost",
            format="₹%.2f"
        ),
        "bill_date": st.column_config.DateColumn(
            "Bill Date",
            format="DD-MM-YYYY"
        )
    },
    hide_index=True,
    use_container_width=True
)

# Add download button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download as CSV",
    csv,
    "bills.csv",
    "text/csv",
    key='download-csv'
) 