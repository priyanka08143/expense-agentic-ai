import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Agentic Expense AI", page_icon="💸", layout="wide")

# ---------------- UI STYLE ---------------- #
st.markdown("""
<style>
.main { background-color:#0f1117; }
.card {
    background:#1c1f26;
    padding:20px;
    border-radius:15px;
    box-shadow:0 0 10px rgba(0,0,0,0.4);
    margin-bottom:15px;
    color:white;
}
.title { font-size:34px; font-weight:700; color:white; }
.subtitle { font-size:18px; color:#b0b0b0; }
.metric {
    background:#1c1f26;
    padding:15px;
    border-radius:12px;
    text-align:center;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- AGENTS ---------------- #
class InputAgent:
    def collect_manual(self, date, amount, category, desc):
        return {"date": date, "amount": amount, "category": category, "description": desc}

class CleaningAgent:
    def clean(self, df):
        df = df.dropna()
        df["amount"] = df["amount"].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")
        return df

class AnalysisAgent:
    def analyze(self, df):
        total = df["amount"].sum()
        by_cat = df.groupby("category")["amount"].sum().reset_index()
        by_month = df.groupby("month")["amount"].sum().reset_index()
        return total, by_cat, by_month

class DecisionAgent:
    def detect_overspend(self, df, limit=3000):
        alerts=[]
        for c,g in df.groupby("category"):
            if g["amount"].sum()>limit:
                alerts.append(f"⚠️ High spending in {c}: ₹{g['amount'].sum()}")
        return alerts

class RecommendationAgent:
    def recommend(self,total):
        if total>15000:
            return "High spending pattern. Reduce non-essential expenses."
        elif total>8000:
            return "Moderate spending. Optimize discretionary costs."
        else:
            return "Excellent financial discipline. Good savings pattern."

# ---------------- INIT ---------------- #
input_agent = InputAgent()
cleaning_agent = CleaningAgent()
analysis_agent = AnalysisAgent()
decision_agent = DecisionAgent()
recommendation_agent = RecommendationAgent()

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["date","amount","category","description"])

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("🤖 Agentic AI")
menu = st.sidebar.radio("Navigation", ["Dashboard","Add Expense","Manage Data","Reports"])

# ---------------- HEADER ---------------- #
st.markdown('<div class="title">💸 Agentic Personal Expense AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Autonomous Financial Intelligence System</div>', unsafe_allow_html=True)
st.divider()

# ---------------- ADD EXPENSE ---------------- #
if menu=="Add Expense":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("➕ Add Expense")

    with st.form("add", clear_on_submit=True):
        col1,col2 = st.columns(2)
        with col1: date = st.date_input("Date", datetime.today())
        with col2: amount = st.number_input("Amount", min_value=0.0, value=0.0)

        category = st.selectbox("Category",["Food","Travel","Shopping","Entertainment","Utilities","Other"])
        custom=""
        if category=="Other":
            custom = st.text_input("Custom Category")

        desc = st.text_input("Description")
        submit = st.form_submit_button("Save Expense")

    if submit and amount>0:
        final_cat = custom if category=="Other" and custom!="" else category
        data = input_agent.collect_manual(date,amount,final_cat,desc)
        st.session_state.data = pd.concat([st.session_state.data,pd.DataFrame([data])],ignore_index=True)
        st.success("✅ Expense Added")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- MANAGE DATA ---------------- #
elif menu=="Manage Data":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📂 Data Management")

    file = st.file_uploader("Upload CSV",type=["csv"])
    if file:
        df=pd.read_csv(file)
        st.session_state.data=pd.concat([st.session_state.data,df],ignore_index=True)
        st.success("CSV Uploaded")

    search = st.text_input("🔍 Search")

    if not st.session_state.data.empty:
        df = st.session_state.data.reset_index()

        if search:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search,case=False).any(),axis=1)]

        st.markdown("### 🧾 Expense Records")

        for i, row in df.iterrows():
            col1,col2,col3,col4,col5,col6 = st.columns([2,2,2,3,1,1])

            col1.write(pd.to_datetime(row["date"]).date())
            col2.write(f"₹ {row['amount']}")
            col3.write(row["category"])
            col4.write(row["description"])

            if col5.button("✏️", key=f"edit_{i}"):
                st.session_state.edit_index = row["index"]

            if col6.button("🗑️", key=f"del_{i}"):
                st.session_state.data = st.session_state.data.drop(row["index"]).reset_index(drop=True)
                st.success("Deleted successfully")
                st.experimental_rerun()

    # -------- EDIT MODE -------- #
    if st.session_state.edit_index is not None:
        st.divider()
        st.subheader("✏️ Edit Expense")

        row = st.session_state.data.loc[st.session_state.edit_index]

        with st.form("edit_form"):
            date = st.date_input("Date", pd.to_datetime(row["date"]))
            amount = st.number_input("Amount", min_value=0.0, value=float(row["amount"]))
            category = st.text_input("Category", row["category"])
            desc = st.text_input("Description", row["description"])

            colA,colB = st.columns(2)
            with colA:
                update = st.form_submit_button("✅ Update")
            with colB:
                cancel = st.form_submit_button("❌ Cancel")

        if update:
            st.session_state.data.loc[st.session_state.edit_index] = [date, amount, category, desc]
            st.session_state.edit_index = None
            st.success("Updated Successfully")
            st.experimental_rerun()

        if cancel:
            st.session_state.edit_index = None
            st.experimental_rerun()

    if not st.session_state.data.empty:
        csv = st.session_state.data.to_csv(index=False).encode()
        st.download_button("⬇️ Export CSV",csv,"expenses.csv","text/csv")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- DASHBOARD ---------------- #
elif menu=="Dashboard":
    if not st.session_state.data.empty:
        df=cleaning_agent.clean(st.session_state.data)

        total,by_cat,by_month = analysis_agent.analyze(df)
        alerts = decision_agent.detect_overspend(df)
        rec = recommendation_agent.recommend(total)

        col1,col2,col3 = st.columns(3)
        with col1: st.markdown(f'<div class="metric">💰<br>Total<br>₹ {total}</div>',unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric">🧾<br>Entries<br>{len(df)}</div>',unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric">📊<br>Categories<br>{df["category"].nunique()}</div>',unsafe_allow_html=True)

        st.divider()

        colA,colB = st.columns(2)
        with colA:
            st.subheader("Category Spending")
            fig,ax=plt.subplots(figsize=(6,4))
            ax.bar(by_cat["category"],by_cat["amount"])
            plt.xticks(rotation=30)
            st.pyplot(fig)

        with colB:
            st.subheader("Monthly Spending")
            fig2,ax2=plt.subplots(figsize=(6,4))
            ax2.plot(by_month["month"],by_month["amount"],marker="o")
            plt.xticks(rotation=45)
            st.pyplot(fig2)

        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.subheader("🤖 AI Insights")
        for a in alerts: st.error(a)
        st.info(rec)
        st.markdown('</div>',unsafe_allow_html=True)

    else:
        st.info("No data available")

# ---------------- REPORTS ---------------- #
elif menu=="Reports":
    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.subheader("📑 AI Financial Report")

    if not st.session_state.data.empty:
        df=cleaning_agent.clean(st.session_state.data)
        total,by_cat,by_month = analysis_agent.analyze(df)

        st.write("### Summary")
        st.write(f"Total Spent: ₹ {total}")
        st.write(f"Total Transactions: {len(df)}")
        st.write(f"Top Category: {by_cat.sort_values('amount',ascending=False).iloc[0]['category']}")

        st.write("### Category Breakdown")
        st.dataframe(by_cat,use_container_width=True)

        st.write("### Monthly Breakdown")
        st.dataframe(by_month,use_container_width=True)

    else:
        st.info("No data to generate report")

    st.markdown('</div>',unsafe_allow_html=True)