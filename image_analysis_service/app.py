from flask import Flask, jsonify
import boto3
import os
from dotenv import load_dotenv
from openai import OpenAI
import base64

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


@app.route("/analyze-image/<file_id>", methods=["POST"])
def analyze_image(file_id):
    # Download file
    obj = s3.get_object(Bucket=BUCKET, Key=file_id)
    img_bytes = obj["Body"].read()
    b64_img = base64.b64encode(img_bytes).decode("utf-8")

    data_uri = f"data:image/png;base64,{b64_img}"  # adjust MIME type if needed

    # Call OpenAI Vision
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # ✅ vision-capable model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ],
            }
        ]
    )

    description = response.choices[0].message.content

    # Save result
    TABLE.update_item(
        Key={"file_id": file_id},
        UpdateExpression="SET #s = :s, #r = :r",
        ExpressionAttributeNames={"#s": "status", "#r": "result"},
        ExpressionAttributeValues={":s": "DONE", ":r": description},
    )

    return jsonify({"file_id": file_id, "description": description})


if __name__ == "__main__":
    app.run(port=5003, debug=True)
