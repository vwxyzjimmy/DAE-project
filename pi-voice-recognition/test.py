import speech_recognition as sr
import pyaudio
r=sr.Recognizer()
def listen():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('now say something')
        print(r.energy_threshold)
        audio=r.listen(source)
        f1=open('Recorded.wav','wb')
        f1.write(audio.get_wav_data())
        f1.close()
        print(r.energy_threshold)
listen()
