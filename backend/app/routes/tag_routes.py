from flask import Blueprint, jsonify, request, make_response
from app.models.event import TagMaster
from app.models import db

tag_bp = Blueprint('tag', __name__)

@tag_bp.route('/list', methods=['GET'])
def getTags():
    if request.method == "OPTIONS":
        # プリフライトリクエストに対しては何もしないで 200 を返す
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    tags = TagMaster.query.filter_by(is_active=True).all()
    tag_list = [
        {
            'id': tag.id,
            'tag_name': tag.tag_name
        }
        for tag in tags
    ]
    return jsonify({'tags': tag_list})
