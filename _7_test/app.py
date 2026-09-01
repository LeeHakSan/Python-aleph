import yaml
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime

app = Flask(__name__)

# 1. YML 설정 파일 로드
with open('application.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 2. Flask app에 YML 설정 적용
app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config['database']['track_modifications']
app.config['JWT_SECRET_KEY'] = config['jwt']['secret_key']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=config['jwt']['access_token_expires_hours'])

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "이미 존재하는 사용자입니다."}), 400
    new_user = User(username=data['username'], password=generate_password_hash(data['password']))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "회원가입 성공"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"msg": "아이디 또는 비밀번호가 틀렸습니다."}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token, username=user.username), 200

@app.route('/api/posts', methods=['GET'])
def get_posts():
    cursor = request.args.get('cursor', type=int)
    limit = request.args.get('limit', default=5, type=int)
    search = request.args.get('search', default='', type=str)
    
    query = Post.query
    if search:
        query = query.filter((Post.title.contains(search)) | (Post.content.contains(search)))
    if cursor:
        query = query.filter(Post.id < cursor)
        
    posts = query.order_by(Post.id.desc()).limit(limit).all()
    result = [{
        "id": p.id,
        "title": p.title,
        "content": p.content,
        "author": p.author.username,
        "created_at": p.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for p in posts]
    
    next_cursor = result[-1]['id'] if len(result) == limit else None
    return jsonify({"posts": result, "next_cursor": next_cursor}), 200

@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user_id = get_jwt_identity()
    data = request.json
    new_post = Post(title=data['title'], content=data['content'], author_id=int(current_user_id))
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"msg": "게시글 작성 완료"}), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    if post.author_id != int(current_user_id):
        return jsonify({"msg": "권한이 없습니다."}), 403
        
    data = request.json
    post.title = data['title']
    post.content = data['content']
    db.session.commit()
    return jsonify({"msg": "수정되었습니다."}), 200

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    current_user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    if post.author_id != int(current_user_id):
        return jsonify({"msg": "권한이 없습니다."}), 403
        
    db.session.delete(post)
    db.session.commit()
    return jsonify({"msg": "삭제되었습니다."}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)