# python imports
from flask import Flask, render_template, request, jsonify, send_file
import requests
import pyttsx3
import tempfile
import os

# create the Flask app
app = Flask(__name__)

# serve the index.html page
@app.route('/')
def index():
    return render_template('index.html')

# handle image uploads and OCR processing
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            text_output = process_image(file)
            return jsonify({'text': text_output})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# process the image to extract text
def process_image(file):
    api_endpoint = "https://yonchee-ai-service.cognitiveservices.azure.com/vision/v3.2/ocr"
    api_key = '38fda8ef3d6243b8bb7739e9a20f0d07' # your API key
    headers = {'Ocp-Apim-Subscription-Key': api_key, 'Content-Type': 'application/octet-stream'}
    params = {'language': 'unk', 'detectOrientation': 'true'}

    response = requests.post(api_endpoint, headers=headers, params=params, data=file.read())
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error: {e.response.status_code} - {e.response.reason}"
        app.logger.error(error_msg)
        raise Exception(f"OCR API Connection Failed: {error_msg}") from e

    analysis = response.json()
    if "error" in analysis:
        error_message = analysis['error']['message']
        app.logger.error('OCR API returned an error: %s', error_message)
        raise Exception(f"OCR API Error: {error_message}")

    text_output = ' '.join(
        [' '.join([word['text'] for word in line['words']])
         for region in analysis.get('regions', [])
         for line in region['lines']]
    )
    return text_output

# synthesize text into speech
@app.route('/synthesize-speech', methods=['POST'])
def synthesize_speech():
    text = request.data.decode('utf-8')
    if text:
        temp_dir = tempfile.mkdtemp()
        filename = os.path.join(temp_dir, 'output.mp3')
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.save_to_file(text, filename)
        engine.runAndWait()
        return send_file(filename, as_attachment=True, mimetype='audio/mpeg')
    return jsonify({'error': 'No text provided'}), 400

# run the Flask app
if __name__ == '__main__':
    app.run(debug=True)