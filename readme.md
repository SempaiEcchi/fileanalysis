# 📂 File Analysis Distributed System

This project implements a **simple distributed system** for file analysis, built with **Python, Flask, Docker, AWS (S3, DynamoDB, SQS)**, and the **OpenAI API**.  
It demonstrates modular service-based architecture where uploaded files are processed asynchronously and results are persisted for retrieval through a web dashboard.

---

## 🚀 Features

- **Upload Service**
    - Accepts file uploads through a REST API.
    - Stores raw files in **AWS S3**.
    - Inserts metadata into **DynamoDB** with a status flag (`PENDING`).
    - Pushes a task message into **SQS** for asynchronous processing.

- **Orchestrator Service**
    - Listens to SQS messages.
    - Determines file type (text vs image).
    - Updates DynamoDB to `PROCESSING`.
    - Invokes the correct downstream analysis service.

- **Text Analysis Service**
    - Downloads PDFs or text files from S3.
    - For PDFs, uploads the file to **OpenAI** using the new `files.create` API (`purpose="user_data"`).
    - Submits a chat completion with the file attached and a summarization prompt.
    - Writes results back into DynamoDB with status `DONE`.

- **Image Analysis Service**
    - Downloads images from S3.
    - Converts them to base64 Data URIs.
    - Calls OpenAI Vision-capable models (`gpt-4o-mini`) with both text and image content.
    - Stores analysis results in DynamoDB.

- **Frontend**
    - A lightweight HTML/JS/CSS dashboard.
    - Allows file uploads.
    - Displays a live table of uploaded files with status badges.
    - Provides a modal viewer for completed analysis results.
    - Auto-refreshes every 5 seconds.

---

## 🏗️ System Architecture

```
Frontend (HTML/JS)
        |
        v
 Upload Service (Flask) ---> S3 (binary files)
        |                         |
        v                         v
 DynamoDB (metadata) <--- Orchestrator <--- SQS (task queue)
        |                                  |
        v                                  v
Text Analysis Service              Image Analysis Service
        |
        v
   DynamoDB (results)
```

**Key points:**
- **Asynchronous processing** is achieved via SQS.
- **State management** is centralized in DynamoDB (`PENDING`, `PROCESSING`, `DONE`).
- **File persistence** is handled by S3; services only pass around IDs, not raw files.
- **Extensibility**: new analysis services can be added by subscribing to SQS and writing to DynamoDB.

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone ...
```

### 2. Environment Variables
Each service has its own `.env`. Example (`upload_service/.env`):

```env
AWS_REGION=eu-north-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

S3_BUCKET=rs-files-uni
DYNAMO_TABLE=FileMetadata
SQS_QUEUE_URL=https://sqs.eu-north-1.amazonaws.com/123456789012/FileAnalysis

OPENAI_API_KEY=sk-xxxxxx
```

### 3. DynamoDB Table
Create the DynamoDB table:

```bash
aws dynamodb create-table \
  --table-name FileMetadata \
  --attribute-definitions AttributeName=file_id,AttributeType=S \
  --key-schema AttributeName=file_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-north-1
```

### 4. Docker Compose
Build and start all services:

```bash
docker compose up --build
```

Services are available at:
- **Upload Service** → `http://localhost:5001`
- **Text Analysis Service** → `http://localhost:5002`
- **Image Analysis Service** → `http://localhost:5003`
- **Frontend** → `http://localhost:8080`

---

## 🧪 Example Flow

1. User uploads `document.pdf` in frontend.
2. Upload Service → stores in S3 + metadata in DynamoDB + sends SQS message.
3. Orchestrator consumes message → routes to Text Analysis Service.
4. Text Analysis Service → uploads PDF to OpenAI → retrieves summary → stores result in DynamoDB.
5. Frontend auto-refresh shows status as `DONE` and displays summary in modal.

---

