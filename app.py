import os
import uuid

from flask import Flask, request, jsonify, abort
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = set(['wav'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MONGO_DBNAME'] = 'laeneco_db'
mongo = PyMongo(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/cases', methods=['POST'])
def create_case():
    if request.method == 'POST':

        # check if the post request has the file part
        if 'file' not in request.files:
            abort(400)

        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            abort(400)

        if not allowed_file(file.filename):
            abort(400)

        case_id = uuid.uuid1()
        filename = secure_filename(file.filename)
        unique_filename = '_'.join([str(case_id), filename])

        file.save(os.path.join(
            app.config['UPLOAD_FOLDER'],
            unique_filename
        ))

        filepath = os.path.join(
            PROJECT_PATH, app.config['UPLOAD_FOLDER'], unique_filename)
        cnn_result = os.popen(
            "python cnn_lung/example.py -audio_path {}".format(
                filepath)
        ).read()

        case = {
            'id': case_id,
            'filename': unique_filename,
            'result': cnn_result
        }

        insert_result = mongo.db.cases.insert_one(case)
        return jsonify({'case': case}), 201


# @app.route('/api/cases/<int:case_id>', methods=['GET'])
# def get_case(case_id):
#     case = filter(lambda t: t['id'] == case_id, cases)
#     if len(case) == 0:
#         abort(404)
#     return jsonify({'case': case[0]})



if __name__ == '__main__':
    app.run(debug=True)
