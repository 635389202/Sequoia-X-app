package com.sequoiax.app.data

import androidx.room.Entity
import androidx.room.Index

@Entity(primaryKeys = ["packageId"])
data class ImportBatchEntity(
    val packageId: String,
    val sourceFileName: String,
    val generatedAt: String,
    val latestDate: String,
    val importedAt: Long,
)

@Entity(primaryKeys = ["symbol"])
data class StockBasicEntity(
    val symbol: String,
    val name: String,
    val exchange: String,
    val status: String,
    val stockType: String,
    val updatedAt: String,
)

@Entity(
    primaryKeys = ["symbol", "date"],
    indices = [Index(value = ["symbol", "date"])],
)
data class StockDailyEntity(
    val symbol: String,
    val date: String,
    val open: Double?,
    val high: Double?,
    val low: Double?,
    val close: Double?,
    val volume: Double?,
    val turnover: Double?,
)

@Entity(
    primaryKeys = ["date", "strategy", "symbol"],
    indices = [Index(value = ["date", "strategy", "symbol"]), Index(value = ["symbol"])],
)
data class StrategyResultEntity(
    val date: String,
    val strategy: String,
    val symbol: String,
)

@Entity(primaryKeys = ["symbol"], indices = [Index(value = ["symbol"])])
data class StockContextEntity(
    val symbol: String,
    val sector: String,
    val majorInfo: String,
    val updatedAt: String,
)

@Entity(primaryKeys = ["strategy"])
data class StrategyNoteEntity(
    val strategy: String,
    val label: String,
    val explain: String,
    val advice: String,
)

@Entity(
    primaryKeys = ["date", "strategy", "symbol"],
    indices = [
        Index(value = ["date", "strategy"]),
        Index(value = ["symbol"]),
        Index(value = ["latestClose"]),
    ],
)
data class ResultDisplayRowEntity(
    val date: String,
    val strategy: String,
    val symbol: String,
    val name: String,
    val sector: String,
    val majorInfo: String,
    val latestClose: Double?,
    val change5: Double?,
    val change20: Double?,
    val change60: Double?,
    val sparklineCsv: String,
)

enum class SortMode(val value: String) {
    Strategy("strategy"),
    PriceDesc("price_desc"),
    PriceAsc("price_asc"),
    Change5("change_5"),
    Change20("change_20"),
    Change60("change_60"),
}
