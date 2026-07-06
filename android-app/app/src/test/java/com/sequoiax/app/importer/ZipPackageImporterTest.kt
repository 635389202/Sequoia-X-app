package com.sequoiax.app.importer

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sequoiax.app.data.AppDatabase
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test

class ZipPackageImporterTest {
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
    fun importsZipAndBuildsDisplayRows() = runBlocking {
        val importer = ZipPackageImporter(db)

        val summary = importer.importPackage(ByteArrayInputStream(sampleZip()), "sample.zip")
        val latestDate = db.displayRowDao().latestDate()
        val rows = db.displayRowDao().queryRows("2026-07-01", "", "", "price_asc")

        assertEquals("2026-07-01", summary.latestDate)
        assertEquals("2026-07-01", latestDate)
        assertEquals(1, rows.size)
        assertEquals("600601", rows[0].symbol)
        assertEquals("方正科技", rows[0].name)
        assertEquals(13.97, rows[0].latestClose!!, 0.001)
        assertNotNull(db.importDao().latestBatch())
    }

    private fun sampleZip(): ByteArray {
        val out = ByteArrayOutputStream()
        ZipOutputStream(out).use { zip ->
            zip.writeText("manifest.json", """{"format_version":1,"generated_at":"2026-07-02 09:00:00","latest_date":"2026-07-01"}""")
            zip.writeText("stock_basic.jsonl", """{"symbol":"600601","name":"方正科技","exchange":"sh","status":"1","stock_type":"1","updated_at":"2026-07-02"}""" + "\n")
            zip.writeText(
                "stock_daily.jsonl",
                listOf(
                    "2026-06-26" to 13.00,
                    "2026-06-27" to 13.10,
                    "2026-06-28" to 13.20,
                    "2026-06-29" to 12.58,
                    "2026-06-30" to 13.84,
                    "2026-07-01" to 13.97,
                ).joinToString("\n") { (date, close) ->
                    """{"symbol":"600601","date":"$date","open":$close,"high":$close,"low":$close,"close":$close,"volume":1000,"turnover":10000}"""
                } + "\n"
            )
            zip.writeText("results.jsonl", """{"date":"2026-07-01","strategy":"LimitUpShakeoutStrategy","symbol":"600601"}""" + "\n")
            zip.writeText("stock_context.jsonl", """{"symbol":"600601","sector":"计算机、通信和其他电子设备制造业","major_info":"方正科技公告","updated_at":"2026-07-02"}""" + "\n")
            zip.writeText("strategy_notes.json", """{"LimitUpShakeoutStrategy":{"label":"涨停洗盘","explain":"解释","advice":"建议"}}""")
        }
        return out.toByteArray()
    }

    private fun ZipOutputStream.writeText(name: String, text: String) {
        putNextEntry(ZipEntry(name))
        write(text.toByteArray(Charsets.UTF_8))
        closeEntry()
    }
}
