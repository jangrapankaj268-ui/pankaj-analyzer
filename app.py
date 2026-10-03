import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import numbers
api_key = "davqv99r01qn6m7td900davqv99r01qn6m7td90g"

def get_company_data(symbol):

    url = "https://finnhub.io/api/v1/stock/financials-reported"

    parameters = {"symbol": symbol,"token": api_key}

    try:
        response = requests.get(url, params=parameters, timeout=10)
        response.raise_for_status()

        data = response.json()

        return data

    except requests.RequestException:
        return {"Error": "Unable to connect to the financial data service."}

def normalize_income_statement(data):

    income_statements = []

    for report in data.get("data", []):

        income_statement = report.get("report", {}).get("ic", [])

        cash_flow_statement = report.get("report", {}).get("cf", [])

        normalized = {"year": report.get("year"),"period": report.get("endDate")}

        revenue = None
        net_income = None
        gross_profit = None
        operating_income = None
        pre_tax_income = None
        income_tax_expense = None
        operating_cash_flow = None
        investing_cash_flow = None
        financing_cash_flow = None
        capital_expenditure = None
        interest_expense = None
        eps_diluted = None
        cost_of_revenue = None

        revenue_parts = []

        for item in income_statement:

            concept = item.get("concept", "")
            label = item.get("label", "")
            value = item.get("value")

            concept_lower = concept.lower()
            label_lower = label.lower()

            if value is None:
                continue

            if concept in ["us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax","us-gaap_Revenues","us-gaap_SalesRevenueNet"]:
                revenue = value

            elif label_lower in ["revenue","revenue, net","net sales","sales revenue net"]:
                if revenue is None:
                    revenue = value

            elif concept in ["us-gaap_SalesRevenueGoodsNet","SalesRevenueGoodsNet","us-gaap_SalesRevenueServicesNet","SalesRevenueServicesNet","us-gaap_FinancialServicesRevenue","FinancialServicesRevenue"]:
                revenue_parts.append(value)

            elif concept == "us-gaap_CostOfGoodsAndServicesSold":
                cost_of_revenue = value

            elif concept in ["us-gaap_GrossProfit"]:
                gross_profit = value

            elif label_lower in ["gross profit","gross margin"]:
                if gross_profit is None:
                    gross_profit = value

            elif concept in ["us-gaap_NetIncomeLoss","us-gaap_ProfitLoss","ProfitLoss"]:
                net_income = value

            elif concept == "us-gaap_OperatingIncomeLoss":
                operating_income = value

            elif label_lower == "operating income":
                if operating_income is None:
                    operating_income = value

            elif concept == "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest":
                pre_tax_income = value

            elif label_lower in ["income before provision for income taxes","income before income taxes","income before taxes"]:
                if pre_tax_income is None:
                    pre_tax_income = value

            elif concept == "us-gaap_IncomeTaxExpenseBenefit":
                income_tax_expense = value

            elif "income tax" in label_lower and ("expense" in label_lower or "provision" in label_lower):
                if income_tax_expense is None:
                    income_tax_expense = value

            elif label_lower in ["net income","net income (loss)","net income (loss) attributable to parent"]:
                if net_income is None:
                    net_income = value

            elif concept == "us-gaap_InterestExpense":
                interest_expense = value

            elif "interest expense" in label_lower:
                if interest_expense is None:
                    interest_expense = value

            elif concept == "us-gaap_EarningsPerShareDiluted":
                eps_diluted = value

            elif "diluted" in label_lower and "earnings per share" in label_lower:
                if eps_diluted is None:
                    eps_diluted = value

        if revenue is None and revenue_parts:
            revenue = sum(revenue_parts)

        if gross_profit is None and revenue is not None and cost_of_revenue is not None:
            gross_profit = revenue - cost_of_revenue

        for item in cash_flow_statement:

            concept = item.get("concept", "")
            label = item.get("label", "")
            value = item.get("value")

            if value is None:
                continue

            if concept in ["us-gaap_NetCashProvidedByUsedInOperatingActivities","us-gaap_NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]:
                operating_cash_flow = value

            elif concept == "us-gaap_NetCashProvidedByUsedInInvestingActivities":
                investing_cash_flow = value

            elif concept == "us-gaap_NetCashProvidedByUsedInFinancingActivities":
                financing_cash_flow = value

            elif concept == "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment":
                capital_expenditure = value

        normalized["Revenue"] = revenue
        normalized["Gross Profit"] = gross_profit
        normalized["Operating Income"] = operating_income
        normalized["Pre-Tax Income"] = pre_tax_income
        normalized["Income Tax Expense"] = income_tax_expense
        normalized["Operating Cash Flow"] = operating_cash_flow
        normalized["Investing Cash Flow"] = investing_cash_flow
        normalized["Financing Cash Flow"] = financing_cash_flow
        normalized["Capital Expenditure"] = capital_expenditure
        normalized["Net Income"] = net_income
        normalized["Interest Expense"] = interest_expense
        normalized["EPS Diluted"] = eps_diluted

        income_statements.append(normalized)

    return pd.DataFrame(income_statements)

st.title("Pankaj Analyzer")
symbol = st.text_input("enter company ticker")
if st.button("Analyze"):
    
    if symbol:
        
        data = get_company_data(symbol.upper())

        st.session_state["financial_data"] = data
        
        if "Error" in data:
            st.error(data["Error"])

        elif "Information" in data:
            st.error(data["Information"])
            
    else:

        st.write("Please enter a ticker.")
        
if "financial_data" in st.session_state:

    data = st.session_state["financial_data"]

    if "data" in data:
        
        df = normalize_income_statement(data)

        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")

        df["Net Income"] = pd.to_numeric(df["Net Income"], errors="coerce")

        df["period"] = pd.to_datetime(df["period"])

        df = df.sort_values("period")

        years = sorted(df["period"].dt.year.unique())

        analysis_range = st.selectbox("Analysis Period",["1 Year", "2 Years", "3 Years", "4 Years", "5 Years", "All Available", "Custom"])

        if analysis_range == "Custom":

            start_year = st.selectbox("From Year", years)
            end_year = st.selectbox("To Year", years, index=len(years) - 1)

            if start_year <= end_year:
                analysis_df = df[(df["period"].dt.year >= start_year) & (df["period"].dt.year <= end_year)]

            else:
                st.error("From Year must be less than or equal to To Year.")
                analysis_df = df.iloc[0:0]

        else:

            if analysis_range == "1 Year":
                selected_years = 1

            elif analysis_range == "2 Years":
                selected_years = 2

            elif analysis_range == "3 Years":
                selected_years = 3

            elif analysis_range == "4 Years":
                selected_years = 4

            elif analysis_range == "5 Years":
                selected_years = 5

            else:
                selected_years = len(df)

            analysis_df = df.tail(selected_years)

        df["Revenue Growth"] = df["Revenue"].pct_change() * 100

        df["EPS Growth"] = df["EPS Diluted"].pct_change() * 100

        df["Gross Margin"] = (df["Gross Profit"] / df["Revenue"]) * 100

        df["Operating Margin"] = (df["Operating Income"] / df["Revenue"]) * 100

        df["Profit Margin"] = (df["Net Income"] / df["Revenue"]) * 100

        df["Free Cash Flow"] = df["Operating Cash Flow"] - df["Capital Expenditure"]

        df["FCF Growth"] = df["Free Cash Flow"].pct_change() * 100

        analysis_df = analysis_df.copy()

        analysis_df["Revenue Growth"] = df.loc[analysis_df.index, "Revenue Growth"]
        analysis_df["Gross Margin"] = df.loc[analysis_df.index, "Gross Margin"]
        analysis_df["Operating Margin"] = df.loc[analysis_df.index, "Operating Margin"]
        analysis_df["Profit Margin"] = df.loc[analysis_df.index, "Profit Margin"]
        analysis_df["EPS Growth"] = df.loc[analysis_df.index, "EPS Growth"]
        analysis_df["Free Cash Flow"] = df.loc[analysis_df.index, "Free Cash Flow"]
        analysis_df["FCF Growth"] = df.loc[analysis_df.index, "FCF Growth"]

        st.subheader("Cash Flow Statement")

        cash_flow_table = analysis_df.set_index("year")[["Operating Cash Flow","Investing Cash Flow","Financing Cash Flow","Capital Expenditure","Free Cash Flow"]].T

        cash_flow_table = cash_flow_table.map(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")

        st.dataframe(cash_flow_table, use_container_width=True)

        st.subheader("Income Statement")

        field_names = {"period": "Period","year": "Year","Revenue": "Revenue","Gross Profit": "Gross Profit","Operating Income": "Operating Income","Interest Expense": "Interest Expense", "Pre-Tax Income": "Pre-Tax Income","Income Tax Expense": "Income Tax Expense","Net Income": "Net Income","EPS Diluted": "EPS Diluted"}

        statement = analysis_df.set_index("year")[["Revenue","Gross Profit","Operating Income","Interest Expense","Pre-Tax Income","Income Tax Expense","Net Income","EPS Diluted"]].T

        statement = statement.map(lambda x: f"{x:,.0f}"if isinstance(x, numbers.Number) and pd.notna(x)else ("N/A" if pd.isna(x) else str(x)))

        statement.index = [field_names.get(field, field)for field in statement.index]

        st.dataframe(statement,use_container_width=True)

        st.subheader("Financial Analysis")

        analysis_table = analysis_df.set_index("year")[["Revenue Growth","Gross Margin","Operating Margin","Profit Margin","EPS Growth","FCF Growth"]].T

        analysis_table = analysis_table.map(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

        st.dataframe(analysis_table, use_container_width=True)

        st.subheader("Revenue vs Net Income")

        fig, ax = plt.subplots()

        ax.plot(analysis_df["year"], analysis_df["Revenue"], label="Revenue")
        ax.plot(analysis_df["year"], analysis_df["Net Income"], label="Net Income")

        ax.set_xlabel("Year")
        ax.set_ylabel("Amount")
        ax.set_title("Revenue vs Net Income")
        ax.legend()

        st.pyplot(fig)
        
        st.subheader("Revenue Growth")

        fig2, ax2 = plt.subplots()

        ax2.plot(analysis_df["year"], analysis_df["Revenue Growth"], marker="o")

        ax2.set_xlabel("Year")
        ax2.set_ylabel("Growth (%)")
        ax2.set_title("Annual Revenue Growth")

        ax2.grid(True)

        st.pyplot(fig2)

        st.subheader("Profitability Margins")

        fig3, ax3 = plt.subplots()

        ax3.plot(analysis_df["year"], analysis_df["Gross Margin"], marker="o", label="Gross Margin")
        ax3.plot(analysis_df["year"], analysis_df["Operating Margin"], marker="o", label="Operating Margin")
        ax3.plot(analysis_df["year"], analysis_df["Profit Margin"], marker="o", label="Profit Margin")

        ax3.set_xlabel("Year")
        ax3.set_ylabel("Margin (%)")
        ax3.set_title("Profitability Margins")
        ax3.legend()
        ax3.grid(True)

        st.pyplot(fig3)

        
