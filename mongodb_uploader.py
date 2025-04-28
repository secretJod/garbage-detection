# mongodb_uploader.py
import os
import datetime
from pymongo import MongoClient
from gridfs import GridFS

def store_image_in_mongodb(image_path: str, area_name: str):
    """
    Store an image in MongoDB GridFS and create a document reference
    Args:
        image_path: Full path to the image file
        area_name: Name of the area being uploaded
    """
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["cleanliness_db"]
    fs = GridFS(db)
    
    try:
        with open(image_path, "rb") as f:
            # Store file in GridFS
            file_id = fs.put(
                f,
                filename=os.path.basename(image_path),
                area_name=area_name,
                content_type="image/jpeg"
            )
            
        # Create reference document
        db.images.insert_one({
            "file_id": file_id,
            "area_name": area_name,
            "status": "unprocessed",
            "created_at": datetime.datetime.utcnow(),
            "original_filename": os.path.basename(image_path)
        })
        print(f"Successfully stored image: {image_path}")
        
    except Exception as e:
        print(f"Error storing image: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    store_image_in_mongodb(
        image_path="/Users/secret/my_project/garbage_detection/garbage3.jpeg",
        area_name="downtown"
    )