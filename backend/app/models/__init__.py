"""Importing this package registers every table on Base.metadata (used by Alembic)."""

from app.models.deposits import FixedDeposit, RecurringDeposit
from app.models.finance import BankAccount, ExpenseRecord, IncomeRecord, Liability, MonthlyBudget, Transaction
from app.models.goals import InvestmentGoal, SavingsGoal
from app.models.investments import Holding, Instrument, InvestmentTransaction, Portfolio
from app.models.market import (
    DataIngestionLog,
    MarketDataSource,
    ModelPrediction,
    ModelRegistry,
    NewsArticle,
    PaperAccount,
    PaperOrder,
    PaperPosition,
    PaperTrade,
    PredictionResult,
)
from app.models.system import Alert, AuditLog
from app.models.user import AuthSession, User, UserSettings

__all__ = [
    "Alert", "AuditLog", "AuthSession", "BankAccount", "DataIngestionLog", "ExpenseRecord", "FixedDeposit",
    "Holding", "IncomeRecord", "Instrument", "InvestmentGoal", "InvestmentTransaction", "Liability",
    "MarketDataSource", "ModelPrediction", "ModelRegistry", "MonthlyBudget", "NewsArticle", "PaperAccount",
    "PaperOrder", "PaperPosition", "PaperTrade", "Portfolio", "PredictionResult", "RecurringDeposit",
    "SavingsGoal", "Transaction", "User", "UserSettings",
]
