package com.sequoiax.app.ui

data class StrategyDisplayNote(
    val label: String,
    val explain: String,
    val advice: String,
)

private val StrategyNotes = mapOf(
    "MovingAverageVolumeStrategy" to StrategyDisplayNote(
        label = "均线放量",
        explain = "均线趋势配合成交量放大，偏向寻找趋势刚启动或放量突破的标的。",
        advice = "适合先做候选池，重点复核突破位置、量能是否持续，以及是否追高。",
    ),
    "TurtleTradingStrategy" to StrategyDisplayNote(
        label = "海龟突破",
        explain = "参考海龟交易思路，关注阶段新高和趋势延续信号。",
        advice = "适合趋势行情，建议结合止损位和回撤承受能力，不适合无计划追涨。",
    ),
    "HighTightFlagStrategy" to StrategyDisplayNote(
        label = "高位紧旗形",
        explain = "寻找大幅上涨后高位窄幅整理的强势形态。",
        advice = "信号稀少但波动通常较大，建议只在放量突破且市场情绪配合时观察。",
    ),
    "LimitUpShakeoutStrategy" to StrategyDisplayNote(
        label = "涨停洗盘",
        explain = "关注涨停后回踩洗盘，再重新确认强势的形态。",
        advice = "适合短线观察，重点看回踩是否缩量、再次走强是否放量。",
    ),
    "OversoldReboundStrategy" to StrategyDisplayNote(
        label = "超跌反弹",
        explain = "寻找上升趋势中出现极端下跌后可能快速修复的标的。",
        advice = "风险较高，建议优先排查利空原因，确认不是基本面或监管风险。",
    ),
    "RpsBreakoutStrategy" to StrategyDisplayNote(
        label = "RPS强度突破",
        explain = "用相对强度筛选明显跑赢市场并尝试突破的股票。",
        advice = "适合强势股池筛选，建议叠加行业强度、成交额和均线结构复核。",
    ),
    "PrivatePlacementStrategy" to StrategyDisplayNote(
        label = "定增事件",
        explain = "关注近期定增事件，偏事件驱动筛选。",
        advice = "建议核对公告质量、发行价格、锁定期和资金用途，不宜只看事件名称。",
    ),
)

private val StrategyAliases = mapOf(
    "MaVolumeStrategy" to "MovingAverageVolumeStrategy",
    "TurtleTradeStrategy" to "TurtleTradingStrategy",
    "UptrendLimitDownStrategy" to "OversoldReboundStrategy",
)

fun strategyNote(strategy: String): StrategyDisplayNote =
    StrategyNotes[strategy] ?: StrategyAliases[strategy]?.let { StrategyNotes[it] } ?: StrategyDisplayNote(
        label = strategy.ifBlank { "未命名策略" },
        explain = "暂无说明。",
        advice = "仅作为候选池线索，需要结合走势和风险复核。",
    )

fun strategyLabel(strategy: String): String = strategyNote(strategy).label
