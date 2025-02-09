from flask import Flask, request, render_template
import os
import openai
import subprocess
import time

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["AUDIO_FOLDER"] = AUDIO_FOLDER

#client = openai.OpenAI(api_key="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")

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def convert_mp4_to_mp3(video_path):
    """Extracts audio using ffmpeg."""
    audio_path = os.path.join(app.config["AUDIO_FOLDER"], os.path.basename(video_path).replace(".mp4", ".mp3"))
    command = f'ffmfpeg -i "{video_path}" -q:a 0 -map a "{audio_path}"'
    subprocess.run(command, shell=True)
    return audio_path

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text

def get_chat_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def summarize_text(text):
    """Summarizes the transcribed text in the same language as the input."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful AI that summarizes text while keeping the same language as the input."},  # ✅ Ensure same language
            {"role": "user", "content": f"Summarize this text:\n{text}"}
        ]
    )
    return response.choices[0].message.content


@app.route("/", methods=["GET", "POST"])
def upload_file():
    transcription = ""
    summary = ""

    if request.method == "GET":
        return render_template("upload.html")  # ✅ Fix

    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # If it's an mp4 file, extract audio and transcribe it
        if file.filename.endswith(".mp4"):
            audio_path = convert_mp4_to_mp3(file_path)
            transcription = transcribe_audio(audio_path)
        else:
            transcription = transcribe_audio(file_path)
        
        summary = summarize_text(transcription)

        print("Transcription:", transcription)  # ✅ Debugging Output
        print("Summary:", summary)  # ✅ Debugging Output

        return render_template("upload_result.html", transcription=transcription, summary=summary)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True)
