from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import MONEY, PRICE, QUANTITY, Base, IdMixin, TimestampMixin, str_enum
from app.models.enums import DataSource, InstrumentType, InvestmentTxnType
from app.models.finance import source_column, user_fk


class Instrument(IdMixin, TimestampMixin, Base):
    """Security master (stocks, mutual-fund schemes, ETFs...). Shared across users."""

    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("instrument_type", "symbol", "exchange"),)

    instrument_type: Mapped[InstrumentType] = mapped_column(str_enum(InstrumentType, "instrument_type"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")  # NSE/BSE/"" for MF
    isin: Mapped[str | None] = mapped_column(String(12), unique=True)
    scheme_code: Mapped[str | None] = mapped_column(String(20), index=True)  # AMFI code for mutual funds
    sector: Mapped[str | None] = mapped_column(String(80))
    source: Mapped[DataSource] = source_column()


class Portfolio(IdMixin, TimestampMixin, Base):
    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    user_id: Mapped[int] = user_fk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[DataSource] = source_column()

    holdings: Mapped[list["Holding"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class Holding(IdMixin, TimestampMixin, Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "instrument_id"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("avg_cost >= 0", name="avg_cost_non_negative"),
    )

    portfolio_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    source: Mapped[DataSource] = source_column()

    portfolio: Mapped[Portfolio] = relationship(back_populates="holdings")
    instrument: Mapped[Instrument] = relationship()


class InvestmentTransaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "investment_transactions"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("price >= 0", name="price_non_negative"),
        CheckConstraint("fees >= 0", name="fees_non_negative"),
        Index("ix_investment_transactions_portfolio_date", "portfolio_id", "txn_date"),
    )

    portfolio_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False, index=True)
    txn_type: Mapped[InvestmentTxnType] = mapped_column(str_enum(InvestmentTxnType, "investment_txn_type"), nullable=False)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(QUANTITY, nullable=False)
    price: Mapped[Decimal] = mapped_column(PRICE, nullable=False)
    fees: Mapped[Decimal] = mapped_column(MONEY, nullable=False, server_default="0")
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[DataSource] = source_column()
