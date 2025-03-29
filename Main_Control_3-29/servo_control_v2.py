import RPi.GPIO as GPIO
import time

# 引脚定义
SERVO_PIN = 12  # 物理引脚位置 (BOARD 模式下的 Pin 12)

servo = None  # 全局变量，伺服电机的 PWM 对象
servo_initialized = False  # 引脚初始化状态变量


def init_servo():
    global servo, servo_initialized

    if not servo_initialized:  # 确保只初始化一次
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        servo = GPIO.PWM(SERVO_PIN, 50)  # 初始化 PWM (50Hz)
     
    if GPIO.getmode() is None:
        GPIO.setmode(GPIO.BOARD)
    elif GPIO.getmode() == GPIO.BCM:
        raise RuntimeError('GPIO 模式已被设置为 BCM，与 BOARD 不兼容。')

    GPIO.setwarnings(False)
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    servo.start(0)
    servo_initialized = True


def unlock():
    init_servo()
    print("解锁中...")
    servo.ChangeDutyCycle(7.5)  # 转到 90 度 (解锁)
    time.sleep(2)
    servo.ChangeDutyCycle(0)


def lock():
    init_servo()
    print("锁定中...")
    servo.ChangeDutyCycle(2.5)  # 转到 0 度 (锁定)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

def cleanup():
    global servo
    if servo:
        servo.stop()
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        print("解锁中...")
        unlock()
        print("锁定中...")
        lock()
    finally:
        cleanup()
