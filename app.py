import streamlit as st

# ✅ MUST BE FIRST Streamlit command
st.set_page_config(page_title="✈️ Flight Data Explorer", layout="wide")

import pandas as pd
import requests
import plotly.express as px
from streamlit_lottie import st_lottie
import time
import io
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- DB Setup using Streamlit secrets ---
DB_URL = st.secrets["db_url"]
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Initialize session state keys ---
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "query_result" not in st.session_state:
    st.session_state.query_result = None

# --- Lottie loader ---
@st.cache_data
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

plane_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_bhw1ul4g.json")

# --- Execute SQL Query ---
def execute_sql_query(query: str):
    try:
        with SessionLocal() as session:
            df = pd.read_sql(query, con=session.bind)
            return df
    except Exception as e:
        st.error(f"SQL Execution Error: {e}")
        return pd.DataFrame()

# ✈️ Flying Emoji Header
st.markdown("""
<style>
@keyframes flyplane {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100vw); }
}
.flying-plane {
  font-size: 28px;
  white-space: nowrap;
  display: inline-block;
  animation: flyplane 8s linear infinite;
}
</style>
<div class="flying-plane">🛫&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✈️&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🛬</div>
""", unsafe_allow_html=True)

# --- App header ---
col1, col2 = st.columns([1, 6])
with col1:
    st_lottie(plane_animation, height=80, key="looping-plane")
with col2:
    st.markdown("## 🛫 Flight Data Explorer")
    st.markdown("Visualize and query flight data in style.")

st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🕓 Query History")
    for q in st.session_state.query_history[-5:][::-1]:
        st.code(q)
    st.markdown("---")
    st.markdown("#### ✈️  🛬   ✈️  🛫")

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 Explore Tables", "🧠 Custom SQL Query"])

# === TABLE VIEW TAB ===
with tab1:
    st.subheader("📦 Table Viewer")
    table_name = st.selectbox("Select a Table", [
        "countries", "cities", "airlines", "airports", "crew", "flightcrew", 
        "tickets", "fuelconsumption", "incidents", "baggage", "passengers", 
        "aircraft", "flights", "routes", "weather"
    ])
    col1, col2 = st.columns([1, 1])
    with col1:
        refresh = st.checkbox("🔁 Auto-refresh every 60s")
    with col2:
        load_data = st.button("🚀 Load Data")

    if load_data or refresh:
        with st.spinner("📡 Fetching data..."):
            df = execute_sql_query(f"SELECT * FROM {table_name} LIMIT 1000")
            if not df.empty:
                st.success(f"✅ `{table_name}` loaded with {len(df)} rows")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, f"{table_name}.csv", "text/csv")

                search_term = st.text_input("🔍 Search table")
                if search_term:
                    filtered = df.astype(str).apply(
                        lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
                    st.dataframe(df[filtered])
                    st.success(f"{filtered.sum()} result(s) found.")
            else:
                st.warning("No data returned.")

    if refresh:
        time.sleep(60)
        st.experimental_rerun()

# === SQL QUERY TAB ===
with tab2:
    st.subheader("🧠 Run Custom SQL")

    examples = {
        "Avg weight of passengers who have atleast 2 bags": """
SELECT 
    p.passenger_id,
    p.first_name,
    p.last_name,
    COUNT(b.baggage_id) AS num_bags,
    AVG(b.weight) AS avg_weight
FROM passengers p
JOIN baggage b ON p.passenger_id = b.passenger_id
GROUP BY p.passenger_id, p.first_name, p.last_name
HAVING COUNT(b.baggage_id) >= 2
ORDER BY avg_weight DESC
""",
        "List of flights with delayed status and weather details at departure": """
SELECT 
    f.flight_number,
    a.airline_name,
    ap.airport_name AS departure_airport,
    w.temperature,
    w.wind_speed,
    w.precipitation,
    f.departure_time
FROM flights f
JOIN airlines a ON f.airline_id = a.airline_id
JOIN airports ap ON f.departure_airport_id = ap.airport_id
JOIN weather w ON f.weather_id = w.weather_id
WHERE f.flight_status = 'Delayed'
ORDER BY f.flight_number

);
"""
    }

    example_key = st.selectbox("📚 Example Queries", list(examples.keys()))
    if st.button("🔎 Load Example"):
        st.session_state.example_query = examples[example_key]

    sql_query = st.text_area("Enter SQL Query:", value=st.session_state.get("example_query", ""), height=200)

    if st.button("▶️ Execute SQL"):
        if sql_query.strip():
            df = execute_sql_query(sql_query)
            if not df.empty:
                st.session_state.query_result = df
                st.session_state.query_history.append(sql_query)
                st.success("✅ Query executed successfully!")
            else:
                st.warning("Query returned no data.")
        else:
            st.warning("Please enter a SQL query.")

    result = st.session_state.query_result
    if result is not None:
        st.markdown("### 📄 Query Results")
        st.dataframe(result)

        csv = result.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "query_result.csv", "text/csv")

        st.markdown("### 📈 Visualize Results")
        chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot"])
        numeric_cols = result.select_dtypes(include='number').columns.tolist()
        all_cols = result.columns.tolist()

        if len(all_cols) >= 2:
            x_axis = st.selectbox("X-axis", all_cols)
            y_axis = st.selectbox("Y-axis", numeric_cols)
            color = st.selectbox("Group/Color (optional)", [None] + all_cols)
            facet = st.selectbox("Facet Column (optional)", [None] + all_cols)

            if x_axis and y_axis:
                try:
                    if chart_type == "Bar Chart":
                        fig = px.bar(result, x=x_axis, y=y_axis, color=color, facet_col=facet)
                    elif chart_type == "Line Chart":
                        fig = px.line(result, x=x_axis, y=y_axis, color=color)
                    elif chart_type == "Scatter Plot":
                        fig = px.scatter(result, x=x_axis, y=y_axis, color=color, facet_col=facet)

                    st.plotly_chart(fig, use_container_width=True)

                    img_bytes = fig.to_image(format="png")
                    st.download_button("🖼 Download Chart", img_bytes, file_name="chart.png", mime="image/png")
                except Exception as e:
                    st.warning(f"⚠️ Couldn't plot chart: {e}")
