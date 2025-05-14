from flask import Blueprint, jsonify, request, make_response
from app.models.area import AreaList

area_bp = Blueprint('area', __name__)

@area_bp.route("/list", methods=["GET", "OPTIONS"])
def get_area_list():
    if request.method == "OPTIONS":
        # プリフライトリクエストに対しては何もしないで 200 を返す
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    areas = AreaList.query.all()
    return jsonify({
        "areas": [area.to_dict() for area in areas]
    })
