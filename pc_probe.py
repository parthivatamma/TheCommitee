from fastapi import FastAPI
import GPUtil
import uvicorn
import subprocess

app = FastAPI()

@app.get("/stats")
def get_stats():
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        return {
            "online": True, 
            "gpu_percent": int(gpu.load * 100), 
            "vram_gb": round(gpu.memoryUsed / 1024, 1)
        }
    return {"online": True, "gpu_percent": 0, "vram_gb": 0}

@app.post("/kill-ai")
def kill_pc_ai():
    try:
        # This tells Windows to reach into WSL and kill the vLLM process!
        subprocess.run(["wsl", "-e", "pkill", "-f", "vllm"])
        return {"status": "killed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
if __name__ == "__main__":
    # Runs on port 8001 so it doesn't fight with vLLM on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8001)
