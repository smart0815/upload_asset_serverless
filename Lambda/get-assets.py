import boto3
import json
import os
from datetime import datetime

# Initialize S3 client
s3_client = boto3.client('s3')

# Retrieve environment variables
BUCKET_NAME = os.environ.get("BUCKET_NAME")

def list_json_files_in_bucket():
    """
    Lists all JSON files in the specified S3 bucket.
    """
    try:
        # List all objects in the specified S3 bucket
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)

        # Filter out only JSON files
        json_files = []
        if 'Contents' in response:
            for item in response['Contents']:
                if item['Key'].endswith('.json'):
                    # Add timestamp to the json files list
                    json_files.append({
                        'Key': item['Key'],
                        'LastModified': item['LastModified']
                    })

        return json_files

    except Exception as e:
        return {"error": str(e)}

def get_json_file_content(file_key):
    """
    Retrieves the content of a specific JSON file from the S3 bucket.
    """
    try:
        # Get the content of the JSON file from S3
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse the content into JSON
        json_content = json.loads(content)
        
        return json_content

    except Exception as e:
        return {"error": str(e)}

def format_timestamp_with_milliseconds(timestamp):
    """
    Format the timestamp with milliseconds.
    """
    return timestamp.strftime('%Y-%m-%d %H:%M:%S.') + f'{timestamp.microsecond // 1000:03d}'

def lambda_handler(event, context):
    """
    Main handler for retrieving and returning JSON file details from S3 with timestamps.
    """
    try:
        # List all JSON files in the bucket
        json_files = list_json_files_in_bucket()
        
        if not json_files:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "No JSON files found in the bucket."})
            }

        # Create a list to store details of all JSON files
        all_json_files = []
        
        for json_file in json_files:
            # Get the content of each JSON file
            json_file_key = json_file['Key']
            json_file_content = get_json_file_content(json_file_key)
            
            # Get the timestamp with milliseconds
            last_modified_timestamp = json_file['LastModified']
            formatted_timestamp = format_timestamp_with_milliseconds(last_modified_timestamp)
            
            # Add the file details to the list
            all_json_files.append({
                'file_key': json_file_key,
                'content': json_file_content,
                'last_modified': formatted_timestamp
            })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "JSON files content retrieved successfully.",
                "json_files": all_json_files
            })
        }

    except Exception as e:
        # Handle errors
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
