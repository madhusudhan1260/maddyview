from fastapi import APIRouter

from app.api.v1.crud import crud_router
from app.core import clock
from app.repositories import investment_goal_repo, savings_goal_repo
from app.schemas.goals import (
    InvestmentGoalCreate,
    InvestmentGoalOut,
    InvestmentGoalUpdate,
    SavingsGoalCreate,
    SavingsGoalOut,
    SavingsGoalUpdate,
)
from app.services import goal_service

router = APIRouter()
router.include_router(crud_router(
    path="/savings-goals", tag="goals", repo=savings_goal_repo, create_schema=SavingsGoalCreate,
    update_schema=SavingsGoalUpdate, out_schema=SavingsGoalOut, entity="savings_goal",
    view=lambda ctx, g: goal_service.savings_goal_view(g, clock.today()),
))
router.include_router(crud_router(
    path="/investment-goals", tag="goals", repo=investment_goal_repo, create_schema=InvestmentGoalCreate,
    update_schema=InvestmentGoalUpdate, out_schema=InvestmentGoalOut, entity="investment_goal",
    view=lambda ctx, g: goal_service.investment_goal_view(g, clock.today()),
))
