package com.sequoiax.app.repository

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.sync.ReleaseClient
import com.sequoiax.app.sync.ReleaseManifestDto
import com.sequoiax.app.sync.RemoteManifest
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class GitHubSyncRepositoryTest {
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
    fun rejectsDownloadedPackageWhenChecksumDoesNotMatch() = runBlocking {
        val client = object : ReleaseClient {
            override suspend fun fetchLatestManifest(): RemoteManifest =
                RemoteManifest(
                    manifest = ReleaseManifestDto(
                        schemaVersion = 1,
                        date = "2026-07-06",
                        packageType = "delta",
                        requiresFullPackage = true,
                        deltaAsset = "delta.zip",
                        fullAsset = "full.zip",
                        sha256 = mapOf("full.zip" to "not-a-real-checksum"),
                        candidateCount = 1,
                        generatedAt = "now",
                    ),
                    assets = mapOf("full.zip" to "https://example.test/full.zip"),
                )

            override suspend fun downloadAsset(assetName: String, assets: Map<String, String>): ByteArray =
                "bad package".toByteArray()
        }
        val repository = StockRepository(db, client)

        val error = runCatching {
            repository.syncFromGitHubRelease(localLatestDate = null)
        }.exceptionOrNull()

        assertTrue(error?.message?.contains("校验失败") == true)
    }
}
