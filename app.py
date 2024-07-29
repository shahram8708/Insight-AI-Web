import os
import requests
import markdown
from flask import Flask, request, render_template, jsonify
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.environ['API_KEY'])

api_url = 'https://api.microlink.io'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        page_url = request.form['url']
        extra_field = request.form['extra_field']
        params = {
            'url': page_url,
            'pdf': 'true'
        }
        
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            pdf_url = data.get('data', {}).get('pdf', {}).get('url')
            
            if pdf_url:
                pdf_response = requests.get(pdf_url)
                
                if pdf_response.status_code == 200:
                    save_dir = 'static/pdfs'
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    
                    pdf_path = os.path.join(save_dir, 'page.pdf')
                    
                    with open(pdf_path, 'wb') as file:
                        file.write(pdf_response.content)
                    
                    return render_template('index.html', pdf_path='pdfs/page.pdf', extra_field=extra_field)
                else:
                    return "Failed to load. Status code: {}".format(pdf_response.status_code)
            else:
                return "URL not found in the response."
        else:
            return "Request failed. Status code: {}".format(response.status_code)
    
    return render_template('index.html', pdf_path=None, extra_field=None)

@app.route('/process', methods=['POST'])
def process():
    try:
        images = request.files.getlist("images")

        image_data_list = []
        for file in images:
            image_data = {
                'mime_type': file.content_type,
                'data': file.read()
            }
            image_data_list.append(image_data)

        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(image_data_list)
        markdown_text = response.text
        html_text = markdown.markdown(markdown_text)

        return jsonify({"html": html_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
