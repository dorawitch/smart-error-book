from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config import DB_URI


engine_kwargs = {"future": True}
if DB_URI.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URI, **engine_kwargs)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)

Base = declarative_base()


class ErrorQuestion(Base):
    __tablename__ = "error_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, default="")
    answer = Column(Text, nullable=True)
    knowledge_point = Column(String(255), nullable=True)
    error_type = Column(String(255), nullable=True)
    image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self, image_url=None):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "knowledge_point": self.knowledge_point,
            "error_type": self.error_type,
            "image_path": self.image_path,
            "image_url": image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def get_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(bind=engine)
