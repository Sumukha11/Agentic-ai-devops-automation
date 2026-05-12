from fastapi import FastAPI
from pydantic import BaseModel
from adk_agent.agent import run_agent, init_llm, call_llm
from fast_api.jenkins_client import get_status, get_logs
import asyncio
import time

app = FastAPI()


class Query(BaseModel):
    prompt: str


@app.on_event("startup")
async def startup_warmup():
    """Pre-warm the LLM model on startup for faster first response."""
    print("\n" + "="*80)
    print("🔥 STARTUP: Pre-warming LLM model in background...")
    print("="*80)
    
    # Run warmup in background without blocking startup
    asyncio.create_task(_warmup_llm_background())


async def _warmup_llm_background():
    """Warm up LLM by calling it with a dummy prompt."""
    try:
        await asyncio.sleep(2)  # Small delay to let Ollama stabilize
        
        print("⏳ Initializing LLM client...")
        start_time = time.time()
        
        llm = init_llm()
        
        if llm is None:
            print("⚠️ LLM client initialization returned None")
            return
        
        print("✅ LLM client initialized successfully")
        print("⏳ Making warm-up call to load model into memory...")
        
        try:
            # Make a dummy call to trigger model loading
            warmup_response = call_llm("say hello briefly")
            elapsed = time.time() - start_time
            
            print(f"✅ LLM warmed up successfully in {elapsed:.1f}s")
            print(f"✅ First user request will be instant!")
            print("✅ Agent ready for requests\n")
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"⚠️ Warmup call failed after {elapsed:.1f}s: {e}")
            print("   First user request will be slower")
    
    except Exception as e:
        print(f"❌ Warmup error: {e}")


@app.post("/query")
def query(q: Query):
    print("\n=== REQUEST RECEIVED ===")
    print("Prompt:", q.prompt)

    response = run_agent(q.prompt)

    print("Response:", response)
    print("========================\n")

    # Return the agent payload directly (no double-wrapping)
    return response

@app.get("/status/{job}/{build}")
def status(job: str, build: int):
    return get_status(job, build)


@app.get("/logs/{job}/{build}")
def logs(job: str, build: int):
    return get_logs(job, build)


@app.get("/debug/llm")
def debug_llm():
    """Return LLM initialization status and Ollama model list."""
    try:
        from adk_agent.agent import init_llm, llm, OLLAMA_URL
    except Exception:
        from adk_agent.agent import init_llm, llm, OLLAMA_URL
    init_llm()
    status = {"llm_initialized": False, "models": None, "ollama_url": OLLAMA_URL}
    try:
        status["llm_initialized"] = llm is not None
    except Exception:
        pass
    try:
        import requests
        resp = requests.get(f"{OLLAMA_URL.rstrip('/')}/api/models", timeout=5)
        if resp.status_code == 200:
            status["models"] = resp.text
        else:
            status["models"] = f"HTTP {resp.status_code}"
    except Exception as e:
        status["models"] = str(e)
    return status