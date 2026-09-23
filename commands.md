### Python Environment

#### Setup 
python3 -m venv .venv
source .venv/bin/activate

#### verify
which python
python --version

### Python Commands
python -m compileall app/common/db
python tests/integration/test_health_record_repository.py

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

docker compose -f compose.dev.yaml up -d --build
docker compose -f compose.dev.yaml ps
docker compose -f compose.dev.yaml down
docker compose down

#### Validate compose
    docker compose config
    docker compose -f compose.dev.yaml config

## Docker postgre 
    > (Check version) docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "SELECT version();"
    > (Check Tables) docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "\dt"
    > (Check Table Schema) docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "\d health_records"
    > (Check Records) docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "SELECT id, message, created_at FROM health_records;"
    > docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "\dt"
    > docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "\d tenants"
    > docker exec -it enterprise-document-intelligence-postgres psql -U app -d enterprise_document_intelligence -c "SELECT id, name, slug, status FROM tenants ORDER BY created_at;"

## Alembic 
    It manage schema changes in versioned migration scripts

    > (init alembic migration) alembic init migrations 

            migrations/
                ├── versions/
                ├── env.py
                ├── README
                └── script.py.mako

                alembic.ini
    
    > (generate migration) alembic revision --autogenerate -m "create health records" 

    > (apply migration) alembic upgrade head 

    > alembic current
    > alembic heads