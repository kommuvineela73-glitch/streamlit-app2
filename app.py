import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from model import calculate_profit

# ---------- CREATE FILES IF NOT EXIST ----------
if not os.path.exists("users.csv"):
    pd.DataFrame(columns=["username","email","password"]).to_csv("users.csv", index=False)

if not os.path.exists("transactions.csv"):
    pd.DataFrame(columns=["type","amount","description"]).to_csv("transactions.csv", index=False)

if not os.path.exists("inventory.csv"):
    pd.DataFrame(columns=["product","quantity","price"]).to_csv("inventory.csv", index=False)

if not os.path.exists("login_history.csv"):
    pd.DataFrame(columns=["username","login_time","logout_time","time_spent","login_count"]).to_csv("login_history.csv", index=False)

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "inventory_uploaded" not in st.session_state:
    st.session_state.inventory_uploaded = False
if "inventory_added_manual" not in st.session_state:
    st.session_state.inventory_added_manual = False
if "manager_authenticated" not in st.session_state:
    st.session_state.manager_authenticated = False
if "login_time" not in st.session_state:
    st.session_state.login_time = None

# ---------- REGISTER FUNCTION ----------
def register():
    st.subheader("Register New User")
    username = st.text_input("Create Username").strip()
    email = st.text_input("Email").strip()
    password = st.text_input("Create Password", type="password").strip()
    if st.button("Register"):
        users = pd.read_csv("users.csv", dtype=str)
        if username in users["username"].values:
            st.error("Username already exists")
        else:
            new_user = pd.DataFrame([[username,email,password]], columns=["username","email","password"])
            users = pd.concat([users, new_user], ignore_index=True)
            users.to_csv("users.csv", index=False)
            st.success("Registration Successful")

# ---------- LOGIN FUNCTION ----------
def login():
    st.subheader("Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password").strip()

    if st.button("Login"):
        users = pd.read_csv("users.csv", dtype=str)

        if ((users["username"] == username) & (users["password"] == password)).any():

            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login Successful")

            import datetime
            login_time = datetime.datetime.now()

            # Load history
            history = pd.read_csv("login_history.csv")

            # Calculate login count
            prev_count = history[history["username"]==username].shape[0]
            login_count = prev_count + 1

            # Add new row
            new = pd.DataFrame([[username, login_time, None, None, login_count]],
                   columns=["username","login_time","logout_time","time_spent","login_count"])
            history = pd.concat([history,new], ignore_index=True)
            history.to_csv("login_history.csv", index=False)

            # Save login_time in session
            st.session_state.login_time = login_time

            return True
        else:
            st.error("Invalid Credentials")
            return False
# ---------- LOGIN PAGE ----------
if not st.session_state.logged_in:
    st.title("Business Management System")
    option = st.radio("Select Option", ["Login", "Register"])
    if option == "Login":
        login()
    else:
        register()
    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Menu", ["Dashboard", "Inventory", "Reports", "AI Prediction", "Admin", "Logout"])
st.sidebar.write("Logged in as:", st.session_state.username)

# ================== DASHBOARD ==================
if menu == "Dashboard":

    st.title("Dashboard")

    transactions = pd.read_csv("transactions.csv")

    # -------- Business Overview --------
    st.subheader("Business Overview")

    sales = transactions[transactions["type"] == "Sales"]
    expenses = transactions[transactions["type"] == "Expense"]

    total_sales = sales["amount"].sum()
    total_expenses = expenses["amount"].sum()

    col1, col2 = st.columns(2)

    col1.metric("Total Sales", total_sales)
    col2.metric("Total Expenses", total_expenses)

    # -------- Pie Chart --------
    st.subheader("Sales vs Expenses Distribution")

    pie_data = pd.DataFrame({
        "Category": ["Sales", "Expenses"],
        "Amount": [total_sales, total_expenses]
    })

    fig_pie = px.pie(
        pie_data,
        values="Amount",
        names="Category",
        hole=0.4,
        title="Business Distribution"
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # -------- Add Transaction --------
    st.subheader("Add Transaction")

    t_type = st.selectbox("Type", ["Sales", "Expense"])
    amount = st.number_input("Amount", 0)
    desc = st.text_input("Description")

    if st.button("Add Transaction"):
        new = pd.DataFrame([[t_type, amount, desc]],
                           columns=["type", "amount", "description"])

        transactions = pd.concat([transactions, new], ignore_index=True)
        transactions.to_csv("transactions.csv", index=False)

        st.success("Transaction Added")

    # -------- Transactions Table --------
    st.subheader("Transactions")

    st.dataframe(transactions)

    # -------- Bar Chart --------
    st.subheader("Transaction Analysis")

    fig_bar = px.bar(
        transactions,
        x="type",
        y="amount",
        color="type",
        title="Sales and Expense Transactions"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# ================== INVENTORY ==================
elif menu == "Inventory":
    st.title("Inventory")

    # ---------- SESSION STATE ----------
    if "manual_inventory" not in st.session_state:
        st.session_state.manual_inventory = pd.DataFrame(columns=["product", "quantity", "price"])
    if "uploaded_inventory" not in st.session_state:
        st.session_state.uploaded_inventory = pd.DataFrame(columns=["product", "quantity", "price"])

    # ================== MANUAL ADD PRODUCT ==================
    st.subheader("Add Product Manually")
    product = st.text_input("Product Name", key="manual_product")
    qty = st.number_input("Quantity", 0, step=1, key="manual_qty")
    price = st.number_input("Price", 0, step=1, key="manual_price")

    if st.button("Add Product Manually"):
        if product.strip() == "":
            st.error("Enter a product name")
        else:
            new_row = pd.DataFrame([[product.strip(), qty, price]], columns=["product", "quantity", "price"])
            st.session_state.manual_inventory = pd.concat([st.session_state.manual_inventory, new_row], ignore_index=True)
            st.success(f"Product '{product}' added successfully!")

    # Show Manual Inventory Table
    if not st.session_state.manual_inventory.empty:
        st.subheader("Manual Inventory Table")
        st.dataframe(st.session_state.manual_inventory.fillna("-"))

        if st.button("Clear Manual Inventory Table"):
            st.session_state.manual_inventory = pd.DataFrame(columns=["product", "quantity", "price"])
            st.success("Manual inventory cleared.")

    # ================== UPLOAD CSV / EXCEL ==================
    st.subheader("Upload Inventory CSV/Excel")
    file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], key="upload_file")

    if file is not None:
        try:
            if file.name.endswith("csv"):
                df = pd.read_csv(file)
            else:
                xls = pd.ExcelFile(file)
                sheet_name = st.selectbox("Select sheet to upload", xls.sheet_names)
                df = pd.read_excel(xls, sheet_name=sheet_name)

            df.columns = df.columns.str.strip().str.lower()
            rename_map = {}
            for col in df.columns:
                if "product" in col:
                    rename_map[col] = "product"
                elif "quantity" in col or "qty" in col:
                    rename_map[col] = "quantity"
                elif "price" in col or "cost" in col:
                    rename_map[col] = "price"
            df.rename(columns=rename_map, inplace=True)

            if set(["product", "quantity", "price"]).issubset(df.columns):
                df = df[["product", "quantity", "price"]]
                st.session_state.uploaded_inventory = df
                st.success("File uploaded successfully!")
            else:
                st.error("CSV/Excel must have columns: product, quantity, price")

        except Exception as e:
            st.error(f"Error uploading file: {e}")

    # Show Uploaded Inventory Table
    if not st.session_state.uploaded_inventory.empty:
        st.subheader("Uploaded Inventory Table")
        st.dataframe(st.session_state.uploaded_inventory.fillna("-"))

        if st.button("Clear Uploaded Inventory Table"):
            st.session_state.uploaded_inventory = pd.DataFrame(columns=["product", "quantity", "price"])
            st.success("Uploaded inventory cleared.")

# ================== REPORTS ==================
elif menu == "Reports":
    st.title("Reports")

    transactions = pd.read_csv("transactions.csv")

    total_sales = transactions[transactions["type"]=="Sales"]["amount"].sum()
    total_expenses = transactions[transactions["type"]=="Expense"]["amount"].sum()

    report = pd.DataFrame({
        "Metric":["Total Sales","Total Expenses"],
        "Amount":[total_sales,total_expenses]
    })

    st.dataframe(report)

    # ---------- Excel Report ----------
    report.to_excel("report.xlsx", index=False)

    with open("report.xlsx","rb") as f:
        st.download_button("Download Excel Report", f, "report.xlsx")

    # ---------- PDF Report ----------
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"Business Report",ln=True)

    pdf.set_font("Arial","",12)
    pdf.cell(0,10,f"Total Sales: {total_sales}",ln=True)
    pdf.cell(0,10,f"Total Expenses: {total_expenses}",ln=True)

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Download PDF Report", f, "report.pdf")
# ================== AI PREDICTION ==================
elif menu == "AI Prediction":

    st.title("AI Future Sales Forecast (3–4 Months)")

    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn.linear_model import LinearRegression

    transactions = pd.read_csv("transactions.csv")

    sales = transactions[transactions["type"]=="Sales"]["amount"]

    if len(sales) < 5:
        st.warning("Add more sales transactions to generate prediction.")
    else:

        sales = sales.values

        X = np.arange(len(sales)).reshape(-1,1)
        y = sales

        model = LinearRegression()
        model.fit(X, y)

        # Radio button for prediction months
        months = st.radio(
            "Select Future Prediction Period",
            ["1 Month", "3 Months", "4 Months"]
        )

        if months == "1 Month":
            days = 30
        elif months == "3 Months":
            days = 90
        else:
            days = 120

        future_X = np.arange(len(sales), len(sales)+days).reshape(-1,1)
        predictions = model.predict(future_X)

        future_df = pd.DataFrame({
            "Day": range(len(sales)+1, len(sales)+days+1),
            "Predicted Sales": predictions
        })

        st.subheader("Future Sales Prediction")
        st.dataframe(future_df)

        # Chart
        fig, ax = plt.subplots()

        ax.plot(range(len(sales)), sales, label="Actual Sales")
        ax.plot(range(len(sales), len(sales)+days), predictions, label="Predicted Sales")

        ax.set_title("Sales Forecast (Future Months)")
        ax.set_xlabel("Days")
        ax.set_ylabel("Sales")

        ax.legend()

        st.pyplot(fig)
# ================== ADMIN ==================
elif menu == "Admin":
    manager_pass = "admin123"

    # Initialize session state for manager authentication
    if "manager_authenticated" not in st.session_state:
        st.session_state.manager_authenticated = False

    # Password input (always visible until correct password)
    if not st.session_state.manager_authenticated:
        entered_pass = st.text_input("Enter Manager Password", type="password")
        if entered_pass:
            if entered_pass == manager_pass:
                st.session_state.manager_authenticated = True
                st.success("Manager authenticated!")
            else:
                st.warning("Incorrect manager password")

    # Show Admin dashboard immediately if authenticated
    if st.session_state.manager_authenticated:
        st.title("Admin Dashboard")

        # ---------- Load Data ----------
        users = pd.read_csv("users.csv")
        inventory = pd.read_csv("inventory.csv")
        transactions = pd.read_csv("transactions.csv")
        history = pd.read_csv("login_history.csv")

        # ---------- Dashboard Metrics ----------
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", len(users))
        col2.metric("Total Products", len(inventory))
        col3.metric("Total Transactions", len(transactions))

        # ---------- Registered Users Table ----------
        st.subheader("Registered Users")
        st.dataframe(users)

        # ---------- Change User Password ----------
        st.subheader("Change User Password")
        selected_user = st.selectbox("Select User", users["username"])
        new_pass = st.text_input("New Password for selected user", type="password")
        if st.button("Update Password"):
            users.loc[users["username"] == selected_user, "password"] = new_pass
            users.to_csv("users.csv", index=False)
            st.success(f"Password for {selected_user} updated successfully!")

        # ---------- Full Login History ----------
        st.subheader("User Login History")
        st.dataframe(history)

        # ---------- Filter Login History ----------
        st.subheader("Filter Login History by User")
        user_filter = st.radio("Select User", options=["All"] + list(users["username"]))
        if user_filter != "All":
            filtered_history = history[history["username"] == user_filter]
        else:
            filtered_history = history
        st.dataframe(filtered_history)

        # ---------- Total Logins Per User ----------
        st.subheader("Total Logins per User")
        if "login_count" in history.columns:
            login_summary = history.groupby("username")["login_count"].max().reset_index()
            login_summary.rename(columns={"login_count": "total_logins"}, inplace=True)
            st.dataframe(login_summary)
        else:
            st.info("No login count data available yet")
# ================== LOGOUT ==================
elif menu == "Logout":
    if st.session_state.logged_in:

        import datetime

        logout_time = datetime.datetime.now()
        login_time = st.session_state.login_time

        if login_time is not None:
            time_spent = logout_time - login_time
        else:
            time_spent = ""

        history = pd.read_csv("login_history.csv")

        # Find latest login row for user
        user_rows = history[history["username"] == st.session_state.username]

        if not user_rows.empty:
            last_index = user_rows.index[-1]

            history.loc[last_index, "logout_time"] = logout_time
            history.loc[last_index, "time_spent"] = str(time_spent)

        history.to_csv("login_history.csv", index=False)

    st.session_state.logged_in = False
    st.session_state.username = ""

    st.success("Logged Out Successfully")