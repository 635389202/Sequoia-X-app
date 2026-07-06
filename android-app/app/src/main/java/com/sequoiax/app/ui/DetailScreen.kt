package com.sequoiax.app.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.sequoiax.app.data.StockDailyEntity
import kotlin.math.max
import kotlin.math.roundToInt

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun DetailScreen(symbol: String, viewModel: AppViewModel, marketColorMode: MarketColorMode) {
    val state by viewModel.detail.collectAsState()
    LaunchedEffect(symbol) {
        viewModel.loadDetail(symbol)
    }
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text(symbol, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        }
        items(state.rows) { row ->
            val note = strategyNote(row.strategy)
            ElevatedCard(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
            ) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("${row.name}  ${formatPrice(row.latestClose)}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("策略：${note.label}", color = MaterialTheme.colorScheme.secondary, fontWeight = FontWeight.SemiBold)
                    Text("解释：${note.explain}", style = MaterialTheme.typography.bodySmall)
                    Text("建议：${note.advice}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
                    Text("板块：${row.sector.ifEmpty { "未缓存" }}", fontWeight = FontWeight.SemiBold)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        val change5Tone = marketTone(row.change5, marketColorMode)
                        val change20Tone = marketTone(row.change20, marketColorMode)
                        val change60Tone = marketTone(row.change60, marketColorMode)
                        AssistChip(
                            onClick = {},
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = change5Tone.container,
                                labelColor = change5Tone.content,
                            ),
                            label = { Text("5日 ${formatPct(row.change5)}", fontWeight = FontWeight.Bold) },
                        )
                        AssistChip(
                            onClick = {},
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = change20Tone.container,
                                labelColor = change20Tone.content,
                            ),
                            label = { Text("20日 ${formatPct(row.change20)}", fontWeight = FontWeight.Bold) },
                        )
                        AssistChip(
                            onClick = {},
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = change60Tone.container,
                                labelColor = change60Tone.content,
                            ),
                            label = { Text("60日 ${formatPct(row.change60)}", fontWeight = FontWeight.Bold) },
                        )
                    }
                    Text(row.majorInfo.ifEmpty { "暂无近期重大信息" })
                }
            }
        }
        item {
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("近期价格趋势", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    PriceTrendChart(daily = state.daily, marketColorMode = marketColorMode)
                }
            }
        }
    }
}

@Composable
private fun PriceTrendChart(daily: List<StockDailyEntity>, marketColorMode: MarketColorMode) {
    val allPoints = daily
        .asReversed()
        .mapNotNull { item -> item.close?.let { item.date to it } }

    if (allPoints.size < 2) {
        Text("暂无足够价格数据", style = MaterialTheme.typography.bodySmall)
        return
    }

    val periods = listOf(20, 60, 120)
    var period by remember { mutableIntStateOf(60) }
    val points = allPoints.takeLast(period.coerceAtMost(allPoints.size))
    var selectedIndex by remember(period, points.size) { mutableIntStateOf(points.lastIndex) }

    val first = points.first()
    val last = points.last()
    val selected = points[selectedIndex.coerceIn(0, points.lastIndex)]
    val minPrice = points.minOf { it.second }
    val maxPrice = points.maxOf { it.second }
    val lineColor = marketLineColor(last.second >= first.second, marketColorMode)
    val fillColor = lineColor.copy(alpha = 0.18f)
    val gridColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.35f)
    val markerFillColor = MaterialTheme.colorScheme.surface
    val periodChange = if (first.second == 0.0) null else (last.second - first.second) / first.second * 100

    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        periods.forEach { item ->
            FilterChip(
                selected = period == item,
                onClick = { period = item },
                label = { Text("${item}日") },
            )
        }
    }

    Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
        Text(
            "${selected.first}  ${formatPrice(selected.second)}",
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Bold,
            color = lineColor,
        )
        Text(
            "区间 ${formatPct(periodChange)}",
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.SemiBold,
        )
    }

    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(188.dp)
            .pointerInput(points) {
                fun updateSelection(x: Float) {
                    val leftPadding = 6.dp.toPx()
                    val rightPadding = 6.dp.toPx()
                    val chartWidth = (size.width - leftPadding - rightPadding).coerceAtLeast(1f)
                    selectedIndex = (((x - leftPadding) / chartWidth) * points.lastIndex)
                        .roundToInt()
                        .coerceIn(0, points.lastIndex)
                }
                detectTapGestures { offset -> updateSelection(offset.x) }
            }
            .pointerInput(points) {
                fun updateSelection(x: Float) {
                    val leftPadding = 6.dp.toPx()
                    val rightPadding = 6.dp.toPx()
                    val chartWidth = (size.width - leftPadding - rightPadding).coerceAtLeast(1f)
                    selectedIndex = (((x - leftPadding) / chartWidth) * points.lastIndex)
                        .roundToInt()
                        .coerceIn(0, points.lastIndex)
                }
                detectDragGestures(
                    onDragStart = { offset -> updateSelection(offset.x) },
                    onDrag = { change, _ -> updateSelection(change.position.x) },
                )
            },
    ) {
        val leftPadding = 6.dp.toPx()
        val rightPadding = 6.dp.toPx()
        val topPadding = 10.dp.toPx()
        val bottomPadding = 16.dp.toPx()
        val chartWidth = size.width - leftPadding - rightPadding
        val chartHeight = size.height - topPadding - bottomPadding
        val range = max(maxPrice - minPrice, 0.01)

        fun xAt(index: Int): Float =
            leftPadding + chartWidth * index / (points.lastIndex.coerceAtLeast(1))

        fun yAt(price: Double): Float {
            val normalized = ((price - minPrice) / range).toFloat()
            return topPadding + chartHeight * (1f - normalized)
        }

        repeat(3) { step ->
            val y = topPadding + chartHeight * step / 2f
            drawLine(
                color = gridColor,
                start = Offset(leftPadding, y),
                end = Offset(size.width - rightPadding, y),
                strokeWidth = 1.dp.toPx(),
            )
        }

        val linePath = Path()
        points.forEachIndexed { index, point ->
            val x = xAt(index)
            val y = yAt(point.second)
            if (index == 0) linePath.moveTo(x, y) else linePath.lineTo(x, y)
        }

        val fillPath = Path().apply {
            addPath(linePath)
            lineTo(xAt(points.lastIndex), topPadding + chartHeight)
            lineTo(xAt(0), topPadding + chartHeight)
            close()
        }

        drawPath(
            path = fillPath,
            brush = Brush.verticalGradient(
                colors = listOf(fillColor, Color.Transparent),
                startY = topPadding,
                endY = topPadding + chartHeight,
            ),
        )
        drawPath(
            path = linePath,
            color = lineColor,
            style = Stroke(width = 2.5.dp.toPx(), cap = StrokeCap.Round),
        )

        val lastOffset = Offset(xAt(points.lastIndex), yAt(last.second))
        drawCircle(color = lineColor, radius = 4.dp.toPx(), center = lastOffset)

        val selectedOffset = Offset(xAt(selectedIndex), yAt(points[selectedIndex].second))
        drawLine(
            color = lineColor.copy(alpha = 0.65f),
            start = Offset(selectedOffset.x, topPadding),
            end = Offset(selectedOffset.x, topPadding + chartHeight),
            strokeWidth = 1.dp.toPx(),
        )
        drawCircle(color = markerFillColor, radius = 6.dp.toPx(), center = selectedOffset)
        drawCircle(color = lineColor, radius = 4.dp.toPx(), center = selectedOffset)
    }

    Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
        Text("${first.first}  ${formatPrice(first.second)}", style = MaterialTheme.typography.labelSmall)
        Text(
            "低 ${formatPrice(minPrice)}  高 ${formatPrice(maxPrice)}",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text("${last.first}  ${formatPrice(last.second)}", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold)
    }
}
