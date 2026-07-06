from sequoia_x.data.engine import BAOSTOCK_ADJUST_FLAG


def test_data_engine_uses_unadjusted_daily_prices_for_dashboard_consistency():
    assert BAOSTOCK_ADJUST_FLAG == "3"
