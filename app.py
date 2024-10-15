import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    # Renders the homepage with the form to upload an image
    return render_template('index.html')

@app.route('/upload-image', methods=['POST'])
def upload_image():
    # Ensure an image part is present in the uploaded request
    if 'image' not in request.files:
        return 'No image part', 400
    file = request.files['image']
    # Ensure a file was actually uploaded
    if file.filename == '':
        return 'No selected file', 400
    
    # Process only if a file is uploaded
    if file:
        try:
            response_text = process_image(file.stream)
            return response_text
        except Exception as e:
            # Logging and returning error details
            app.logger.error(f"Error processing image: {str(e)}")
            return jsonify({'error': str(e)}), 500

def process_image(file_stream):
    # Configuration for the OCR API
    api_endpoint = "https://yonchee-ai-service.cognitiveservices.azure.com/vision/v3.2/ocr"
    api_key = '38fda8ef3d6243b8bb7739e9a20f0d07'
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/octet-stream'
    }
    params = {
        'language': 'unk',
        'detectOrientation': 'true'
    }
    # Making the POST request to the OCR API
    response = requests.post(api_endpoint, headers=headers, params=params, data=file_stream)
    analysis = response.json()

    # Check for errors in the API response
    if 'error' in analysis:
        raise Exception(analysis['error']['message'])

    # Extracting text from the response
    text_output = []
    for region in analysis.get('regions', []):
        for line in region.get('lines', []):
            line_text = ' '.join([word['text'] for word in line.get('words', [])])
            text_output.append(line_text)
    return ' '.join(text_output)

if __name__ == '__main__':
    app.run(debug=True)  # Run in debug mode