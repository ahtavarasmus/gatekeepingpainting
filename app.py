import base64
from pathlib import Path
from flask import Flask, render_template, redirect, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/redirect-to-instagram')
def redirect_to_instagram():
    return redirect('https://www.instagram.com')

@app.route('/generate_password_text')
def generate_password_text():
    # here call replicate to generate photo of the said password and return it

    # Read the image file from static directory
    image_path = Path('static/overlay.png')  # Make sure to place your image in static folder
    
    # Read and encode the image
    with open(image_path, 'rb') as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    return jsonify({
        'image': f'data:image/png;base64,{img_data}'
    })

@app.route('/get_password_response_video')
def get_password_response_video():
    # here just check if the password is correct and return one of the two videos
    #password_correct = True if hash('random') % 2 == 0 else False
    password_correct = False
    
    if password_correct:
        return jsonify({
            'video_url': '/static/success_v1.mp4',  # Make sure to place your first video in static folder
            'password_correct': True
        })
    
    return jsonify({
        'video_url': '/static/refusal_v1.mp4',  # Make sure to place your second video in static folder
        'password_correct': False
    })

if __name__ == '__main__':
    app.run(debug=True)

