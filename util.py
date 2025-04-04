import cv2
import time
import math
import numpy as np
import HandTrackingModule as htm
import pyautogui

# Disable pyautogui safety feature
pyautogui.FAILSAFE = False

# Camera settings
wCam, hCam = 640, 480

# Try multiple camera indices
camera_indices = [0, 1]  # Try both 0 and 1
cap = None

for idx in camera_indices:
    print(f"Trying camera index: {idx}")
    cap = cv2.VideoCapture(idx)
    if cap.isOpened():
        ret, test_frame = cap.read()
        if ret:
            print(f"Successfully opened camera at index {idx}")
            break
        else:
            cap.release()

if cap is None or not cap.isOpened():
    print("Error: Could not open any camera. Exiting.")
    exit()

cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

# Create hand detector object
detector = htm.handDetector(maxHands=1, detectionCon=0.7, trackCon=0.7)

# Fingertip IDs
tipIds = [4, 8, 12, 16, 20]
mode = ''
active = 0

# Function to display text on screen
def putText(mode, loc=(250, 450), color=(0, 255, 255)):
    cv2.putText(img, str(mode), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL,
                3, color, 3)

# Main program loop
while True:
    success, img = cap.read()
    if not success:
        print("Failed to grab frame")
        # Try to reinitialize camera
        cap = cv2.VideoCapture(camera_indices[0])
        continue
        
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    fingers = []

    if len(lmList) != 0:
        # Thumb
        if lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1]:
            if lmList[tipIds[0]][1] >= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1]:
            if lmList[tipIds[0]][1] <= lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # Other fingers
        for id in range(1, 5):
            if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        # Determine mode based on finger positions
        if (fingers == [0, 0, 0, 0, 0]) & (active == 0):
            mode = 'N'
        elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) & (active == 0):
            mode = 'Scroll'
            active = 1
        elif (fingers == [1, 1, 1, 1, 1]) & (active == 0):
            mode = 'Cursor'
            active = 1

    # Scroll mode
    if mode == 'Scroll':
        active = 1
        putText(mode)
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        if len(lmList) != 0:
            if fingers == [0, 1, 0, 0, 0]:
                putText(mode='U', loc=(200, 455), color=(0, 255, 0))
                pyautogui.scroll(300)
            if fingers == [0, 1, 1, 0, 0]:
                putText(mode='D', loc=(200, 455), color=(0, 0, 255))
                pyautogui.scroll(-300)
            elif fingers == [0, 0, 0, 0, 0]:
                active = 0
                mode = 'N'

    # Cursor control mode
    if mode == 'Cursor':
        active = 1
        putText(mode)
        cv2.rectangle(img, (110, 20), (620, 350), (255, 255, 255), 3)

        if fingers[1:] == [0, 0, 0, 0]:  # Except thumb
            active = 0
            mode = 'N'
            print(mode)
        else:
            if len(lmList) != 0:
                x1, y1 = lmList[8][1], lmList[8][2]
                # Get screen dimensions
                w, h = pyautogui.size()
                X = int(np.interp(x1, [110, 620], [0, w - 1]))
                Y = int(np.interp(y1, [20, 350], [0, h - 1]))
                cv2.circle(img, (lmList[8][1], lmList[8][2]), 7, (255, 255, 255), cv2.FILLED)
                cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 255, 0), cv2.FILLED)  # Thumb

                if X % 2 != 0:
                    X = X - X % 2
                if Y % 2 != 0:
                    Y = Y - Y % 2
                
                # Smooth movement
                try:
                    # Move cursor using pyautogui
                    pyautogui.moveTo(X, Y)
                    
                    # Click when thumb is down
                    if fingers[0] == 0:
                        cv2.circle(img, (lmList[4][1], lmList[4][2]), 10, (0, 0, 255), cv2.FILLED)  # Thumb
                        pyautogui.click()
                except Exception as e:
                    print(f"Error moving cursor: {e}")

    # Calculate and display frame rate
    cTime = time.time()
    fps = 1 / ((cTime + 0.01) - pTime)
    pTime = cTime

    cv2.putText(img, f'FPS:{int(fps)}', (480, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
    cv2.imshow('Hand LiveFeed', img)

    # Exit by pressing q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()