import os
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/selfhealing")

engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=0)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Log(Base):
    __tablename__ = "logs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String, nullable=True)
    level: Mapped[str] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    raw_log: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

class DetectedError(Base):
    __tablename__ = "detected_errors"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    log_id: Mapped[str] = mapped_column(String)
    error_type: Mapped[str] = mapped_column(String, nullable=True)
    file_path: Mapped[str] = mapped_column(String, nullable=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=True)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="DETECTED")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FixSuggestion(Base):
    __tablename__ = "fix_suggestions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    error_id: Mapped[str] = mapped_column(String)
    original_code: Mapped[str] = mapped_column(Text, nullable=True)
    fixed_code: Mapped[str] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    agent_attempt: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AgentOutput(Base):
    __tablename__ = "agent_outputs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    execution_id: Mapped[str] = mapped_column(String)
    agent_name: Mapped[str] = mapped_column(String)
    input_data: Mapped[str] = mapped_column(Text, nullable=True)
    output_data: Mapped[str] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="OK")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ExecutionHistory(Base):
    __tablename__ = "execution_history"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    error_id: Mapped[str] = mapped_column(String)
    pipeline_status: Mapped[str] = mapped_column(String)
    total_duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    final_fix_id: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)