import os
from flask import Flask, request, send_file, render_template, redirect, url_for
import pandas as pd
import zipfile
from PIL import Image, ImageEnhance
import random
import shutil

app = Flask(__name__)

# Create uploads and output directories if they don't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

if not os.path.exists('output'):
    os.makedirs('output')

# Function to read CSV file for domain names
def get_domain_names_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)  # Read CSV file
        domains = df.iloc[:, 0].tolist()  # Assuming domain names are in the first column (column A)
        return domains
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

# Image processing function to make images unique
def make_image_unique(image_path, output_path):
    try:
        image = Image.open(image_path)
        enhancer = ImageEnhance.Brightness(image)
        image_enhanced = enhancer.enhance(0.95)

        pixels = image_enhanced.load()
        for i in range(image_enhanced.size[0]):
            for j in range(image_enhanced.size[1]):
                r, g, b = pixels[i, j]
                noise = random.uniform(-10, 10)
                pixels[i, j] = (int(r + noise), int(g + noise), int(b + noise))

        rotated_image = image_enhanced.rotate(random.uniform(-0.5, 0.5))
        rotated_image.save(output_path)
    except Exception as e:
        print(f"Error processing image: {e}")

# Function to create a zip file from a folder
def create_zip(zip_name, folder_path):
    try:
        shutil.make_archive(zip_name, 'zip', folder_path)
    except Exception as e:
        print(f"Error creating zip: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files():
    try:
        csv_file = request.files['csv_file']
        csv_file_path = os.path.join('uploads', csv_file.filename)
        csv_file.save(csv_file_path)

        domains = get_domain_names_from_csv(csv_file_path)

        image_zip = request.files['image_zip']
        image_zip_path = os.path.join('uploads', image_zip.filename)
        image_zip.save(image_zip_path)

        with zipfile.ZipFile(image_zip_path, 'r') as zip_ref:
            zip_ref.extractall('uploads/images')

        for domain in domains:
            domain = domain.strip()
            domain_folder = f"output/{domain}"
            os.makedirs(domain_folder, exist_ok=True)

            for i in range(100):
                set_folder = os.path.join(domain_folder, f"set_{i+1}")
                os.makedirs(set_folder, exist_ok=True)
                for image_file in os.listdir('uploads/images'):
                    if image_file.endswith('.jpeg'):
                        image_path = os.path.join('uploads/images', image_file)
                        output_image_path = os.path.join(set_folder, image_file)
                        make_image_unique(image_path, output_image_path)

            zip_name = f"output/{domain}_unique_images"
            create_zip(zip_name, domain_folder)

        return redirect(url_for('download'))

    except Exception as e:
        return "An error occurred during processing."

@app.route('/download')
def download():
    zip_files = [f for f in os.listdir('output') if f.endswith('.zip')]
    return render_template('download.html', zip_files=zip_files)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join('output', filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
