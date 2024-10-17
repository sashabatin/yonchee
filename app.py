# Python imports
from flask import Flask, render_template, request, jsonify, send_file
import requests
import azure.cognitiveservices.speech as speechsdk
import tempfile
import os

# Create the Flask app
app = Flask(__name__)

# Serve the index.html page
@app.route('/')
def index():
    return render_template('index.html')

# Handle image uploads and OCR processing
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        text_output = process_image(file)
        return jsonify({'text': text_output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Process image to extract text through the OCR API
def process_image(file):
    api_endpoint = "https://eastus.api.cognitive.microsoft.com/vision/v3.2/ocr"
    api_key = os.environ.get('OCR_API_KEY')
    headers = {'Ocp-Apim-Subscription-Key': api_key, 'Content-Type': 'application/octet-stream'}
    params = {'language': 'unk', 'detectOrientation': 'true'}

    try:
        response = requests.post(api_endpoint, headers=headers, params=params, data=file.read())
        response.raise_for_status()
    except requests.HTTPError as e:
        app.logger.error(f"HTTP Error: {response.status_code} - {response.reason}")
        raise Exception(f"OCR API connection failed: HTTP Error: {response.status_code} - {response.reason}")
    except requests.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

    analysis = response.json()
    if "error" in analysis:
        error_message = analysis['error']['message']
        raise Exception(f"OCR API Error: {error_message}")

    text_output = ' '.join([' '.join([word['text'] for word in line['words']]) for region in analysis.get('regions', []) for line in region['lines']])
    return text_output

# Synthesize text into speech using Azure AI
@app.route('/synthesize-speech', methods=['POST'])
def synthesize_speech():
    text = request.data.decode('utf-8')
    if text:
        speech_key = os.environ.get('AZURE_SPEECH_KEY')
        service_region = os.environ.get('AZURE_SERVICE_REGION')
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_voice_name = "uk-UA-OstapNeural"

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            temp_dir = tempfile.mkdtemp()
            filename = os.path.join(temp_dir, 'output.mp3')
            with open(filename, "wb") as audio_file:
                audio_file.write(result.audio_data)
            return send_file(filename, as_attachment=True, mimetype='audio/mpeg')
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return jsonify({'error': f"Speech synthesis canceled: {cancellation_details.reason}"}), 500

        return jsonify({'error': 'Text-to-speech synthesis failed.'}), 500

    return jsonify({'error': 'No text provided'}), 400