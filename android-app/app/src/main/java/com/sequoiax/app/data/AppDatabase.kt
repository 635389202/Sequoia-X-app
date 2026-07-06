package com.sequoiax.app.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        ImportBatchEntity::class,
        StockBasicEntity::class,
        StockDailyEntity::class,
        StrategyResultEntity::class,
        StockContextEntity::class,
        StrategyNoteEntity::class,
        ResultDisplayRowEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun importDao(): ImportDao
    abstract fun stockDao(): StockDao
    abstract fun displayRowDao(): DisplayRowDao

    companion object {
        fun create(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "sequoia-x.db").build()
    }
}
