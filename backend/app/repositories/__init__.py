from app.models import (
    BankAccount,
    ExpenseRecord,
    FixedDeposit,
    IncomeRecord,
    InvestmentGoal,
    Liability,
    RecurringDeposit,
    SavingsGoal,
)
from app.repositories.base import OwnedRepository, visible_sources

income_repo = OwnedRepository(IncomeRecord, "Income record")
expense_repo = OwnedRepository(ExpenseRecord, "Expense record")
bank_account_repo = OwnedRepository(BankAccount, "Bank account")
liability_repo = OwnedRepository(Liability, "Liability")
fd_repo = OwnedRepository(FixedDeposit, "Fixed deposit")
rd_repo = OwnedRepository(RecurringDeposit, "Recurring deposit")
savings_goal_repo = OwnedRepository(SavingsGoal, "Savings goal")
investment_goal_repo = OwnedRepository(InvestmentGoal, "Investment goal")

__all__ = [
    "OwnedRepository", "visible_sources", "income_repo", "expense_repo", "bank_account_repo", "liability_repo",
    "fd_repo", "rd_repo", "savings_goal_repo", "investment_goal_repo",
]
