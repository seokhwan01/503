import math
import json
from utils import haversine, cosine_similarity

class AmbulanceStatus:
    def __init__(self):
        self.data = {}  # 🚑 구급차 최신 상태 저장
        self.crossed = False
        self.last_same_lane = None
        self.same_lane_count = 0
        self.stable_same_lane = None

    def update(self, payload):
        self.data = payload
        # print(f"\n🚑 긴급차량 정보 갱신: 목적지={payload.get('dest')}, 좌표={payload.get('current')}")

    def calculate_status(self, my_pos, my_next):
        print("경로 계산중")
        try:
            route_info = self.data.get("route_info", {})
            current = self.data.get("current", {})
            if not route_info or not current:
                return None, None, None, None

            # 네비 API 응답: routes → sections → roads
            roads = route_info["routes"][0]["sections"][0]["roads"]

            # (1) 내 위치/구급차 위치를 roads 단위에서 매핑
            my_idx = min(range(len(roads)),
                         key=lambda i: haversine(my_pos["lat"], my_pos["lng"],
                                                 roads[i]["vertexes"][1], roads[i]["vertexes"][0]))
            ambu_idx = min(range(len(roads)),
                           key=lambda j: haversine(current["lat"], current["lng"],
                                                   roads[j]["vertexes"][1], roads[j]["vertexes"][0]))

            # (2) ETA 계산: 단순 road duration 합산
            if my_idx <= ambu_idx:
                eta = sum(r["duration"] for r in roads[my_idx:ambu_idx+1])
            else:
                eta = sum(r["duration"] for r in roads[ambu_idx:my_idx+1])

            # (3) 경로 vertex 평탄화 (방향/거리 판정용)
            route_points = []
            for road in roads:
                verts = road["vertexes"]
                for k in range(0, len(verts), 2):
                    lng, lat = verts[k], verts[k+1]
                    route_points.append({"lat": lat, "lng": lng})

            # 내 차에서 가장 가까운 vertex
            nearest_idx = min(range(len(route_points)),
                              key=lambda idx: haversine(my_pos["lat"], my_pos["lng"],
                                                        route_points[idx]["lat"], route_points[idx]["lng"]))
            min_d = haversine(my_pos["lat"], my_pos["lng"],
                              route_points[nearest_idx]["lat"], route_points[nearest_idx]["lng"])
            on_route = (min_d <= 30)
            same_lane = None
            print(f"📏 내 차량-구급차 경로 거리: {min_d:.2f} m")

            # (4) 진행 방향 동일 여부
            if on_route and 0 < nearest_idx < len(route_points)-1:
                prev_p, next_p = route_points[nearest_idx-1], route_points[nearest_idx+1]
                v_route = (next_p["lng"] - prev_p["lng"], next_p["lat"] - prev_p["lat"])
                v_car = (my_next["lng"] - my_pos["lng"], my_next["lat"] - my_pos["lat"]) if my_next else (0, 0)
                cos_theta = cosine_similarity(v_car, v_route)

                raw_same_lane = None
                if cos_theta > 0.2:
                    raw_same_lane = True
                elif cos_theta < -0.2:
                    raw_same_lane = False

                # 안정화 처리
                if raw_same_lane is not None:
                    if raw_same_lane == self.last_same_lane:
                        self.same_lane_count += 1
                    else:
                        self.same_lane_count = 1
                        self.last_same_lane = raw_same_lane
                    if self.same_lane_count >= 3:
                        self.stable_same_lane = raw_same_lane

                same_lane = self.stable_same_lane

            # (5) 직선 거리
            dist_m = haversine(my_pos["lat"], my_pos["lng"], current["lat"], current["lng"])

            # ✅ 교차 여부 추적
            if dist_m < 30:
                self.crossed = True
            if self.crossed and dist_m > 30:
                print("🚑 구급차가 이미 지나감 → idle 처리")
                return None, None, False, False

            # (6) 최종 판정
            is_same_road_and_dir = False
            is_nearby = False

            if on_route and same_lane is True:
                print("같은 경로")
                is_same_road_and_dir = True
            elif dist_m <= 500:
                print("⚠️ 다른 경로지만 가까움")
                is_nearby = True

            return eta, dist_m, is_same_road_and_dir, is_nearby

        except Exception as e:
            print("⚠️ 상태 계산 실패:", e)
            return None, None, None, None
