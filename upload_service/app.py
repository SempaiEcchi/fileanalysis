from flask import Flask, request, jsonify
import boto3
import os
import uuid
from dotenv import load_dotenv
import datetime

load_dotenv()

app = Flask(__name__)

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
dynamo = boto3.resource("dynamodb",     region_name=os.getenv("AWS_REGION"),
                        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),)
sqs = boto3.client("sqs",     region_name=os.getenv("AWS_REGION"),
                   aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                   aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),)

BUCKET = os.getenv("S3_BUCKET")
TABLE = dynamo.Table(os.getenv("DYNAMO_TABLE"))
QUEUE_URL = os.getenv("SQS_QUEUE_URL")


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    file_id = str(uuid.uuid4())
    filename = file.filename
    content_type = file.content_type

    # Upload to S3
    s3.upload_fileobj(file, BUCKET, file_id)

    # Insert metadata into DynamoDB
    TABLE.put_item(
        Item={
            "file_id": file_id,
            "filename": filename,
            "type": content_type,
            "status": "PENDING",
            "created_at": str(datetime.datetime.utcnow()),
        }
    )

    # Push job to SQS
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=file_id
    )

    return jsonify({"file_id": file_id, "status": "uploaded"})


@app.route("/status/<file_id>", methods=["GET"])
def status(file_id):
    res = TABLE.get_item(Key={"file_id": file_id})
    return jsonify(res.get("Item", {}))


@app.route("/files", methods=["GET"])
def list_files():
    # Scan the whole DynamoDB table (for demo)
    res = TABLE.scan()
    items = res.get("Items", [])

    # Sort by created_at (descending)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return jsonify(items)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
