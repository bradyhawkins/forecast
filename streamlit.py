import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load initial employee data
file_path = 'path_to_your_employee_data.xlsx'  # Update this path with the correct location
employee_data = pd.read_excel(file_path)

# Helper function to calculate DROP level
def calculate_drop_level(years_of_service):
    if years_of_service >= 34:
        return 8
    elif 25 <= years_of_service < 26:
        return 1
    elif 26 <= years_of_service < 27:
        return 2
    elif 27 <= years_of_service < 28:
        return 3
    elif 28 <= years_of_service < 29:
        return 4
    elif 29 <= years_of_service < 30:
        return 5
    elif 30 <= years_of_service < 31:
        return 6
    elif 31 <= years_of_service < 32:
        return 7
    elif 32 <= years_of_service < 34:
        return 8
    else:
        return 0  # Not in DROP

# Initialize UI elements in the sidebar
st.sidebar.header("Model Parameters")
# Retirement probability sliders for each DROP level
retire_prob_6th = st.sidebar.slider("6th Year Retirement Probability (%)", 0, 100, 50)
retire_prob_7th = st.sidebar.slider("7th Year Retirement Probability (%)", 0, 100, 50)
retire_prob_8th = st.sidebar.slider("8th Year Retirement Probability (%)", 0, 100, 100)

# Age in model toggle
include_age = st.sidebar.checkbox("Include Age in Model", value=False)

# Hiring and terminations settings
hiring_plan = {2025: 50, 2026: 30, 2027: 30, 2028: 30, 2029: 30, 2030: 30}
annual_terminations = st.sidebar.number_input("Annual Terminations", min_value=0, value=5)
num_simulations = st.sidebar.number_input("Monte Carlo Simulations", min_value=1, value=1000)

# Button to run models
if st.sidebar.button("Run Model"):
    # Prepare employee data for simulation
    employees = employee_data.copy()
    employees['Current_DROP_Level'] = employees['Years_of_Service'].apply(calculate_drop_level)

    # Define functions based on notebook code
    def calculate_retirement(row):
        prob = retire_prob_8th if row['Current_DROP_Level'] == 8 else \
               retire_prob_7th if row['Current_DROP_Level'] == 7 else \
               retire_prob_6th if row['Current_DROP_Level'] == 6 else 0
        return np.random.rand() < prob / 100

    # Regular model
    results_regular = {'Year': [], 'Total Employees': []}
    total_employee_count = len(employees)
    for year in range(2025, 2031):
        # Apply retirements
        employees['Retire'] = employees.apply(calculate_retirement, axis=1)
        retirees = employees[employees['Retire']]
        employees = employees[~employees['Retire']]
        
        # Select non-retirement terminations
        eligible_for_termination = employees[employees['Years_of_Service'] <= 2]
        terminations = eligible_for_termination.sample(n=min(annual_terminations, len(eligible_for_termination)))
        employees = employees[~employees['Employee_ID'].isin(terminations['Employee_ID'])]
        
        # Update employee count and add new hires
        total_employee_count = len(employees) + hiring_plan.get(year, 0)
        results_regular['Year'].append(year)
        results_regular['Total Employees'].append(total_employee_count)
    
    # Convert results to DataFrame
    regular_model_df = pd.DataFrame(results_regular)
    
    # Monte Carlo Simulation
    monte_carlo_results = []
    for _ in range(num_simulations):
        mc_employees = employee_data.copy()
        mc_employee_count = []
        for year in range(2025, 2031):
            mc_employees['Retire'] = mc_employees.apply(calculate_retirement, axis=1)
            retirees = mc_employees[mc_employees['Retire']]
            mc_employees = mc_employees[~mc_employees['Retire']]
            eligible_for_termination = mc_employees[mc_employees['Years_of_Service'] <= 2]
            terminations = eligible_for_termination.sample(n=min(annual_terminations, len(eligible_for_termination)))
            mc_employees = mc_employees[~mc_employees['Employee_ID'].isin(terminations['Employee_ID'])]
            total_mc_employee_count = len(mc_employees) + hiring_plan.get(year, 0)
            mc_employee_count.append(total_mc_employee_count)
        monte_carlo_results.append(mc_employee_count)
    
    # Create DataFrame of Monte Carlo results and calculate statistics
    monte_carlo_df = pd.DataFrame(monte_carlo_results, columns=range(2025, 2031))
    monte_carlo_summary = monte_carlo_df.agg(['mean', 'std']).T
    monte_carlo_summary.columns = ['Mean', 'Std Dev']

    # Display results
    st.header("Regular Model Results")
    st.table(regular_model_df)
    st.line_chart(regular_model_df.set_index("Year")["Total Employees"])

    st.header("Monte Carlo Simulation Results")
    st.table(monte_carlo_summary)
    st.line_chart(monte_carlo_summary["Mean"])

    # Histogram of Monte Carlo distribution for the last year
    st.subheader("Monte Carlo Distribution for 2030")
    plt.figure(figsize=(10, 6))
    plt.hist(monte_carlo_df[2030], bins=30, edgecolor="black")
    plt.xlabel("Projected Employee Count in 2030")
    plt.ylabel("Frequency")
    plt.title("Monte Carlo Simulation Distribution")
    st.pyplot(plt)

else:
    st.write("Adjust parameters and click 'Run Model' to generate forecasts.")
