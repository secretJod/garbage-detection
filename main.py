from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import numpy as np
import logging
import os

app = FastAPI(title="Garbage Cleanliness Rater")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TILE_SIZE = 512
CONF_THRESHOLD = 0.4
model = None

@app.on_event("startup")
async def load_model():
    global model
    try:
        model_path = '/Users/secret/my_project/garbage_detection/best (3).pt'
        model = YOLO(model_path)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        raise RuntimeError("Model initialization failed")

def process_image(image: np.ndarray) -> tuple:
    """Process image and return (total_garbage_count, total_garbage_area)"""
    h, w = image.shape[:2]
    total_area = h * w
    garbage_count = 0
    garbage_area = 0

    # Process in tiles
    for y in range(0, h, TILE_SIZE):
        for x in range(0, w, TILE_SIZE):
            tile = image[y:y+TILE_SIZE, x:x+TILE_SIZE]
            
            # Temporary file handling
            temp_path = f"temp_{x}_{y}.jpg"
            cv2.imwrite(temp_path, tile)
            
            results = model.predict(temp_path, conf=CONF_THRESHOLD, verbose=False)
            os.remove(temp_path)
            
            # Process detections
            if results[0].boxes:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    garbage_area += (x2 - x1) * (y2 - y1)
                garbage_count += len(results[0].boxes)

    return garbage_count, garbage_area

def calculate_cleanliness(image: np.ndarray, garbage_area: int) -> float:
    """Calculate 0-10 cleanliness score"""
    h, w = image.shape[:2]
    total_pixels = h * w
    
    if total_pixels == 0:
        return 0.0
    
    coverage = (garbage_area / total_pixels) * 100
    score = max(0.0, 10.0 - (coverage / 10))  # 0.1 deduction per 1% coverage
    return round(score, 1)

@app.post("/rate-image/")
async def rate_image(
    area_name: str = Form(...),
    image: UploadFile = File(...)
):
    # Validate input
    if not image.content_type.startswith('image/'):
        raise HTTPException(400, detail="Invalid image file type")

    try:
        # Read and decode image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(400, detail="Invalid image file")

        # Process image
        garbage_count, garbage_area = process_image(img)
        cleanliness_score = calculate_cleanliness(img, garbage_area)

        return {
            "area_name": area_name,
            "marks": cleanliness_score,
            "total_garbage_items": garbage_count,
            "garbage_coverage_percent": round((garbage_area / (img.shape[0] * img.shape[1])) * 100, 1)
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail="Processing error")

@app.get("/health")
async def health_check():
    return {"status": "operational", "model_loaded": model is not None}