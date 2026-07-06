package com.sequoiax.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.SettingsSuggest
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.snapshotFlow
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import com.sequoiax.app.ui.theme.ThemeMode

@Composable
fun HomeScreen(
    viewModel: AppViewModel,
    onOpenDetail: (String) -> Unit,
    themeMode: ThemeMode,
    onToggleTheme: () -> Unit,
    marketColorMode: MarketColorMode,
) {
    val state by viewModel.home.collectAsState()
    val listState = rememberLazyListState()
    var headerExpanded by remember { mutableStateOf(true) }
    var searchExpanded by remember { mutableStateOf(false) }
    var highlightedRowKey by remember { mutableStateOf("") }
    val showSearchField = searchExpanded || state.query.isNotEmpty()

    LaunchedEffect(listState) {
        var previousIndex = listState.firstVisibleItemIndex
        var previousOffset = listState.firstVisibleItemScrollOffset
        var accumulatedDown = 0
        snapshotFlow { listState.firstVisibleItemIndex to listState.firstVisibleItemScrollOffset }
            .collect { (index, offset) ->
                val delta = (index - previousIndex) * 1000 + (offset - previousOffset)
                when {
                    index == 0 && offset == 0 -> {
                        headerExpanded = true
                        accumulatedDown = 0
                    }
                    delta > 0 -> {
                        accumulatedDown += delta
                        if (headerExpanded && accumulatedDown > 96) headerExpanded = false
                    }
                    delta < 0 -> accumulatedDown = 0
                }
                previousIndex = index
                previousOffset = offset
            }
    }

    LaunchedEffect(listState, state.rows.size, state.canLoadMoreRows) {
        snapshotFlow { listState.layoutInfo.visibleItemsInfo }
            .collect { visibleItems ->
                if (visibleItems.isEmpty()) return@collect
                val viewportCenter = (listState.layoutInfo.viewportStartOffset + listState.layoutInfo.viewportEndOffset) / 2
                val centerItem = visibleItems.minByOrNull { item ->
                    kotlin.math.abs((item.offset + item.size / 2) - viewportCenter)
                } ?: return@collect
                val centerIndex = centerItem.index
                state.rows.getOrNull(centerIndex)?.let { row ->
                    highlightedRowKey = "${row.date}-${row.strategy}-${row.symbol}"
                }
                if (state.canLoadMoreRows && centerIndex >= state.rows.lastIndex - 6) {
                    viewModel.loadMoreRows()
                }
            }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 12.dp, vertical = 4.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (headerExpanded) {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                HeaderSummary(
                    state = state,
                    themeMode = themeMode,
                    onToggleTheme = onToggleTheme,
                    onToggleSearch = { searchExpanded = !searchExpanded },
                )
                if (showSearchField) {
                    SearchField(
                        state = state,
                        viewModel = viewModel,
                        onClose = {
                            viewModel.setQuery("")
                            searchExpanded = false
                        },
                    )
                }
                StrategyHelp(state)
            }
        }
        if (state.isImporting) LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        FilterRow(state = state, viewModel = viewModel)
        LazyColumn(
            modifier = Modifier.weight(1f),
            state = listState,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(
                items = state.rows,
                key = { "${it.date}-${it.strategy}-${it.symbol}" },
                contentType = { "stock-result" },
            ) { row ->
                val key = "${row.date}-${row.strategy}-${row.symbol}"
                ResultRow(
                    row = row,
                    highlighted = key == highlightedRowKey,
                    marketColorMode = marketColorMode,
                    strategyHits = state.strategyHitsBySymbol[row.symbol].orEmpty(),
                    onClick = { onOpenDetail(row.symbol) },
                )
            }
        }
    }
}

@Composable
private fun HeaderSummary(
    state: HomeUiState,
    themeMode: ThemeMode,
    onToggleTheme: () -> Unit,
    onToggleSearch: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("今日候选", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            IconButton(onClick = onToggleSearch) {
                Icon(Icons.Filled.Search, contentDescription = "搜索")
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = if (state.latestDate.isEmpty()) "尚未导入" else "${state.latestDate} · ${state.totalRows}条",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.SemiBold,
            )
            IconButton(onClick = onToggleTheme) {
                Icon(homeThemeIcon(themeMode), contentDescription = "切换主题：${themeMode.label}")
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SearchField(state: HomeUiState, viewModel: AppViewModel, onClose: () -> Unit) {
    OutlinedTextField(
        value = state.query,
        onValueChange = viewModel::setQuery,
        placeholder = { Text("搜索代码、名称、板块或重大信息") },
        trailingIcon = {
            IconButton(onClick = onClose) {
                Icon(Icons.Filled.Close, contentDescription = "关闭搜索")
            }
        },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun FilterRow(state: HomeUiState, viewModel: AppViewModel) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        StrategyMenu(state, viewModel, Modifier.weight(1f))
        SortMenu(state, viewModel, Modifier.weight(1f))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun StrategyMenu(state: HomeUiState, viewModel: AppViewModel, modifier: Modifier) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }, modifier = modifier) {
        OutlinedTextField(
            value = if (state.strategy.isEmpty()) "全部策略" else strategyLabel(state.strategy),
            onValueChange = {},
            readOnly = true,
            label = { Text("策略") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            DropdownMenuItem(text = { Text("全部策略") }, onClick = { viewModel.setStrategy(""); expanded = false })
            state.strategies.sortedBy(::strategyLabel).forEach { strategy ->
                DropdownMenuItem(
                    text = { Text(strategyLabel(strategy)) },
                    onClick = { viewModel.setStrategy(strategy); expanded = false },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SortMenu(state: HomeUiState, viewModel: AppViewModel, modifier: Modifier) {
    var expanded by remember { mutableStateOf(false) }
    val labels = mapOf(
        SortMode.Strategy to "按策略",
        SortMode.PriceDesc to "股价从高到低",
        SortMode.PriceAsc to "股价从低到高",
        SortMode.Change5 to "5日涨跌幅",
        SortMode.Change20 to "20日涨跌幅",
        SortMode.Change60 to "60日涨跌幅",
    )
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }, modifier = modifier) {
        OutlinedTextField(
            value = labels.getValue(state.sortMode),
            onValueChange = {},
            readOnly = true,
            label = { Text("排序") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            labels.forEach { (mode, label) ->
                DropdownMenuItem(text = { Text(label) }, onClick = { viewModel.setSortMode(mode); expanded = false })
            }
        }
    }
}

@Composable
private fun StrategyHelp(state: HomeUiState) {
    val strategy = state.strategy.ifEmpty { state.strategies.firstOrNull().orEmpty() }
    if (strategy.isEmpty()) return
    val note = strategyNote(strategy)
    var expanded by remember(strategy) { mutableStateOf(state.strategy.isNotEmpty()) }
    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
        ),
    ) {
        Column(modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("策略说明", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
                    Text(note.label, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold)
                }
                TextButton(onClick = { expanded = !expanded }) {
                    Text(if (expanded) "收起" else "说明")
                }
            }
            if (expanded) {
                Text("解释：${note.explain}", style = MaterialTheme.typography.bodySmall)
                Text("建议：${note.advice}", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
private fun ResultRow(
    row: ResultDisplayRowEntity,
    highlighted: Boolean,
    marketColorMode: MarketColorMode,
    strategyHits: List<String>,
    onClick: () -> Unit,
) {
    val note = strategyNote(row.strategy)
    val boardLabel = stockBoardLabel(row.symbol)
    ElevatedCard(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        colors = CardDefaults.elevatedCardColors(
            containerColor = if (highlighted) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
            contentColor = if (highlighted) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface,
        ),
        elevation = CardDefaults.elevatedCardElevation(
            defaultElevation = if (highlighted) 8.dp else 1.dp,
            pressedElevation = if (highlighted) 8.dp else 1.dp,
        ),
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("${row.symbol} ${row.name}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(note.label, color = MaterialTheme.colorScheme.secondary, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold)
                }
                Text(formatPrice(row.latestClose), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                if (strategyHits.size > 1) {
                    AssistChip(
                        onClick = {},
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer,
                            labelColor = MaterialTheme.colorScheme.onSecondaryContainer,
                        ),
                        label = {
                            Text(
                                "多策略 ${strategyHits.size}项：${strategyHits.take(3).joinToString("、", transform = ::strategyLabel)}",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                            )
                        },
                    )
                }
                if (boardLabel != null) {
                    AssistChip(
                        onClick = {},
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                            labelColor = MaterialTheme.colorScheme.onTertiaryContainer,
                        ),
                        label = {
                            Text(boardLabel, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
                        },
                    )
                }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                val change5Tone = marketTone(row.change5, marketColorMode)
                val change20Tone = marketTone(row.change20, marketColorMode)
                val change60Tone = marketTone(row.change60, marketColorMode)
                AssistChip(
                    onClick = {},
                    colors = AssistChipDefaults.assistChipColors(
                        containerColor = change5Tone.container,
                        labelColor = change5Tone.content,
                    ),
                    label = { Text("5日 ${formatPct(row.change5)}", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold) },
                )
                AssistChip(
                    onClick = {},
                    colors = AssistChipDefaults.assistChipColors(
                        containerColor = change20Tone.container,
                        labelColor = change20Tone.content,
                    ),
                    label = { Text("20日 ${formatPct(row.change20)}", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold) },
                )
                AssistChip(
                    onClick = {},
                    colors = AssistChipDefaults.assistChipColors(
                        containerColor = change60Tone.container,
                        labelColor = change60Tone.content,
                    ),
                    label = { Text("60日 ${formatPct(row.change60)}", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold) },
                )
            }
            Text("板块：${row.sector.ifEmpty { "未缓存" }}", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold)
            Text(previewText(row.majorInfo.ifEmpty { "暂无近期重大信息" }), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun stockBoardLabel(symbol: String): String? =
    when {
        symbol.startsWith("688") || symbol.startsWith("689") -> "科创板"
        symbol.startsWith("300") || symbol.startsWith("301") -> "创业板"
        else -> null
    }

private fun homeThemeIcon(themeMode: ThemeMode) =
    when (themeMode) {
        ThemeMode.System -> Icons.Filled.SettingsSuggest
        ThemeMode.Light -> Icons.Filled.LightMode
        ThemeMode.Dark -> Icons.Filled.DarkMode
    }
