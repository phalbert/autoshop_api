from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from autoshop.commons.dbaccess import query, search


class SearchList(Resource):
    """get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        query = request.args.get("query")
        response = search(query)
        return response, 200


class QueryList(Resource):
    """get_all
    """

    method_decorators = [jwt_required]

    def get(self):
        sql = request.args.get("sql")

        response = query(sql)
        return response, 200
