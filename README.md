# CFB Recruit Vis Service

Backend for CFB RecruitVis, a college football recruiting visualization project.

## Features

- Provides API endpoints to fetch and serve college football recruiting data for [CFB Recruit Vis UI](https://github.com/howens157/CFB-RecruitVis-UI).

## Prerequisites

- Python 3.x installed on your local machine.
- Password for PostgreSQL database (contact me if interested)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CFB-RecruitVis-Service.git
cd CFB-RecruitVis-Service
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

* On Windows:
  ```bash
  .venv\Scripts\activate
  ```
* On macOS and Linux:
  ```bash
  Source .venv/bin/activate
  ```

### 4. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Configure Environment Variable

You need to set the CFB_DB_URL environment variable to the PostgreSQL database url.

* On Windows:
  ```bash
  $env:CFBD_DB_URL = database_url
  ```
* On macOS and Linux:
  ```bash
  export CFBD_DB_URL = database_url
  ```

### 6. Run Application

```bash
uvicorn app.main:app --reload
```

The server will start and you can access the API documentation at `http://127.0.0.1:8000/docs`.

## Endpoints

The available endpoints and their usage can be explored via the automatically generated API documentation provided by FastAPI. Navigate to `http://127.0.0.1:8000/docs` in your web browser to see the interactive documentation.

## Improvements and Bug Fixes

If you notice any bugs that slipped by me, or have any suggested improvements, please contact me through the contact methods in my profile!

***

Please enjoy!
