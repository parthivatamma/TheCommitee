from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import os
import psutil  # <--- NEW IMPORT
import time  # <--- NEW IMPORT
from crewai import Agent, Task, Crew, Process, LLM

app = FastAPI()
os.environ["OPENAI_API_KEY"] = "sk-local"

mac_llm = LLM(
    model="ollama/qwen2.5-coder:14b", base_url="http://localhost:11434", timeout=300
)
pc_llm = LLM(
    model="openai/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ",
    base_url="http://100.108.192.43:8000/v1",
    timeout=300,
    temperature=0.1,
)  # KEEP YOUR PC TAILSCALE IP HERE


class ChatInput(BaseModel):
    prompt: str


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r") as file:
        return file.read()

    # --- ADD THIS NEW ROUTE TO api_server.py ---


@app.get("/api/telemetry")
async def get_live_telemetry():
    # Quick 0.1s sample so the API responds almost instantly
    mac_cpu_percent = psutil.cpu_percent(interval=0.1)

    mac_memory = psutil.virtual_memory()
    try:
        real_used_memory = mac_memory.active + mac_memory.wired
    except AttributeError:
        real_used_memory = mac_memory.total - mac_memory.available

    mac_mem_gb = round(real_used_memory / (1024**3), 1)
    mac_mem_percent = round((real_used_memory / mac_memory.total) * 100, 1)

    return {
        "mac_cpu": mac_cpu_percent,
        "mac_mem_gb": mac_mem_gb,
        "mac_mem_percent": mac_mem_percent,
    }


@app.post("/api/chat")
async def handle_chat(user_input: ChatInput):

    # 1. Start the stopwatch
    start_time = time.time()

    # (Your exact CrewAI setup stays the same)
    architect = Agent(
        role="Senior Systems Architect",
        goal="Design elegant software structures.",
        backstory="You design the logic on an M1 Mac.",
        llm=mac_llm,
    )
    developer = Agent(
        role="Full-Stack Software Engineer",
        goal="Write flawless code.",
        backstory="You execute designs on an RTX 4060 Ti.",
        llm=pc_llm,
    )

    task_design = Task(
        description=f"Analyze: {user_input.prompt}. Write a brief plan.",
        expected_output="A short text blueprint.",
        agent=architect,
    )
    task_code = Task(
        description="Read the blueprint and write the code.",
        expected_output="Final code deliverable.",
        agent=developer,
    )

    committee = Crew(
        agents=[architect, developer],
        tasks=[task_design, task_code],
        process=Process.sequential,
    )

    # Run the AI
    result = committee.kickoff()

    # 2. Stop the stopwatch
    execution_time = time.time() - start_time

    # 3. Read the Mac's REAL hardware vitals
    # By passing interval=0.5, we force psutil to watch the CPU for half a second
    # to get a realistic average load, rather than an instant post-task dropoff.
    mac_cpu_percent = psutil.cpu_percent(interval=0.5)

    mac_memory = psutil.virtual_memory()

    # macOS Activity Monitor calculates "Used Memory" roughly as (Active + Wired)
    # We use a try/except because Windows/Linux don't have these exact tags
    try:
        real_used_memory = mac_memory.active + mac_memory.wired
    except AttributeError:
        real_used_memory = mac_memory.total - mac_memory.available

    # Convert bytes to Gigabytes for the UI
    mac_mem_gb = round(real_used_memory / (1024**3), 1)
    mac_mem_percent = round((real_used_memory / mac_memory.total) * 100, 1)

    # 4. Send EVERYTHING back to the UI
    return {
        "response": str(result),
        "telemetry": {
            "mac_cpu": mac_cpu_percent,
            "mac_mem_gb": mac_mem_gb,
            "mac_mem_percent": mac_mem_percent,
            "duration_seconds": round(execution_time, 2),
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8500)
