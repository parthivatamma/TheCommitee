import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM
import os

# Set page config at the very top
st.set_page_config(page_title="AI Control Center Builder", layout="wide")

# Dummy key for local endpoints
os.environ["OPENAI_API_KEY"] = "sk-local"

st.title("👨‍💻 Distributed AI Development Team")
st.subheader("Architect (M1 Mac) ➔ Developer (RTX 4060 Ti)")

# User input for the project
project_idea = st.text_area(
    "Describe the UI/Features you want:",
    "A clean ChatGPT clone with a sliding sidebar for GPU telemetry and model stats.",
)

# 1. Hardware & LLM Configuration
# Update the base_url with your actual PC Tailscale IP
mac_llm = LLM(
    model="ollama/qwen2.5-coder:14b", base_url="http://localhost:11434", timeout=300
)

pc_llm = LLM(
    model="openai/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ",
    base_url="http://100.X.X.X:8000/v1",  # <--- REPLACE WITH YOUR PC IP
    timeout=300,
    temperature=0.1,
)

# 2. Agent Personas
architect = Agent(
    role="Senior Systems Architect",
    goal="Design elegant software structures and technical blueprints.",
    backstory="You are a veteran engineer on an M1 Pro. You design the logic and UI flow.",
    llm=mac_llm,
    verbose=True,
)

developer = Agent(
    role="Full-Stack Software Engineer",
    goal="Write flawless, production-ready code in HTML, CSS, and JS.",
    backstory="You are an expert coder on an RTX 4060 Ti. You execute the Architect's designs perfectly.",
    llm=pc_llm,
    verbose=True,
)

# 3. Execution Logic
if st.button("Initialize Committee", key="unique_launch_button_v1"):
    with st.spinner("The Committee is collaborating across your network..."):

        # Define Tasks INSIDE the button block to ensure fresh context
        task_design = Task(
            description=f"Design a 3-step sprint for: {project_idea}. Focus on a single-file index.html with Tailwind.",
            expected_output="A master architectural blueprint.",
            agent=architect,
        )

        task_ui = Task(
            description="Write the HTML/Tailwind skeleton and the sidebar toggle logic.",
            expected_output="The complete <html> structure and CSS.",
            agent=developer,
            context=[task_design],
        )

        task_logic = Task(
            description="Add the JavaScript chat logic, auto-scroll, and telemetry data simulation.",
            expected_output="The full <script> logic integrated into the HTML.",
            agent=developer,
            context=[task_ui],
        )

        # Initialize and Kickoff the Crew
        committee = Crew(
            agents=[architect, developer],
            tasks=[task_design, task_ui, task_logic],
            process=Process.sequential,
            memory=True,
        )

        result = committee.kickoff()

        # Display results only after kickoff is finished
        st.success("Project Complete!")
        st.divider()
        st.subheader("Final Code Output")
        st.code(result, language="html")
        st.download_button("Download index.html", str(result), file_name="index.html")
