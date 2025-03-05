# Python imports
from flask import Flask, render_template, request, jsonify, send_file
import azure.cognitiveservices.speech as speechsdk
import tempfile
import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error('No image part in the request')
        return jsonify({'error': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        logger.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    try:
        text_output = process_image(file)
        return jsonify({'text': text_output})
    except Exception as e:
        logger.error(f'Error processing image: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Process image to extract text through the Document Intelligence API
def process_image(file):
    endpoint = os.environ.get('DOCUMENT_INTELLIGENCE_ENDPOINT')
    key = os.environ.get('DOCUMENT_INTELLIGENCE_KEY')
    if not endpoint or not key:
        raise Exception("DOCUMENT_INTELLIGENCE_ENDPOINT or DOCUMENT_INTELLIGENCE_KEY is not set")

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    # Read file content and send to Azure Document Intelligence
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-read", file.read()
    )
    result = poller.result()

    # Extract text from the result
    text_output = ''
    for page in result.pages:
        for line in page.lines:
            text_output += line.content + '\n'

    return text_output

# Synthesize text into speech using Azure AI
@app.route('/synthesize-speech', methods=['POST'])
def synthesize_speech():
    data = request.get_json()
    text = data.get('text')
    language = data.get('language', 'en')

    if text:
        speech_key = os.environ.get('AZURE_SPEECH_KEY')
        service_region = os.environ.get('AZURE_SERVICE_REGION')
        if not speech_key or not service_region:
            logger.error("AZURE_SPEECH_KEY or AZURE_SERVICE_REGION is not set")
            return jsonify({'error': "AZURE_SPEECH_KEY or AZURE_SERVICE_REGION is not set"}), 500

        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

        # Set the voice based on the chosen language
        if language == 'uk':
            speech_config.speech_synthesis_voice_name = "uk-UA-OstapNeural"
        elif language == 'ru':
            speech_config.speech_synthesis_voice_name = "ru-RU-DmitryNeural"
        elif language == 'es':
            speech_config.speech_synthesis_voice_name = "es-ES-AlvaroNeural"
        else:  # Default to English
            speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

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
            logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
            return jsonify({'error': f"Speech synthesis canceled: {cancellation_details.reason}"}), 500

        logger.error('Text-to-speech synthesis failed.')
        return jsonify({'error': 'Text-to-speech synthesis failed.'}), 500

    logger.error('No text provided')
    return jsonify({'error': 'No text provided'}), 400

# Run the application using Waitress if executed directly
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)