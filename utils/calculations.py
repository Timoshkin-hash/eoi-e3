"""Расчёты для экзаменационной задачи №3."""
from __future__ import annotations

import math
from typing import Iterable


def arpu(price: float, conversion: float) -> float:
    return price * conversion


def ltv(arpu_value: float, churn: float) -> float:
    return arpu_value / churn


def ltv_cac(ltv_value: float, cac: float) -> float:
    return ltv_value / cac


def user_bases(initial_users: int, growth_rates: Iterable[float]) -> list[float]:
    bases = [float(initial_users)]
    for rate in growth_rates:
        bases.append(bases[-1] * (1 + rate))
    return bases


def annual_profit(
    base_users: float,
    new_users: float,
    monthly_arpu: float,
    monthly_maintenance: float,
    cac: float,
    development_cost: float = 0.0,
) -> float:
    revenue = base_users * monthly_arpu * 12
    maintenance = monthly_maintenance * 12
    acquisition = new_users * cac
    return revenue - maintenance - acquisition - development_cost


def discount_factor(year: int, annual_rate: float) -> float:
    return 1 / ((1 + annual_rate) ** year)


def npv(cash_flows: Iterable[float], annual_rate: float) -> float:
    return sum(cf / ((1 + annual_rate) ** year) for year, cf in enumerate(cash_flows))


def sensitivity_npv(
    strategy: dict,
    bases: list[float],
    growth_rates: list[float],
    maintenance: float,
    cac: float,
    development_cost: float,
    annual_rate: float,
    conversion_multiplier: float = 1.0,
    churn_multiplier: float = 1.0,
    cac_multiplier: float = 1.0,
) -> float:
    conversion = strategy["conversion"] * conversion_multiplier
    monthly_arpu = strategy["price_rub_month"] * conversion
    # The base case must remain equal to the main cash-flow model. For churn
    # scenarios, scale the effective revenue by the relative retention change.
    # This is an explicit annual approximation because the task gives no monthly
    # customer cohort schedule.
    base_retention = 1 - strategy["churn"]
    scenario_retention = 1 - strategy["churn"] * churn_multiplier
    monthly_arpu *= scenario_retention / base_retention
    flows = [-development_cost]
    previous = bases[0]
    for year in range(1, len(bases)):
        current = bases[year]
        flows.append(
            annual_profit(
                current,
                current - previous,
                monthly_arpu,
                maintenance,
                cac * cac_multiplier,
            )
        )
        previous = current
    return npv(flows, annual_rate)
