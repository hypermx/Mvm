"""SQLAlchemy ORM models for the MVM backend."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserProfileORM(Base):
    """Persisted user profile."""

    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(16))
    migraine_history_years: Mapped[float] = mapped_column(Float)
    average_migraine_frequency: Mapped[float] = mapped_column(Float)
    personal_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    logs: Mapped[list[DailyLogORM]] = relationship(
        "DailyLogORM", back_populates="user", cascade="all, delete-orphan"
    )


class DailyLogORM(Base):
    """Persisted daily health log."""

    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user_profiles.user_id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[float] = mapped_column(Float)
    stress_level: Mapped[float] = mapped_column(Float)
    hydration_liters: Mapped[float] = mapped_column(Float)
    caffeine_mg: Mapped[float] = mapped_column(Float, default=0.0)
    alcohol_units: Mapped[float] = mapped_column(Float, default=0.0)
    exercise_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    weather_pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    menstrual_cycle_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    migraine_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    migraine_intensity: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped[UserProfileORM] = relationship("UserProfileORM", back_populates="logs")
