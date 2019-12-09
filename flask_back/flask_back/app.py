from flask import Flask, Request, Response, json
from flask_cors import *

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_pyfile('config.py')

@app.route('/')
@cross_origin()
def hello_world():
    return 'Hello World!'

@app.route('/rule/hl7/add', methods=['POST'])
@cross_origin()
def rule_hl7_add():
    if Request.method == 'POST':
        # f = Request.files['file']
        json_data = Request.get_json()

    return

@app.route('/ip_position', methods=['POST'])
@cross_origin()
def ip_position():
    return Response(json.dumps({'status':200, 'message': "成功", 'data' : {'ip' : '192.168.10.132', 'address' : "山东省威海市", 'equipment': '核磁共振仪', 'institution' : 'HIT'}}), content_type='application/json')


if __name__ == '__main__':
    app.run()
