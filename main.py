from flask import Flask, render_template, request, jsonify
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

# --- SETUP ---
# This line is correct. It looks for a 'templates' folder.
app = Flask(__name__, static_folder="static", template_folder="templates")

# Pre-trained fallback trend model
months = np.array([1, 2, 3, 4, 5, 6]).reshape(-1, 1)
expenses_sample = np.array([25000, 26000, 27500, 29000, 31000, 32500])
trend_model = LinearRegression().fit(months, expenses_sample)

# In-memory store (demo only)
USER_DATA = {}
# CRITICAL FIX: Global variable to store the last generated report for chat context
LATEST_REPORT = {} 

# ----------------------------------------------------------------------
# --- UTILITY FUNCTIONS ---
# ----------------------------------------------------------------------

def calculate_risk(income: float, fixed: float, variable: float, debt: float, credit_score: float, dependents: int) -> dict:
    try:
        income = float(income)
        fixed = max(0.0, float(fixed))
        variable = max(0.0, float(variable))
        debt = max(0.0, float(debt))
        credit_score = float(credit_score)
        dependents = int(dependents)
    except Exception:
        return {"score": 100.0, "label": "🔴 High Risk: Invalid Input"}

    if income <= 0:
        return {"score": 100.0, "label": "🔴 High Risk: Income must be positive"}

    essentials = fixed + variable
    savings_ratio = max(-1.0, (income - essentials) / income)
    debt_ratio = debt / (income + 1e-9)

    credit_penalty = 0.0
    if credit_score < 580:
        credit_penalty = 15
    elif credit_score < 670:
        credit_penalty = 7
    elif credit_score < 740:
        credit_penalty = 3

    dependent_penalty = min(15, dependents * 3)
    # The 'raw' score composition is a simplified financial model
    raw = (1 - savings_ratio) * 40 + min(60, debt_ratio * 40) + credit_penalty + dependent_penalty
    score = max(0.0, min(100.0, raw))

    if score >= 70:
        label = "🔴 High Risk"
    elif score >= 40:
        label = "🟠 Medium Risk"
    else:
        label = "🟢 Low Risk"

    return {"score": round(score, 2), "label": label}

def emergency_fund_target(fixed: float, variable: float, dependents: int, months_buffer: int = 3):
    monthly_needed = fixed + variable
    # Increase buffer by 0.5 months per dependent
    buffer = months_buffer + (dependents * 0.5)
    return max(0.0, round(monthly_needed * buffer, 2)), int(buffer)

def recommend_budget_plans(income: float, fixed: float, variable: float):
    plan_50_30_20 = {
        "needs": round(income * 0.5, 2),
        "wants": round(income * 0.3, 2),
        "savings": round(income * 0.2, 2)
    }
    monthly_total = fixed + variable
    disposable = max(0.0, income - monthly_total)
    custom = {
        "essentials": round(fixed, 2),
        "variable": round(variable, 2),
        "disposable": round(disposable, 2),
        "suggest_savings": round(min(disposable, income * 0.2), 2)
    }
    return plan_50_30_20, custom

def debt_payoff_plan(debt: float, disposable: float):
    debt = max(0.0, debt)
    # Suggest dedicating 40% of disposable income to debt repayment
    disposable_for_debt = max(1.0, disposable * 0.4) 
    if debt == 0:
        return {"months": 0, "monthly_payment": 0.0, "note": "No debt detected. Focus on saving and investing."}
    
    monthly_payment = min(debt, disposable_for_debt)
    months = int(np.ceil(debt / monthly_payment)) if monthly_payment > 0 else "∞"
    
    note = f"Estimated {months} months paying ₹{round(monthly_payment,2)}/mo toward debt (using ~40% of disposable income)."
    return {"months": months, "monthly_payment": round(monthly_payment,2), "note": note}

def investment_allocation_by_risk(risk_label: str, age: int, experience: str):
    age = int(age)
    # Base allocation based on risk label
    if risk_label.startswith("🔴"):
        alloc = {"bonds": 70, "index_funds": 20, "crypto": 0, "cash": 10}
    elif risk_label.startswith("🟠"):
        alloc = {"bonds": 40, "index_funds": 40, "crypto": 5, "cash": 15}
    else: # Low Risk
        alloc = {"bonds": 20, "index_funds": 60, "crypto": 10, "cash": 10}
        
    # Adjustments based on age (younger = more aggressive)
    if age < 30:
        alloc["index_funds"] = min(90, alloc["index_funds"] + 10)
        alloc["bonds"] = max(0, alloc["bonds"] - 10)
        
    # Adjustments based on experience (less experienced = less speculative/volatile)
    if experience == "low":
        alloc["crypto"] = 0
        alloc["cash"] += 5
        
    # Rebalance to 100% if needed (due to max/min limits)
    total = sum(alloc.values())
    if total != 100:
        diff = 100 - total
        alloc["index_funds"] += diff # Distribute remainder to core asset
        
    return alloc

def personalize_prediction(user_history, income):
    # Expenses here should be fixed + variable
    user_data_for_ml = [{"income": e["income"], "expenses": e["fixed"] + e["variable"]} for e in user_history if "fixed" in e and "variable" in e]
    
    if len(user_data_for_ml) >= 2:
        try:
            # Predict *next month's expenses* based on *past income*
            X_train = np.array([e["income"] for e in user_data_for_ml[:-1]]).reshape(-1, 1)
            y_train = np.array([e["expenses"] for e in user_data_for_ml[1:]])
            personal_model = LinearRegression().fit(X_train, y_train)
            
            pred = float(personal_model.predict(np.array([[income]]))[0])
            return max(0.0, round(pred, 2))
        except Exception:
            pass
            
    # Fallback to the global trend model
    history_len = max(1, len(user_history))
    next_month_index = np.array([[6 + history_len]])
    return float(trend_model.predict(next_month_index)[0])

# ----------------------------------------------------------------------
# --- ROUTES ---
# ----------------------------------------------------------------------

@app.route("/")
def home():
    # This will now correctly find 'templates/index.html'
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # CRITICAL FIX: Reference the global report store
    global LATEST_REPORT
    payload = request.get_json() or {}
    user_id = str(payload.get("user_id", "demo_user"))
    
    # Input extraction and validation (using reasonable defaults)
    try:
        income = float(payload.get("income", 0))
        fixed = float(payload.get("fixed_expenses", 0))
        variable = float(payload.get("variable_expenses", 0))
        debt = float(payload.get("debt", 0))
        credit_score = float(payload.get("credit_score", 650))
        age = int(payload.get("age", 25))
        dependents = int(payload.get("dependents", 0))
        savings_goal = float(payload.get("savings_goal", 0))
        savings_target_months = int(payload.get("savings_target_months", 12))
        investment_experience = payload.get("investment_experience", "medium")
    except ValueError:
        return jsonify({"error": "All inputs must be valid numbers."}), 400

    # Data Store Update
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "income": income,
        "fixed": fixed,
        "variable": variable,
        "debt": debt,
        "credit_score": credit_score,
        "age": age,
        "dependents": dependents
    }
    USER_DATA.setdefault(user_id, []).append(entry)
    USER_DATA[user_id] = USER_DATA[user_id][-36:] # Keep last 36 entries

    # Analysis
    risk = calculate_risk(income, fixed, variable, debt, credit_score, dependents)
    ef_target, ef_months = emergency_fund_target(fixed, variable, dependents, months_buffer=3)
    plan_50_30_20, custom_plan = recommend_budget_plans(income, fixed, variable)
    disposable = max(0.0, income - (fixed + variable))
    debt_plan = debt_payoff_plan(debt, disposable)
    invest_alloc = investment_allocation_by_risk(risk["label"], age, investment_experience)
    predicted_expense = personalize_prediction(USER_DATA[user_id], income)

    if savings_goal > 0 and savings_target_months > 0:
        monthly_needed = savings_goal / savings_target_months
        # Suggest dedicating 50% of disposable income to savings goal, if needed
        suggestion = min(monthly_needed, max(0.0, disposable * 0.5))
        savings_plan = {"monthly_needed": round(monthly_needed,2), "suggested_monthly": round(suggestion,2), "months_target": savings_target_months}
    else:
        savings_plan = {"message": "No savings goal provided. Recommended monthly savings are calculated in the Custom Budget.", "suggested_monthly": round(min(disposable * 0.2, income * 0.2),2)}

    advice = []
    if credit_score < 580:
        advice.append("Credit: Your score is poor — focus on on-time payments and lowering utilization to under 30%.")
    elif credit_score < 670:
        advice.append("Credit: Your score is fair — prioritize debt reduction and dispute any errors to improve it.")
    else:
        advice.append("Credit: Your score is good — maintain on-time payments and prudently manage new credit.")

    if disposable <= 0:
        advice.append("Budget: Your income doesn't cover essentials — immediately cut variable costs or seek to increase income.")
    else:
        advice.append(f"Budget: Maintain a positive disposable income of ₹{round(disposable,2)} and automate savings.")

    advice.append(f"Savings: Emergency fund target: ₹{ef_target} (~{ef_months} months of essentials).")
    advice.append(f"Debt: {debt_plan['note']}")

    # --- Resources for Frontend ---
    resources = [
        {"title":"Khan Academy - Personal Finance", "url":"https://www.khanacademy.org/college-careers-more/personal-finance"},
        {"title":"Investopedia - Investing Basics", "url":"https://www.investopedia.com/investing-4427685"},
        {"title":"Investopedia - How to Start Investing", "url":"https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title":"YouTube: Investing for Beginners (example)", "url":"https://www.youtube.com/watch?v=2KgH0UpiRiw"},
        {"title":"Beginner books: 'The Intelligent Investor', 'The Little Book of Common Sense Investing'", "url":"https://www.investopedia.com/articles/pf/08/personal-finance-books.asp"}
    ]

    history = [
        {"t": e["timestamp"], "income": e["income"], "expenses": e["fixed"] + e["variable"], "debt": e["debt"]}
        for e in USER_DATA[user_id]
    ]

    result = {
        "predicted_expense": round(predicted_expense,2),
        "risk": risk,
        "emergency_fund": {"target": ef_target, "months": ef_months},
        "budget_50_30_20": plan_50_30_20,
        "custom_budget": custom_plan,
        "disposable_income": round(disposable,2),
        "debt_plan": debt_plan,
        "investment_allocation": invest_alloc,
        "savings_plan": savings_plan,
        "advice": advice,
        "history": history,
        "user_id": user_id, 
        "resources": resources
    }
    
    LATEST_REPORT[user_id] = result # Store for chat context
    
    return jsonify(result)

# CRITICAL FIX: Add the new /chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    """
    Endpoint for the conversational AI assistant.
    This uses a sophisticated keyword/contextual placeholder.
    """
    payload = request.get_json() or {}
    user_id = str(payload.get("user_id", "demo_user"))
    user_question = payload.get("question", "").strip()
    
    report_data = LATEST_REPORT.get(user_id)
    if not report_data or not user_question:
        return jsonify({"response": "Please run the financial analysis first to give the assistant context."})

    # --- LLM API INTEGRATION PLACEHOLDER (Current logic for hackathon) ---
    lower_q = user_question.lower()
    
    if "reduce expense" in lower_q or "cut cost" in lower_q:
        fixed = report_data["custom_budget"]["essentials"]
        variable = report_data["custom_budget"]["variable"]
        suggestion = f"The best way to cut costs is by focusing on your Variable Expenses. Your current variable spending is ₹{variable}. Review non-essential spending like dining out or subscriptions. Your Fixed costs (₹{fixed}) are harder to change, but can be reviewed annually."
    
    elif "investment" in lower_q or "investing" in lower_q:
        alloc = report_data["investment_allocation"]
        risk_label = report_data["risk"]["label"]
        suggestion = f"Your current risk profile is {risk_label}. Based on this, your suggested allocation is: Index Funds ({alloc.get('index_funds',0)}%), Bonds ({alloc.get('bonds',0)}%), and Cash ({alloc.get('cash',0)}%). Focus on long-term, low-cost index funds."
    
    elif "debt" in lower_q:
        debt_note = report_data["debt_plan"]["note"]
        suggestion = f"Your debt payoff plan is summarized as: '{debt_note}'. Focus on high-interest debt (Avalanche method) to save the most money over time, or the smallest balances (Snowball method) for motivation."
        
    elif "credit" in lower_q:
        score = report_data["credit_score"]
        if score < 670:
            suggestion = f"Your credit score ({score}) needs improvement. Key steps: Pay all bills 100% on time, keep credit card balances below 30% of the limit, and avoid closing old accounts."
        else:
            suggestion = f"Your credit score ({score}) is strong. Continue making on-time payments and prudently manage new credit. Monitoring your score once a year is advised."
    
    elif "budget" in lower_q or "50/30/20" in lower_q:
        needs = report_data["budget_50_30_20"]["needs"]
        wants = report_data["budget_50_30_20"]["wants"]
        savings = report_data["budget_50_30_20"]["savings"]
        suggestion = f"The 50/30/20 rule suggests: Needs (₹{needs}), Wants (₹{wants}), and Savings/Debt (₹{savings}). Compare this to your actual monthly spending to identify where you are over-allocating."
        
    else:
        suggestion = "I'm the FINESIGHT Assistant. I provide context-aware answers based on your financial report. Try asking: 'How to save for my goal?' or 'Explain the risk score.'"

    return jsonify({"response": suggestion})


@app.route("/history/<user_id>")
def history_route(user_id):
    return jsonify({"history": USER_DATA.get(str(user_id), [])})

@app.route("/resources")
def resources_route():
    # return same static curated resources
    res = [
        {"title":"Khan Academy - Personal Finance","url":"https://www.khanacademy.org/college-careers-more/personal-finance"},
        {"title":"Investopedia - Investing Basics","url":"https://www.investopedia.com/investing-4427685"},
        {"title":"Investopedia - How to Start Investing","url":"https://www.investopedia.com/articles/basics/06/invest1000.asp"},
        {"title":"YouTube - Investing for Beginners (example)","url":"https://www.youtube.com/watch?v=2KgH0UpiRiw"},
        {"title":"Book recommendations: The Intelligent Investor; The Little Book of Common Sense Investing","url":"https://www.investopedia.com/articles/pf/08/personal-finance-books.asp"}
    ]
    return jsonify({"resources": res})

if __name__ == "__main__":
    app.run(debug=True, port=5000)