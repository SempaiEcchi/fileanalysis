from flask import Flask, jsonify
import boto3
import os
import base64
import tempfile
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
dynamo = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BUCKET = os.getenv("S3_BUCKET")
TABLE = dynamo.Table(os.getenv("DYNAMO_TABLE"))


@app.route("/analyze-text/<file_id>", methods=["POST"])
def analyze_text(file_id):
    # Download PDF from S3
    obj = s3.get_object(Bucket=BUCKET, Key=file_id)
    file_bytes = obj["Body"].read()

    # Save temporarily (OpenAI needs a file handle)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    # Upload to OpenAI as a file
    file_obj = client.files.create(
        file=open(tmp_path, "rb"),
        purpose="user_data"
    )

    # Ask a question / request summary
    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "file", "file": {"file_id": file_obj.id}},
                    {"type": "text", "text": "Please summarize this PDF document."},
                ],
            }
        ],
    )

    summary = completion.choices[0].message.content

    # Save to DynamoDB
    TABLE.update_item(
        Key={"file_id": file_id},
        UpdateExpression="SET #s = :s, #r = :r",
        ExpressionAttributeNames={"#s": "status", "#r": "result"},
        ExpressionAttributeValues={":s": "DONE", ":r": summary},
    )

    return jsonify({"file_id": file_id, "summary": summary})


if __name__ == "__main__":
    app.run(port=5002, debug=True)
