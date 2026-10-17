PY ?= python

.PHONY: setup index demo view eval eval-resume reset

# Cài thư viện, tạo .env từ mẫu, sinh log giả lập, build index RAG, reset state
setup:
	$(PY) -m pip install -r requirements.txt
	$(PY) -c "import os, shutil; os.path.exists('.env') or shutil.copy('.env.example', '.env')"
	$(PY) scripts/seed_logs.py
	$(PY) scripts/build_index.py
	$(PY) scripts/reset_state.py

index:
	$(PY) scripts/build_index.py --force

# Hỏi agent 1 câu (mặc định: kiểm tra IP 203.0.113.7)
demo: reset
	$(PY) scripts/ask.py $(Q)

# Xem lại log mới nhất theo Thought / Action / Observation (ghi thêm file .txt)
view:
	$(PY) scripts/view_log.py --save

# Chạy toàn bộ tests/testset.jsonl -> results/eval.csv, results/eval.png
eval:
	$(PY) scripts/run_eval.py

eval-resume:
	$(PY) scripts/run_eval.py --resume

reset:
	$(PY) scripts/reset_state.py
