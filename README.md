## setup & Run
<details>
<summary>1- Install Requirements</summary>

```bash
pip install -r requirements.txt
pip install pytest
pip install unicorn
```
</details>
<details>
<summary>2- create a database</summary>

### create database

```bash
python -m pytest
```
</details>

<summary>3- Run server</summary>

### [Optional] Set environment variables

```bash
export JWT_SECRET_KEY=$(openssl rand -base64 32)
export JWT_REFRESH_SECRET_KEY=$(openssl rand -base64 32)
```

### Run server

```bash
python app.py
```
</details>

<details>
<summary>4- Read API docs</summary>
 - swagger ui: <a href="http://127.0.0.1:8000/docs" target="_blank">http://127.0.0.1:8000/docs</a>
 - redoc: <a href="http://127.0.0.1:8000/redoc" target="_blank">http://127.0.0.1:8000/redoc</a>
</details>