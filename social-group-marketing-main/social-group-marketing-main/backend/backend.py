from flask import request, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # Changed import
from functools import wraps
from flask_cors import CORS  # Add this import
from db import create_app
from models import init_models

# 創建應用和數據庫實例
app, db = create_app()

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://104.199.254.153", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"]
    }
})

if not app or not db:
    raise RuntimeError("無法初始化應用程序或數據庫連接")

# 初始化數據模型
models = init_models(db)

# Initialize database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# 身份驗證裝飾器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'No Authorization header'}), 401

        try:
            # 正確處理 Bearer token
            if ' ' not in auth_header:
                return jsonify({'message': 'Invalid token format. Expected "Bearer <token>"'}), 401
                
            auth_type, token = auth_header.split(' ', 1)
            
            if auth_type.lower() != 'bearer':
                return jsonify({'message': 'Invalid token type. Expected "Bearer"'}), 401

            # 解碼 token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = models.User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'message': f'Invalid token: {str(e)}'}), 401
        except Exception as e:
            return jsonify({'message': f'Error processing token: {str(e)}'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# API路由
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    
    new_user = models.User(
        username=data['username'],
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = models.User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password, data['password']):
        token = jwt.encode({  # Changed from jwt.encode to pyjwt.encode
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        return jsonify({
            'token': token,
            'token_type': 'Bearer',
            'message': 'Login successful'
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/teams', methods=['POST'])
@token_required
def create_team(current_user):
    data = request.get_json()
    new_team = models.Team(name=data['name'])
    db.session.add(new_team)
    
    # 添加創建者作為團隊成員
    team_member = models.TeamMember(
        team_id=new_team.id,
        user_id=current_user.id
    )
    db.session.add(team_member)
    db.session.commit()
    
    return jsonify({'message': 'Team created successfully', 'team_id': new_team.id})

@app.route('/api/teams/join', methods=['POST'])
@token_required
def join_team(current_user):
    data = request.get_json()
    
    if 'team_id' not in data:
        return jsonify({'message': 'Team ID is required'}), 400
        
    team = models.Team.query.get(data['team_id'])
    if not team:
        return jsonify({'message': 'Team not found'}), 404
        
    # 檢查用戶是否已經是團隊成員
    existing_member = models.TeamMember.query.filter_by(
        team_id=team.id,
        user_id=current_user.id
    ).first()
    
    if existing_member:
        return jsonify({'message': 'User is already a team member'}), 400
        
    # 創建新的團隊成員關係
    new_member = models.TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        weight=1.0  # 默認權重
    )
    
    db.session.add(new_member)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully joined the team',
        'team_id': team.id,
        'team_name': team.name
    })

@app.route('/api/checkin', methods=['POST'])
@token_required
def checkin(current_user):
    data = request.get_json()
    new_checkin = models.CheckIn(
        team_id=data['team_id'],
        post_url=data['post_url']
    )
    db.session.add(new_checkin)
    db.session.commit()
    
    return jsonify({'message': 'Check-in recorded successfully'})

def calculate_team_score(team_id, alpha=1.0, beta=2.0):
    team = models.Team.query.get(team_id)
    checkins = models.CheckIn.query.filter_by(team_id=team_id).order_by(models.CheckIn.check_in_time).all()
    
    if not checkins:
        return 0
    
    # 計算團隊默契 S (最後一個打卡時間與第一個打卡時間的差距，以小時計)
    time_diff = (checkins[-1].check_in_time - checkins[0].check_in_time).total_seconds() / 3600
    
    # 計算團隊人數 T (考慮權重)
    team_members = models.TeamMember.query.filter_by(team_id=team_id).all()
    T = sum(member.weight for member in team_members)
    
    # 計算新會員數量 N
    new_members = sum(1 for member in team_members 
                     if models.User.query.get(member.user_id).is_new)
    
    # 使用公式計算分數
    score = T / (alpha * (time_diff + 1)) + beta * new_members
    return score

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    teams = models.Team.query.all()
    rankings = []
    
    for team in teams:
        score = calculate_team_score(team.id)
        rankings.append({
            'team_id': team.id,
            'team_name': team.name,
            'score': score
        })
    
    # 按分數排序，取前20名
    rankings.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'rankings': rankings[:20]})

if __name__ == '__main__': 
    if app:
        app.run(host='0.0.0.0', debug=True)
    else:
        print("應用程序初始化失敗")