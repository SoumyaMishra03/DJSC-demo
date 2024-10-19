import base64
from flask import Flask, request, jsonify, render_template
import os
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import io
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key="****"  # Replace with your actual API key
)

# Function to extract images from PDF and return as base64 strings
def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF
    images = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert image to base64 for OpenAI processing
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
            images.append(base64_image)
    
    return images

# Flask route to render the upload page
@app.route('/')
def index():
    return render_template('upload.html', vulnerabilities=None)

# Flask route to handle PDF upload and OpenAI processing
@app.route('/upload', methods=['POST'])
def upload_document():
    # Check if a file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save the uploaded file temporarily
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    # Extract images from the PDF
    extracted_images = extract_images_from_pdf(file_path)

    # If no images are found in the PDF
    if not extracted_images:
        return jsonify({'message': 'No images found in the PDF'}), 200

    vulnerabilities = ""

    # Call the OpenAI Vision model to analyze each image
    try:
        for base64_image in extracted_images:
            image_response = client.chat.completions.create(
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
            image_vulnerabilities = image_response.choices[0].message.content.strip()
            vulnerabilities += f"<br><br>Image Analysis:<br>{image_vulnerabilities}"

        # Format vulnerabilities for HTML display
        formatted_vulnerabilities = vulnerabilities.replace("\n", "<br>").replace("**", "<strong>").replace("   -", "&nbsp;&nbsp;-")

        return render_template('upload.html', vulnerabilities=formatted_vulnerabilities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ensure that the uploads folder exists
if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
