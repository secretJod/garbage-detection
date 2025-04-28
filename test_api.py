import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

def test_upload():
    url = "http://localhost:8000/rate-image/"
    
    # Use with-statement to ensure file closure
    with open('/Users/secret/my_project/garbage_detection/142980439-many-garbage-and-dirty-streets-after-holy-festival-hari-raya-aidilfitri-ramzan-ramadan-in-kuala.jpg', 'rb') as f:
        mp_encoder = MultipartEncoder(
            fields={
                'area_name': 'downtown',
                'image': ('test.jpg', f, 'image/jpeg')  # Fixed syntax
            }
        )
        
        response = requests.post(
            url,
            data=mp_encoder,
            headers={'Content-Type': mp_encoder.content_type}
        )
    
    print(f"\nStatus Code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except:
        print("Raw Response:", response.text[:500])

if __name__ == "__main__":
    test_upload()