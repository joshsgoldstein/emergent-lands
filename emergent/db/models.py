import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from emergent.db.base import Base


class SimulationSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    world_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="created")
    current_turn_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Landmark(Base):
    __tablename__ = "landmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    x_coord: Mapped[float] = mapped_column(Float)
    z_coord: Mapped[float] = mapped_column(Float)
    category: Mapped[Optional[str]] = mapped_column(String)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String)
    personality: Mapped[Optional[str]] = mapped_column(Text)
    drive: Mapped[Optional[str]] = mapped_column(Text)
    north_star: Mapped[Optional[str]] = mapped_column(Text)
    energy: Mapped[float] = mapped_column(Float, default=100.0)
    knowledge: Mapped[float] = mapped_column(Float, default=100.0)
    influence: Mapped[float] = mapped_column(Float, default=100.0)
    credits: Mapped[int] = mapped_column(Integer, default=10)
    mood: Mapped[str] = mapped_column(String, default="neutral")
    home_location_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    status: Mapped[str] = mapped_column(String, default="alive")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class AgentTurn(Base):
    __tablename__ = "agent_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    turn_number: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String, default="pending")
    turn_type: Mapped[str] = mapped_column(String, default="regular")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "turn_number"),
    )


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    turn_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("agent_turns.id")
    )
    tool_name: Mapped[str] = mapped_column(String)
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String, default="long_term")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class SoulEntry(Base):
    __tablename__ = "soul_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    content: Mapped[dict] = mapped_column(JSON)
    mood: Mapped[Optional[str]] = mapped_column(String)
    entry_date: Mapped[date] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint("agent_id", "entry_date"),
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    relationship_type: Mapped[str] = mapped_column(String, default="neutral")
    trust: Mapped[float] = mapped_column(Float, default=0.5)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("agent_id", "target_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    subject: Mapped[Optional[str]] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Speech(Base):
    __tablename__ = "speech"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String, default="say")
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String, default="others")
    status: Mapped[str] = mapped_column(String, default="submitted")
    votes_for: Mapped[int] = mapped_column(Integer, default=0)
    votes_against: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("proposals.id")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    vote: Mapped[str] = mapped_column(String)

    __table_args__ = (
        CheckConstraint("vote IN ('for', 'against')"),
        UniqueConstraint("proposal_id", "agent_id"),
    )


class ConstitutionArticle(Base):
    __tablename__ = "constitution_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active")
    created_by_proposal_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("proposals.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class Pitch(Base):
    __tablename__ = "pitches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    cycle_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String)
    evidence_url: Mapped[Optional[str]] = mapped_column(String)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    reward: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("agent_id", "cycle_number"),
    )


class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    title: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class WorldEvent(Base):
    __tablename__ = "world_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String, default="ambient")
    location_name: Mapped[Optional[str]] = mapped_column(String)
    turn_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa_func.now()
    )


class CommunityEvent(Base):
    __tablename__ = "community_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id")
    )
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("landmarks.id")
    )
    status: Mapped[str] = mapped_column(String, default="proposed")
    rsvp_list: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
