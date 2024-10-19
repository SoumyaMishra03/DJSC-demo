import base64
from flask import Flask, request, jsonify, render_template
import os
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key="****"  # Replace with your actual API key
)

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Flask route to render the upload page
@app.route('/')
def index():
    return render_template('upload.html', vulnerabilities=None)  # HTML form for uploading image

# Flask route to handle image upload and OpenAI processing
@app.route('/upload', methods=['POST'])
def upload_image():
    # Check if an image file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save the uploaded file temporarily
    image_path = os.path.join('uploads', file.filename)
    file.save(image_path)

    # Convert the image to base64 for processing
    base64_image = encode_image(image_path)

    # Call the OpenAI vision model to analyze the image
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """The image has a network diagram. Understand it and list out all the possible cybersecurity vulnerabilities . 
                                       in the network and nothing else.""",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )

        # Get the output from the OpenAI model
        vulnerabilities = response.choices[0].message.content.strip()

        formatted_vulnerabilities = vulnerabilities.replace("\n", "<br>").replace("**", "<strong>").replace("   -", "&nbsp;&nbsp;-")

        return render_template('upload.html', vulnerabilities=formatted_vulnerabilities)

        # Return the vulnerabilities as JSON response
        return jsonify({
            'message': 'Image processed successfully!',
            'vulnerabilities': vulnerabilities
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ensure that the uploads folder exists
if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
