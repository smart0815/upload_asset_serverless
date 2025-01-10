import boto3
import base64
import json
import uuid
import os
import mimetypes
import time

# Initialize S3 and Rekognition clients
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
sns_client = boto3.client('sns')

# Retrieve environment variables
BUCKET_NAME = os.environ.get("BUCKET_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")  # SNS topic ARN for notifications

def get_content_type(file_name):
    """
    Determines the content type (MIME type) of a file based on its extension.
    """
    content_type, _ = mimetypes.guess_type(file_name)
    if not content_type:
        content_type = "application/octet-stream"  # Default content type
    return content_type

def start_video_analysis(video_file_name):
    """
    Starts the video label detection job for video files.
    """
    try:
        response = rekognition_client.start_label_detection(
            Video={'S3Object': {'Bucket': BUCKET_NAME, 'Name': video_file_name}},
            MinConfidence=50,  # Confidence threshold for label detection
            NotificationChannel={
                'SNSTopicArn': SNS_TOPIC_ARN,  # SNS topic for notifications
                'RoleArn': os.environ['ROLE_ARN']  
            }
        )
        
        job_id = response['JobId']
        
        return job_id

    except Exception as e:
        return {"error": str(e)}

def lambda_handler(event, context):
    """
    Main handler for processing image and video file uploads.
    """
    try:
        # Extract file information from the event
        file_name = event.get('file_name')
        file_content_base64 = event.get('file_content')

        # Ensure file content is base64 encoded and decode it
        file_content = base64.b64decode(file_content_base64)
        
        if not file_name or not file_content_base64:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'file_name' or 'file_content' in request"})
            }

        # Generate a unique file name for S3
        unique_file_name = f"{uuid.uuid4()}_{file_name}"

        # Get the content type (MIME type) based on the file extension
        content_type = get_content_type(file_name)

        # Upload the file to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_file_name,
            Body=file_content,
            ContentType=content_type
        )

        # URL for accessing the uploaded file in S3
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_file_name}"

        # Determine the file type
        file_type = "image" if content_type.startswith('image/') else "video" if content_type.startswith('video/') else "unknown"

        # Process based on content type
        labels = []
        labels_file_name = None
        
        if file_type == "image":
            # For image files: Use Rekognition Image to detect labels
            rekognition_response = rekognition_client.detect_labels(
                Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': unique_file_name}},
                MaxLabels=10  # Limit to top 10 labels
            )
            
            # Parse Rekognition results
            labels = [
                {"Name": label["Name"], "Confidence": label["Confidence"]}
                for label in rekognition_response["Labels"]
            ]
        
        elif file_type == "video":
            # For video files: Start Rekognition Video analysis asynchronously
            job_id = start_video_analysis(unique_file_name)
            labels = [{"JobId": job_id, "Status": "Video analysis started. Check the SNS notification for results."}]

        # Generate JSON with labels and file URL
        labels_json = json.dumps({
            "file_url": s3_url,
            "labels": labels,
            "file_type": file_type  # Add the file type to the response
        })

        # Store labels in a JSON file on S3
        labels_file_name = f"labels_{uuid.uuid4()}_{file_name}.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=labels_file_name,
            Body=labels_json,
            ContentType="application/json"
        )

        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "File uploaded and analyzed successfully.",
                "file_key": unique_file_name,
                "labels_file_key": labels_file_name,
                "file_url": s3_url,
                "labels": labels,
                "file_type": file_type  # Include file type in the response
            })
        }

    except Exception as e:
        # Handle errors
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
