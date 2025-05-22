from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import base64
import threading
import webbrowser
import time
from collections import deque, Counter
import numpy as np
from keras.models import load_model
from flask import Flask, jsonify, session  # session eklediğine dikkat et

app = Flask(__name__)
app.secret_key = 'gizli_bir_anahtar'  # session kullanmak için zorunlu

# Duyguyu session'da sakladığını varsayıyorum
@app.route('/get_emotion')
def get_emotion():
    emotion = session.get('emotion', 'neutral')  # varsayılan: neutral
    return jsonify({'emotion': emotion})

socketio = SocketIO(app)

cap = None


model = load_model("models/model (7).h5", compile=False)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

emotions = ['Angry','Happy', 'Neutral','Sad', 'Surprise']
current_emotion = "Detecting..."

emotion_history = deque(maxlen=60)  # 3 saniyeye yetecek kadar

def reset_emotion_state():
    global current_emotion, emotion_history, final_decided_emotion, start_time
    current_emotion = "Detecting..."
    emotion_history.clear()
    final_decided_emotion = None
    start_time = time.time()

def get_stable_emotion():
    if not emotion_history:
        return "?"
    emotion_counts = Counter(emotion_history)
    most_common_emotion, _ = emotion_counts.most_common(1)[0]
    return most_common_emotion

final_decided_emotion = None
start_time = time.time()
observation_duration = 2.2  # saniye

def get_emotion_from_frame(frame):
    global current_emotion

    faces = face_cascade.detectMultiScale(frame, 1.3, 5)

    if len(faces) > 0:
        (x, y, w, h) = max(faces, key=lambda b: b[2] * b[3])
        face = frame[y:y + h, x:x + w]

        face = cv2.resize(face, (48, 48))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        face = face / 255.0
        face = np.reshape(face, (1, 48, 48, 1))

        prediction = model.predict(face, verbose=0)
        confidence = np.max(prediction)

        if confidence > 0.1:
            emotion_label = np.argmax(prediction)
            current_emotion = emotions[emotion_label]
            emotion_history.append(current_emotion)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(frame, current_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)

def detect_dominant_emotion():
    if not emotion_history:
        return None
    emotion_counts = Counter(emotion_history)
    most_common = emotion_counts.most_common(1)
    return most_common[0][0] if most_common else None

def video_emitter():
    global final_decided_emotion, start_time
    cap = cv2.VideoCapture(0)  # Kamerayı şimdi başlat

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        get_emotion_from_frame(frame)

        current_time = time.time()
        elapsed = current_time - start_time

        # 3 saniye gözlem, sonra karar ver
        if elapsed < observation_duration:
            dominant_emotion = None
        elif final_decided_emotion is None:
            final_decided_emotion = detect_dominant_emotion()
            print("Karar verilen duygu:", final_decided_emotion)
            dominant_emotion = final_decided_emotion
        else:
            dominant_emotion = final_decided_emotion

        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('video_feed', {
            'data': frame_base64,
            'emotion': current_emotion,
            'final_emotion': dominant_emotion
        })

        time.sleep(0.05)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print("Web client connected!")
    reset_emotion_state()

@socketio.on('start_camera')
def handle_start_camera():
    print("Kamera başlatılıyor...")
    reset_emotion_state()
    
    threading.Thread(target=video_emitter, daemon=True).start()



def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
  #  threading.Thread(target=video_emitter, daemon=True).start()
    threading.Timer(1.25, open_browser).start()
    socketio.run(app, debug=False)
