# mongo_processor.py
import requests
from pymongo import MongoClient
from gridfs import GridFS
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoProcessor:
    def __init__(self):
        # MongoDB Configuration
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["cleanliness_db"]
        self.fs = GridFS(self.db)
        
        # API Configuration
        self.api_url = "http://localhost:8000/rate-image/"
        
    def process_images(self):
        """Process unprocessed images from MongoDB"""
        while True:
            try:
                # Get unprocessed document
                doc = self.db.images.find_one({"status": "unprocessed"})
                
                if not doc:
                    logger.info("No unprocessed images found. Sleeping for 10 seconds...")
                    time.sleep(10)
                    continue
                
                logger.info(f"Processing document ID: {doc['_id']}")
                
                # Get image from GridFS
                grid_out = self.fs.get(doc['file_id'])
                image_data = grid_out.read()
                
                # Prepare API request
                mp_encoder = MultipartEncoder(
                    fields={
                        'area_name': doc.get('area_name', 'unknown'),
                        'image': (grid_out.filename, image_data, 'image/jpeg')
                    }
                )
                
                # Send to FastAPI
                response = requests.post(
                    self.api_url,
                    data=mp_encoder,
                    headers={'Content-Type': mp_encoder.content_type}
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"API Error: {response.text}")
                
                # Update document with results
                result = response.json()
                self.db.images.update_one(
                    {'_id': doc['_id']},
                    {'$set': {
                        'status': 'processed',
                        'score': result['marks'],
                        'garbage_count': result['total_garbage_items'],
                        'coverage_percent': result['garbage_coverage_percent'],
                        'processed_at': time.time()
                    }}
                )
                logger.info(f"Successfully processed document {doc['_id']}")
                
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                self.db.images.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'status': 'error', 'error': str(e)}}
                )
                time.sleep(5)

if __name__ == "__main__":
    processor = MongoProcessor()
    processor.process_images()