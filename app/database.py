from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, ForeignKey, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - use SQLite for simplicity
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_duel_arena.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # Google user ID
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to games
    games = relationship("Game", back_populates="user")


class Game(Base):
    __tablename__ = "games"
    
    id = Column(String, primary_key=True, index=True)  # game_id
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    game_type = Column(String, nullable=False)
    white_model = Column(String, nullable=True)
    black_model = Column(String, nullable=True)
    result = Column(String, nullable=True)
    winner = Column(String, nullable=True)
    moves_count = Column(Integer, default=0)
    is_over = Column(Integer, default=0)  # SQLite doesn't have boolean
    white_tokens = Column(Integer, default=0)  # Token usage for white model
    black_tokens = Column(Integer, default=0)  # Token usage for black model
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    game_state = Column(Text, nullable=True)  # Store full game state as JSON
    
    # Relationship to user
    user = relationship("User", back_populates="games")


def init_db():
    """Initialize the database tables and ensure schema migrations"""
    Base.metadata.create_all(bind=engine)

    # SQLite doesn't auto-migrate. Make sure token columns exist.
    try:
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('games')}
        with engine.connect() as conn:
            if 'white_tokens' not in columns:
                conn.execute(text('ALTER TABLE games ADD COLUMN white_tokens INTEGER DEFAULT 0'))
            if 'black_tokens' not in columns:
                conn.execute(text('ALTER TABLE games ADD COLUMN black_tokens INTEGER DEFAULT 0'))
            conn.commit()
    except Exception:
        # Best effort; schema may already be correct or database may not exist yet.
        pass


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

