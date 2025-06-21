import base64
import os
import random
from pathlib import Path
from flask import Flask, render_template, redirect, jsonify, request, session
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
)
import asyncio
from functools import partial
import replicate
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# List of Harry Potter themed passwords
PASSWORDS = [
    "alohomora",    # Unlocking spell
    "lumos",        # Light spell
    "wingardium",   # Levitation spell
    "expecto",      # Part of patronus spell
    "accio",        # Summoning spell
    "nox",          # Darkness spell
    "riddikulus",   # Anti-boggart spell
    "protego",      # Shield spell
    "leviosa",      # Part of levitation spell
    "patronus",     # Protection spell
    "stupefy",      # Stunning spell
    "expelliarmus", # Disarming spell
]

def call_flux_kontext(word):
    """
    Generate an image using Replicate Flux model with a word embedded in the prompt.
    
    Args:
        word (str): The word to embed in the prompt
        
    Returns:
        str: Base64 encoded image data URL for direct embedding in HTML
        
    Raises:
        Exception: If image generation fails
    """
    try:
        # Create a magical Harry Potter themed prompt that embeds the word
        prompt = f"A wooden plack with a '{word}' in elegant glowing letters, Harry Potter magical style, enchanted atmosphere, golden light, magical particles, ethereal glow, fantasy art, high quality, detailed"
        
        input = {
            "prompt": prompt,
            "input_image": "",
            "output_format": "jpg"
        }

        output = replicate.run(
            "black-forest-labs/flux-kontext-pro",
            input=input
        )
        
        # Get the image URL from the output
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        else:
            raise Exception("No image URL returned from Flux model")
        
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Convert to PIL Image
        image = Image.open(BytesIO(response.content))
        
        # Convert to base64 for embedding in HTML
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Return as data URL for direct embedding
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"Error generating image with Flux: {str(e)}")
        # Return a fallback/placeholder image or None
        return None

def run_async(func):
    """Decorator to run an async function in a synchronous context"""
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    def sync_wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(wrapper(*args, **kwargs))
        finally:
            loop.close()
    
    sync_wrapper.__name__ = func.__name__
    return sync_wrapper

@app.route('/')
def index():
    # Set a random password in the session if not already set
    if 'password' not in session:
        session['password'] = random.choice(PASSWORDS)
    hovering_image = call_flux_kontext(session['password'])
    return render_template('index.html', password=session['password'], hovering_image=hovering_image)

@app.route('/clear-session', methods=['POST'])
def clear_session():
    session.clear()
    return jsonify({'success': True})

@app.route('/redirect-to-instagram')
def redirect_to_instagram():
    return redirect('https://www.instagram.com')

# Load environment variables
load_dotenv()

# Initialize Deepgram
api_key = os.getenv('DEEPGRAM_API_KEY')
if not api_key:
    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
deepgram = DeepgramClient(api_key)


from deepgram import DeepgramClient, PrerecordedOptions, FileSource

@app.route('/generate_password_text', methods=['POST'])
@run_async
async def generate_password_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not audio_file.filename:
        return jsonify({'error': 'Empty audio file provided'}), 400

    try:
        # Read the audio file content
        audio_data = audio_file.read()
        if not audio_data:
            return jsonify({'error': 'Empty audio content'}), 400

        options = PrerecordedOptions(
                    punctuate=True,
                    model="nova-3"
                )

        payload: FileSource = {
            "buffer": audio_data,
            "mimetype": audio_file.content_type,
        }

        # CORRECTED: Use rest client instead of deprecated prerecorded
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)


        transcription = response.results.channels[0].alternatives[0].transcript

        transcription = transcription.strip().rstrip('.').strip().lower()
        print("Transcription: ", transcription)

        if not transcription:
            return jsonify({'error': 'No transcription generated'}), 500

        return jsonify({'text': transcription})
    except Exception as e:
        app.logger.error(f'Error in generate_password_text: {str(e)}')
        return jsonify({'error': 'Failed to process audio file'}), 500

@app.route('/get_password_response_video', methods=['POST'])
def get_password_response_video():
    data = request.get_json()
    transcription = data.get('transcription', '').lower().strip()
    
    # Check if the transcription matches the session password
    password_correct = transcription == session.get('password', '')
    
    if password_correct:
        return jsonify({
            'video_url': '/static/success_funny_v2.mp4',  # Make sure to place your first video in static folder
            'password_correct': True
        })
    
    return jsonify({
        'video_url': '/static/refusal_try_again_v2.mp4',  # Make sure to place your second video in static folder
        'password_correct': False
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)

