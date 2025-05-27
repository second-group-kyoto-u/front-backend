from flask import Blueprint, jsonify
from app.models import db
from app.models.character import Character

character_bp = Blueprint("character", __name__)

@character_bp.route("/characters", methods=["GET"])
def get_characters():
    """すべてのキャラクターを取得するエンドポイント"""
    try:
        characters = Character.query.all()
        result = [character.to_dict() for character in characters]
        return jsonify({"characters": result}), 200
    except Exception as e:
        return jsonify({"error": f"キャラクター取得に失敗しました: {str(e)}"}), 500

@character_bp.route("/characters/<character_id>", methods=["GET"])
def get_character(character_id):
    """指定されたIDのキャラクターを取得するエンドポイント"""
    try:
        character = Character.query.filter_by(id=character_id).first()
        if not character:
            return jsonify({"error": "指定されたキャラクターが見つかりません"}), 404
        
        return jsonify({"character": character.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": f"キャラクター取得に失敗しました: {str(e)}"}), 500

@character_bp.route("/<character_id>", methods=["GET"])
def get_character_direct(character_id):
    """指定されたIDのキャラクターを取得するエンドポイント（直接IDを指定）"""
    try:
        character = Character.query.filter_by(id=character_id).first()
        if not character:
            return jsonify({"error": "指定されたキャラクターが見つかりません"}), 404
        
        return jsonify({"character": character.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": f"キャラクター取得に失敗しました: {str(e)}"}), 500 