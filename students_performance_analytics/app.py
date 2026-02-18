import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ==============================================================================
# CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="Academic Performance Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .alert-box {
        background-color: #ffe6e6;
        border-left: 5px solid #ff4d4d;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# DATABASE MANAGEMENT CLASS
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_name="academic_tracker.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create Students Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                enrollment_date TEXT
            )
        ''')
        
        # Create Assessments Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT NOT NULL,
                marks REAL NOT NULL,
                assessment_type TEXT,
                date_recorded TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        ''')
        conn.commit()
        conn.close()

    def add_student(self, roll_number, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO students (roll_number, name, enrollment_date) VALUES (?, ?, ?)",
                           (roll_number, name, date))
            conn.commit()
            return True, "Student added successfully."
        except sqlite3.IntegrityError:
            return False, "Error: Roll Number already exists."
        finally:
            conn.close()

    def add_assessment(self, roll_number, subject, marks, type_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get Student ID
            cursor.execute("SELECT id FROM students WHERE roll_number = ?", (roll_number,))
            result = cursor.fetchone()
            if not result:
                return False, "Error: Student Roll Number not found."
            
            student_id = result[0]
            date = datetime.now().strftime("%Y-%m-%d")
            
            cursor.execute('''
                INSERT INTO assessments (student_id, subject, marks, assessment_type, date_recorded)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, subject, marks, type_name, date))
            conn.commit()
            return True, "Assessment recorded successfully."
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_all_data(self):
        conn = self.get_connection()
        query = '''
            SELECT s.roll_number, s.name, a.subject, a.marks, a.assessment_type, a.date_recorded
            FROM assessments a
            JOIN students s ON a.student_id = s.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

# ==============================================================================
# ANALYTICS ENGINE
# ==============================================================================
class AnalyticsEngine:
    def __init__(self, df):
        self.df = df

    def get_student_summary(self):
        if self.df.empty:
            return pd.DataFrame()
        summary = self.df.groupby(['roll_number', 'name']).agg(
            total_assessments=('subject', 'count'),
            average_marks=('marks', 'mean'),
            min_marks=('marks', 'min'),
            max_marks=('marks', 'max')
        ).reset_index()
        return summary

    def identify_at_risk_students(self, threshold=50.0):
        if self.df.empty:
            return pd.DataFrame()
        summary = self.get_student_summary()
        at_risk = summary[summary['average_marks'] < threshold].copy()
        at_risk['status'] = 'Needs Attention'
        return at_risk.sort_values(by='average_marks', ascending=True)

    def get_subject_performance(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df.groupby('subject')['marks'].mean().reset_index(name='average_marks')

# ==============================================================================
# USER INTERFACE (STREAMLIT)
# ==============================================================================
def main():
    db = DatabaseManager()
    
    # Sidebar Navigation
    st.sidebar.title("🎓 Academic Tracker")
    st.sidebar.markdown("---")
    menu = ["Dashboard", "Data Entry", "At-Risk Report", "Raw Data"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    st.sidebar.markdown("---")
    st.sidebar.info("System Version: 2.0.1\nDepartment of Computer Science")

    # ---------------- DASHBOARD PAGE ----------------
    if choice == "Dashboard":
        st.title("📊 Performance Dashboard")
        st.markdown("Overview of academic performance across all subjects.")
        
        df = db.get_all_data()
        
        if df.empty:
            st.warning("No data available. Please enter data in the 'Data Entry' section.")
        else:
            engine = AnalyticsEngine(df)
            summary = engine.get_student_summary()
            subject_perf = engine.get_subject_performance()
            
            # KPI Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", summary['roll_number'].nunique())
            with col2:
                st.metric("Total Assessments", len(df))
            with col3:
                avg_overall = round(df['marks'].mean(), 2)
                st.metric("Overall Average", avg_overall)
            with col4:
                at_risk_count = len(engine.identify_at_risk_students())
                st.metric("At-Risk Students", at_risk_count, delta_color="inverse")

            st.markdown("---")
            
            # Charts
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Average Marks by Subject")
                if not subject_perf.empty:
                    fig_sub = px.bar(subject_perf, x='subject', y='average_marks', 
                                     color='average_marks', color_continuous_scale='Viridis')
                    st.plotly_chart(fig_sub, use_container_width=True)
                else:
                    st.info("No subject data.")
            
            with c2:
                st.subheader("Student Performance Distribution")
                if not summary.empty:
                    fig_hist = px.histogram(summary, x='average_marks', nbins=20, 
                                            title="Distribution of Student Averages")
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No student data.")

    # ---------------- DATA ENTRY PAGE ----------------
    elif choice == "Data Entry":
        st.title("📝 Data Entry")
        
        tab1, tab2 = st.tabs(["Add New Student", "Record Assessment"])
        
        with tab1:
            st.subheader("Register Student")
            with st.form("student_form"):
                s_roll = st.text_input("Roll Number")
                s_name = st.text_input("Full Name")
                submitted_s = st.form_submit_button("Register Student")
                
                if submitted_s:
                    if s_roll and s_name:
                        success, msg = db.add_student(s_roll, s_name)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill all fields.")
        
        with tab2:
            st.subheader("Enter Marks")
            with st.form("mark_form"):
                m_roll = st.text_input("Student Roll Number")
                m_subject = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "Computer Science", "English"])
                m_marks = st.number_input("Marks Obtained", min_value=0.0, max_value=100.0, step=0.5)
                m_type = st.selectbox("Assessment Type", ["Internal Test 1", "Internal Test 2", "Mid Term", "Assignment"])
                submitted_m = st.form_submit_button("Submit Marks")
                
                if submitted_m:
                    if m_roll and m_subject:
                        success, msg = db.add_assessment(m_roll, m_subject, m_marks, m_type)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill all fields.")

    # ---------------- AT-RISK REPORT PAGE ----------------
    elif choice == "At-Risk Report":
        st.title("⚠️ Student Attention Report")
        st.markdown("Students identified with an average score below **50%**.")
        
        df = db.get_all_data()
        if df.empty:
            st.warning("No data available to analyze.")
        else:
            engine = AnalyticsEngine(df)
            at_risk_df = engine.identify_at_risk_students(threshold=50.0)
            
            if at_risk_df.empty:
                st.success("🎉 Great! No students are currently below the threshold.")
            else:
                st.error(f"Found {len(at_risk_df)} students requiring intervention.")
                
                # Highlight the table
                st.dataframe(at_risk_df.style.format({"average_marks": "{:.2f}"}).background_gradient(subset=['average_marks'], cmap='Reds'), use_container_width=True)
                
                # Download Option
                csv = at_risk_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Intervention List (CSV)",
                    csv,
                    "at_risk_students.csv",
                    "text/csv",
                    key='download-csv'
                )

    # ---------------- RAW DATA PAGE ----------------
    elif choice == "Raw Data":
        st.title("🗄️ Database Records")
        df = db.get_all_data()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Full Data (CSV)",
                csv,
                "full_academic_data.csv",
                "text/csv",
                key='download-full-csv'
            )
        else:
            st.info("Database is empty.")

if __name__ == '__main__':
    main()