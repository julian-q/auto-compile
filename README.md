# auto-compile

**Setup**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run Eval Loop**
```bash
python loop.py --num_examples 0 # zero-shot learning
python loop.py --num_examples 1 # one-shot learning
python loop.py --num_examples 2 # ...
python loop.py --num_examples 3
```
