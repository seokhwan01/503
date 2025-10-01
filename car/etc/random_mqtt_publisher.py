import json
import random
import time
import paho.mqtt.client as mqtt

# MQTT 브로커 설정
BROKER = "localhost"   # 필요시 브로커 주소 변경
PORT = 1883
TOPIC = "car/status"

# MQTT 클라이언트 초기화
client = mqtt.Client()
client.connect(BROKER, PORT, 60)

while True:
    # 랜덤 데이터 생성
    payload = {
        "lanes": 3,
        "currentLane": random.randint(1, 3),      # 1~3 랜덤
        "avoidDir": random.choice([0, 1, 2]),     # 0=직진, 1=오른쪽, 2=왼쪽
        "ambulanceLane": random.randint(1, 3),    # 구급차 차선
        "state":"samePath",
        "eta": f"{random.randint(1,20)}m {random.randint(0,59)}s" 
    }

    # JSON 직렬화
    message = json.dumps(payload, ensure_ascii=False)

    # MQTT 발행
    client.publish(TOPIC, message)
    print(f"[MQTT Sent] {TOPIC} {message}")

    # 1초마다 전송 (원하면 조절 가능)
    time.sleep(4)
