import json
import queue
import subprocess
import threading
import time

cmd = r"C:\Users\takas\AppData\Local\OpenAI\Codex\bin\2993767bd1dfb009\codex.exe"
proc = subprocess.Popen([cmd, "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
lines = queue.Queue()

def read_output():
    for line in proc.stdout:
        lines.put(line)

threading.Thread(target=read_output, daemon=True).start()

def send(message):
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()

def response(request_id, timeout=40):
    deadline = time.monotonic() + timeout
    while True:
        line = lines.get(timeout=max(0.1, deadline - time.monotonic()))
        message = json.loads(line)
        if message.get("id") == request_id:
            return message

try:
    send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "blender_mcp_check", "title": "Blender MCP check", "version": "1.0"}, "capabilities": {"experimentalApi": True}}})
    init = response(1)
    if "error" in init:
        raise RuntimeError(init["error"])
    send({"method": "initialized", "params": {}})
    send({"id": 2, "method": "mcpServerStatus/list", "params": {"serverName": "blender", "detail": "toolsAndAuthOnly"}})
    status = response(2)
    if "error" in status:
        raise RuntimeError(status["error"])
    data = status.get("result", {})
    print(json.dumps(data, ensure_ascii=False)[:12000])
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
