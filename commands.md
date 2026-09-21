### Python Environment

#### Setup 
python3 -m venv .venv
source .venv/bin/activate

#### verify
which python
python --version

### Packages

#### Install
pip install fastapi uvicorn

#### List
pip list

### Run local service
uvicorn app.main:app --reload
http://127.0.0.1:8000/health
