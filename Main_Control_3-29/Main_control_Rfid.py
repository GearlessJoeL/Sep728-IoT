import time
import RPi.GPIO as GPIO
import rfid_reader_v2 as rfid_reader
import led_control_v2 as led_control
import buzzer_control_v3 as buzzer_control
import servo_control_v2 as servo_control
import threading
from rfid_reader_v2 import exit_event
from face_recog import FaceRecognition
from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import queue
import json

# PubNub Configuration
pnconfig = PNConfiguration()
pnconfig.subscribe_key = 'sub-c-a6797b99-e665-4db1-b0ec-2cb77ad995ed'
pnconfig.publish_key = 'pub-c-e478cfb1-92ef-4faa-93cc-d1c4022ecb19'
pnconfig.uuid = '321'
pubnub = PubNub(pnconfig)

# Channel names
CONTROL_CHANNEL = "MingyiHUO728"
STATUS_CHANNEL = "MingyiHUO728"

# Initialize GPIO mode
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Initialize modules
face = FaceRecognition()

rfid_success = False
face_success = False
remote_unlock = False
card = None

class MySubscribeCallback(SubscribeCallback):
    def message(self, pubnub, message):
        global remote_unlock
        if message.channel == CONTROL_CHANNEL:
            if message.message.get('message_type') == "control" and message.message.get('action') == 'unlock':
                remote_unlock = True
                print("message received")

pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels([CONTROL_CHANNEL]).execute()

def publish_status(status_data):
    status_data["message_type"] = "status"  # Add message type
    pubnub.publish().channel(STATUS_CHANNEL).message(status_data).sync()

def rfid_authentication():
    global rfid_success, card
    while not rfid_success and not face_success and not remote_unlock:
        if face_success or remote_unlock:
            print("Face recognition succeeded or remote unlock activated, RFID thread exiting.")
            exit_event.set()
            return

        led_control.led_waiting()
        card_id = rfid_reader.read_rfid()
        print(card_id)

        if card_id != None:
            rfid_success = True
            card = card_id
            if card_id == '860338929300':
                print('RFID verification successful')
                led_control.led_success()
                buzzer_control.buzzer_success()
                servo_control.unlock()
                
            else:
                print('fake card!')
                
            return


def remote_authentication():
    global remote_unlock
    while not rfid_success and not face_success and not remote_unlock:
        time.sleep(0.5)
        if remote_unlock == True:
            print("Received remote unlock command")
            led_control.led_success()
            buzzer_control.buzzer_success()
            servo_control.unlock()
            exit_event.set()
            return
        


def face_authentication():
    global face_success
    fail_count = 0
    print('please face the camera...')
    while not rfid_success and not face_success and not remote_unlock:
        face.recognize()
        time.sleep(0.5)
        if face.get_name() != "":
            if face.get_name() == "Unknown":
                fail_count += 1
#                 print(fail_count)
                if fail_count > 4:
                    status_data = {
                        "state": 0,
                        "type": "face",
                        "time": time.time(),
                        "name": "Unknown"
                    }
                    print("Unknown person detected")
                    publish_status(status_data)
                    fail_count = 0
            else:
                led_control.led_success()
                buzzer_control.buzzer_success()
                servo_control.unlock()
                face_success = True
                exit_event.set()
#                 print("ex")
                return

try:
    rfid_thread = threading.Thread(target=rfid_authentication)
    face_thread = threading.Thread(target=face_authentication)
    remote_thread = threading.Thread(target=remote_authentication)

    rfid_thread.start()
    face_thread.start()
    remote_thread.start()

    rfid_thread.join()
    face_thread.join()
    remote_thread.join()
#     print("exed")
    if face_success or rfid_success or remote_unlock: #or fingerprint_success
        status_data = {
            "state": 1,
            "type": "",
            "time": time.time(),
            "name": ""
        }

        if face_success:
            status_data["type"] = "face"
            status_data["name"] = face.get_name()
        elif rfid_success:
            status_data["type"] = "rfid"
            status_data["name"] = card
            status_data["state"] = 1 if card == '860338929300' else  0 
        elif remote_unlock:
            status_data["type"] = "remote"
            status_data["name"] = "Remote Access"
        # elif fingerprint_success:
        #     status_data["type"] = "fingerprint"
        #     status_data["name"] = "Fingerprint"
        else:
            status_data["type"] = "unknown"
            status_data["name"] = "Unknown"

        status_data["time"] = time.time()
        publish_status(status_data)
        
        print("The door will lock in 5 seconds!")
        time.sleep(5)
        
        face.clear_name()
        servo_control.lock()
        
        # Publish locked status
        status_data["state"] = 0

        
        time.sleep(0.1)
        print("The door has been locked!")




except KeyboardInterrupt:
    print('Program interrupted. Cleaning up GPIO settings...')

finally:
    pubnub.unsubscribe().channels([CONTROL_CHANNEL]).execute()
    GPIO.cleanup()
