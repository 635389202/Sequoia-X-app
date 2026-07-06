package com.sequoiax.app.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction

@Dao
interface ImportDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBatch(batch: ImportBatchEntity)

    @Query("SELECT * FROM ImportBatchEntity ORDER BY importedAt DESC")
    suspend fun batches(): List<ImportBatchEntity>

    @Query("SELECT * FROM ImportBatchEntity ORDER BY importedAt DESC LIMIT 1")
    suspend fun latestBatch(): ImportBatchEntity?
}

@Dao
interface StockDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBasics(rows: List<StockBasicEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDaily(rows: List<StockDailyEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertResults(rows: List<StrategyResultEntity>)

    @Query("DELETE FROM StrategyResultEntity WHERE date = :date")
    suspend fun deleteResultsForDate(date: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertContexts(rows: List<StockContextEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNotes(rows: List<StrategyNoteEntity>)

    @Query("SELECT * FROM StockDailyEntity WHERE symbol = :symbol ORDER BY date DESC LIMIT :limit")
    suspend fun recentDaily(symbol: String, limit: Int): List<StockDailyEntity>

    @Query("SELECT * FROM StockDailyEntity WHERE symbol = :symbol AND date <= :date ORDER BY date DESC LIMIT :limit")
    suspend fun recentDailyThrough(symbol: String, date: String, limit: Int): List<StockDailyEntity>

    @Query("SELECT * FROM StockBasicEntity")
    suspend fun allBasics(): List<StockBasicEntity>

    @Query("SELECT * FROM StockContextEntity")
    suspend fun allContexts(): List<StockContextEntity>

    @Query("SELECT * FROM StrategyResultEntity WHERE symbol = :symbol ORDER BY date DESC")
    suspend fun resultsForSymbol(symbol: String): List<StrategyResultEntity>

    @Query("SELECT * FROM StrategyResultEntity WHERE date = :date ORDER BY strategy, symbol")
    suspend fun resultsForDate(date: String): List<StrategyResultEntity>

    @Query("SELECT * FROM StrategyResultEntity ORDER BY date DESC, strategy, symbol")
    suspend fun allResults(): List<StrategyResultEntity>

    @Query("SELECT COUNT(*) FROM StockDailyEntity")
    suspend fun countDailyRows(): Int
}

@Dao
interface DisplayRowDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRows(rows: List<ResultDisplayRowEntity>)

    @Query("DELETE FROM ResultDisplayRowEntity")
    suspend fun clearRows()

    @Transaction
    suspend fun replaceRows(rows: List<ResultDisplayRowEntity>) {
        clearRows()
        insertRows(rows)
    }

    @Query(
        """
        SELECT * FROM ResultDisplayRowEntity
        WHERE date = :date
          AND (:strategy = '' OR strategy = :strategy)
          AND (
            :query = ''
            OR symbol LIKE '%' || :query || '%'
            OR name LIKE '%' || :query || '%'
            OR sector LIKE '%' || :query || '%'
            OR majorInfo LIKE '%' || :query || '%'
          )
        ORDER BY
          CASE WHEN :sort = 'price_asc' THEN latestClose IS NULL END ASC,
          CASE WHEN :sort = 'price_asc' THEN latestClose END ASC,
          CASE WHEN :sort = 'price_desc' THEN latestClose IS NULL END ASC,
          CASE WHEN :sort = 'price_desc' THEN latestClose END DESC,
          CASE WHEN :sort = 'change_5' THEN change5 IS NULL END ASC,
          CASE WHEN :sort = 'change_5' THEN change5 END DESC,
          CASE WHEN :sort = 'change_20' THEN change20 IS NULL END ASC,
          CASE WHEN :sort = 'change_20' THEN change20 END DESC,
          CASE WHEN :sort = 'change_60' THEN change60 IS NULL END ASC,
          CASE WHEN :sort = 'change_60' THEN change60 END DESC,
          CASE WHEN :sort = 'strategy' THEN strategy END ASC,
          symbol ASC
        LIMIT :limit OFFSET :offset
        """
    )
    suspend fun queryRows(date: String, query: String, strategy: String, sort: String, limit: Int, offset: Int): List<ResultDisplayRowEntity>

    @Query(
        """
        SELECT COUNT(*) FROM ResultDisplayRowEntity
        WHERE date = :date
          AND (:strategy = '' OR strategy = :strategy)
          AND (
            :query = ''
            OR symbol LIKE '%' || :query || '%'
            OR name LIKE '%' || :query || '%'
            OR sector LIKE '%' || :query || '%'
            OR majorInfo LIKE '%' || :query || '%'
          )
        """
    )
    suspend fun countRows(date: String, query: String, strategy: String): Int

    @Query("SELECT DISTINCT strategy FROM ResultDisplayRowEntity WHERE date = :date ORDER BY strategy")
    suspend fun strategies(date: String): List<String>

    @Query("SELECT * FROM ResultDisplayRowEntity WHERE date = :date ORDER BY symbol, strategy")
    suspend fun rowsForDate(date: String): List<ResultDisplayRowEntity>

    @Query("SELECT MAX(date) FROM ResultDisplayRowEntity")
    suspend fun latestDate(): String?

    @Query("SELECT * FROM ResultDisplayRowEntity WHERE symbol = :symbol ORDER BY date DESC, strategy")
    suspend fun rowsForSymbol(symbol: String): List<ResultDisplayRowEntity>
}
