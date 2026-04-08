from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import os
import psutil
import time
import requests
import socket
import subprocess
from crewai import Agent, Task, Crew, Process, LLM

app = FastAPI()
os.environ["OPENAI_API_KEY"] = "sk-local"

# --- NETWORK CONFIG ---
# PUT YOUR PC'S TAILSCALE IP HERE
PC_IP = "100.108.192.43"
PC_VLLM_URL = f"http://{PC_IP}:8000/v1/models"
PC_PROBE_URL = f"http://{PC_IP}:8001/stats"


def is_node_alive(ip, port, timeout=0.1):
    """Bypasses HTTP to instantly check if a machine is alive on the network."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
        return True
    except Exception:
        return False


mac_llm = LLM(
    model="ollama/qwen2.5-coder:14b", base_url="http://localhost:11434", timeout=300
)
pc_llm = LLM(
    model="openai/Qwen/Qwen2.5-Coder-3B-Instruct-AWQ",
    base_url=f"http://{PC_IP}:8000/v1",
    timeout=300,
    temperature=0.1,
)


class ChatInput(BaseModel):
    prompt: str
    history: List[Dict[str, str]] = []


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r") as file:
        return file.read()


# --- THE LIVE TELEMETRY HEARTBEAT ---
@app.get("/api/telemetry")
async def get_live_telemetry():
    # 1. Mac Vitals
    mac_cpu = psutil.cpu_percent(interval=None)
    mac_mem = psutil.virtual_memory()
    try:
        used = mac_mem.active + mac_mem.wired
    except:
        used = mac_mem.total - mac_mem.available

    # 2. HEALTH CHECKS
    # Check if Mac Ollama is alive (Port 11434)
    mac_llm_online = is_node_alive("127.0.0.1", 11434)

    # Check if PC is alive (Ports 8000 AND 8001)
    pc_online = False
    pc_gpu = 0
    pc_vram = 0
    if is_node_alive(PC_IP, 8000) and is_node_alive(PC_IP, 8001):
        try:
            resp = requests.get(PC_PROBE_URL, timeout=0.5)
            if resp.status_code == 200:
                data = resp.json()
                pc_gpu = data.get("gpu_percent", 0)
                pc_vram = data.get("vram_gb", 0)
                pc_online = True
        except:
            pass

    return {
        "mac_cpu": mac_cpu,
        "mac_mem_gb": round(used / (1024**3), 1),
        "mac_mem_percent": mac_mem.percent,
        "mac_llm_online": mac_llm_online,
        "pc_online": pc_online,
        "pc_gpu": pc_gpu,
        "pc_vram": pc_vram,
    }


# --- NEW REMOTE BOOT ROUTE ---
@app.post("/api/boot-mac")
async def boot_mac_node():
    try:
        # This tells the Mac OS to launch the Ollama background daemon silently
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return {"status": "booting"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- NEW: SYSTEM KILL SWITCHES ---
@app.post("/api/kill-mac")
async def kill_mac_node():
    try:
        # Kills the local Ollama daemon
        subprocess.run(["pkill", "-f", "ollama"])
        return {"status": "killed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/kill-pc")
async def kill_pc_node():
    try:
        # Forwards the kill command across Tailscale to the Windows probe
        requests.post(f"http://{PC_IP}:8001/kill-ai", timeout=2.0)
        return {"status": "killed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/chat")
async def handle_chat(user_input: ChatInput):
    # Format History
    context_string = ""
    if user_input.history:
        context_string = "PREVIOUS CONVERSATION CONTEXT:\n"
        for msg in user_input.history[-4:]:
            speaker = "User" if msg["role"] == "user" else "Committee"
            context_string += f"{speaker}: {msg['content']}\n\n"
        context_string += "CURRENT REQUEST:\n"
    final_prompt = f"{context_string}{user_input.prompt}"

    # NODE HEALTH CHECKS
    mac_is_alive = is_node_alive("127.0.0.1", 11434)
    pc_is_alive = is_node_alive(PC_IP, 8000)

    # 1. TOTAL FAILURE MODE
    if not mac_is_alive and not pc_is_alive:
        return {
            "response": "CRITICAL SYSTEM FAILURE: All AI compute nodes are offline. Cannot process prompt.",
            "mode": "SYSTEM OFFLINE",
        }

    # 2. CLUSTER MODE (Both Alive)
    elif mac_is_alive and pc_is_alive:
        architect = Agent(
            role="Senior Architect",
            goal="Design structures.",
            backstory="You design on an M1.",
            llm=mac_llm,
        )
        developer = Agent(
            role="Full-Stack Engineer",
            goal="Write code.",
            backstory="You execute on an RTX 4060 Ti.",
            llm=pc_llm,
        )
        committee = Crew(
            agents=[architect, developer],
            tasks=[
                Task(
                    description=f"Plan: {final_prompt}",
                    expected_output="A blueprint.",
                    agent=architect,
                ),
                Task(description="Execute.", expected_output="Code.", agent=developer),
            ],
            process=Process.sequential,
        )
        result = committee.kickoff()
        mode_used = "CLUSTER MODE (MAC + PC)"

    # 3. FALLBACK MODE (Mac Only)
    elif mac_is_alive and not pc_is_alive:
        solo_dev = Agent(
            role="Lead Engineer",
            goal="Design and execute.",
            backstory="Running solo on an M1 Mac.",
            llm=mac_llm,
        )
        committee = Crew(
            agents=[solo_dev],
            tasks=[
                Task(
                    description=f"Execute: {final_prompt}",
                    expected_output="Deliverable.",
                    agent=solo_dev,
                )
            ],
        )
        result = committee.kickoff()
        mode_used = "FALLBACK MODE (MAC ONLY)"

    # 4. FALLBACK MODE (PC Only)
    elif not mac_is_alive and pc_is_alive:
        solo_pc = Agent(
            role="Lead Engineer",
            goal="Design and execute.",
            backstory="Running solo on RTX 4060 Ti.",
            llm=pc_llm,
        )
        committee = Crew(
            agents=[solo_pc],
            tasks=[
                Task(
                    description=f"Execute: {final_prompt}",
                    expected_output="Deliverable.",
                    agent=solo_pc,
                )
            ],
        )
        result = committee.kickoff()
        mode_used = "FALLBACK MODE (PC ONLY)"

    return {"response": str(result), "mode": mode_used}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8500)
