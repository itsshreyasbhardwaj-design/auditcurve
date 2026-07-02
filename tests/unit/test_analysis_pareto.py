from auditcurve.analysis.pareto import StrategyPoint, pareto_frontier


def test_pareto_frontier_excludes_dominated_points():
    points = [
        StrategyPoint("full_review", None, mean_cost_usd=0.01, mean_latency_ms=100, f1=0.5, n=10),
        StrategyPoint("spot_check", 1, mean_cost_usd=0.005, mean_latency_ms=80, f1=0.3, n=10),
        StrategyPoint(
            "spot_check", 4, mean_cost_usd=0.02, mean_latency_ms=150, f1=0.4, n=10
        ),  # dominated: costs more than full_review but has lower F1
        StrategyPoint("streaming", None, mean_cost_usd=0.03, mean_latency_ms=200, f1=0.8, n=10),
    ]

    frontier = pareto_frontier(points, "cost")
    frontier_keys = {(p.strategy_name, p.budget) for p in frontier}

    # spot_check budget=4 is dominated (higher cost than full_review, lower F1) -- excluded
    assert ("spot_check", 4) not in frontier_keys
    # cheapest point is always on the frontier
    assert ("spot_check", 1) in frontier_keys
    # highest F1 overall is always on the frontier (nothing costs more AND scores worse)
    assert ("streaming", None) in frontier_keys


def test_pareto_frontier_is_monotonically_increasing_in_f1():
    points = [
        StrategyPoint("a", None, mean_cost_usd=0.01, mean_latency_ms=10, f1=0.2, n=5),
        StrategyPoint("b", None, mean_cost_usd=0.02, mean_latency_ms=20, f1=0.5, n=5),
        StrategyPoint("c", None, mean_cost_usd=0.03, mean_latency_ms=30, f1=0.9, n=5),
    ]
    frontier = pareto_frontier(points, "cost")
    f1s = [p.f1 for p in sorted(frontier, key=lambda p: p.mean_cost_usd)]
    assert f1s == sorted(f1s)


def test_pareto_frontier_latency_axis():
    points = [
        StrategyPoint("a", None, mean_cost_usd=0.05, mean_latency_ms=10, f1=0.9, n=5),
        StrategyPoint("b", None, mean_cost_usd=0.01, mean_latency_ms=50, f1=0.2, n=5),
    ]
    frontier = pareto_frontier(points, "latency")
    # "a" has both lower latency AND higher F1 -- "b" is fully dominated on the latency axis
    assert len(frontier) == 1
    assert frontier[0].strategy_name == "a"
