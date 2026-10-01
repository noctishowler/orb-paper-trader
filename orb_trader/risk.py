from dataclasses import dataclass


@dataclass
class PositionPlan:
    symbol: str
    entry: float
    stop: float
    dollars: float
    risk_dollars: float
    risk_per_share: float


class RiskManager:
    def __init__(self, config: dict):
        self.account = config["virtual_account"]
        self.strategy = config["strategy"]

    def position_plan(
        self,
        symbol: str,
        entry: float,
        atr: float,
    ) -> PositionPlan | None:

        stop_distance = atr * self.strategy["atr_stop_multiple"]

        if stop_distance <= 0:
            return None

        stop = entry - stop_distance

        risk_budget = self.account["risk_per_trade"]

        risk_pct = stop_distance / entry

        if risk_pct <= 0:
            return None

        dollars_by_risk = risk_budget / risk_pct

        dollars = min(
            dollars_by_risk,
            self.account["max_position_value"],
        )

        if dollars < 1:
            return None

        actual_risk = dollars * risk_pct

        return PositionPlan(
            symbol=symbol,
            entry=entry,
            stop=stop,
            dollars=round(dollars, 2),
            risk_dollars=round(actual_risk, 2),
            risk_per_share=stop_distance,
        )
