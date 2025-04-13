# Smart Travel Planner with Netflix-quality UI (Light Purple Transparent Theme)
import os
import streamlit as st
from typing import List, Dict, Any
from litellm import completion
from datetime import datetime
from fpdf import FPDF
import base64

# Set up the page
st.set_page_config(page_title="🛫 Smart Travel Planner", layout="wide")

# Custom light purple transparent-style UI
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, rgba(245, 240, 255, 0.85), rgba(240, 250, 255, 0.85));
    font-family: 'Segoe UI', sans-serif;
    color: #2e2e2e;
}

h1, h2, h3, h4, h5, h6 {
    color: #5e3c99;
}

.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stNumberInput > div > input {
    background-color: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid #cccccc;
    border-radius: 10px;
    padding: 10px;
    color: #333333 !important;
}

.stButton > button {
    background: linear-gradient(145deg, #a066d1, #c99beb);
    color: white;
    font-size: 16px;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    transition: 0.3s;
}

.stButton > button:hover {
    background: #8d3ecb;
}

.st-expanderHeader {
    background-color: rgba(230, 220, 250, 0.7) !important;
    color: #4b2e83;
    font-weight: 600;
    border-radius: 6px;
    padding: 10px;
}

hr {
    border: none;
    height: 1px;
    background-color: #d3c2f2;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("🔐 Configuration")
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
email = st.sidebar.text_input("Email to Share Plan (optional)")

if api_key:
    os.environ["GROQ_API_KEY"] = api_key
else:
    st.sidebar.warning("⚠️ Please enter your Groq API Key to use this app.")

# Tool and Agent Classes
class Tool:
    def __init__(self, name: str, func: callable, description: str):
        self.name = name
        self.func = func
        self.description = description

class Agent:
    def __init__(self, role: str, goal: str, backstory: str, tools: List[Tool]):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools

    def execute_task(self, task_description: str) -> str:
        prompt = f"""
        Role: {self.role}
        Goal: {self.goal}
        Background: {self.backstory}

        Available Tools:
        {self._format_tools()}

        Task: {task_description}

        Please respond with a well-formatted markdown plan with headers, bullet points, and details.
        """
        try:
            response = completion(
                model="groq/llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _format_tools(self) -> str:
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

class TravelCrew:
    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def execute_plan(self, travel_details: Dict[str, Any]) -> Dict[str, str]:
        results = {}
        for agent in self.agents:
            task = self._generate_task(agent, travel_details)
            results[agent.role] = agent.execute_task(task)
        return results

    def _generate_task(self, agent: Agent, details: Dict[str, Any]) -> str:
        return f"""
        Plan a trip from {details['from_location']} to {details['to']} for {details['travelers']} travelers.
        - Dates: {details['dates']}
        - Budget: ${details['budget']}
        - Preferences: {details['preferences']}

        Your task: {agent.goal}
        """

# Tools
search_tool = Tool("Search", lambda q: f"Search: {q}", "Search travel info")
scrape_tool = Tool("Scraper", lambda url: f"Scrape: {url}", "Scrape travel data")

# Agents
agents = [
    Agent("Flight Specialist", "Find best flights", "Airfare wizard", [search_tool]),
    Agent("Accommodation Expert", "Recommend hotels", "Hotel finder pro", [search_tool]),
    Agent("Activity Planner", "Create an itinerary", "Loves planning memorable trips", [search_tool])
]

crew = TravelCrew(agents)

# Main Content
st.title("🛫 Smart Travel Planner")
st.markdown("Design your dream vacation with smart AI travel agents.")
st.markdown("---")

# Trip Form
with st.form("trip_form"):
    col1, col2 = st.columns(2)
    with col1:
        from_location = st.text_input("From", "New York")
        to = st.text_input("To", "Paris")
        date_range = st.date_input("Select Travel Dates", [])
        if isinstance(date_range, list) and len(date_range) == 2:
            dates = f"{date_range[0].strftime('%B %d, %Y')} - {date_range[1].strftime('%B %d, %Y')}"
        else:
            dates = "Not selected"
    with col2:
        budget = st.number_input("Budget ($)", value=1500)
        travelers = st.number_input("Travelers", min_value=1, value=2)
        preferences = st.text_area("Preferences", "Museums, beach, food")

    submitted = st.form_submit_button("✈️ Generate Plan")

# History
if 'history' not in st.session_state:
    st.session_state.history = []

# Generate plan
if submitted and api_key:
    with st.spinner("Thinking and planning..."):
        details = {
            "from_location": from_location,
            "to": to,
            "dates": dates,
            "budget": budget,
            "travelers": travelers,
            "preferences": preferences
        }
        results = crew.execute_plan(details)
        st.session_state.history.append((datetime.now().strftime("%Y-%m-%d %H:%M"), results))

        st.subheader("🌟 Your Personalized Travel Plan")
        for role, res in results.items():
            with st.expander(f"🔍 {role}"):
                st.markdown(res, unsafe_allow_html=True)

        # Export PDF
        if st.button("📄 Export to PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for role, res in results.items():
                pdf.multi_cell(0, 10, f"{role}\n{res}\n")
            pdf_file = "travel_plan.pdf"
            pdf.output(pdf_file)
            with open(pdf_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="travel_plan.pdf">Download PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

# Trip History
if st.session_state.history:
    st.markdown("### 🖓 Previous Plans")
    for timestamp, plan in reversed(st.session_state.history[-3:]):
        with st.expander(f"🗓️ {timestamp}"):
            for role, res in plan.items():
                st.markdown(f"**{role}**\n\n{res}", unsafe_allow_html=True)
