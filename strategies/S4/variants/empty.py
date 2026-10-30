"""Baseline that never trades (timing reference)."""
from datamodel import TradingState


class Trader:
    def run(self, state: TradingState):
        return {}, 0, ""
