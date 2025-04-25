import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_lottie import st_lottie
import time
import io

# Page config
st.set_page_config(page_title="✈️ Flight Data Explorer", layout="wide")

# Load Lottie animation
@st.cache_data
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

plane_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_bhw1ul4g.json")

# Session init
if "query_result" not in st.session_state:
    st.session_state.query_result = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "example_query" not in st.session_state:
    st.session_state.example_query = ""

API_URL = "http://127.0.0.1:8000/data"

# ----------------------------------------
# ✈️ Flying Plane Illusion (Top of page)
# ----------------------------------------
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

# ----------------------------------------
# Header with Lottie airplane animation
# ----------------------------------------
col1, col2 = st.columns([1, 6])
with col1:
    st_lottie(plane_animation, height=80, key="looping-plane")
with col2:
    st.markdown("## 🛫 Flight Data Explorer")
    st.markdown("Visualize and query flight data with sky-high style.")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### 🕓 Query History")
    for q in st.session_state.query_history[-5:][::-1]:
        st.code(q)
    st.markdown("---")
    st.markdown("#### ✈️  🛬   ✈️  🛫")

# Tabs
tab1, tab2 = st.tabs(["📋 Explore Tables", "🧠 Custom SQL Query"])

# === Table Viewer ===
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
        with st.spinner("📡 Contacting air traffic control..."):
            try:
                response = requests.get(f"{API_URL}/{table_name}")
                if response.status_code == 200:
                    data = pd.DataFrame(response.json())
                    if not data.empty:
                        st.success(f"🎉 `{table_name}` loaded with {len(data)} rows")
                        st.dataframe(data)

                        csv = data.to_csv(index=False).encode("utf-8")
                        st.download_button("⬇️ Download CSV", csv, f"{table_name}.csv", "text/csv")

                        search_term = st.text_input("🔍 Search table")
                        if search_term:
                            filtered = data.astype(str).apply(
                                lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
                            st.dataframe(data[filtered])
                            st.success(f"{filtered.sum()} result(s) found.")
                    else:
                        st.warning("Table is empty.")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.exception(e)

    if refresh:
        time.sleep(60)
        st.experimental_rerun()

# === SQL Query Tab ===
with tab2:
    st.subheader("🧠 Run Custom SQL")

    examples = {
        "Top 5 busiest routes": "SELECT route, COUNT(*) as flights FROM flights GROUP BY route ORDER BY flights DESC LIMIT 5;",
        "Total passengers by city": "SELECT city, SUM(passengers) as total_passengers FROM flights GROUP BY city ORDER BY total_passengers DESC;"
    }

    example_key = st.selectbox("📚 Example Queries", list(examples.keys()))
    if st.button("🔎 Load Example"):
        st.session_state.example_query = examples[example_key]

    sql_query = st.text_area("Enter SQL Query:", value=st.session_state.example_query, height=150)

    if st.button("▶️ Execute SQL"):
        if sql_query.strip():
            try:
                response = requests.post(f"{API_URL}/execute_sql", json={"query": sql_query})
                if response.status_code == 200:
                    result = pd.DataFrame(response.json())
                    if not result.empty:
                        st.session_state.query_result = result
                        st.session_state.query_history.append(sql_query)
                        st.success("✅ Query successful!")
                    else:
                        st.warning("Query returned no data.")
                else:
                    st.error(f"❌ Failed: {response.text}")
            except Exception as e:
                st.exception(e)
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
