package com.sequoiax.app.importer

import androidx.room.withTransaction
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.StockBasicEntity
import com.sequoiax.app.data.StockContextEntity
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.data.StrategyNoteEntity
import com.sequoiax.app.data.StrategyResultEntity
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.util.UUID
import java.util.zip.ZipInputStream
import kotlinx.serialization.json.Json
import kotlin.math.round

class ZipPackageImporter(private val db: AppDatabase) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun importPackage(inputStream: InputStream, sourceName: String): ImportSummary {
        var manifest: ManifestDto? = null
        var resultRows = 0
        var stockDailyRows = 0

        db.withTransaction {
            ZipInputStream(inputStream).use { zip ->
                var replacedDeltaResults = false
                while (true) {
                    val entry = zip.nextEntry ?: break
                    if (!entry.isDirectory) {
                        val reader = BufferedReader(InputStreamReader(zip, Charsets.UTF_8))
                        when (entry.name) {
                            "manifest.json" -> {
                                manifest = json.decodeFromString<ManifestDto>(reader.readText()).also { dto ->
                                    require(dto.formatVersion == 1) { "Unsupported format_version: ${dto.formatVersion}" }
                                    require(dto.packageType == "full" || dto.packageType == "delta") {
                                        "Unsupported package_type: ${dto.packageType}"
                                    }
                                    if (dto.packageType == "delta" && dto.requiresFullPackage && db.stockDao().countDailyRows() == 0) {
                                        error("请先导入一次全量数据包，再导入每日增量包")
                                    }
                                }
                            }
                            "stock_basic.jsonl" -> importJsonl(reader, 1_000) { rows: List<StockBasicDto> ->
                                db.stockDao().insertBasics(rows.map { StockBasicEntity(it.symbol, it.name, it.exchange, it.status, it.stockType, it.updatedAt) })
                            }
                            "stock_daily.jsonl" -> importJsonl(reader, 2_000) { rows: List<StockDailyDto> ->
                                stockDailyRows += rows.size
                                db.stockDao().insertDaily(rows.map { StockDailyEntity(it.symbol, it.date, it.open, it.high, it.low, it.close, it.volume, it.turnover) })
                            }
                            "results.jsonl" -> {
                                val checkedManifest = manifest
                                if (!replacedDeltaResults && checkedManifest?.packageType == "delta") {
                                    db.stockDao().deleteResultsForDate(checkedManifest.latestDate)
                                    replacedDeltaResults = true
                                }
                                importJsonl(reader, 1_000) { rows: List<StrategyResultDto> ->
                                    resultRows += rows.size
                                    db.stockDao().insertResults(rows.map { StrategyResultEntity(it.date, it.strategy, it.symbol) })
                                }
                            }
                            "stock_context.jsonl" -> importJsonl(reader, 1_000) { rows: List<StockContextDto> ->
                                db.stockDao().insertContexts(rows.map { StockContextEntity(it.symbol, it.sector, it.majorInfo, it.updatedAt) })
                            }
                            "strategy_notes.json" -> {
                                val notes = json.decodeFromString<Map<String, StrategyNoteValueDto>>(reader.readText())
                                db.stockDao().insertNotes(notes.map { (strategy, note) ->
                                    StrategyNoteEntity(strategy, note.label, note.explain, note.advice)
                                })
                            }
                        }
                    }
                    zip.closeEntry()
                }
            }

            val checkedManifest = requireNotNull(manifest) { "Missing manifest.json" }
            db.displayRowDao().replaceRows(buildDisplayRows())
            db.importDao().insertBatch(
                ImportBatchEntity(
                    packageId = UUID.randomUUID().toString(),
                    sourceFileName = sourceName,
                    generatedAt = checkedManifest.generatedAt,
                    latestDate = checkedManifest.latestDate,
                    importedAt = System.currentTimeMillis(),
                )
            )
        }

        val checkedManifest = requireNotNull(manifest) { "Missing manifest.json" }
        return ImportSummary(checkedManifest.latestDate, resultRows, stockDailyRows, checkedManifest.packageType)
    }

    private suspend inline fun <reified T> importJsonl(
        reader: BufferedReader,
        chunkSize: Int,
        crossinline insert: suspend (List<T>) -> Unit,
    ) {
        val chunk = mutableListOf<T>()
        while (true) {
            val line = reader.readLine() ?: break
            val trimmed = line.trim()
            if (trimmed.isNotEmpty()) {
                chunk += json.decodeFromString<T>(trimmed)
                if (chunk.size >= chunkSize) {
                    val rows = chunk.toList()
                    chunk.clear()
                    insert(rows)
                }
            }
        }
        if (chunk.isNotEmpty()) insert(chunk)
    }

    private suspend fun buildDisplayRows(): List<ResultDisplayRowEntity> {
        val names = db.stockDao().allBasics().associateBy { it.symbol }
        val contexts = db.stockDao().allContexts().associateBy { it.symbol }
        return db.stockDao().allResults().map { result ->
            val historyDesc = db.stockDao().recentDailyThrough(result.symbol, result.date, 61)
            val history = historyDesc.asReversed()
            val closes = history.mapNotNull { it.close }
            val context = contexts[result.symbol]
            ResultDisplayRowEntity(
                date = result.date,
                strategy = result.strategy,
                symbol = result.symbol,
                name = names[result.symbol]?.name.orEmpty(),
                sector = context?.sector.orEmpty(),
                majorInfo = context?.majorInfo.orEmpty(),
                latestClose = closes.lastOrNull(),
                change5 = pctChange(closes, 5),
                change20 = pctChange(closes, 20),
                change60 = pctChange(closes, 60),
                sparklineCsv = closes.takeLast(30).joinToString(","),
            )
        }
    }

    private fun pctChange(closes: List<Double>, sessions: Int): Double? {
        if (closes.size <= sessions) return null
        val base = closes[closes.size - sessions - 1]
        val latest = closes.last()
        if (base == 0.0) return null
        return round((latest / base - 1.0) * 10000.0) / 100.0
    }
}
