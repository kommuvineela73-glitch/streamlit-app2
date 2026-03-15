import pandas as pd

def calculate_profit():

    data = pd.read_csv("transactions.csv")

    sales = data[data["type"] == "Sales"]["amount"].sum()
    expense = data[data["type"] == "Expense"]["amount"].sum()

    profit = sales - expense

    return sales, expense, profit