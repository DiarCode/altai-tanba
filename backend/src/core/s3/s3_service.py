import io
from typing import List
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from src.core.config.settings import settings


class S3Service:
    """Service for interacting with MinIO/S3 storage."""

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ACCESS_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path' if settings.S3_PATH_STYLE else 'virtual'}
            )
        )
        self.bucket = settings.S3_BUCKET

    async def download_document_images(self, prefix: str) -> List[tuple[str, bytes]]:
        """
        Download all PNG images from a document's pages folder.
        
        Args:
            document_id: The document ID
            
        Returns:
            List of tuples containing (filename, image_bytes)
            
        Raises:
            Exception: If download fails
        """
        try:
            prefix = f"{prefix}/pages/"
            
            # List all objects with the given prefix
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                raise Exception(f"No images found for prefix {prefix}")
            
            images = []
            for obj in response['Contents']:
                key = obj['Key']
                
                # Only process PNG files
                if not key.lower().endswith('.png'):
                    continue
                
                # Download the image
                file_obj = io.BytesIO()
                self.client.download_fileobj(self.bucket, key, file_obj)
                file_obj.seek(0)
                
                # Extract filename from key
                filename = key.split('/')[-1]
                images.append((filename, file_obj.read()))
            
            if not images:
                raise Exception(f"No PNG images found in {prefix}")
            
            return images
            
        except ClientError as e:
            raise Exception(f"Failed to download images from S3: {str(e)}")
        except Exception as e:
            raise Exception(f"Error downloading document images: {str(e)}")

    async def upload_file(self, file_bytes: bytes, key: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload a file to S3.
        
        Args:
            file_bytes: File content as bytes
            key: S3 object key (path)
            content_type: MIME type of the file
            
        Returns:
            The S3 key of the uploaded file
        """
        try:
            file_obj = io.BytesIO(file_bytes)
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs={'ContentType': content_type}
            )
            return key
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")


# Singleton instance
s3_service = S3Service()
