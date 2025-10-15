from datetime import datetime

class Models:
    def __init__(self):
        self.User = None
        self.Team = None
        self.TeamMember = None
        self.CheckIn = None

def init_models(db):
    if hasattr(init_models, '_models'):
        return init_models._models

    class User(db.Model):
        __tablename__ = 'users'  # Explicitly name tables
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(512), nullable=False)  # Increased from 120 to 512
        is_new = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class Team(db.Model):
        __tablename__ = 'teams'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class TeamMember(db.Model):
        __tablename__ = 'team_members'
        id = db.Column(db.Integer, primary_key=True)
        team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))  # Updated from 'team.id'
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Updated from 'user.id'
        weight = db.Column(db.Float, default=1.0)

    class CheckIn(db.Model):
        __tablename__ = 'check_ins'
        id = db.Column(db.Integer, primary_key=True)
        team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))  # Updated from 'team.id'
        post_url = db.Column(db.String(200))
        check_in_time = db.Column(db.DateTime, default=datetime.utcnow)

    models = Models()
    models.User = User
    models.Team = Team
    models.TeamMember = TeamMember
    models.CheckIn = CheckIn
    
    init_models._models = models
    return models
