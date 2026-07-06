package com.sequoiax.app.repository

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

class DisplayRowsTest {
    private lateinit var db: AppDatabase

    @Before
    fun setUp() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java,
        ).allowMainThreadQueries().build()
    }

    @After
    fun tearDown() {
        db.close()
    }

    @Test
    fun displayRowsSortByPriceBothDirections() = runBlocking {
        db.displayRowDao().replaceRows(
            listOf(
                ResultDisplayRowEntity("2026-07-01", "A", "600601", "方正科技", "电子", "信息", 13.97, 5.12, 10.26, 38.87, "13,14"),
                ResultDisplayRowEntity("2026-07-01", "A", "688361", "中科飞测", "设备", "信息", 422.0, 1.0, 2.0, 3.0, "400,422"),
            )
        )

        val highToLow = db.displayRowDao().queryRows("2026-07-01", "", "", SortMode.PriceDesc.value)
        val lowToHigh = db.displayRowDao().queryRows("2026-07-01", "", "", SortMode.PriceAsc.value)

        assertEquals(listOf("688361", "600601"), highToLow.map { it.symbol })
        assertEquals(listOf("600601", "688361"), lowToHigh.map { it.symbol })
    }
}
