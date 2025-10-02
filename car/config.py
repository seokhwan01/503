# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # MQTT 설정
    MQTT_BROKER = "10.210.98.208"   # ✅ 여기에 브로커 IP만 바꾸면 됨(변경 필수!!!!!)
    MQTT_PORT = 1883