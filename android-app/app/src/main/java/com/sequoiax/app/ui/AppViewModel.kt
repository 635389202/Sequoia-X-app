package com.sequoiax.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.repository.StockRepository
import java.io.InputStream
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class HomeUiState(
    val latestDate: String = "",
    val query: String = "",
    val strategy: String = "",
    val sortMode: SortMode = SortMode.Strategy,
    val strategies: List<String> = emptyList(),
    val rows: List<ResultDisplayRowEntity> = emptyList(),
    val strategyHitsBySymbol: Map<String, List<String>> = emptyMap(),
    val totalRows: Int = 0,
    val isLoadingRows: Boolean = false,
    val canLoadMoreRows: Boolean = false,
    val batches: List<ImportBatchEntity> = emptyList(),
    val isImporting: Boolean = false,
    val message: String = "",
)

data class DetailUiState(
    val rows: List<ResultDisplayRowEntity> = emptyList(),
    val daily: List<StockDailyEntity> = emptyList(),
)

class AppViewModel(private val repository: StockRepository) : ViewModel() {
    private companion object {
        const val RowPageSize = 24
    }

    private val _home = MutableStateFlow(HomeUiState())
    val home: StateFlow<HomeUiState> = _home

    private val _detail = MutableStateFlow(DetailUiState())
    val detail: StateFlow<DetailUiState> = _detail

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            val latest = repository.latestDate().orEmpty()
            val strategies = if (latest.isNotEmpty()) repository.strategies(latest) else emptyList()
            val strategyHits = if (latest.isNotEmpty()) {
                repository.rowsForDate(latest)
                    .groupBy { it.symbol }
                    .mapValues { (_, rows) -> rows.map { it.strategy }.distinct().sortedBy(::strategyLabel) }
            } else {
                emptyMap()
            }
            val batches = repository.batches()
            _home.update {
                it.copy(
                    latestDate = latest,
                    strategies = strategies,
                    strategyHitsBySymbol = strategyHits,
                    batches = batches,
                )
            }
            reloadRows()
        }
    }

    fun setQuery(value: String) {
        _home.update { it.copy(query = value) }
        reloadRows()
    }

    fun setStrategy(value: String) {
        _home.update { it.copy(strategy = value) }
        reloadRows()
    }

    fun setSortMode(value: SortMode) {
        _home.update { it.copy(sortMode = value) }
        reloadRows()
    }

    fun loadMoreRows() {
        viewModelScope.launch {
            val state = _home.value
            if (state.latestDate.isEmpty() || state.isLoadingRows || !state.canLoadMoreRows) return@launch
            _home.update { it.copy(isLoadingRows = true) }
            val nextRows = withContext(Dispatchers.IO) {
                repository.queryRows(
                    date = state.latestDate,
                    query = state.query,
                    strategy = state.strategy,
                    sortMode = state.sortMode,
                    limit = RowPageSize,
                    offset = state.rows.size,
                )
            }
            _home.update {
                val merged = it.rows + nextRows
                it.copy(
                    rows = merged,
                    isLoadingRows = false,
                    canLoadMoreRows = merged.size < it.totalRows,
                )
            }
        }
    }

    fun importFrom(sourceName: String, openInput: suspend () -> InputStream) {
        viewModelScope.launch {
            _home.update { it.copy(isImporting = true, message = "正在导入 $sourceName") }
            try {
                val summary = withContext(Dispatchers.IO) {
                    openInput().use { repository.importPackage(it, sourceName) }
                }
                val typeLabel = if (summary.packageType == "delta") "增量包" else "全量包"
                _home.update {
                    it.copy(
                        isImporting = false,
                        message = "导入完成：$typeLabel ${summary.latestDate}，结果${summary.resultRows}条，日线${summary.stockDailyRows}条",
                    )
                }
                refresh()
            } catch (exc: Exception) {
                _home.update { it.copy(isImporting = false, message = "导入失败：${exc.message ?: "未知错误"}") }
            }
        }
    }

    fun loadDetail(symbol: String) {
        viewModelScope.launch {
            val rows = repository.rowsForSymbol(symbol)
            val daily = repository.recentDaily(symbol, 120)
            _detail.value = DetailUiState(rows, daily)
        }
    }

    private fun reloadRows() {
        viewModelScope.launch {
            val state = _home.value
            if (state.latestDate.isEmpty()) {
                _home.update { it.copy(rows = emptyList(), totalRows = 0, canLoadMoreRows = false, isLoadingRows = false) }
                return@launch
            }
            _home.update { it.copy(isLoadingRows = true) }
            val total = withContext(Dispatchers.IO) {
                repository.countRows(state.latestDate, state.query, state.strategy)
            }
            val rows = withContext(Dispatchers.IO) {
                repository.queryRows(
                    date = state.latestDate,
                    query = state.query,
                    strategy = state.strategy,
                    sortMode = state.sortMode,
                    limit = RowPageSize,
                    offset = 0,
                )
            }
            _home.update {
                it.copy(
                    rows = rows,
                    totalRows = total,
                    isLoadingRows = false,
                    canLoadMoreRows = rows.size < total,
                )
            }
        }
    }
}
