import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (CheckConstraint("type in ('income','expense')", name="categories_type_check"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="expense")
    color: Mapped[str] = mapped_column(Text, nullable=False, default="#7CA8E3")
    monthly_limit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("type in ('corrente','risparmio','investimento','contanti','carta')", name="accounts_type_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    initial_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    color: Mapped[str] = mapped_column(Text, nullable=False, default="#6FE3A0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (CheckConstraint("target > 0", name="goals_target_check"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    deadline: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Movement(Base):
    __tablename__ = "movements"
    __table_args__ = (
        CheckConstraint("type in ('income','expense','transfer')", name="movements_type_check"),
        CheckConstraint("amount > 0", name="movements_amount_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    person_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Investment(Base):
    __tablename__ = "investments"
    __table_args__ = (
        CheckConstraint("type in ('azione','etf','obbligazione','crypto','altro')", name="investments_type_check"),
        CheckConstraint("qty > 0", name="investments_qty_check"),
        CheckConstraint("avg_price > 0", name="investments_avg_price_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    isin: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    cur_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    added_at: Mapped[date_type] = mapped_column(Date, nullable=False, server_default=func.current_date())
    updated_at: Mapped[date_type] = mapped_column(Date, nullable=False, server_default=func.current_date())


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"
    __table_args__ = (
        CheckConstraint("type in ('income','expense')", name="recurring_expenses_type_check"),
        CheckConstraint("amount > 0", name="recurring_expenses_amount_check"),
        CheckConstraint("day_of_month between 1 and 31", name="recurring_expenses_day_of_month_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="expense")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    account_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    person_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    day_of_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    end_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_generated_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
