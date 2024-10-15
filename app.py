import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to the OCR API Service"

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return 'No image part'
    file = request.files['image']
    if file.filename == '':
        return 'No selected file'
    if file:
        response_text = process_image(file)
        return response_text

def process_image(file_stream):
    api_endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
    api_key = os.getenv('AZURE_COMPUTER_VISION_KEY')
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/octet-stream'
    }
    params = {
        'language': 'unk',
        'detectOrientation': 'true'
    }
    response = requests.post(api_endpoint + "vision/v3.2/ocr", headers=headers, params=params, data=file_stream)
    analysis = response.json()
    # Extracting text from the response
    text_output = ' '.join([line['text'] for region in analysis['regions'] for line in region['lines']])
    return text_output

if __name__ == '__main__':
    app.run(debug=True)