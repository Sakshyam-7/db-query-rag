import random
import uuid
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.ticket import Ticket, TicketStatus, TicketPriority

def seed_database():
    db = SessionLocal()
    try:
        print("Checking for existing users...")
        users = db.query(User).all()
        
        if not users:
            print("No users found. Creating a single dummy user for foreign key constraints...")
            dummy_user = User(
                name="Dummy User",
                email=f"dummy_{uuid.uuid4().hex[:8]}@example.com",
                password_hash="dummy_hash",
                role=UserRole.MEMBER
            )
            db.add(dummy_user)
            db.commit()
            db.refresh(dummy_user)
            users = [dummy_user]
            print(f"Created dummy user: {dummy_user.email}")
        
        print("Seeding Projects (10 rows)...")
        projects = []
        for i in range(10):
            project = Project(
                owner_id=random.choice(users).id,
                name=f"Seeded Project {uuid.uuid4().hex[:6]}",
                description=f"This is an automatically generated project for testing purposes.",
                status=random.choice(list(ProjectStatus))
            )
            db.add(project)
            projects.append(project)
        
        db.commit()
        for project in projects:
            db.refresh(project)
        print("10 projects seeded successfully.")

        print("Seeding Tickets (10 rows)...")
        for i in range(10):
            ticket = Ticket(
                user_id=random.choice(users).id,
                project_id=random.choice(projects).id,
                title=f"Seeded Ticket {uuid.uuid4().hex[:6]}",
                description=f"This is an automatically generated ticket for testing purposes.",
                status=random.choice(list(TicketStatus)),
                priority=random.choice(list(TicketPriority))
            )
            db.add(ticket)
        
        db.commit()
        print("10 tickets seeded successfully.")

    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database seeding process...")
    seed_database()
    print("Database seeding completed.")
