# django-template

djangoをDockerを用いて開発する際に使用するテンプレートリポジトリ

## Usage

1. Change the URL written in the package.json
2. `npm install`
3. `python -m venv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. Change this README
7. Create django.env
    - SECRET_KEY
    - ENV_STATE
    - DB_ENGINE=django.db.backends.postgresql
    - DB_NAME=project name
    - DB_USER
    - DB_PASSWORD
    - DB_HOST=postgres
    - DB_PORT=5432
    - DB=postgres
8. Create postgres.env
    - POSTGRES_DB=project name
    - POSTGRES_USER
    - POSTGRES_PASSWORD
