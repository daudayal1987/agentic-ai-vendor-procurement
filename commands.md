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

### Docker
docker build -t enterprise-document-intelligence:day2 .
docker images | grep enterprise-document-intelligence

docker run --rm --name enterprise-document-intelligence  -p 8000:8000  ent-doc-intl:day2
docker run --rm --name enterprise-document-intelligence  -p 8000:8000  ent-doc-intl:day2 --detach

docker ps
docker logs enterprise-document-intelligence    
docker image inspect ent-doc-intl:day2 --format '{{.Architecture}}'

docker container stop enterprise-document-intelligence


### Docker compose
docker compose up --build
docker compose up -d --build

docker compose ps
docker compose logs api

docker compose down


Use compose.dev.yaml if you don't want to rebuild docker image everytime on code change:

docker compose -f compose.dev.yaml up --build
docker compose -f compose.dev.yaml ps
docker compose -f compose.dev.yaml down
docker compose down

#### Validate compose
    docker compose config
    docker compose -f compose.dev.yaml config