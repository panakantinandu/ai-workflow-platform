from db.database import engine
from db.base import Base

# 🔥 FORCE IMPORT OF MODELS
import db.models  # <-- THIS LINE IS CRITICAL

def init():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init()