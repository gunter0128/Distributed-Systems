import aiohttp
import asyncio
import random
import time
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketingCampaignLoadTester:
    def __init__(self, backend_url, max_teams=1000):
        self.backend_url = backend_url
        self.max_teams = max_teams # Maximum number of teams to create
        self.users = {}  # Store user credentials
        self.teams = {}  # Store team info
        self.tokens = {}  # Store authentication tokens

    async def register_user(self, session):
        """Register a new user and get authentication token"""
        user_id = random.randint(1, self.max_teams * 3)  # More users than teams
        username = f"user_{user_id}"
        
        if username in self.users:
            return username
        
        user_data = {
            "username": username,
            "password": "testpass123"
        }
        
        try:
            async with session.post(f"{self.backend_url}/api/register", json=user_data) as response:
                if response.status == 200:
                    self.users[username] = user_data
                    logger.info(f"Registered user: {username}")
                    
                    # Login to get token
                    async with session.post(f"{self.backend_url}/api/login", json=user_data) as login_response:
                        if login_response.status == 200:
                            token_data = await login_response.json()
                            self.tokens[username] = token_data['token']
                            return username
        except Exception as e:
            logger.error(f"Error registering/login user {username}: {e}")
        return None

    async def create_team(self, session, username):
        """Create a new team"""
        if not username or username not in self.tokens:
            return None
            
        team_id = random.randint(1, self.max_teams * 2)
        team_name = f"Team_{team_id}"
        
        if team_name in self.teams:
            return team_name
            
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        team_data = {"name": team_name}
        
        try:
            async with session.post(
                f"{self.backend_url}/api/teams",
                headers=headers,
                json=team_data
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    self.teams[team_name] = response_data['team_id']
                    logger.info(f"Created team: {team_name}")
                    return team_name
        except Exception as e:
            logger.error(f"Error creating team {team_name}: {e}")
        return None

    async def join_team(self, session, username, team_name):
        """Join an existing team"""
        if not username or username not in self.tokens or team_name not in self.teams:
            return False
            
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        join_data = {"team_id": self.teams[team_name]}
        
        try:
            async with session.post(
                f"{self.backend_url}/api/teams/join",
                headers=headers,
                json=join_data
            ) as response:
                if response.status == 200:
                    logger.info(f"User {username} joined team {team_name}")
                    return True
        except Exception as e:
            logger.error(f"Error joining team {team_name}: {e}")
        return False

    async def checkin(self, session, username, team_name):
        """Submit a check-in for a team"""
        if not username or username not in self.tokens or team_name not in self.teams:
            return False
            
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        checkin_data = {
            "team_id": self.teams[team_name],
            "post_url": f"https://social.example.com/post_{random.randint(1000, 9999)}"
        }
        
        try:
            async with session.post(
                f"{self.backend_url}/api/checkin",
                headers=headers,
                json=checkin_data
            ) as response:
                if response.status == 200:
                    logger.info(f"Check-in recorded for team {team_name}")
                    return True
        except Exception as e:
            logger.error(f"Error recording check-in for team {team_name}: {e}")
        return False

    async def get_rankings(self, session):
        """Get current team rankings"""
        try:
            async with session.get(f"{self.backend_url}/api/rankings") as response:
                if response.status == 200:
                    rankings = await response.json()
                    logger.info("Current top teams:")
                    for rank, team in enumerate(rankings['rankings'][:5], 1):
                        logger.info(f"{rank}. {team['team_name']} - Score: {team['score']:.2f}")
        except Exception as e:
            logger.error(f"Error getting rankings: {e}")

    async def run_load_test(self, duration_minutes=30):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            
            while time.time() < end_time:
                # Calculate time-based concurrency
                time_ratio = (time.time() - start_time) / (end_time - start_time)
                concurrent_requests = int(10 + (90 * time_ratio))  # Scale from 10 to 100
                
                tasks = []
                for _ in range(concurrent_requests):
                    # Random activity selection with increasing checkin probability near the end
                    activity = random.choices(
                        ['register', 'create_team', 'join_team', 'checkin'],
                        weights=[
                            10 * (1 - time_ratio),  # Decrease registration
                            10 * (1 - time_ratio),  # Decrease team creation
                            20 * (1 - time_ratio),  # Decrease team joining
                            60 * (1 + time_ratio)   # Increase checkins
                        ]
                    )[0]
                    
                    if activity == 'register':
                        tasks.append(asyncio.create_task(self.register_user(session)))
                    elif activity == 'create_team' and len(self.users) > 0:
                        username = random.choice(list(self.users.keys()))
                        tasks.append(asyncio.create_task(self.create_team(session, username)))
                    elif activity == 'join_team' and len(self.teams) > 0:
                        username = random.choice(list(self.users.keys()))
                        team_name = random.choice(list(self.teams.keys()))
                        tasks.append(asyncio.create_task(self.join_team(session, username, team_name)))
                    elif activity == 'checkin' and len(self.teams) > 0:
                        username = random.choice(list(self.users.keys()))
                        team_name = random.choice(list(self.teams.keys()))
                        tasks.append(asyncio.create_task(self.checkin(session, username, team_name)))
                
                if tasks:
                    await asyncio.gather(*tasks)
                    if random.random() < 0.1:  # 10% chance to check rankings
                        await self.get_rankings(session)
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                
                # Log progress
                logger.info(f"Progress: {int(time_ratio * 100)}% complete")
                logger.info(f"Users: {len(self.users)}, Teams: {len(self.teams)}")

async def main():
    backend_url = "http://35.221.140.146:5000"  # Update with your backend URL
    tester = MarketingCampaignLoadTester(backend_url, max_teams=1000)
    
    logger.info("Starting marketing campaign load test...")
    await tester.run_load_test(duration_minutes=30)
    logger.info("Load test completed")

if __name__ == "__main__":
    asyncio.run(main())
