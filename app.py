import os
import pytesseract
from PIL import Image
from flask import Flask, request, render_template, jsonify
import re
import cv2
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  

# Configure the upload folder for Aadhar card images
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to extract the name from extracted text
def extract_name(text):
    # Split the text into lines and look for patterns that might indicate the name
    lines = text.split('\n')
    for line in lines:
        if re.match(r"(जन्म तारीख/DOB): (\d{2}/\d{2}/\d{4})", line.strip()):
            return line.strip()
    return None

def extract_address(text):
    # Implement your logic to extract the address based on known patterns and keywords
    address = None

    # Example: Look for "Address" or "ठिकाना" in the text and capture the following lines
    lines = text.split('\n')
    for i in range(len(lines)):
        if "Address" in lines[i] or "ठिकाना" in lines[i]:
            # Capture lines following "Address" or "ठिकाना" until an empty line is encountered
            address = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                address.append(lines[j].strip())
                j += 1
            address = ' '.join(address)
            break

    return address

# Function to extract the date of birth from the text
def extract_dob(text):
    # Implement your logic to extract the date of birth based on known patterns and keywords
    dob = None

    # Example: Look for "DOB" or "जन्म तारीख" in the text and capture the following lines
    lines = text.split('\n')
    for i in range(len(lines)):
        if "DOB" in lines[i] or "जन्म तारीख" in lines[i]:
            # Capture lines following "DOB" or "जन्म तारीख" until an empty line is encountered
            dob = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                dob.append(lines[j].strip())
                j += 1
            dob = ' '.join(dob)
            break

    return dob


# Image preprocessing function to enhance OCR accuracy
def preprocess_image(image_path):
    # Load the image using OpenCV
    image = cv2.imread(image_path)
    
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to enhance text
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Save the preprocessed image for reference
    preprocessed_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'preprocessed_image.png')
    cv2.imwrite(preprocessed_image_path, thresh)
    
    return preprocessed_image_path

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/extract_name', methods=['POST'])
def extract_name_from_aadhar():
    # Ensure the request contains an image file
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image = request.files['image']
    
    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Save the uploaded image to the upload folder
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
        image.save(image_path)
        
        # Preprocess the image to enhance OCR accuracy
        preprocessed_image_path = preprocess_image(image_path)
        
        # Perform OCR on the preprocessed image
        text = pytesseract.image_to_string(Image.open(preprocessed_image_path))
        
        # Extract the name from the OCR result
        name = extract_name(text)
        address = extract_address(text)
        dobb = extract_dob(text)
        
        if name:
            print(name)
            return jsonify({'name': name,'dob': dobb, 'address': address})
        else:
            return jsonify({'error': 'Name not found in the Aadhar card'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
