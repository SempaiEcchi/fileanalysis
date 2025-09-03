import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
dynamo = boto3.resource("dynamodb",     region_name=os.getenv("AWS_REGION"),
                        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
TABLE = dynamo.Table(os.getenv("DYNAMO_TABLE"))

while True:
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    for msg in messages:
        file_id = msg["Body"]

        # Fetch metadata
        item = TABLE.get_item(Key={"file_id": file_id}).get("Item")
        if not item:
            continue

        file_type = item["type"]
        if "text" in file_type or "pdf" in file_type or "word" in file_type:
            analysis_type = "text"
        elif "image" in file_type:
            analysis_type = "image"
        else:
            analysis_type = "unsupported"

        TABLE.update_item(
            Key={"file_id": file_id},
            UpdateExpression="SET #s=:s, analysis_type=:a",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "PROCESSING", ":a": analysis_type},
        )

        print(f"Queued {file_id} for {analysis_type} analysis")

        # Delete from SQS after processing
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=msg["ReceiptHandle"]
        )

        import requests

        if analysis_type == "text":
            requests.post(f"http://localhost:5002/analyze-text/{file_id}")
        elif analysis_type == "image":
            requests.post(f"http://localhost:5003/analyze-image/{file_id}")

    time.sleep(1)
