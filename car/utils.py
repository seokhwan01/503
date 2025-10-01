import math
import json

def load_my_coords(file_path="car_coords.txt"):
    coords = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            arr = json.load(f)
            for pair in arr:
                if len(pair) == 2:
                    lat, lng = pair
                    coords.append({"lat": float(lat), "lng": float(lng)})
        print(f"📂 내 차량 경로 좌표 {len(coords)}개 로드 완료")
    except Exception as e:
        print("❌ 차량 좌표 로드 실패:", e)
    return coords

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def cosine_similarity(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    return dot / (mag1 * mag2) if mag1 and mag2 else 0

