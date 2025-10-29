import streamlit as st
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# -------------------------------
# 💠 AXION — Decision Intelligence Module
# -------------------------------

st.set_page_config(page_title="AXION | Genesis 5.0", layout="wide")

# --- Styling (Light Mode + Dark Sidebar) ---
st.markdown("""
<style>
/* App background */
body { background-color: #ffffff; }
.main { background-color: #ffffff; }
.stApp {
    background-color: #ffffff;
    color: #000000;
}

/* Text colors (main area) */
h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stCaption {
    color: #000000 !important;
}

/* ✅ Sidebar styling: dark navy with white text */
section[data-testid="stSidebar"] {
    background-color: #0b1a33 !important;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Metrics */
div[data-testid="stMetric"],
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: black !important;
}

/* Alerts */
div[data-testid="stInfo"] div,
div[data-testid="stSuccess"] div,
div[data-testid="stError"] div {
    color: black !important;
}

/* ✅ Custom dark-blue warning box */
div[data-testid="stWarning"] {
    background-color: #0b1a33 !important;
    border: 1px solid #0b1a33 !important;
    border-radius: 10px !important;
}
div[data-testid="stWarning"] div p,
div[data-testid="stWarning"] div {
    color: white !important;
}

/* Buttons (blue theme) */
.stButton>button {
    background-color: #007bff;
    color: white;
    border-radius: 10px;
    border: none;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #0059b3;
}

/* Sliders (blue accents) */
input[type=range]::-webkit-slider-thumb,
input[type=range]::-moz-range-thumb,
input[type=range]::-ms-thumb {
    background: #007bff;
}
.stSlider > div > div > div:nth-child(1) > div {
    background: #007bff;
}
.stSlider>div>div>div {
    background-color: #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("💠 AXION — Decision & Ethical Intelligence")
st.write("AI-assisted rational and ethical decision-making engine integrated within **Genesis 5.0**.")

# --- Sidebar Inputs ---
st.sidebar.header("⚙️ Decision Parameters")

# User input parameters
logic_score = st.sidebar.slider("Logical Weight", 0.0, 1.0, 0.6)
emotion_score = st.sidebar.slider("Emotional Influence", 0.0, 1.0, 0.4)
risk_tolerance = st.sidebar.slider("Risk Tolerance", 0.0, 1.0, 0.5)
ethical_importance = st.sidebar.slider("Ethical Priority", 0.0, 1.0, 0.8)
context_type = st.sidebar.selectbox("Context", ["Financial", "Personal", "Professional", "Moral Dilemma"])

# --- Core ML Model ---
st.subheader("🧠 Decision Optimization Engine")

# Generate synthetic training data
np.random.seed(42)
data_size = 200
X = np.random.rand(data_size, 4)
y = (0.4*X[:,0] + 0.3*X[:,1] + 0.2*X[:,2] + 0.1*X[:,3]) + np.random.normal(0, 0.02, data_size)

# Train a lightweight Random Forest
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Predict decision efficiency
user_input = np.array([[logic_score, emotion_score, risk_tolerance, ethical_importance]])
efficiency_score = model.predict(user_input)[0]

# Normalize for readability
scaler = MinMaxScaler((0, 100))
scaled_eff = scaler.fit_transform(np.array(y).reshape(-1, 1))
final_score = np.interp(efficiency_score, (np.min(y), np.max(y)), (0, 100))

# --- Display results ---
col1, col2 = st.columns(2)

with col1:
    st.metric("Decision Rationality Index", f"{final_score:.2f}/100")
    if final_score > 75:
        st.success("High Rational Alignment ✅")
    elif final_score > 50:
        st.warning("Moderate Alignment ⚖️")
    else:
        st.error("Low Rational Alignment ❌")

with col2:
    st.write("### 🧭 Ethical Evaluation")
    ethical_assessment = (
        "Ethically Balanced" if ethical_importance >= 0.7 else
        "Needs Moral Review" if ethical_importance >= 0.4 else
        "Ethically Risky"
    )
    st.info(f"Result: **{ethical_assessment}**")

# --- Visualization ---
st.markdown("### 📊 Decision Feature Comparison")

fig, ax = plt.subplots(figsize=(6, 3))
labels = ["Logic", "Emotion", "Risk", "Ethics"]
values = [logic_score, emotion_score, risk_tolerance, ethical_importance]
ax.bar(labels, values, color="#007bff", alpha=0.85)
ax.set_ylim(0, 1)
ax.set_ylabel("Score (0–1)", color='black')
ax.set_title("Decision Component Weights", color='black')
ax.tick_params(axis='x', colors='black')
ax.tick_params(axis='y', colors='black')
fig.patch.set_facecolor('#ffffff')
ax.set_facecolor('#ffffff')
st.pyplot(fig)

# --- Insight Generator ---
st.markdown("### 🧩 Insight Generator")

if final_score > 75:
    insight = f"AXION recommends proceeding confidently with this **{context_type.lower()}** decision — high rational and ethical stability detected."
elif final_score > 50:
    insight = f"AXION suggests reviewing your **emotional and ethical balance** before confirming this {context_type.lower()} decision."
else:
    insight = f"AXION advises **rethinking** the {context_type.lower()} decision — logic-emotion conflict detected."

st.write(f"🔍 **Insight:** {insight}")

# --- Cross-Link Simulation ---
st.divider()
st.write("### 🔗 Cross-Link Simulation (Integration Ready)")
st.caption("This section allows communication with other Genesis modules (AURA, SYNAPSE, FINESIGHT).")

if st.button("Simulate Cross-Link → SYNAPSE"):
    st.info("Synapse link activated. Adjusting decision based on behavioral and emotional metrics...")

if st.button("Simulate Cross-Link → FINESIGHT"):
    st.info("Finesight link activated. Financial risk parameters updated for ethical coherence...")

st.success("✅ AXION module initialized successfully within Genesis 5.0.")