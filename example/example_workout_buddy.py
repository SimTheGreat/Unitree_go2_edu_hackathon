from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.video.video_client import VideoClient
import cv2
import numpy as np
import sys
import time
import PoseModule as pm
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_go_msg_dds__SportModeState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_
from unitree_sdk2py.go2.sport.sport_client import (
    SportClient,
    PathPoint,
    SPORT_PATH_POINT_SIZE,
)
import math
from dataclasses import dataclass
#all downloads

@dataclass
class TestOption:
    name: str
    id: int

option_list = [
    TestOption(name="damp", id=0),         
    TestOption(name="stand_up", id=1),     
    TestOption(name="stand_down", id=2),   
    TestOption(name="move forward", id=3),         
    TestOption(name="move lateral", id=4),    
    TestOption(name="move rotate", id=5),  
    TestOption(name="stop_move", id=6),  
    TestOption(name="switch_gait", id=7),    
    TestOption(name="switch_gait", id=8),
    TestOption(name="balanced stand", id=9),     
    TestOption(name="recovery", id=10),
    TestOption(name="recovery", id=10),       
    TestOption(name="left flip", id=11),      
    TestOption(name="back flip", id=12),
    TestOption(name="free walk", id=13),  
    TestOption(name="free bound", id=14), 
    TestOption(name="free avoid", id=15),  
    TestOption(name="walk stair", id=16), 
    TestOption(name="walk upright", id=17),
    TestOption(name="cross step", id=18),
    TestOption(name="free jump", id=19)       
]
#different motions the sdk offers

class UserInterface:
    def __init__(self):
        self.test_option_ = None

    def convert_to_int(self, input_str):
        try:
            return int(input_str)
        except ValueError:
            return None

    def terminal_handle(self):
        input_str = input("Enter id or name: \n")

        if input_str == "list":
            self.test_option_.name = None
            self.test_option_.id = None
            for option in option_list:
                print(f"{option.name}, id: {option.id}")
            return

        for option in option_list:
            if input_str == option.name or self.convert_to_int(input_str) == option.id:
                self.test_option_.name = option.name
                self.test_option_.id = option.id
                print(f"Test: {self.test_option_.name}, test_id: {self.test_option_.id}")
                return

        print("No matching test option found.")


cv2.namedWindow("front_camera",cv2.WINDOW_NORMAL)
cv2.resizeWindow("front_camera", 740, 780)#resizes window




def update_feedback_and_count(elbow, shoulder, hip, direction, count, form):
    """Determines the feedback message and updates the count based on the angles."""
    feedback = "Fix Form"
    if elbow > 160 and shoulder > 40 and hip > 160:
        form = 1
    if form == 1:
        if elbow <= 90 and hip > 160:
            feedback = "Up"
            if direction == 0:
                count += 0.5
                direction = 1
        elif elbow > 160 and shoulder > 40 and hip > 160:
            feedback = "Down"
            if direction == 1:
                count += 0.5
                direction = 0
        else:
            feedback = "Fix Form"
    return feedback, count, direction, form

def draw_ui(img, per, bar, count, feedback, form):#Draws the UI elements on the frame
    
    if form == 1:
        cv2.rectangle(img, (580, 50), (600, 380), (0, 255, 0), 3)
        cv2.rectangle(img, (580, int(bar)), (600, 380), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(per)}%', (565, 430), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    cv2.rectangle(img, (0, 380), (100, 480), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, str(int(count)), (25, 455), cv2.FONT_HERSHEY_PLAIN, 5, (255, 0, 0), 5)
    
    cv2.rectangle(img, (500, 0), (640, 40), (255, 255, 255), cv2.FILLED)
    cv2.putText(img, feedback, (500, 40), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)


def get_black_screen():#Creates a black screen if there's an issue with the camera feed.
    
    return np.zeros((480, 640, 3), dtype=np.uint8)  
  

if __name__ == "__main__":#enter interface of ethernet cable connection
    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)
    detector = pm.poseDetector()
    count = 0
    direction = 0
    form = 0

    client = VideoClient()  # Create a video client
    
    client.SetTimeout(3.0)
    client.Init()
    test_option = TestOption(name=None, id=None) 
    user_interface = UserInterface()
    user_interface.test_option_ = test_option

    sport_client = SportClient()  
    sport_client.SetTimeout(10.0)
    sport_client.Init()

    while True:
        code, data = client.GetImageSample()
	
        if code == 0:
            # Convert to numpy image
            image_data = np.frombuffer(bytes(data), dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            if image is None:
                print("Warning: Received empty image. Displaying black screen.")
                image = get_black_screen()
        else:
            print("Get image sample error. Code:", code, "Retrying...")
            image = get_black_screen()
            time.sleep(1)  # Wait before retrying

        img = detector.findPose(image, False)
        lmList = detector.findPosition(img, False)
        if len(lmList) != 0:
            elbow = detector.findAngle(img, 11, 13, 15)
            shoulder = detector.findAngle(img, 13, 11, 23)
            hip = detector.findAngle(img, 11, 23, 25)
            per = np.interp(elbow, (90, 160), (0, 100))
            bar = np.interp(elbow, (90, 160), (380, 50))
            feedback, count, direction, form = update_feedback_and_count(elbow, shoulder, hip, direction, count, form)
            
            draw_ui(img, per, bar, count, feedback,form)
            
            if direction==1:#if down in pushup the robot goes down too
            	sport_client.StandDown()
            	
 
            else:#else robot goes up
            	sport_client.StandUp()
            	

            
        
        cv2.imshow("front_camera", img)


        # Press ESC to stop
        if cv2.waitKey(20) == 27:
            break
    print(count)
    cv2.destroyAllWindows()
