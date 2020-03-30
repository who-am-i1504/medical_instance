from flask_back import db
from flask import jsonify
import flask_back.constant as cnts

def add(json_data, back, inSql):
    # inSql.id = 10
    inSql.value = json_data['value']
    try:
        db.session.add(inSql)
        db.session.commit()
        db.session.flush()
        back['data'] = {}
        back['data']['id'] = inSql.id
        back['data']['value'] = inSql.value
    except:
        back['status'] = cnts.database_error
        back['message'] = cnts.database_error
        return jsonify(back)

    return jsonify(back)

def getList(json_data, back, sql1, sql2):
    page_size = 20
    size = 0
    back = copy.deepcopy(cnts.back_message)
    try:
        result = db.session.execute(sql1)
        db.session.commit()
        size = result.fetchall()[0][0]
        result = db.session.execute(
            sql2 % ((json_data['page'] - 1)*page_size, page_size))
        db.session.commit()
        data = result.fetchall()
        back['data'] = []
        for i in data:
            a = {}
            a['id'] = i.id
            a['value'] = i.value
            back['data'].append(a)
    except:
        back['message'] = cnts.database_error_message
        back['status'] = cnts.database_error
        return jsonify(back)
    back['page'] = json_data['page']
    back['size'] = size
    return jsonify(back)
