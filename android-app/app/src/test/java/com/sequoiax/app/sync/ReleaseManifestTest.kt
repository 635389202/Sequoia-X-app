package com.sequoiax.app.sync

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReleaseManifestTest {
    @Test
    fun parsesManifest() {
        val json = """
            {
              "schema_version": 1,
              "date": "2026-07-06",
              "package_type": "delta",
              "requires_full_package": true,
              "delta_asset": "sequoia_app_delta_2026-07-06.zip",
              "full_asset": "sequoia_app_data_latest.zip",
              "sha256": {"sequoia_app_delta_2026-07-06.zip": "abc"},
              "candidate_count": 110,
              "generated_at": "2026-07-06T19:15:00+08:00"
            }
        """.trimIndent()

        val manifest = parseReleaseManifest(json)

        assertEquals("2026-07-06", manifest.date)
        assertEquals("sequoia_app_delta_2026-07-06.zip", manifest.deltaAsset)
        assertEquals(110, manifest.candidateCount)
    }

    @Test
    fun choosesFullAssetWhenNoLocalData() {
        val manifest = ReleaseManifestDto(
            schemaVersion = 1,
            date = "2026-07-06",
            packageType = "delta",
            requiresFullPackage = true,
            deltaAsset = "delta.zip",
            fullAsset = "full.zip",
            sha256 = mapOf("delta.zip" to "a", "full.zip" to "b"),
            candidateCount = 1,
            generatedAt = "now",
        )

        assertEquals("full.zip", chooseAsset(null, hasLocalDailyRows = false, manifest))
    }

    @Test
    fun choosesDeltaAssetWhenLocalDataExists() {
        val manifest = ReleaseManifestDto(1, "2026-07-06", "delta", true, "delta.zip", "full.zip", mapOf(), 1, "now")

        assertEquals("delta.zip", chooseAsset("2026-07-05", hasLocalDailyRows = true, manifest))
    }

    @Test
    fun detectsCurrentData() {
        assertTrue(isAlreadyCurrent(localLatestDate = "2026-07-06", remoteDate = "2026-07-06"))
        assertFalse(isAlreadyCurrent(localLatestDate = "2026-07-05", remoteDate = "2026-07-06"))
    }

    @Test
    fun computesSha256() {
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", sha256("abc".toByteArray()))
    }
}
