import os
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Get API key from environment variables
FISH_API_KEY = os.environ.get('FISH_API_KEY')
FISH_API_URL = 'https://api.fish.audio/v1/tts'
DEFAULT_VOICE_ID = 'default'

@app.route('/tts', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        if not FISH_API_KEY:
            logger.error('FISH_API_KEY not set')
            return jsonify({'error': 'API key not configured'}), 500
        
        voice_id = data.get('voice_id', DEFAULT_VOICE_ID)
        
        headers = {
            'Authorization': f'Bearer {FISH_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'text': text,
            'voice_id': voice_id,
        }
        
        logger.info(f'Generating speech for: {text[:50]}...')
        
        response = requests.post(FISH_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            error_msg = f'Fish API Error: {response.status_code}'
            try:
                error_data = response.json()
                error_msg = error_data.get('message', error_msg)
            except:
                pass
            logger.error(error_msg)
            return jsonify({'error': error_msg}), response.status_code
        
        logger.info('Speech generated successfully')
        return send_file(
            io.BytesIO(response.content),
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
        
    except requests.exceptions.Timeout:
        logger.error('Request timed out')
        return jsonify({'error': 'Request timed out'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {str(e)}')
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(FISH_API_KEY)
    })

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Fish Audio TTS Proxy',
        'status': 'running',
        'endpoints': {
            '/tts': 'POST - Convert text to speech',
            '/health': 'GET - Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
