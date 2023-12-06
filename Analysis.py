import streamlit as st
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import matplotlib.colors as mcolors

# Function to calculate monthly mortgage payment
def calculate_mortgage(principal, annual_interest_rate, years=30):
    monthly_interest_rate = annual_interest_rate / 12
    num_payments = years * 12
    mortgage_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)
    return mortgage_payment

# Function to run simulations with savings check
def run_simulations_with_savings_check(purchase_price, savings, annual_base_income_range, annual_base_expense_range, down_payment_percentage, interest_rate_range, closing_cost_percentage_range, additional_upfront_costs_range, additional_annual_income_range, additional_annual_costs_range, property_growth_rate_range, inflation_rate_range, years, target_irr):
    favorable_outcomes = 0
    total_simulations = 1_000
    irrs = []
    count_irr_above_target = 0

    for _ in range(total_simulations):
        # Random values within ranges
        income = np.random.uniform(*annual_base_income_range)
        expense = np.random.uniform(*annual_base_expense_range)
        interest_rate = np.random.uniform(*interest_rate_range)
        closing_cost_percentage = np.random.uniform(*closing_cost_percentage_range)
        additional_upfront_costs = np.random.uniform(*additional_upfront_costs_range)
        additional_annual_income = np.random.uniform(*additional_annual_income_range)
        additional_annual_costs = np.random.uniform(*additional_annual_costs_range)
        property_growth_rate = np.random.uniform(*property_growth_rate_range)
        inflation_rate = np.random.uniform(*inflation_rate_range)

        # Initial calculations
        down_payment = purchase_price * down_payment_percentage
        loan_amount = purchase_price - down_payment
        closing_costs = loan_amount * closing_cost_percentage
        initial_outlay = down_payment + closing_costs + additional_upfront_costs

        # Check if savings are sufficient for initial outlay
        if savings < initial_outlay:
            continue  # Skip simulation as it's unfavorable

        cash_flows = [-initial_outlay]
        debt = 0

        monthly_mortgage = calculate_mortgage(loan_amount, interest_rate)
        annual_mortgage_payment = monthly_mortgage * 12

        for year in range(1, years + 1):
            # Adjust for inflation
            income *= (1 + inflation_rate)
            expense *= (1 + inflation_rate)
            additional_annual_income *= (1 + inflation_rate)
            additional_annual_costs *= (1 + inflation_rate)

            # Annual cash flow
            annual_cash_flow = income + additional_annual_income - expense - annual_mortgage_payment - additional_annual_costs

            # Managing debt if cash flow is negative
            if annual_cash_flow < 0:
                debt += abs(annual_cash_flow)  # Adding negative cash flow to debt
                debt *= 1.10  # Applying 10% interest on the debt
            else:
                # If there's enough cash flow to pay off the debt
                if annual_cash_flow > debt:
                    annual_cash_flow -= debt  # Paying off the debt
                    debt = 0
                else:
                    debt -= annual_cash_flow  # Paying as much as possible
                    annual_cash_flow = 0  # All cash flow goes to debt repayment

            cash_flows.append(annual_cash_flow)

        # Final year sale price calculation with closing costs
        gross_sale_price = purchase_price * (1 + property_growth_rate)**years
        sale_closing_costs = gross_sale_price * 0.06
        final_sale_price = gross_sale_price - sale_closing_costs
        cash_flows[-1] += final_sale_price

        # Calculate IRR
        try:
            irr = npf.irr(cash_flows)
        except ValueError:
            continue

        if not np.isnan(irr) and not np.isinf(irr):
            irrs.append(irr)
            if irr > target_irr:
                count_irr_above_target += 1

        if annual_cash_flow >= 0:
            favorable_outcomes += 1

    favorable_percentage = favorable_outcomes / total_simulations * 100
    average_irr = np.mean(irrs) if irrs else None
    percent_above_target_irr = count_irr_above_target / len(irrs) * 100 if irrs else 0

    # Initialize accumulators for mean calculations
    total_down_payments = total_closing_costs = total_additional_upfront_costs = total_net_upfront = 0
    total_annual_mortgage_payments = total_annual_base_expenses = total_additional_annual_costs = 0
    total_annual_base_incomes = total_additional_annual_incomes = total_net_annual_profit = 0

    # Update accumulators
    total_down_payments += down_payment
    total_closing_costs += closing_costs
    total_additional_upfront_costs += additional_upfront_costs
    total_net_upfront += (savings - initial_outlay)
    total_annual_mortgage_payments += annual_mortgage_payment
    total_annual_base_expenses += expense
    total_additional_annual_costs += additional_annual_costs
    total_annual_base_incomes += income
    total_additional_annual_incomes += additional_annual_income
    total_net_annual_profit += annual_cash_flow

    # Calculate means
    mean_down_payment = total_down_payments / total_simulations
    mean_closing_costs = total_closing_costs / total_simulations
    mean_additional_upfront_costs = total_additional_upfront_costs / total_simulations
    mean_net_upfront = total_net_upfront / total_simulations
    mean_annual_mortgage_payment = total_annual_mortgage_payments / total_simulations
    mean_annual_base_expense = total_annual_base_expenses / total_simulations
    mean_additional_annual_costs = total_additional_annual_costs / total_simulations
    mean_annual_base_income = total_annual_base_incomes / total_simulations
    mean_additional_annual_income = total_additional_annual_incomes / total_simulations
    mean_net_annual_profit = total_net_annual_profit / total_simulations

    return (favorable_percentage, average_irr, percent_above_target_irr, mean_down_payment, mean_closing_costs, mean_additional_upfront_costs, mean_net_upfront, mean_annual_mortgage_payment, mean_annual_base_expense, mean_additional_annual_costs, mean_annual_base_income, mean_additional_annual_income, mean_net_annual_profit)

# Function to update and display plots adapted for Streamlit
def update_plots(savings_amount, interest_rate_range, down_payment_percentage, closing_cost_percentage_range, additional_upfront_costs_range, annual_base_income_range, annual_base_expense_range, additional_annual_income_range, additional_annual_costs_range, property_growth_rate_range, inflation_rate_range, years, target_irr):
    purchase_prices = np.arange(1_000_000, 4_100_000, 100_000)
    results = [run_simulations_with_savings_check(...) for price in purchase_prices]

    # Extracting the results
    favorable_percentages, average_irrs, percentages_above_target, mean_values = zip(*results)

    # Create a DataFrame for displaying the table
    data = {
        'Purchase Price': purchase_prices,
        'Mean Down Payment': mean_values[0],
        'Mean Closing Costs': mean_values[1],
        'Mean Additional Upfront Costs': mean_values[2],
        'Mean Net Upfront (Reserves)': mean_values[3],
        'Mean Annual Mortgage Payment': mean_values[4],
        'Mean Annual Base Expenses': mean_values[5],
        'Mean Additional Annual Costs': mean_values[6],
        'Mean Annual Base Income': mean_values[7],
        'Mean Additional Annual Income': mean_values[8],
        'Mean Net Annual Profit': mean_values[9]
    }
    df = pd.DataFrame(data)

    # Display the table in Streamlit
    st.table(df)

    # Plotting logic adapted for Streamlit
    fig, axs = plt.subplots(2, 1, figsize=(10, 16))

    # First plot: Favorable Percentages
    axs[0].plot(purchase_prices, favorable_percentages, label='Favorable Percentages')
    axs[0].set_xlabel('Purchase Price ($)')
    axs[0].set_ylabel('Percentage Favorable (%)')
    axs[0].set_title('Percentage Affording Upfront & On-going Costs')
    axs[0].set_yticks(np.arange(0, 101, 10))

    # Second plot: Percentages Above Target IRR
    axs[1].plot(purchase_prices, percentages_above_target, label='Percentages Above Target IRR')
    axs[1].set_xlabel('Purchase Price ($)')
    axs[1].set_ylabel('Percentage Above Target IRR (%)')
    axs[1].set_title('Percentage Above Target IRR vs. Purchase Price')
    axs[1].set_yticks(np.arange(0, 101, 10))

    st.pyplot(fig)

# Interactive Inputs Function
def interactive_inputs():
    savings_amount = st.slider('Savings Amount', 100000, 1000000, 600000, step=5000)
    interest_rate_range = st.slider('Interest Rate Range', 0.01, 0.1, (0.07, 0.08), step=0.001)
    down_payment_percentage = st.slider('Down Payment %', 0.1, 0.3, 0.2, step=0.01)
    closing_cost_percentage_range = st.slider('Closing Cost % Range', 0.0, 0.1, (0.04, 0.07), step=0.01)
    additional_upfront_costs_range = st.slider('Additional Upfront Costs Range', 0, 100000, (0, 50000), step=5000)
    annual_base_income_range = st.slider('Annual Base Income Range', 100000, 500000, (250000, 350000), step=10000)
    annual_base_expense_range = st.slider('Annual Base Expense Range', 50000, 200000, (80000, 150000), step=10000)
    additional_annual_income_range = st.slider('Additional Annual Income Range', 0, 100000, (0, 50000), step=5000)
    additional_annual_costs_range = st.slider('Additional Annual Costs Range', 0, 100000, (20000, 80000), step=5000)
    property_growth_rate_range = st.slider('Property Growth Rate Range', -0.1, 0.1, (-0.04, 0.06), step=0.01)
    inflation_rate_range = st.slider('Inflation Rate Range', 0.0, 0.1, (0.0, 0.04), step=0.01)
    years = st.slider('Years', 5, 30, 20)
    target_irr = st.slider('Target IRR', 0.05, 0.1, 0.065, step=0.005)

    return (savings_amount, interest_rate_range, down_payment_percentage, closing_cost_percentage_range,
            additional_upfront_costs_range, annual_base_income_range, annual_base_expense_range,
            additional_annual_income_range, additional_annual_costs_range, property_growth_rate_range,
            inflation_rate_range, years, target_irr)

def main():
    st.title("Mortgage and Investment Analysis Tool")

    inputs = interactive_inputs()

    if st.button('Update Plots'):
        update_plots(*inputs)

if __name__ == "__main__":
    main()
