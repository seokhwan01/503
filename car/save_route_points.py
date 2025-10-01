# save_route_points.py
import json
from kakao_client import KakaoClient

# ✅ Kakao API Key
REST_API_KEY = "f345f684051191769c60a3d5f15d3774"
kakao = KakaoClient(api_key=REST_API_KEY)

# ✅ 출발지: 사당역
origin_lat, origin_lng = 37.476495715095176, 126.98159314899723

# ✅ 목적지: 중앙대학교 병원
dest_lat, dest_lng = 37.50148432510155, 126.96014984711951

# ✅ Kakao 경로 요청
route = kakao.request_route(origin_lng, origin_lat, dest_lng, dest_lat)
if route["success"]:
    # 전체 경로 좌표 추출
    points = kakao.extract_all_points(route["raw"])
    n = len(points)

    if n > 2:
        # ✅ 1/3 ~ 2/3 구간 슬라이싱
        selected_coords = points[n//3:(2*n)//3 + 1]
    else:
        selected_coords = points  # 너무 짧으면 전체 사용

    # ✅ [lat, lng] 배열로 변환
    coords_array = [[p["lat"], p["lng"]] for p in selected_coords]

    # ✅ JSON 배열로 저장
    with open("car_coords.txt", "w", encoding="utf-8") as f:
        json.dump(coords_array, f, ensure_ascii=False, indent=2)

    print(f"📥 사당역 → 중앙대병원 경로 {len(coords_array)}개 좌표 (1/3~2/3 구간) 저장 완료 → car_coords.txt")
else:
    print("❌ 경로 요청 실패:", route["error"])
