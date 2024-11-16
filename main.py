import cv2
import speech_recognition as sr
import threading
from translate import Translator
import pyttsx3

# Initialize the translator (English to German)
translator = Translator(to_lang="german")

# Load Haar cascades for face and eye detection
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

# Initialize the recognizer
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Initialize pyttsx3 for text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

# Flag to stop the loop
stop_flag = False
recognized_text = "Listening for speech..."
translated_text = "Translation will appear here."


def speak_text(text):
    """Function to convert text to speech."""
    engine.say(text)
    engine.runAndWait()


def recognize_and_translate():
    """Thread function to perform speech recognition and translation."""
    global recognized_text, translated_text, stop_flag
    print("Adjusting microphone for background noise... Please wait.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    print("You can start speaking now...")

    while not stop_flag:
        try:
            with mic as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5)
            # Recognize speech
            try:
                recognized_text = recognizer.recognize_google(audio)
                print(f"Recognized Speech: {recognized_text}")

                # Translate to German
                translated_text = translator.translate(recognized_text)
                print(f"Translated to German: {translated_text}")

                # Speak the translated text
                speak_text(translated_text)
            except sr.UnknownValueError:
                recognized_text = "Sorry, I didn't understand that."
                translated_text = ""
            except sr.RequestError as e:
                recognized_text = f"Speech Recognition Error: {e}"
                translated_text = ""
        except Exception as e:
            print(f"Error during recognition: {e}")


# Start speech recognition and translation in a separate thread
speech_thread = threading.Thread(target=recognize_and_translate)
speech_thread.start()

# Open the default camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not access the camera.")
    stop_flag = True
    exit()

print("Press 'q' to exit.")

try:
    while True:
        # Capture frame-by-frame
        ret, frame = camera.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            # Detect eyes within the face region
            eyes = eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 127, 255), 2)

        # Add recognized text and translation to the video frame
        cv2.putText(frame, "English: " + recognized_text, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "German: " + translated_text, (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA)

        # Display the frame
        cv2.imshow('Live Camera Feed with Speech Recognition, Translation, and Face Detection', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_flag = True
            break
except KeyboardInterrupt as e:
    stop_flag = True
    print(e)
finally:
    # Release resources
    camera.release()
    cv2.destroyAllWindows()
    speech_thread.join()
