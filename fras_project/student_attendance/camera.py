

import cv2
import face_recognition
import mediapipe as mp
import numpy as np
from datetime import datetime
import time  

from .models import Student  
from .attendance_utils import mark_login, mark_logout


class VideoCamera:
    def __init__(self, known_face_encodings, known_face_names, recognize_faces=True, detection_model='hog', action=None):
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        self.known_face_encodings = known_face_encodings
        self.known_face_names = known_face_names
        self.recognize_faces = recognize_faces
        self.detection_model = detection_model
        self.action = action

        # Mediapipe Face Mesh for landmarks
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

        # Blink detection variables
        self.EAR_THRESHOLD = 0.25 
        self.CONSEC_FRAMES = 3 

        self.blink_counter = 0  
        self.total_blinks = 0

        self.frame_counter = 0
        self.last_face_locations = []
        self.last_face_names = []

        self.last_action_time = {}  

        print("✅ Loaded roll numbers:", self.known_face_names)

    def __del__(self):
        if self.video.isOpened():
            self.video.release()
        cv2.destroyAllWindows()

    def eye_aspect_ratio(self, eye_landmarks):
        
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def get_eye_landmarks(self, landmarks, image_width, image_height):
        
        right_eye_indices = [33, 160, 158, 133, 153, 144]
        left_eye_indices = [362, 385, 387, 263, 373, 380]

        right_eye = []
        left_eye = []

        for idx in right_eye_indices:
            lm = landmarks[idx]
            right_eye.append(np.array([lm.x * image_width, lm.y * image_height]))

        for idx in left_eye_indices:
            lm = landmarks[idx]
            left_eye.append(np.array([lm.x * image_width, lm.y * image_height]))

        return np.array(right_eye), np.array(left_eye)

    def get_frame(self):
        success, frame = self.video.read()
        if not success:
            return None

        image_height, image_width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        
        results = self.face_mesh.process(rgb_frame)

        blinked = False

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            
            right_eye, left_eye = self.get_eye_landmarks(landmarks, image_width, image_height)

           
            right_ear = self.eye_aspect_ratio(right_eye)
            left_ear = self.eye_aspect_ratio(left_eye)
            avg_ear = (right_ear + left_ear) / 2.0

           
            if avg_ear < self.EAR_THRESHOLD:
                self.blink_counter += 1
            else:
                if self.blink_counter >= self.CONSEC_FRAMES:
                    self.total_blinks += 1
                    blinked = True
                self.blink_counter = 0

       
        self.frame_counter += 1
        if self.frame_counter % 3 == 0:
            small_frame = cv2.resize(frame, (0, 0), fx=0.15, fy=0.15)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame, model=self.detection_model)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []

            tolerance = 0.6

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]

                      
                        if self.total_blinks < 1:  
                            name = "Fake/No Blink"
                            print("❌ Blink not detected. Skipping attendance.")
                        else:
                            if self.action and name != "Fake/No Blink":
                                now_ts = time.time()
                                cooldown_seconds = 60 
                                last_time = self.last_action_time.get(name, 0)
                                if now_ts - last_time > cooldown_seconds:
                                    self.last_action_time[name] = now_ts  
                                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    print(f"✅ {name} - {self.action.upper()} at {now_str}")

                                    try:
                                        student = Student.objects.get(Roll_no=name)
                                        print(f"🎯 Student found: {student.Fullname} ({student.Roll_no})")

                                        if self.action == 'login':
                                            mark_login(student)
                                            print("✅ mark_login() called.")
                                        elif self.action == 'logout':
                                            mark_logout(student)
                                            print("✅ mark_logout() called.")

                                    except Student.DoesNotExist:
                                        print(f"❌ Student not found in DB: {name}")
                                    except Exception as e:
                                        print(f"🔥 Error calling attendance function: {e}")
                                else:
                                    print(f"⏳ Cooldown active for {name}, skipping attendance call.")

                face_names.append(name)

            self.last_face_locations = face_locations
            self.last_face_names = face_names

        
        for (top, right, bottom, left), name in zip(self.last_face_locations, self.last_face_names):
            top *= 6
            right *= 6
            bottom *= 6
            left *= 6

            color = (0, 255, 0) if name != "Fake/No Blink" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

            
            cv2.putText(frame, f"Blinks: {self.total_blinks}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes() if ret else None
