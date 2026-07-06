package com.sequoiax.app.repository

import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.importer.ImportSummary
import com.sequoiax.app.importer.ZipPackageImporter
import com.sequoiax.app.sync.GitHubReleaseClient
import com.sequoiax.app.sync.ReleaseClient
import com.sequoiax.app.sync.chooseAsset
import com.sequoiax.app.sync.sha256
import java.io.ByteArrayInputStream
import java.io.InputStream

class StockRepository(
    private val db: AppDatabase,
    private val releaseClient: ReleaseClient = GitHubReleaseClient(),
) {
    private val importer = ZipPackageImporter(db)

    suspend fun importPackage(inputStream: InputStream, sourceName: String): ImportSummary =
        importer.importPackage(inputStream, sourceName)

    suspend fun syncFromGitHubRelease(localLatestDate: String?): ImportSummary {
        val remote = releaseClient.fetchLatestManifest()
        val hasLocalDailyRows = db.stockDao().countDailyRows() > 0
        val assetName = chooseAsset(localLatestDate, hasLocalDailyRows, remote.manifest)
        if (assetName.isBlank()) {
            return ImportSummary(remote.manifest.date, resultRows = 0, stockDailyRows = 0, packageType = "current")
        }
        val bytes = releaseClient.downloadAsset(assetName, remote.assets)
        val expected = remote.manifest.sha256[assetName]
        if (!expected.isNullOrBlank() && sha256(bytes) != expected) {
            error("数据包校验失败")
        }
        return importPackage(ByteArrayInputStream(bytes), assetName)
    }

    suspend fun latestDate(): String? = db.displayRowDao().latestDate()

    suspend fun queryRows(
        date: String,
        query: String,
        strategy: String,
        sortMode: SortMode,
        limit: Int,
        offset: Int,
    ): List<ResultDisplayRowEntity> = db.displayRowDao().queryRows(date, query, strategy, sortMode.value, limit, offset)

    suspend fun countRows(date: String, query: String, strategy: String): Int =
        db.displayRowDao().countRows(date, query, strategy)

    suspend fun strategies(date: String): List<String> = db.displayRowDao().strategies(date)

    suspend fun rowsForDate(date: String): List<ResultDisplayRowEntity> = db.displayRowDao().rowsForDate(date)

    suspend fun batches(): List<ImportBatchEntity> = db.importDao().batches()

    suspend fun rowsForSymbol(symbol: String): List<ResultDisplayRowEntity> = db.displayRowDao().rowsForSymbol(symbol)

    suspend fun recentDaily(symbol: String, limit: Int): List<StockDailyEntity> = db.stockDao().recentDaily(symbol, limit)
}
