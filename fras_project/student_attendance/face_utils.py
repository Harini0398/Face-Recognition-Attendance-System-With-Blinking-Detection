
import os
import face_recognition
from django.conf import settings

def load_known_faces():
    known_face_encodings = []
    known_face_names = []

    base_folder = settings.STUDENT_PROFILE_ROOT  

    
    for student_folder in os.listdir(base_folder):
        student_folder_path = os.path.join(base_folder, student_folder)
        if os.path.isdir(student_folder_path):
           
            for filename in os.listdir(student_folder_path):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(student_folder_path, filename)
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        known_face_encodings.append(encodings[0])
                        known_face_names.append(student_folder)  

    return known_face_encodings, known_face_names
