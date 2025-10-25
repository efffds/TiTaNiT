import subprocess
import threading
import sys
import signal
import time

# --- команды для серверов ---
FRONT_CMD = "npm run dev --prefix ./frontend"
BACK_CMD = "python -m uvicorn backend.app.main:app --reload --port 8000"

procs = []

def stream_process(name, cmd):
    """Запускает процесс, стримит stdout/stderr с меткой"""
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    procs.append(p)

    def reader():
        for line in p.stdout:
            sys.stdout.write(f"[{name}] {line}")
            sys.stdout.flush()
    threading.Thread(target=reader, daemon=True).start()
    return p

def stop_processes(sig, frame):
    print(f"\n[MANAGER] Got signal {sig}, stopping all servers...")
    for p in procs:
        if p.poll() is None:
            p.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # ловим Ctrl+C
    signal.signal(signal.SIGINT, stop_processes)
    signal.signal(signal.SIGTERM, stop_processes)

    # запускаем фронт и бэк
    front_proc = stream_process("FRONT", FRONT_CMD)
    back_proc  = stream_process("BACK", BACK_CMD)

    print("[MANAGER] FRONT and BACK processes started. Check logs above for actual ports.")

    # ждём, пока процессы живы
    try:
        while True:
            time.sleep(1)
            # если какой-то процесс умер, выводим сообщение
            for p in procs[:]:
                if p.poll() is not None:
                    print(f"[MANAGER] {p.args} exited")
                    procs.remove(p)
    except KeyboardInterrupt:
        stop_processes(signal.SIGINT, None)
