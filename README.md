# THE COMMITTEE // HA Local AI Cluster

> A fault-tolerant, high-availability local LLM control center routing multi-agent workloads across Apple Silicon and Nvidia CUDA architectures over a Tailscale mesh network.

![UI Status](https://img.shields.io/badge/UI_Aesthetic-Monochrome_Brutalist-black?style=flat-square)
![Network](https://img.shields.io/badge/Mesh-Tailscale-white?style=flat-square)
![Stack](https://img.shields.io/badge/Stack-FastAPI_%7C_CrewAI_%7C_Vanilla_JS-black?style=flat-square)

## Overview

**The Committee** is not just a UI wrapper; it is a distributed compute scheduler. It seamlessly coordinates a CrewAI multi-agent team across an M1 Pro (handling systems architecture) and an 8GB RTX 4060 Ti via WSL2 (handling code execution). 

Built with a strict "Nothing-inspired" monochrome design language, the system features sub-second hardware telemetry, physical socket-level health checks, and cross-VM remote process assassination.

## Architecture & Failover Matrix

The system implements a **4-State Graceful Degradation Matrix**. Because LLM inference is memory-bandwidth bound, distributed network reliability is prioritized. The FastAPI backend utilizes a lightning-fast `0.1s` raw socket ping (`is_node_alive`) to determine hardware health before ever attempting HTTP data transfer.

| State | M1 Pro (Ollama) | 4060 Ti (vLLM) | Task Routing | UI State |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `ONLINE` | `ONLINE` | `CLUSTER MODE` - Distributed CrewAI | Pure White |
| **02** | `ONLINE` | `OFFLINE` | `FALLBACK` - Rerouted to Mac exclusively | Red Warning |
| **03** | `OFFLINE` | `ONLINE` | `FALLBACK` - Rerouted to PC exclusively | Red Warning |
| **04** | `OFFLINE` | `OFFLINE` | `SYS.HALT` - Hardware Lockout engaged | Critical Red |

## Core Engineering Features

* **Sub-Second Telemetry Heartbeat:** A background `setInterval` loop polls the FastAPI server every 800ms. The backend aggregates macOS unified memory (Active + Wired via `psutil`) and reads live VRAM bus allocation directly from the Windows GPU probe.
* **Split-Brain Prevention:** The UI enforces a strict hardware lockout. If physical nodes go dark, the client intercepts the HTTP POST request and halts execution, preventing ghost-state hangs.
* **Remote Remediation:** Built-in Kill Switches allow the Mac to send a command across the Tailscale tunnel, bridging the Windows OS into the WSL2 environment to selectively assassinate the `vLLM` Linux process, or silently reboot the macOS `launchd` Ollama daemon.
* **Rolling State Persistence:** Utilizes a zero-dependency HTML5 `localStorage` database to maintain context window memory and calculate live token consumption (heuristic: 1 Token ≈ 4 Characters) across session reboots.

## Tech Stack

**Backend (Mac Node)**
* `FastAPI` / `Uvicorn` for asynchronous API routing.
* `CrewAI` for multi-agent logic orchestration.
* `psutil` for direct macOS hardware interfacing.
* `socket` / `requests` for zero-latency network probes.

**Probe Node (Windows / WSL2)**
* `vLLM` (AWQ Quantized) running the Qwen 2.5 3B Coder model.
* `GPUtil` broadcasting hardware thermals and VRAM via a dedicated port.

**Frontend**
* Vanilla JavaScript + TailwindCSS (Zero heavy frontend frameworks).
* `Marked.js` + `Highlight.js` for dynamic, dark-mode markdown injection.

## Installation & Boot Sequence

### 1. The Developer Node (Windows PC)
Initialize the hardware probe and the inference engine:

```cmd
# Start the telemetry broadcaster (Port 8001)
python pc_probe.py
```

```bash
# Start the vLLM engine inside WSL (Port 8000)
python3 -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-Coder-3B-Instruct-AWQ --quantization awq --dtype half --gpu-memory-utilization 0.5
```

### 2. The Architect Node (Mac)
Ensure Tailscale is connected, inject your Tailscale IP into `api_server.py`, and ignite the server:

```bash
# Install dependencies
pip install fastapi uvicorn crewai psutil requests

# Boot the orchestrator
python3 api_server.py
```

Navigate to `http://localhost:8500` to enter the Control Center.
