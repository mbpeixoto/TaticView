# run_all.py

import os
import subprocess

print("🔍 Rodando análise no vídeo (main.py)...")
subprocess.run(["python", "main.py"])

print("📊 Abrindo o dashboard interativo (app.py)...")
subprocess.run(["streamlit", "run", "app.py"])
