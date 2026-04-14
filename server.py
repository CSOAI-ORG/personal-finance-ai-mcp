"""
Personal Finance AI MCP Server - Financial Planning Intelligence
Built by MEOK AI Labs | https://meok.ai

Budget tracking, savings calculations, debt payoff planning,
investment analysis, and tax estimation.
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import time
import math
from datetime import datetime, timezone
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "personal-finance-ai")

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
_RATE_LIMITS = {"free": {"requests_per_hour": 60}, "pro": {"requests_per_hour": 5000}}
_request_log: list[float] = []
_tier = "free"


def _check_rate_limit() -> bool:
    now = time.time()
    _request_log[:] = [t for t in _request_log if now - t < 3600]
    if len(_request_log) >= _RATE_LIMITS[_tier]["requests_per_hour"]:
        return False
    _request_log.append(now)
    return True


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
_BUDGET_CATEGORIES = {
    "housing": {"recommended_pct": 28, "includes": ["rent/mortgage", "insurance", "property_tax", "maintenance"]},
    "transportation": {"recommended_pct": 12, "includes": ["car_payment", "fuel", "insurance", "public_transit"]},
    "food": {"recommended_pct": 12, "includes": ["groceries", "dining_out"]},
    "utilities": {"recommended_pct": 5, "includes": ["electric", "gas", "water", "internet", "phone"]},
    "healthcare": {"recommended_pct": 8, "includes": ["insurance", "prescriptions", "dental", "vision"]},
    "savings": {"recommended_pct": 20, "includes": ["emergency_fund", "retirement", "investments"]},
    "personal": {"recommended_pct": 5, "includes": ["clothing", "grooming", "subscriptions"]},
    "entertainment": {"recommended_pct": 5, "includes": ["streaming", "hobbies", "events"]},
    "debt_payments": {"recommended_pct": 5, "includes": ["credit_cards", "student_loans", "personal_loans"]},
}

_US_TAX_BRACKETS_2026_SINGLE = [
    (11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
    (243725, 0.32), (609350, 0.35), (float("inf"), 0.37),
]

_US_TAX_BRACKETS_2026_MARRIED = [
    (23200, 0.10), (94300, 0.12), (201050, 0.22), (383900, 0.24),
    (487450, 0.32), (731200, 0.35), (float("inf"), 0.37),
]

_STANDARD_DEDUCTION = {"single": 14600, "married": 29200, "head_of_household": 21900}


@mcp.tool()
def track_budget(
    monthly_income: float,
    expenses: list[dict], api_key: str = "") -> dict:
    """Analyze spending against recommended budget allocations.

    Args:
        monthly_income: Gross monthly income.
        expenses: List of expenses with keys: category, amount, description (optional).
                 Categories: housing, transportation, food, utilities, healthcare,
                 savings, personal, entertainment, debt_payments.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate_limit():
        return {"error": "Rate limit exceeded. Upgrade to pro tier."}

    category_totals: dict[str, float] = {}
    for exp in expenses:
        cat = exp.get("category", "personal")
        category_totals[cat] = category_totals.get(cat, 0) + exp.get("amount", 0)

    total_expenses = sum(category_totals.values())
    remaining = monthly_income - total_expenses

    analysis = []
    over_budget = []
    for cat, info in _BUDGET_CATEGORIES.items():
        actual = category_totals.get(cat, 0)
        recommended = monthly_income * (info["recommended_pct"] / 100)
        actual_pct = round((actual / monthly_income) * 100, 1) if monthly_income > 0 else 0
        diff = round(actual - recommended, 2)

        status = "on_track" if abs(diff) < recommended * 0.1 else "over" if diff > 0 else "under"
        if status == "over":
            over_budget.append(cat)

        analysis.append({
            "category": cat, "actual": round(actual, 2), "recommended": round(recommended, 2),
            "actual_pct": actual_pct, "recommended_pct": info["recommended_pct"],
            "difference": diff, "status": status,
        })

    savings_rate = round((category_totals.get("savings", 0) / monthly_income) * 100, 1) if monthly_income else 0

    return {
        "monthly_income": monthly_income,
        "total_expenses": round(total_expenses, 2),
        "remaining": round(remaining, 2),
        "savings_rate_pct": savings_rate,
        "category_analysis": analysis,
        "alerts": [f"{cat} is over budget" for cat in over_budget],
        "health_score": max(0, min(100, round(100 - len(over_budget) * 15 + (savings_rate * 2)))),
        "recommendation": "Increase savings to 20%+" if savings_rate < 20 else "Great savings rate!",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def calculate_savings(
    target_amount: float,
    current_savings: float = 0,
    monthly_contribution: float = 500,
    annual_return_pct: float = 5.0,
    inflation_pct: float = 2.5, api_key: str = "") -> dict:
    """Calculate time to reach a savings goal with compound interest.

    Args:
        target_amount: Savings target in dollars.
        current_savings: Current savings balance.
        monthly_contribution: Monthly savings amount.
        annual_return_pct: Expected annual return percentage.
        inflation_pct: Expected annual inflation percentage.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate_limit():
        return {"error": "Rate limit exceeded. Upgrade to pro tier."}

    monthly_rate = (annual_return_pct / 100) / 12
    real_return = annual_return_pct - inflation_pct

    balance = current_savings
    months = 0
    max_months = 600  # 50 years cap
    yearly_snapshots = []

    while balance < target_amount and months < max_months:
        balance = balance * (1 + monthly_rate) + monthly_contribution
        months += 1
        if months % 12 == 0:
            total_contributed = current_savings + (monthly_contribution * months)
            interest_earned = balance - total_contributed
            yearly_snapshots.append({
                "year": months // 12, "balance": round(balance),
                "contributed": round(total_contributed),
                "interest_earned": round(interest_earned),
            })

    total_contributed = current_savings + (monthly_contribution * months)
    total_interest = balance - total_contributed

    # Real (inflation-adjusted) final value
    years = months / 12
    real_value = balance / ((1 + inflation_pct / 100) ** years) if years > 0 else balance

    return {
        "target": target_amount,
        "months_to_goal": months,
        "years_to_goal": round(months / 12, 1),
        "final_balance": round(balance, 2),
        "total_contributed": round(total_contributed, 2),
        "total_interest_earned": round(total_interest, 2),
        "real_value_today_dollars": round(real_value, 2),
        "effective_real_return_pct": round(real_return, 2),
        "yearly_projection": yearly_snapshots[:10],
        "achievable": months < max_months,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def plan_debt_payoff(
    debts: list[dict],
    extra_monthly_payment: float = 0,
    strategy: str = "avalanche", api_key: str = "") -> dict:
    """Create a debt payoff plan using avalanche or snowball method.

    Args:
        debts: List with keys: name, balance, interest_rate_pct, min_payment.
              Example: [{"name": "Credit Card", "balance": 5000, "interest_rate_pct": 19.9, "min_payment": 100}]
        extra_monthly_payment: Additional monthly amount above minimums.
        strategy: avalanche (highest interest first) | snowball (smallest balance first).
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate_limit():
        return {"error": "Rate limit exceeded. Upgrade to pro tier."}

    if not debts:
        return {"error": "Provide at least one debt."}

    if strategy == "avalanche":
        ordered = sorted(debts, key=lambda d: d.get("interest_rate_pct", 0), reverse=True)
    else:
        ordered = sorted(debts, key=lambda d: d.get("balance", 0))

    total_balance = sum(d.get("balance", 0) for d in debts)
    total_min = sum(d.get("min_payment", 0) for d in debts)
    total_interest_paid = 0

    # Simulate payoff
    balances = {d["name"]: d["balance"] for d in debts}
    rates = {d["name"]: d["interest_rate_pct"] / 100 / 12 for d in debts}
    mins = {d["name"]: d["min_payment"] for d in debts}
    payoff_months: dict[str, int] = {}
    month = 0
    max_months = 600

    while any(b > 0.01 for b in balances.values()) and month < max_months:
        month += 1
        extra_left = extra_monthly_payment

        for d in ordered:
            name = d["name"]
            if balances[name] <= 0:
                continue

            interest = balances[name] * rates[name]
            total_interest_paid += interest
            balances[name] += interest

            payment = min(balances[name], mins[name])
            balances[name] -= payment

        # Apply extra to priority debt
        for d in ordered:
            name = d["name"]
            if balances[name] <= 0:
                continue
            extra_payment = min(extra_left, balances[name])
            balances[name] -= extra_payment
            extra_left -= extra_payment
            if extra_left <= 0:
                break

        for name, bal in balances.items():
            if bal <= 0.01 and name not in payoff_months:
                payoff_months[name] = month

    plan = []
    for d in ordered:
        name = d["name"]
        plan.append({
            "name": name, "starting_balance": d["balance"],
            "interest_rate_pct": d.get("interest_rate_pct", 0),
            "min_payment": d.get("min_payment", 0),
            "payoff_month": payoff_months.get(name, max_months),
            "payoff_years": round(payoff_months.get(name, max_months) / 12, 1),
        })

    return {
        "strategy": strategy,
        "total_starting_debt": round(total_balance, 2),
        "total_monthly_payment": round(total_min + extra_monthly_payment, 2),
        "total_interest_paid": round(total_interest_paid, 2),
        "total_months": month,
        "total_years": round(month / 12, 1),
        "payoff_order": plan,
        "savings_tip": "Avalanche saves more on interest; snowball gives faster psychological wins.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def analyze_investment(
    initial_investment: float,
    monthly_addition: float = 0,
    years: int = 10,
    allocation: Optional[dict] = None, api_key: str = "") -> dict:
    """Analyze investment growth with asset allocation modeling.

    Args:
        initial_investment: Starting investment amount.
        monthly_addition: Monthly contribution.
        years: Investment horizon in years.
        allocation: Asset allocation percentages. Example: {"stocks": 60, "bonds": 30, "cash": 10}.
                   Defaults to age-based if omitted.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate_limit():
        return {"error": "Rate limit exceeded. Upgrade to pro tier."}

    _ASSET_RETURNS = {
        "stocks": {"avg_return": 10.0, "std_dev": 18.0, "best_year": 33.0, "worst_year": -38.0},
        "bonds": {"avg_return": 4.5, "std_dev": 5.0, "best_year": 15.0, "worst_year": -13.0},
        "cash": {"avg_return": 2.0, "std_dev": 0.5, "best_year": 5.0, "worst_year": 0.0},
        "real_estate": {"avg_return": 8.0, "std_dev": 12.0, "best_year": 25.0, "worst_year": -20.0},
        "crypto": {"avg_return": 15.0, "std_dev": 60.0, "best_year": 300.0, "worst_year": -80.0},
    }

    if not allocation:
        allocation = {"stocks": 60, "bonds": 30, "cash": 10}

    total_pct = sum(allocation.values())
    if abs(total_pct - 100) > 1:
        return {"error": f"Allocation must sum to 100%, got {total_pct}%"}

    weighted_return = sum(
        (pct / 100) * _ASSET_RETURNS.get(asset, {"avg_return": 5})["avg_return"]
        for asset, pct in allocation.items()
    )
    weighted_risk = math.sqrt(sum(
        ((pct / 100) * _ASSET_RETURNS.get(asset, {"std_dev": 10})["std_dev"]) ** 2
        for asset, pct in allocation.items()
    ))

    monthly_rate = weighted_return / 100 / 12
    n_months = years * 12
    balance = initial_investment
    projections = []

    for year in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly_addition
        total_invested = initial_investment + monthly_addition * year * 12
        projections.append({
            "year": year, "balance": round(balance),
            "total_invested": round(total_invested),
            "growth": round(balance - total_invested),
        })

    total_invested = initial_investment + monthly_addition * n_months

    # Scenarios
    optimistic_rate = (weighted_return + weighted_risk * 0.5) / 100 / 12
    pessimistic_rate = max(0, (weighted_return - weighted_risk * 0.5)) / 100 / 12

    opt_balance = initial_investment
    pess_balance = initial_investment
    for _ in range(n_months):
        opt_balance = opt_balance * (1 + optimistic_rate) + monthly_addition
        pess_balance = pess_balance * (1 + pessimistic_rate) + monthly_addition

    return {
        "initial_investment": initial_investment,
        "monthly_addition": monthly_addition,
        "years": years,
        "allocation": allocation,
        "expected_return_pct": round(weighted_return, 2),
        "portfolio_risk_pct": round(weighted_risk, 2),
        "projections": {
            "expected": round(balance),
            "optimistic": round(opt_balance),
            "pessimistic": round(pess_balance),
        },
        "total_invested": round(total_invested),
        "expected_growth": round(balance - total_invested),
        "yearly_projection": projections,
        "risk_profile": "conservative" if weighted_risk < 8 else "moderate" if weighted_risk < 15 else "aggressive",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def estimate_tax(
    gross_income: float,
    filing_status: str = "single",
    deductions: Optional[dict] = None,
    state: Optional[str] = None,
    self_employment_income: float = 0, api_key: str = "") -> dict:
    """Estimate US federal income tax liability.

    Args:
        gross_income: Total gross income.
        filing_status: single | married | head_of_household.
        deductions: Dict of itemized deductions. Example: {"mortgage_interest": 12000, "charity": 3000}.
                   Uses standard deduction if total itemized is lower.
        state: State code for state tax estimate (simplified).
        self_employment_income: Self-employment income (subject to SE tax).
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate_limit():
        return {"error": "Rate limit exceeded. Upgrade to pro tier."}

    standard = _STANDARD_DEDUCTION.get(filing_status, 14600)
    itemized_total = sum(deductions.values()) if deductions else 0
    deduction_used = max(standard, itemized_total)
    deduction_type = "itemized" if itemized_total > standard else "standard"

    taxable_income = max(0, gross_income - deduction_used)

    brackets = _US_TAX_BRACKETS_2026_MARRIED if filing_status == "married" else _US_TAX_BRACKETS_2026_SINGLE
    federal_tax = 0.0
    bracket_breakdown = []
    prev_limit = 0

    for limit, rate in brackets:
        if taxable_income <= 0:
            break
        taxable_in_bracket = min(taxable_income, limit) - prev_limit
        if taxable_in_bracket <= 0:
            prev_limit = limit
            continue
        tax_in_bracket = taxable_in_bracket * rate
        federal_tax += tax_in_bracket
        bracket_breakdown.append({
            "bracket": f"{prev_limit:,}-{limit:,}" if limit < float("inf") else f"{prev_limit:,}+",
            "rate_pct": round(rate * 100, 1),
            "taxable_amount": round(taxable_in_bracket),
            "tax": round(tax_in_bracket, 2),
        })
        prev_limit = limit

    # Self-employment tax
    se_tax = 0.0
    if self_employment_income > 0:
        se_taxable = self_employment_income * 0.9235
        se_tax = se_taxable * 0.153
        if se_taxable > 168600:
            se_tax = 168600 * 0.124 + se_taxable * 0.029

    # FICA (employee portion)
    fica_ss = min(gross_income - self_employment_income, 168600) * 0.062
    fica_medicare = (gross_income - self_employment_income) * 0.0145
    additional_medicare = max(0, gross_income - 200000) * 0.009

    # Simplified state tax
    state_tax = 0.0
    _STATE_RATES = {
        "CA": 0.093, "NY": 0.085, "TX": 0.0, "FL": 0.0, "WA": 0.0,
        "IL": 0.0495, "PA": 0.0307, "OH": 0.04, "NJ": 0.089, "NC": 0.0475,
    }
    if state:
        state_rate = _STATE_RATES.get(state.upper(), 0.05)
        state_tax = taxable_income * state_rate

    total_tax = federal_tax + se_tax + fica_ss + fica_medicare + additional_medicare + state_tax
    effective_rate = round((total_tax / gross_income) * 100, 2) if gross_income else 0

    return {
        "gross_income": gross_income,
        "deduction": {"type": deduction_type, "amount": round(deduction_used)},
        "taxable_income": round(taxable_income),
        "federal_tax": round(federal_tax, 2),
        "bracket_breakdown": bracket_breakdown,
        "fica": {"social_security": round(fica_ss, 2), "medicare": round(fica_medicare + additional_medicare, 2)},
        "self_employment_tax": round(se_tax, 2),
        "state_tax": round(state_tax, 2) if state else None,
        "total_estimated_tax": round(total_tax, 2),
        "effective_tax_rate_pct": effective_rate,
        "take_home_annual": round(gross_income - total_tax),
        "take_home_monthly": round((gross_income - total_tax) / 12),
        "disclaimer": "Estimate only. Consult a tax professional for actual filing.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    mcp.run()
