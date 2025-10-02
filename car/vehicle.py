import json
import time
import threading

class Car:
    def __init__(self, client, coords, car_id="22ga 2222", total_lanes=3 ,car_lane=2): 
        self.client = client
        self.coords = coords
        self.car_id = car_id
        self.car_lane = car_lane
        self.total_lanes=total_lanes
        self.index = 0
        self.topic = "normalcar/web/current"
        self.topic_feedback = "ambulance/feedback"

    def send_position(self, pos):
        payload = {
            "car": self.car_id,
            "current": pos
        }
        self.client.publish(self.topic, json.dumps(payload, ensure_ascii=False))
        print(f"📤 내 차량 좌표 발행 → {payload}")
    
    def send_feedback(self, pos, same_road_and_dir):
        feedback = {
            "car": self.car_id,
            "current": pos,
            "total_lanes" : self.total_lanes,
            "car_lane": self.car_lane,
            "same_road_and_dir": same_road_and_dir,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.client.publish(self.topic_feedback, json.dumps(feedback, ensure_ascii=False))
        print(f"📤 구급차로 차량 정보 전송 → {feedback}")

    def drive_loop(self):
        while self.index < len(self.coords):
            pos = self.coords[self.index]
            print(f"\n🚗 내 차량 위치 업데이트: {pos}")
            self.send_position(pos)
            self.index += 1
            time.sleep(2.5)  # 10초마다 이동

    def start(self):
        t = threading.Thread(target=self.drive_loop, daemon=True)
        t.start()
