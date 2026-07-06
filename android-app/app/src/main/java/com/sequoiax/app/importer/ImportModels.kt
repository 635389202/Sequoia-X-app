package com.sequoiax.app.importer

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ManifestDto(
    @SerialName("format_version") val formatVersion: Int,
    @SerialName("package_type") val packageType: String = "full",
    @SerialName("generated_at") val generatedAt: String = "",
    @SerialName("latest_date") val latestDate: String,
    @SerialName("requires_full_package") val requiresFullPackage: Boolean = false,
)

@Serializable
data class StockBasicDto(
    val symbol: String,
    val name: String = "",
    val exchange: String = "",
    val status: String = "",
    @SerialName("stock_type") val stockType: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class StockDailyDto(
    val symbol: String,
    val date: String,
    val open: Double? = null,
    val high: Double? = null,
    val low: Double? = null,
    val close: Double? = null,
    val volume: Double? = null,
    val turnover: Double? = null,
)

@Serializable
data class StrategyResultDto(
    val date: String,
    val strategy: String,
    val symbol: String,
)

@Serializable
data class StockContextDto(
    val symbol: String,
    val sector: String = "",
    @SerialName("major_info") val majorInfo: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class StrategyNoteValueDto(
    val label: String = "",
    val explain: String = "",
    val advice: String = "",
)

data class ImportSummary(
    val latestDate: String,
    val resultRows: Int,
    val stockDailyRows: Int,
    val packageType: String,
)
