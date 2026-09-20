#!/bin/bash
# smallville.sh — one-command launcher for the Smallville generative agents simulation.
#
#   ./smallville.sh                  start/resume the default sim (smallville-8), queue 2000 steps
#   ./smallville.sh <sim> <steps>    start/resume a specific sim with a custom step count
#   ./smallville.sh stop             save the running sim and shut everything down
#
# What it manages: Ollama (LLM server), Django frontend, reverie.py backend,
# a headless Chrome that drives simulation steps even when no tab is visible,
# and your browser tab for watching. Logs: /tmp/smallville-*.log

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/.venv/bin/python"
STORAGE="$ROOT/environment/frontend_server/storage"
TEMP="$ROOT/environment/frontend_server/temp_storage"
OLLAMA_BIN="/Applications/Ollama.app/Contents/Resources/ollama"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PIPE=/tmp/smallville.pipe
BACKEND_LOG=/tmp/smallville-backend.log
FRONTEND_LOG=/tmp/smallville-frontend.log
HEADLESS_LOG=/tmp/smallville-headless.log
CHROME_PROFILE=/tmp/chrome-smallville
URL="http://localhost:8000/simulator_home"

# Run a shell command fully detached (own session/process group), so it
# survives this script exiting -- regardless of how the script was invoked.
detach() {
  "$PY" -c "import subprocess,sys; subprocess.Popen(['bash','-c',sys.argv[1]], start_new_session=True, stdin=subprocess.DEVNULL)" "$1"
}

# Send a line into a pipe without hanging forever if nothing is reading it.
send_cmd() {
  local pipe="$1" msg="$2"
  [ -p "$pipe" ] || return 1
  ( printf "%s\n" "$msg" > "$pipe" ) &
  local w=$!
  sleep 2
  kill "$w" 2>/dev/null
  wait "$w" 2>/dev/null
  return 0
}

# Gracefully stop a running backend: 'fin' saves all agent memories, then exits.
stop_backend() {
  pgrep -f "reverie.py" >/dev/null || return 0
  echo "* Simulation backend is running -- saving and stopping it first (this can take a minute)..."
  for p in "$PIPE" /tmp/rev_in3 /tmp/rev_in2; do
    send_cmd "$p" "fin"
  done
  for i in $(seq 1 60); do
    pgrep -f "reverie.py" >/dev/null || { echo "  saved and stopped."; return 0; }
    sleep 2
  done
  echo "  WARNING: backend did not exit after 'fin'; force-killing (progress since last save is lost)."
  pkill -f "reverie.py"
  sleep 2
}

stop_all() {
  stop_backend
  pkill -f "user-data-dir=$CHROME_PROFILE" 2>/dev/null && echo "* Headless step-driver stopped."
  pkill -f "caffeinate -w" 2>/dev/null
  echo "* Done. (Ollama and the frontend server stay up for fast restarts.)"
  echo "  To stop those too:  pkill -f 'ollama serve'; pkill -f 'manage.py runserver'"
}

if [ "${1:-}" = "stop" ]; then
  stop_all
  exit 0
fi

# Re-arm the one-shot page handshake so a (re)loaded browser tab shows the map.
if [ "${1:-}" = "arm-tab" ]; then
  CUR_SIM=$("$PY" -c "import json;print(json.load(open('$TEMP/curr_sim_code.json'))['sim_code'])")
  STEP=$(ls "$STORAGE/$CUR_SIM/movement" 2>/dev/null | sed 's/\.json//' | sort -n | tail -1)
  [ -z "$STEP" ] && STEP=0
  printf '{"step": %s}' "$STEP" > "$TEMP/curr_step.json"
  echo "Tab armed for sim '$CUR_SIM' at step $STEP -- reload $URL now."
  exit 0
fi

SIM="${1:-smallville-8}"
STEPS="${2:-2000}"

echo "=== Smallville launcher ==="
echo "sim: $SIM   steps to run: $STEPS"

# --- 1. Ollama ---------------------------------------------------------------
if curl -s --max-time 3 http://localhost:11434/api/version >/dev/null; then
  echo "* Ollama already running."
else
  echo "* Starting Ollama..."
  detach "exec '$OLLAMA_BIN' serve > /tmp/ollama-serve.log 2>&1"
  for i in $(seq 1 30); do
    curl -s --max-time 2 http://localhost:11434/api/version >/dev/null && break
    sleep 1
  done
  curl -s --max-time 2 http://localhost:11434/api/version >/dev/null \
    || { echo "ERROR: Ollama failed to start (see /tmp/ollama-serve.log)"; exit 1; }
  echo "  up."
fi

# --- 2. Django frontend ------------------------------------------------------
if curl -s --max-time 3 -o /dev/null http://localhost:8000/; then
  echo "* Frontend already running at http://localhost:8000"
else
  echo "* Starting frontend server..."
  detach "cd '$ROOT/environment/frontend_server' && exec '$PY' manage.py runserver > '$FRONTEND_LOG' 2>&1"
  for i in $(seq 1 30); do
    curl -s --max-time 2 -o /dev/null http://localhost:8000/ && break
    sleep 1
  done
  curl -s --max-time 2 -o /dev/null http://localhost:8000/ \
    || { echo "ERROR: frontend failed to start (see $FRONTEND_LOG)"; exit 1; }
  echo "  up."
fi

# --- 3. Simulation backend ---------------------------------------------------
stop_backend

# Figure out what to fork from: an existing sim remembers its origin in meta.json.
if [ -f "$STORAGE/$SIM/reverie/meta.json" ]; then
  FORK=$("$PY" -c "import json;print(json.load(open('$STORAGE/$SIM/reverie/meta.json'))['fork_sim_code'])" 2>/dev/null)
  echo "* Resuming existing sim '$SIM' (forked from '$FORK')."
else
  FORK="base_the_ville_isabella_maria_klaus"
  echo "* Sim '$SIM' does not exist -- creating it fresh from '$FORK'."
fi

rm -f "$PIPE"; mkfifo "$PIPE"
# Hold the pipe's write end open forever so commands can be sent at any time.
detach "exec sleep 999999999 > '$PIPE'"
detach "cd '$ROOT/reverie/backend_server' && exec '$PY' -u reverie.py < '$PIPE' > '$BACKEND_LOG' 2>&1"
printf "%s\n%s\n" "$FORK" "$SIM" > "$PIPE"

echo "* Waiting for backend to load personas..."
for i in $(seq 1 60); do
  grep -q "Enter option" "$BACKEND_LOG" 2>/dev/null && break
  pgrep -f "reverie.py" >/dev/null || { echo "ERROR: backend died on startup (see $BACKEND_LOG)"; exit 1; }
  sleep 2
done
grep -q "Enter option" "$BACKEND_LOG" 2>/dev/null \
  || { echo "ERROR: backend never became ready (see $BACKEND_LOG)"; exit 1; }
echo "  ready."

BACKEND_PID=$(pgrep -f "reverie.py" | head -1)
# Keep the Mac awake while the simulation runs; exits automatically with the backend.
detach "exec caffeinate -w $BACKEND_PID -dims"

send_cmd "$PIPE" "run $STEPS"
echo "* Queued 'run $STEPS'."

# --- 4. Headless step-driver -------------------------------------------------
# The sim only advances while a page runs the game engine; browsers pause hidden
# tabs, so a headless Chrome does the driving no matter what you do with yours.
pkill -f "user-data-dir=$CHROME_PROFILE" 2>/dev/null
sleep 1
detach "exec '$CHROME' --headless=new --disable-gpu --window-size=1400,900 --user-data-dir='$CHROME_PROFILE' '$URL' > '$HEADLESS_LOG' 2>&1"
echo "* Headless step-driver started."
sleep 6

# --- 5. Open the map for the human -------------------------------------------
# The map page needs a one-shot handshake file per load; the headless driver
# consumed the backend's one, so write a fresh one for the visible tab.
STEP=$(ls "$STORAGE/$SIM/movement" 2>/dev/null | sed 's/\.json//' | sort -n | tail -1)
[ -z "$STEP" ] && STEP=0
printf '{"step": %s}' "$STEP" > "$TEMP/curr_step.json"
open "$URL"

echo
echo "=== Smallville is running ==="
echo "watch:        $URL   (reload = run ./smallville.sh arm-tab first if it errors)"
echo "more steps:   printf 'run 500\\n'  > $PIPE"
echo "save now:     printf 'save\\n'     > $PIPE"
echo "stop all:     ./smallville.sh stop"
echo "backend log:  tail -f $BACKEND_LOG"
