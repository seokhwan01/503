import json
import time
import paho.mqtt.client as mqtt
from vehicle import Car
from ambulance_status import AmbulanceStatus
from utils import load_my_coords
import subprocess
from avoid_logic import decide_avoid_dir
from config import Config
from avoidance.lcd_display import LcdDisplay
from avoidance.tts_handler import announce_evasion   # ✅ 올바른 import
# ✅ 경로 파일 먼저 갱신

subprocess.run(["python", "save_route_points.py"])

lcd = LcdDisplay(vehicle_name="22ga 2222",vehicle_ip="192.168.137.123")

MQTT_BROKER = Config.MQTT_BROKER
MQTT_PORT = Config.MQTT_PORT
# MQTT_TOPIC = "ambulance/vehicles"
# MQTT_TOPIC = "ambulance/feedback"
# 방향 숫자 → 문자열 매핑

DIRECTION_MAP = {
    0: "직진",
    1: "오른쪽",
    2: "왼쪽"
}
last_calc_time = 0.0   # 처음엔 0초라고 가정

car_coords = load_my_coords()
ambu = AmbulanceStatus()

def send_to_hud(client, eta_sec, total_lanes, current_lane, avoid_dir, ambulance_lane, state="idle"):
    # send_to_hud(client, eta, 3, 2, 1, 2)
    payload = {
        "lanes": total_lanes,
        "currentLane": current_lane,
        "avoidDir": avoid_dir,
        "ambulanceLane": ambulance_lane,
        "state": state
    }

    # ETA 있을 때만 추가
    if eta_sec is not None:
        eta_min, eta_s = divmod(int(eta_sec), 60)
        payload["eta"] = f"{eta_min}m {eta_s}s"

    client.publish("car/hud", json.dumps(payload, ensure_ascii=False))
    print(f"📤 HUD에 전송 → {payload}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT 연결 성공")
        client.subscribe("ambulance/vehicles")
        client.subscribe("car2/current_lane")     # 현재 차선
        
    else:
        print("❌ 연결 실패:", rc)

def on_message(client, userdata, msg):
    
    raw_payload = msg.payload.decode()
    global last_calc_time
    now = time.time()
    raw_payload = msg.payload.decode()

    # 🚑 구급차 위치 메시지
    if msg.topic == "ambulance/vehicles":
        try:
            payload = json.loads(raw_payload)  # dict 기대
            ambu.update(payload)
        except Exception as e:
            print(f"[WARN] ambulance/vehicles 처리 실패 → {e}")


        # ✅ 2초마다 계산하도록 제한
        if now - last_calc_time >= 2.0:
            last_calc_time = now
            if car.index < len(car.coords):
                my_pos = car.coords[car.index]
                my_next = car.coords[car.index+1] if car.index+1 < len(car.coords) else None
                eta, dist, same_road_and_dir, is_nearby = ambu.calculate_status(my_pos, my_next)
                print(f"on_message | eta : {eta}, same_road_and_dir : {same_road_and_dir}")
                car.send_feedback(my_pos, same_road_and_dir)

                # 현재 차선은 car 객체에 저장된 값 사용
                current_lane = car.car_lane
                total_lanes = car.total_lanes
                avoid_dir, ambulance_lane = decide_avoid_dir(current_lane, total_lanes)

                if same_road_and_dir and eta:
                    # ✅ 같은 경로 & ETA 있음 → HUD/LCD/TTS 모두 실행
                    send_to_hud(client, eta, total_lanes, current_lane,
                                avoid_dir, ambulance_lane, state="samePath")

                    lcd.update_eta(int(eta/60), state="approaching")  # ETA 있을 때
                    direction_str = DIRECTION_MAP.get(avoid_dir, "직진")
                    announce_evasion(direction_str, int(eta/60))

                elif is_nearby:
                    # ✅ 같은 경로는 아니지만 가까움 → HUD에는 nearby, LCD는 초기화
                    send_to_hud(client, None, total_lanes, current_lane, None, None, state="nearby")
                    lcd.update_eta(None, state="nearby")              # 근처에만 있을 때

                else: #경로도 다르고 주변도 아님
                    send_to_hud(client, None, total_lanes, current_lane, None, None, state="idle")
                    lcd.update_eta(None, state="idle")                # 아무것도 없을 때
                    
    # 🚗 내 차량 차선 업데이트 메시지
    elif msg.topic == "car2/current_lane":
        try:
            current_lane = int(raw_payload) # int로 발행된다고 가정
            car.car_lane = current_lane   # Car 객체에 업데이트
            print(f"🚗 내 차선 업데이트: {car.car_lane}")
        except Exception as e:
            print(f"[WARN] car/current_lane 처리 실패 → {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

car = Car(client, car_coords)
car.start()
lcd.start()

client.loop_forever()
