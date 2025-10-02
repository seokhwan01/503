
import smbus2
import time
import threading
import os

class LcdDisplay:
    def __init__(self, i2c_addr=0x27, lcd_width=20, vehicle_name="22ga 2222", vehicle_ip=None):
        self.I2C_ADDR = i2c_addr
        self.LCD_WIDTH = lcd_width
        self.VEHICLE_NAME = vehicle_name
        self.VEHICLE_IP = self._get_local_ip(vehicle_ip)
        # LCD 상수
        self.LCD_CHR = 1
        self.LCD_CMD = 0
        self.LINE_ADDR = [0x80, 0xC0, 0x94, 0xD4]
        self.ENABLE = 0b00000100
        self.BACKLIGHT = 0b00001000

        self._bus = None
        self._thread_running = False
        self._lock = threading.Lock()
        self._latest_eta_minutes = None

    def _get_local_ip(self, static_ip=None):
        if static_ip: 
            return static_ip
        try:
            return os.popen("hostname -I").read().strip().split()[0]
        except Exception:
            return "0.0.0.0"
    def print_line(self, line: int, message: str):
        """LCD 특정 라인에 메시지를 출력합니다."""
        # 메시지를 LCD 한 줄 크기에 맞게 패딩
        message = message.ljust(self.LCD_WIDTH, " ")
        # 커서 이동
        self._write(self.LINE_ADDR[line], self.LCD_CMD)
        # 문자 하나씩 출력
        for char in message[:self.LCD_WIDTH]:
            self._write(ord(char), self.LCD_CHR)

    def _write(self, bits, mode):
        high = mode | (bits & 0xF0) | self.BACKLIGHT
        low  = mode | ((bits << 4) & 0xF0) | self.BACKLIGHT
        self._bus.write_byte(self.I2C_ADDR, high)
        self._toggle(high)
        self._bus.write_byte(self.I2C_ADDR, low)
        self._toggle(low)

    def _toggle(self, bits):
        time.sleep(0.0005)
        self._bus.write_byte(self.I2C_ADDR, bits | self.ENABLE)
        time.sleep(0.0005)
        self._bus.write_byte(self.I2C_ADDR, (bits & ~self.ENABLE))
        time.sleep(0.0001)

    def _init_lcd(self):
        self._write(0x33, self.LCD_CMD)
        self.  _write(0x32, self.LCD_CMD)
        self._write(0x06, self.LCD_CMD)
        self._write(0x0C, self.LCD_CMD)
        self._write(0x28, self.LCD_CMD)
        self._write(0x01, self.LCD_CMD)
        time.sleep(0.005)

    def update_eta(self, minutes, state):
            self._latest_eta_minutes = minutes
            eta_text = f"ETA: {minutes:02d} min" if minutes is not None else "ETA: -- min"

            self.print_line(0, f"{self.VEHICLE_NAME}")
            self.print_line(1, f"IP: {self.VEHICLE_IP}")
            self.print_line(2, eta_text)

            # 상태 표시
            if state == "approaching" and minutes is not None:
                self.print_line(3, "Approaching".ljust(self.LCD_WIDTH))
            elif state == "nearby":
                self.print_line(3, "Nearby".ljust(self.LCD_WIDTH))
            elif state == "idle":
                self.print_line(3, "Idle".ljust(self.LCD_WIDTH))
            else:
                self.print_line(3, "ERROR".ljust(self.LCD_WIDTH))
   

    def start(self):
        try:
            self._bus = smbus2.SMBus(1)
            self._init_lcd()
            print("[LCD] ready.")

            # ✅ LCD 기본 표시
            self.update_eta(None, state="idle")   # ETA 없음, Idle 상태로 표시
        except Exception as e:
            print(f"[LCD] init failed: {e}")


    def stop(self):
        try:
            if self._bus is not None:
                self._bus.close()
                self._bus = None
                print("[LCD] stopped.")
        except Exception as e:
            print(f"[LCD] stop error: {e}")