import boto3
from botocore.exceptions import ClientError

def generate_presigned_url(bucket_name, object_name, expiration=300):
    """Generate a presigned URL to share an S3 object"""
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            },
            ExpiresIn=expiration,
        )
    except ClientError as e:
        print(e)
        return None

    return response


def generate_presigned_url_from_s3_uri(s3_uri, expiration=300):
    # s3_uri looks like "s3://bucket/key"
    s3_uri_parts = s3_uri[5:].split("/", 1)
    bucket_name = s3_uri_parts[0]
    object_name = s3_uri_parts[1]
    presigned_url = generate_presigned_url(bucket_name, object_name)
    return presigned_url
