from crewai import Agent, Task, Crew, Process, LLM
import os

# Dummy key for local endpoints
os.environ["OPENAI_API_KEY"] = "sk-local"

# ---------------------------------------------------------
# 1. THE HARDWARE SPLIT (Modern CrewAI Syntax)
# ---------------------------------------------------------

# The Architect: Running locally on your Mac's Ollama instance
mac_llm = LLM(
    model="ollama/qwen2.5-coder:14b",  # Notice the 'ollama/' prefix
    base_url="http://localhost:11434",
    timeout=300,
)

# The Worker: Running remotely on your PC via Tailscale
pc_llm = LLM(
    model="openai/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ",  # Notice the 'openai/' prefix
    base_url="http://100.108.192.43:8000/v1",  # <--- INSERT YOUR PC'S TAILSCALE IP HERE
    timeout=300,
    temperature=0.1,
)

# ---------------------------------------------------------
# 2. THE PERSONAS
# ---------------------------------------------------------

architect = Agent(
    role="Senior Systems Architect",
    goal="Design elegant software structures and break down algorithms.",
    backstory="You are a veteran engineer. You do not write full implementations; you write the blueprints, pseudo-code, and file structures.",
    verbose=True,
    allow_delegation=True,
    llm=mac_llm,
)

developer = Agent(
    role="Junior Python Developer",
    goal="Write flawless, production-ready code based on architectural blueprints.",
    backstory="You are a fast, accurate programmer. You take instructions from the Architect and turn them into perfect syntax.",
    verbose=True,
    allow_delegation=False,
    llm=pc_llm,
)

# ---------------------------------------------------------
# 3. THE ASSIGNMENT
# ---------------------------------------------------------

task_design = Task(
    description="Design a simple Python script to parse a CSV file of student grades and calculate the average. Output only the class structure and method signatures.",
    expected_output="A markdown document with the proposed class structure.",
    agent=architect,
)

task_code = Task(
    description="Take the Architect's blueprint and write the fully executable Python code. Add comments explaining the logic.",
    expected_output="A complete, runnable Python script.",
    agent=developer,
)

# ---------------------------------------------------------
# 4. EXECUTE
# ---------------------------------------------------------

print("Initializing cross-device execution...")
committee = Crew(
    agents=[architect, developer],
    tasks=[task_design, task_code],
    process=Process.sequential,
)

result = committee.kickoff()

print("\n\n######################\nFINAL DELIVERABLE:\n######################\n")
print(result)
