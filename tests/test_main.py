"""主程序入口属性测试。"""

import sys
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

# 预先导入 main 模块，避免在 @given 循环中重复导入
import main as main_module


# Feature: sequoia-x-v2, Property 13: 主程序异常以非零退出码终止
@given(error_msg=st.text(min_size=1, max_size=100))
@h_settings(max_examples=30, deadline=None)
def test_main_exits_nonzero_on_exception(error_msg: str) -> None:
    """属性 13：main() 中任意未捕获异常应导致 sys.exit(1)。"""
    # patch main 模块中直接引用的 get_settings
    with patch.object(main_module, "get_settings", side_effect=RuntimeError(error_msg)):
        with pytest.raises(SystemExit) as exc_info:
            main_module.main()
        assert exc_info.value.code != 0


def test_main_skip_sync_runs_strategies_without_fetching() -> None:
    engine = Mock()
    logger = Mock()
    notifier = Mock()
    selected = ["sh.600000"]
    strategy = Mock()
    strategy.run.return_value = selected
    strategy.webhook_key = "webhook"
    strategy.__class__.__name__ = "MockStrategy"

    with patch.object(main_module, "get_settings", return_value=object()), patch.object(
        main_module, "get_logger", return_value=logger
    ), patch.object(main_module, "DataEngine", return_value=engine), patch.object(
        main_module, "FeishuNotifier", return_value=notifier
    ), patch.object(
        main_module, "MaVolumeStrategy", return_value=strategy
    ), patch.object(
        main_module, "TurtleTradeStrategy", return_value=strategy
    ), patch.object(
        main_module, "HighTightFlagStrategy", return_value=strategy
    ), patch.object(
        main_module, "LimitUpShakeoutStrategy", return_value=strategy
    ), patch.object(
        main_module, "UptrendLimitDownStrategy", return_value=strategy
    ), patch.object(
        main_module, "RpsBreakoutStrategy", return_value=strategy
    ), patch.object(
        main_module, "PrivatePlacementStrategy", return_value=strategy
    ), patch.object(sys, "argv", ["main.py", "--skip-sync"]):
        main_module.main()

    engine.sync_today_bulk.assert_not_called()
    assert strategy.run.call_count == 7
    notifier.send.assert_called()
