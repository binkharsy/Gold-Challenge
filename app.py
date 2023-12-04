import re
import pandas as pd
from flask import Flask, jsonify
from flask import request
from werkzeug.utils import secure_filename
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine



app = Flask(__name__)
app.json_encoder = LazyJSONEncoder
database_file = 'assigntment.db'
engine = create_engine(f'sqlite:///{database_file}')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{database_file}'  # Replace with your desired database file name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

dfAbusive = pd.read_sql_query(f"SELECT * FROM abusive", engine)

db = SQLAlchemy(app)

# bersihin karakter unicode seperti \xf8 - \xfxx
def clean_unicode_chars(text):
    unicode_pattern = re.compile(r'\\x[0-9a-fA-F]{2}')
    cleaned_text = unicode_pattern.sub('', text)
    return cleaned_text

# bersihin escape character seperti \\n \\t 
def clean_escap_chars(text):
    escape_pattern = re.compile(r'\\([nt])')
    cleaned_text = escape_pattern.sub('', text)
    return cleaned_text

# hapus karakter double
def remove_duplicate(text):
    output_string = re.sub(r'\b(\w+)\b\s+\b\1\b', r'\1', text)
    return output_string.lower()

# sensor kata-kata abusive
def cencored_abusive_word(text):
    pattern = '|'.join(rf'\b{word}\b' for word in dfAbusive['kata_abusive'])
    contains_abusive_words = any(re.search(pattern, text, flags=re.IGNORECASE) for word in dfAbusive['kata_abusive'])
    
    # jika variabel text terdapat kata-kata abusive maka kata tersebut di sensor
    # jika tidak akan menampilkan text aslinya 
    if contains_abusive_words:
        censored_text = re.sub(pattern, '*****', text, flags=re.IGNORECASE)
        return censored_text
    else:
        return text

# class model atau representasi struktur tabel
class Data(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.INTEGER,  primary_key=True)
    Tweet = db.Column(db.TEXT),
    HS = db.Column(db.TEXT)
    Abusive = db.Column(db.TEXT)
    HS_Individual = db.Column(db.TEXT)
    HS_Group = db.Column(db.TEXT)
    HS_Religion = db.Column(db.TEXT)
    HS_Race = db.Column(db.TEXT)
    HS_Physical = db.Column(db.TEXT)
    HS_Gender = db.Column(db.TEXT)
    HS_Other = db.Column(db.TEXT)
    HS_Weak = db.Column(db.TEXT)
    HS_Moderate = db.Column(db.TEXT)
    HS_Strong = db.Column(db.TEXT)

    
# fungsi untuk menggantikan layloader
def lazy_string_loader(loader):
    return str(loader())

swagger_template = dict(
    info={
        'title': lazy_string_loader(lambda: 'API Documentation for Data processing and modeling'),
        'version': lazy_string_loader(lambda: '1.0.0'),
        'description': lazy_string_loader(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = request.host if request else '127.0.0.1:5000'
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "docs",
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'data': "Hello World"
    }
    
    response_data = jsonify(json_response)
    return response_data

@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    # mengambil value dari inputan
    text = request.form.get('text')

    # simpan object text ke dalam class model Data
    data = Data(
        Tweet = clean_unicode_chars(clean_escap_chars(cencored_abusive_word(remove_duplicate(text)))),
        HS = '0',
        Abusive = '0',
        HS_Individual = '0',
        HS_Group = '0',
        HS_Religion = '0',
        HS_Race = '0',
        HS_Physical = '0',
        HS_Gender = '0',
        HS_Other = '0',
        HS_Weak = '0',
        HS_Moderate = '0',
        HS_Strong = '0'
    )

    # menyimpan data ke table
    db.session.add(data)

    # tampilkan response api
    json_response = {
        'status_code': 200,
        'data': clean_unicode_chars(clean_escap_chars(cencored_abusive_word(remove_duplicate(text)))),
        'message': 'data berhasil di simpan'
    }

    response_data = jsonify(json_response)
    return response_data

@swag_from("docs/file_processing.yml", methods=['POST'])
@app.route('/file-processing', methods=['POST'])
def file_processing():

    uploaded_file = request.files['file']
    if uploaded_file:
        filename = uploads.save(uploaded_file)
        return jsonify({"message": f"File '{filename}' uploaded successfully"}), 200
    else:
        return jsonify({"message": "No file uploaded"}), 400

if __name__ == '__main__':
    app.run(debug=True)

