import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import time
from database import create_tables, get_connection

# ---------- Setup ----------
st.set_page_config(page_title="Task Manager", layout="wide")
create_tables()
conn = get_connection()
cursor = conn.cursor()

# ---------- Session ----------
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ---------- Style ----------
st.markdown("""
<style>
button {
    border-radius: 8px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.title("📝 Task Management System")

# ---------- AUTH ----------
if st.session_state.user is None:
    st.subheader("🔐 Authentication")
    choice = st.radio("Select Option", ["Login", "Register"], horizontal=True)

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    col1, col2 = st.columns(2)

    if choice == "Login":
        with col1:
            if st.button("🚀 Login", use_container_width=True):
                cursor.execute(
                    "SELECT * FROM users WHERE username=? AND password=?",
                    (username, password)
                )
                if cursor.fetchone():
                    st.session_state.user = username
                    st.session_state.page = "Dashboard"
                    st.success("Login Successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    if choice == "Register":
        with col2:
            if st.button("📝 Register", use_container_width=True):
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password) VALUES (?,?)",
                        (username, password)
                    )
                    conn.commit()
                    st.success("Registration successful! Login now.")
                except:
                    st.error("Username already exists")

# ---------- MAIN APP ----------
else:
    # ---------- Sidebar ----------
    st.sidebar.title(f"👋 Welcome, {st.session_state.user}")

    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"

    if st.sidebar.button("⏰ Alarm", use_container_width=True):
        st.session_state.page = "Alarm"

    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "Dashboard"
        st.rerun()

    # ---------- DASHBOARD ----------
    if st.session_state.page == "Dashboard":
        st.header("📊 Dashboard")

        # ---- Add Task ----
        task = st.text_input("Task Title")
        description = st.text_area("Task Description")
        due_date = st.date_input("Due Date")
        due_time = st.time_input("Due Time")

        if st.button("➕ Add Task"):
            if task:
                cursor.execute(
                    """INSERT INTO tasks
                    (username, task, description, due_date, due_time, status)
                    VALUES (?,?,?,?,?,?)""",
                    (
                        st.session_state.user,
                        task,
                        description,
                        due_date.strftime("%Y-%m-%d"),
                        due_time.strftime("%H:%M"),
                        "Pending"
                    )
                )
                conn.commit()
                st.success("Task added")
                st.rerun()

        # ---- Load Tasks ----
        def load_tasks():
            cursor.execute(
                """SELECT id, task, description, due_date, due_time, status
                   FROM tasks WHERE username=?""",
                (st.session_state.user,)
            )
            data = cursor.fetchall()
            return pd.DataFrame(
                data,
                columns=["ID", "Task", "Description", "Due Date", "Due Time", "Status"]
            )

        df = load_tasks()

        # ---- Filter ----
        filter_option = st.selectbox("Filter Tasks", ["All", "Pending", "Completed"])
        if filter_option != "All":
            df = df[df["Status"] == filter_option]

        # ---- Overdue ----
        if not df.empty:
            now = pd.Timestamp.now()
            df["Overdue"] = (
                pd.to_datetime(df["Due Date"] + " " + df["Due Time"]) < now
            ) & (df["Status"] == "Pending")

        st.dataframe(
            df.style.applymap(
                lambda x: "color:red;" if x else "",
                subset=["Overdue"]
            ) if not df.empty else df,
            use_container_width=True
        )

        # ---- Download Excel ----
        if not df.empty:
            buffer = io.BytesIO()
            df.drop(columns=["Overdue"], errors="ignore").to_excel(
                buffer, index=False, sheet_name="Tasks"
            )

            st.download_button(
                "📥 Download Tasks as Excel",
                buffer.getvalue(),
                file_name="tasks.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # ---- Actions ----
        col1, col2 = st.columns(2)
        ids = df["ID"].tolist() if not df.empty else []

        with col1:
            if ids:
                cid = st.selectbox("Complete Task", ids)
                if st.button("✅ Mark Completed"):
                    cursor.execute(
                        "UPDATE tasks SET status='Completed' WHERE id=? AND username=?",
                        (cid, st.session_state.user)
                    )
                    conn.commit()
                    st.success("Task completed")
                    st.rerun()

        with col2:
            if ids:
                did = st.selectbox("Delete Task", ids)
                if st.button("🗑 Delete Task"):
                    cursor.execute(
                        "DELETE FROM tasks WHERE id=? AND username=?",
                        (did, st.session_state.user)
                    )
                    conn.commit()
                    st.success("Task deleted")
                    st.rerun()

        # ---- Pie Chart ----
        if not df.empty:
            fig, ax = plt.subplots()
            ax.pie(
                df["Status"].value_counts(),
                labels=df["Status"].value_counts().index,
                autopct="%1.1f%%"
            )
            st.pyplot(fig)

    # ---------- ALARM ----------
    elif st.session_state.page == "Alarm":
        st.header("⏰ Alarm")
        alarm_time = st.time_input("Set Alarm Time")

        if st.button("Start Alarm"):
            st.info("Alarm running...")
            while True:
                if time.strftime("%H:%M") == alarm_time.strftime("%H:%M"):
                    st.success("⏰ Alarm Time Reached!")
                    break
