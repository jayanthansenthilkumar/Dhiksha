"""
Sample data generator for local development and testing.
Generates deterministic synthetic users, content, and events.
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import UUID, uuid4

import numpy as np
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.schemas import Content, Event, User
from src.utils.config import settings


# Content metadata
CONTENT_TYPES = ["video", "article", "quiz"]
TAG_POOL = [
    "python", "machine-learning", "data-science", "web-development", "javascript",
    "react", "docker", "kubernetes", "aws", "tensorflow", "pytorch", "sql",
    "algorithms", "data-structures", "system-design", "frontend", "backend",
    "devops", "security", "testing", "git", "linux", "cloud-computing"
]
COHORTS = ["free", "premium", "student", "enterprise"]

# Event generation parameters
EVENT_TYPES = ["view", "complete", "like", "quiz_score"]
EVENT_WEIGHTS = [0.5, 0.25, 0.15, 0.1]  # Probability distribution


class SampleDataGenerator:
    """Generate sample data for the recommendation system."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        
        # Track generated IDs
        self.user_ids: List[UUID] = []
        self.content_ids: List[UUID] = []
    
    def generate_users(self, n: int) -> List[User]:
        """Generate n users with realistic profiles."""
        print(f"Generating {n} users...")
        users = []
        
        for _ in tqdm(range(n), desc="Users"):
            user = User(
                user_id=uuid4(),
                created_at=self.fake.date_time_between(start_date="-2y", end_date="now"),
                cohort_tag=random.choice(COHORTS),
                last_active_at=self.fake.date_time_between(start_date="-30d", end_date="now"),
            )
            users.append(user)
            self.user_ids.append(user.user_id)
        
        return users
    
    def generate_contents(self, n: int) -> List[Content]:
        """Generate n content items."""
        print(f"Generating {n} content items...")
        contents = []
        
        for i in tqdm(range(n), desc="Contents"):
            content_type = random.choice(CONTENT_TYPES)
            
            # Generate realistic titles
            if content_type == "video":
                title = f"{self.fake.catch_phrase()} - Video Tutorial"
            elif content_type == "article":
                title = f"Understanding {self.fake.bs().title()}"
            else:  # quiz
                title = f"{self.fake.catch_phrase()} - Quiz"
            
            # Assign 1-3 tags
            tags = random.sample(TAG_POOL, k=random.randint(1, 3))
            
            content = Content(
                content_id=uuid4(),
                title=title,
                type=content_type,
                tags=tags,
                difficulty=random.randint(1, 5),
                created_at=self.fake.date_time_between(start_date="-1y", end_date="now"),
            )
            contents.append(content)
            self.content_ids.append(content.content_id)
        
        return contents
    
    def generate_events(self, n: int) -> List[Event]:
        """Generate n interaction events with realistic patterns."""
        print(f"Generating {n} events...")
        events = []
        
        if not self.user_ids or not self.content_ids:
            raise ValueError("Must generate users and contents before events")
        
        # Create user preference profiles (some users prefer certain tags)
        user_preferences = {}
        for user_id in self.user_ids:
            user_preferences[user_id] = random.sample(TAG_POOL, k=random.randint(2, 5))
        
        for _ in tqdm(range(n), desc="Events"):
            user_id = random.choice(self.user_ids)
            
            # Bias content selection toward user's preferred tags (80% of the time)
            if random.random() < 0.8 and user_id in user_preferences:
                # Find content matching user preferences
                # In real implementation, query from DB; here we approximate
                content_id = random.choice(self.content_ids)
            else:
                content_id = random.choice(self.content_ids)
            
            event_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0]
            
            # Generate realistic values
            if event_type == "quiz_score":
                value = float(random.randint(0, 100))
            elif event_type == "view":
                value = float(random.randint(10, 600))  # Watch time in seconds
            else:
                value = None
            
            event = Event(
                event_id=uuid4(),
                user_id=user_id,
                content_id=content_id,
                event_type=event_type,
                value=value,
                ts=self.fake.date_time_between(start_date="-60d", end_date="now"),
            )
            events.append(event)
        
        return events
    
    def insert_to_database(self, users: List[User], contents: List[Content], events: List[Event]):
        """Insert generated data into the database."""
        print("Inserting data into database...")
        
        engine = create_engine(settings.DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Insert users
            print("  Inserting users...")
            session.bulk_save_objects(users)
            session.commit()
            print(f"  ✅ Inserted {len(users)} users")
            
            # Insert contents
            print("  Inserting contents...")
            session.bulk_save_objects(contents)
            session.commit()
            print(f"  ✅ Inserted {len(contents)} contents")
            
            # Insert events in batches (to avoid memory issues with large datasets)
            batch_size = 1000
            print(f"  Inserting events (batch size: {batch_size})...")
            for i in tqdm(range(0, len(events), batch_size), desc="  Event batches"):
                batch = events[i:i + batch_size]
                session.bulk_save_objects(batch)
                session.commit()
            print(f"  ✅ Inserted {len(events)} events")
            
            print("✅ All data inserted successfully!")
            
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            session.rollback()
            raise
        
        finally:
            session.close()
            engine.dispose()
    
    def generate_and_save(self, n_users: int, n_contents: int, n_events: int):
        """Generate all data and save to database."""
        print("=" * 60)
        print("Sample Data Generation")
        print("=" * 60)
        print(f"Seed: {self.seed}")
        print(f"Users: {n_users}")
        print(f"Contents: {n_contents}")
        print(f"Events: {n_events}")
        print()
        
        users = self.generate_users(n_users)
        contents = self.generate_contents(n_contents)
        events = self.generate_events(n_events)
        
        print()
        self.insert_to_database(users, contents, events)
        
        print()
        print("=" * 60)
        print("✅ Sample data generation completed!")
        print("=" * 60)
        print()
        print("Data summary:")
        print(f"  - Users: {len(users)}")
        print(f"  - Contents: {len(contents)}")
        print(f"  - Events: {len(events)}")
        print(f"  - Cohorts: {', '.join(COHORTS)}")
        print(f"  - Content types: {', '.join(CONTENT_TYPES)}")
        print()
        print("Next steps:")
        print("  1. Verify data: psql -d recommendations -c 'SELECT COUNT(*) FROM users;'")
        print("  2. Train models: python -m src.models.train_retrieval")


def main():
    parser = argparse.ArgumentParser(description="Generate sample data for learning recommendation system")
    parser.add_argument("--users", type=int, default=1000, help="Number of users to generate")
    parser.add_argument("--items", type=int, default=500, help="Number of content items to generate")
    parser.add_argument("--events", type=int, default=10000, help="Number of events to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    generator = SampleDataGenerator(seed=args.seed)
    generator.generate_and_save(
        n_users=args.users,
        n_contents=args.items,
        n_events=args.events
    )


if __name__ == "__main__":
    main()
