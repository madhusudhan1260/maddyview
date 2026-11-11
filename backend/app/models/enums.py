"""Enumerations shared by models, schemas and services."""

import enum


class DataSource(str, enum.Enum):
    """Provenance label carried by every financial and market record."""

    REAL = "REAL"  # verified from an authoritative external source
    DEMO = "DEMO"  # illustrative sample data, never presented as real
    USER_ENTERED = "USER_ENTERED"  # typed in manually by the user
    SIMULATED = "SIMULATED"  # paper-trading / simulation output
    AI_DERIVED = "AI_DERIVED"  # produced by a model; uncertain by nature


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    UPI = "UPI"
    DEBIT_CARD = "DEBIT_CARD"
    CREDIT_CARD = "CREDIT_CARD"
    NET_BANKING = "NET_BANKING"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"


class AccountType(str, enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    SALARY = "SALARY"
    OTHER = "OTHER"


class TxnDirection(str, enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class LiabilityType(str, enum.Enum):
    HOME_LOAN = "HOME_LOAN"
    PERSONAL_LOAN = "PERSONAL_LOAN"
    CAR_LOAN = "CAR_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"
    CREDIT_CARD = "CREDIT_CARD"
    OTHER = "OTHER"


class CompoundingFrequency(str, enum.Enum):
    SIMPLE = "SIMPLE"  # no compounding
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    YEARLY = "YEARLY"


class PayoutType(str, enum.Enum):
    CUMULATIVE = "CUMULATIVE"  # interest re-invested, paid at maturity
    MONTHLY_PAYOUT = "MONTHLY_PAYOUT"
    QUARTERLY_PAYOUT = "QUARTERLY_PAYOUT"
    HALF_YEARLY_PAYOUT = "HALF_YEARLY_PAYOUT"
    YEARLY_PAYOUT = "YEARLY_PAYOUT"


class DepositStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    CLOSED = "CLOSED"  # closed before maturity
    RENEWED = "RENEWED"


class GoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACHIEVED = "ACHIEVED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class InstrumentType(str, enum.Enum):
    STOCK = "STOCK"
    MUTUAL_FUND = "MUTUAL_FUND"
    ETF = "ETF"
    BOND = "BOND"
    INDEX = "INDEX"
    OTHER = "OTHER"


class InvestmentTxnType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    SIP = "SIP"
    DIVIDEND = "DIVIDEND"
    SWITCH_IN = "SWITCH_IN"
    SWITCH_OUT = "SWITCH_OUT"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class IngestionStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ModelStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Theme(str, enum.Enum):
    DARK = "DARK"
    LIGHT = "LIGHT"
