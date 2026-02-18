import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Startup Resource Allocator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #F3F4F6; }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 5px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #2563EB;
    }
    h1, h2, h3 { color: #1F2937; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# DATABASE MANAGEMENT
# ==============================================================================
class DBManager:
    def __init__(self, db_name="startup_resources.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                effort_hours REAL NOT NULL,
                impact_score INTEGER NOT NULL,
                urgency_score INTEGER NOT NULL,
                strategic_score INTEGER NOT NULL,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sprint_name TEXT UNIQUE NOT NULL,
                total_capacity_hours REAL NOT NULL,
                start_date TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_request(self, title, category, effort, impact, urgency, strategic):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute('''
                INSERT INTO requests (title, category, effort_hours, impact_score, urgency_score, strategic_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, category, effort, impact, urgency, strategic, date))
            conn.commit()
            return True, "Request added successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def set_capacity(self, sprint_name, capacity, start_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO resources (sprint_name, total_capacity_hours, start_date)
                VALUES (?, ?, ?)
            ''', (sprint_name, capacity, start_date))
            conn.commit()
            return True, "Capacity updated."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_requests(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM requests", conn)
        conn.close()
        return df

    def get_capacity(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM resources ORDER BY id DESC LIMIT 1", conn)
        conn.close()
        return df

# ==============================================================================
# ALLOCATION ENGINE
# ==============================================================================
class AllocationEngine:
    def __init__(self, requests_df, capacity_hours):
        self.requests_df = requests_df
        self.capacity_hours = capacity_hours
        self.processed_df = None

    def calculate_priority_score(self):
        df = self.requests_df.copy()
        if df.empty:
            return df
            
        df['weighted_value'] = (df['impact_score'] * 0.4) + (df['urgency_score'] * 0.3) + (df['strategic_score'] * 0.3)
        df['priority_score'] = df['weighted_value'] / (df['effort_hours'] + 0.1)
        df['priority_score'] = df['priority_score'].round(2)
        self.processed_df = df.sort_values(by='priority_score', ascending=False).reset_index(drop=True)
        return self.processed_df

    def allocate_resources(self):
        if self.processed_df is None or self.processed_df.empty:
            return pd.DataFrame()
            
        df = self.processed_df.copy()
        df['status'] = 'Backlog'
        df['cumulative_effort'] = df['effort_hours'].cumsum()
        df.loc[df['cumulative_effort'] <= self.capacity_hours, 'status'] = 'Approved for Sprint'
        return df

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================
def main():
    db = DBManager()
    
    st.sidebar.title("🚀 Resource Allocator")
    st.sidebar.markdown("Data-Driven Decision Support")
    st.sidebar.markdown("---")
    
    menu = ["Dashboard", "New Request", "Capacity Planning", "Backlog Analysis"]
    choice = st.sidebar.radio("Navigation", menu)
    
    # ---------------- DASHBOARD ----------------
    if choice == "Dashboard":
        st.title("📊 Resource Allocation Dashboard")
        
        req_df = db.get_requests()
        cap_df = db.get_capacity()
        
        capacity = cap_df['total_capacity_hours'].values[0] if not cap_df.empty else 0
        sprint_name = cap_df['sprint_name'].values[0] if not cap_df.empty else "No Sprint Defined"
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Requests", len(req_df))
        with c2:
            st.metric("Sprint Capacity", f"{capacity} hrs")
        with c3:
            total_effort = req_df['effort_hours'].sum() if not req_df.empty else 0
            st.metric("Total Demand", f"{total_effort} hrs")
        with c4:
            coverage = (capacity / total_effort * 100) if total_effort > 0 else 0
            st.metric("Capacity Coverage", f"{coverage:.1f}%")

        st.markdown("---")
        
        if not req_df.empty:
            engine = AllocationEngine(req_df, capacity)
            scored_df = engine.calculate_priority_score()
            allocated_df = engine.allocate_resources()
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sprint Allocation Status")
                status_counts = allocated_df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig_pie = px.pie(status_counts, values='Count', names='Status')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Demand by Category")
                cat_counts = req_df['category'].value_counts().reset_index()
                cat_counts.columns = ['Category', 'Count']
                fig_bar = px.bar(cat_counts, x='Category', y='Count')
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("🏆 Prioritized Execution List")
            display_df = allocated_df[['title', 'category', 'effort_hours', 'priority_score', 'status']].copy()
            st.dataframe(display_df, use_container_width=True)
            
        else:
            st.info("No requests found. Please add requests in 'New Request' tab.")

    # ---------------- NEW REQUEST ----------------
    elif choice == "New Request":
        st.title("📝 Submit New Request")
        
        with st.form("request_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Task Title")
                category = st.selectbox("Category", ["Feature Development", "Bug Fix", "Technical Debt", "Customer Request"])
                effort = st.number_input("Estimated Effort (Hours)", min_value=1.0, step=0.5)
            
            with col2:
                st.markdown("**Scoring (1-10)**")
                impact = st.slider("Business Impact", 1, 10, 5)
                urgency = st.slider("Urgency", 1, 10, 5)
                strategic = st.slider("Strategic Alignment", 1, 10, 5)
            
            submitted = st.form_submit_button("Submit Request")
            
            if submitted:
                if title:
                    success, msg = db.add_request(title, category, effort, impact, urgency, strategic)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Please enter a task title.")

    # ---------------- CAPACITY PLANNING ----------------
    elif choice == "Capacity Planning":
        st.title("⚙️ Sprint Capacity Planning")
        
        curr_cap = db.get_capacity()
        current_sprint = curr_cap['sprint_name'].values[0] if not curr_cap.empty else ""
        current_hours = curr_cap['total_capacity_hours'].values[0] if not curr_cap.empty else 0
        
        with st.form("capacity_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sprint_name = st.text_input("Sprint Name", value=current_sprint or f"Sprint {datetime.now().strftime('%W')}")
            with c2:
                hours = st.number_input("Total Available Hours", min_value=1.0, value=current_hours or 40.0)
            with c3:
                start_date = st.date_input("Start Date", value=datetime.now())
            
            submitted = st.form_submit_button("Update Capacity")
            
            if submitted:
                success, msg = db.set_capacity(sprint_name, hours, start_date)
                if success:
                    st.success("Capacity constraints updated.")
                else:
                    st.error(msg)

    # ---------------- BACKLOG ANALYSIS ----------------
    elif choice == "Backlog Analysis":
        st.title("🔍 Backlog & Trade-off Analysis")
        
        req_df = db.get_requests()
        cap_df = db.get_capacity()
        capacity = cap_df['total_capacity_hours'].values[0] if not cap_df.empty else 40
        
        if req_df.empty:
            st.warning("⚠️ No data available. Please add requests first.")
            st.info("💡 Go to 'New Request' tab to add tasks.")
        else:
            engine = AllocationEngine(req_df, capacity)
            df = engine.calculate_priority_score()
            
            # Scatter Plot
            st.subheader("Effort vs. Value Matrix")
            fig_scatter = px.scatter(df, x='effort_hours', y='weighted_value', 
                                     size='priority_score', color='category',
                                     hover_name='title',
                                     labels={'effort_hours': 'Effort (Hours)', 
                                             'weighted_value': 'Weighted Value'})
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # ========== QUADRANT ANALYSIS ==========
            st.subheader("📊 Quadrant Analysis")
            
            median_effort = df['effort_hours'].median()
            median_value = df['weighted_value'].median()
            
            def assign_quadrant(row):
                if row['effort_hours'] <= median_effort and row['weighted_value'] > median_value:
                    return "Quick Wins"
                elif row['effort_hours'] > median_effort and row['weighted_value'] > median_value:
                    return "Major Projects"
                elif row['effort_hours'] <= median_effort and row['weighted_value'] <= median_value:
                    return "Fill-ins"
                else:
                    return "Time Wasters"
            
            df['quadrant'] = df.apply(assign_quadrant, axis=1)
            
            q1, q2, q3, q4 = st.columns(4)
            
            quick_wins = df[df['quadrant'] == "Quick Wins"]
            major_projects = df[df['quadrant'] == "Major Projects"]
            fill_ins = df[df['quadrant'] == "Fill-ins"]
            time_wasters = df[df['quadrant'] == "Time Wasters"]
            
            with q1:
                st.metric("🎯 Quick Wins", f"{len(quick_wins)} tasks")
            with q2:
                st.metric("🚀 Major Projects", f"{len(major_projects)} tasks")
            with q3:
                st.metric("📝 Fill-ins", f"{len(fill_ins)} tasks")
            with q4:
                st.metric("⚠️ Time Wasters", f"{len(time_wasters)} tasks")
            
            st.markdown("---")
            st.markdown("### Quadrant Breakdown")
            
            quadrant_data = []
            
            if not quick_wins.empty:
                for _, row in quick_wins.iterrows():
                    quadrant_data.append({
                        "Task": row['title'],
                        "Quadrant": "🎯 Quick Wins",
                        "Effort": f"{row['effort_hours']}h",
                        "Value": f"{row['weighted_value']:.2f}",
                        "Recommendation": "✅ Do First"
                    })
            
            if not major_projects.empty:
                for _, row in major_projects.iterrows():
                    quadrant_data.append({
                        "Task": row['title'],
                        "Quadrant": "🚀 Major Projects",
                        "Effort": f"{row['effort_hours']}h",
                        "Value": f"{row['weighted_value']:.2f}",
                        "Recommendation": "📅 Schedule Carefully"
                    })
            
            if not fill_ins.empty:
                for _, row in fill_ins.iterrows():
                    quadrant_data.append({
                        "Task": row['title'],
                        "Quadrant": "📝 Fill-ins",
                        "Effort": f"{row['effort_hours']}h",
                        "Value": f"{row['weighted_value']:.2f}",
                        "Recommendation": "⏳ Do If Time Permits"
                    })
            
            if not time_wasters.empty:
                for _, row in time_wasters.iterrows():
                    quadrant_data.append({
                        "Task": row['title'],
                        "Quadrant": "⚠️ Time Wasters",
                        "Effort": f"{row['effort_hours']}h",
                        "Value": f"{row['weighted_value']:.2f}",
                        "Recommendation": "❌ Avoid/Defer"
                    })
            
            # FIXED: Complete condition check
            if len(quadrant_data) > 0:
                quadrant_df = pd.DataFrame(quadrant_data)
                st.dataframe(quadrant_df, use_container_width=True)
            else:
                st.info("No tasks to categorize.")
            
            st.markdown("---")
            st.subheader("Detailed Priority Breakdown")
            st.dataframe(df[['title', 'category', 'effort_hours', 'impact_score', 
                            'urgency_score', 'strategic_score', 'priority_score']], 
                        use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Priority Report", csv, 
                             "priority_report.csv", "text/csv")

if __name__ == '__main__':
    main()