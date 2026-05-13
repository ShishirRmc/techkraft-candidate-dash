"""Seed the database with sample data for development."""

from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.database import SessionLocal, engine, Base
from app.models import User, Candidate, Score

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).first():
        print("Database already seeded.")
        db.close()
        return

    # Users
    admin = User(
        email="admin@techkraft.com",
        hashed_password=pwd_context.hash("admin123"),
        role="admin",
    )
    reviewer1 = User(
        email="reviewer1@techkraft.com",
        hashed_password=pwd_context.hash("reviewer123"),
        role="reviewer",
    )
    reviewer2 = User(
        email="reviewer2@techkraft.com",
        hashed_password=pwd_context.hash("reviewer123"),
        role="reviewer",
    )
    db.add_all([admin, reviewer1, reviewer2])
    db.flush()

    # Candidates
    candidates_data = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "role_applied": "Frontend Engineer",
            "status": "reviewing",
            "skills": "React,TypeScript,CSS,GraphQL",
            "internal_notes": "Strong portfolio. Schedule final round.",
        },
        {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "role_applied": "Backend Engineer",
            "status": "interviewed",
            "skills": "Python,FastAPI,PostgreSQL,Docker",
            "internal_notes": "Good system design answers. Check references.",
        },
        {
            "name": "Carol Williams",
            "email": "carol@example.com",
            "role_applied": "Full Stack Developer",
            "status": "new",
            "skills": "React,Node.js,Python,AWS",
            "internal_notes": None,
        },
        {
            "name": "David Brown",
            "email": "david@example.com",
            "role_applied": "DevOps Engineer",
            "status": "offered",
            "skills": "Kubernetes,Terraform,AWS,CI/CD",
            "internal_notes": "Offer sent. Awaiting response.",
        },
        {
            "name": "Eva Martinez",
            "email": "eva@example.com",
            "role_applied": "Frontend Engineer",
            "status": "rejected",
            "skills": "Vue,JavaScript,Sass",
            "internal_notes": "Did not meet seniority bar.",
        },
        {
            "name": "Frank Lee",
            "email": "frank@example.com",
            "role_applied": "Backend Engineer",
            "status": "reviewing",
            "skills": "Go,gRPC,PostgreSQL,Redis",
            "internal_notes": None,
        },
        {
            "name": "Grace Kim",
            "email": "grace@example.com",
            "role_applied": "Data Engineer",
            "status": "new",
            "skills": "Python,Spark,Airflow,SQL",
            "internal_notes": None,
        },
        {
            "name": "Henry Chen",
            "email": "henry@example.com",
            "role_applied": "Frontend Engineer",
            "status": "interviewed",
            "skills": "React,TypeScript,Next.js,Tailwind",
            "internal_notes": "Excellent coding challenge submission.",
        },
    ]

    candidates = []
    for i, data in enumerate(candidates_data):
        c = Candidate(
            created_at=datetime.now(timezone.utc) - timedelta(days=len(candidates_data) - i),
            **data,
        )
        candidates.append(c)
    db.add_all(candidates)
    db.flush()

    # Scores
    scores_data = [
        # Reviewer 1 scores for Alice
        Score(candidate_id=candidates[0].id, category="technical", score=5, reviewer_id=reviewer1.id, note="Excellent React knowledge"),
        Score(candidate_id=candidates[0].id, category="communication", score=4, reviewer_id=reviewer1.id, note="Clear and concise"),
        # Reviewer 2 scores for Alice
        Score(candidate_id=candidates[0].id, category="technical", score=4, reviewer_id=reviewer2.id, note="Good but missed edge cases"),
        # Reviewer 1 scores for Bob
        Score(candidate_id=candidates[1].id, category="technical", score=4, reviewer_id=reviewer1.id, note="Solid Python skills"),
        Score(candidate_id=candidates[1].id, category="problem_solving", score=5, reviewer_id=reviewer1.id, note="Great system design"),
        # Reviewer 2 scores for Bob
        Score(candidate_id=candidates[1].id, category="technical", score=5, reviewer_id=reviewer2.id),
        # Reviewer 1 scores for Henry
        Score(candidate_id=candidates[7].id, category="technical", score=5, reviewer_id=reviewer1.id, note="Outstanding code quality"),
        Score(candidate_id=candidates[7].id, category="communication", score=5, reviewer_id=reviewer1.id),
    ]
    db.add_all(scores_data)

    db.commit()
    db.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
