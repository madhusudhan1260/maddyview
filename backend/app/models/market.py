"""Market research, AI model tracking and paper trading (schema only in Milestone 1)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import MONEY, PRICE, QUANTITY, Base, IdMixin, TimestampMixin, str_enum
from app.models.enums import DataSource, IngestionStatus, ModelStatus, OrderSide, OrderStatus, OrderType
from app.models.finance import source_column, user_fk


# ---------- market research ----------
class MarketDataSource(IdMixin, TimestampMixin, Base):
    __tablename__ = "market_data_sources"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. NAV, EQUITY_PRICE, NEWS
    base_url: Mapped[str | None] = mapped_column(String(500))
    requires_api_key: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text)


class DataIngestionLog(IdMixin, Base):
    __tablename__ = "data_ingestion_logs"

    data_source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("market_data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[IngestionStatus] = mapped_column(str_enum(IngestionStatus, "ingestion_status"), nullable=False)
    records_ingested: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)


class NewsArticle(IdMixin, TimestampMixin, Base):
    __tablename__ = "news_articles"

    data_source_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("market_data_sources.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))  # AI_DERIVED when set
    source: Mapped[DataSource] = source_column(DataSource.REAL)


# ---------- AI ----------
class ModelRegistry(IdMixin, TimestampMixin, Base):
    __tablename__ = "model_registry"
    __table_args__ = (UniqueConstraint("name", "version"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    model_type: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[ModelStatus] = mapped_column(str_enum(ModelStatus, "model_status"), nullable=False, server_default=ModelStatus.DRAFT.value)


class ModelPrediction(IdMixin, Base):
    __tablename__ = "model_predictions"
    __table_args__ = (CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="confidence_range"),)

    model_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="CASCADE"), index=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    horizon: Mapped[str | None] = mapped_column(String(20))
    prediction: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    source: Mapped[DataSource] = source_column(DataSource.AI_DERIVED)


class PredictionResult(IdMixin, Base):
    __tablename__ = "prediction_results"

    prediction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("model_predictions.id", ondelete="CASCADE"), unique=True, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actual: Mapped[dict | None] = mapped_column(JSONB)
    error_metric: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)


# ---------- paper trading (simulation only — never real money) ----------
class PaperAccount(IdMixin, TimestampMixin, Base):
    __tablename__ = "paper_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "name"),
        CheckConstraint("starting_cash >= 0", name="starting_cash_non_negative"),
    )

    user_id: Mapped[int] = user_fk()
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    starting_cash: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    source: Mapped[DataSource] = source_column(DataSource.SIMULATED)


class PaperOrder(IdMixin, TimestampMixin, Base):
    __tablename__ = "paper_orders"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("order_type <> 'LIMIT' OR limit_price IS NOT NULL", name="limit_needs_price"),
    )

    paper_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)
    side: Mapped[OrderSide] = mapped_column(str_enum(OrderSide, "order_side"), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(str_enum(OrderType, "order_type"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(PRICE)
    status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus, "order_status"), nullable=False, server_default=OrderStatus.OPEN.value)
    source: Mapped[DataSource] = source_column(DataSource.SIMULATED)


class PaperPosition(IdMixin, TimestampMixin, Base):
    __tablename__ = "paper_positions"
    __table_args__ = (UniqueConstraint("paper_account_id", "instrument_id"),)

    paper_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    source: Mapped[DataSource] = source_column(DataSource.SIMULATED)


class PaperTrade(IdMixin, Base):
    __tablename__ = "paper_trades"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

    paper_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("paper_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)
    side: Mapped[OrderSide] = mapped_column(str_enum(OrderSide, "order_side"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source: Mapped[DataSource] = source_column(DataSource.SIMULATED)
