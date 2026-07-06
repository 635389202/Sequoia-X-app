package com.sequoiax.app.sync

import java.security.MessageDigest
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class ReleaseManifestDto(
    @SerialName("schema_version") val schemaVersion: Int,
    val date: String,
    @SerialName("package_type") val packageType: String,
    @SerialName("requires_full_package") val requiresFullPackage: Boolean,
    @SerialName("delta_asset") val deltaAsset: String,
    @SerialName("full_asset") val fullAsset: String? = null,
    val sha256: Map<String, String> = emptyMap(),
    @SerialName("candidate_count") val candidateCount: Int = 0,
    @SerialName("generated_at") val generatedAt: String = "",
)

private val releaseJson = Json { ignoreUnknownKeys = true }

fun parseReleaseManifest(text: String): ReleaseManifestDto =
    releaseJson.decodeFromString(ReleaseManifestDto.serializer(), text)

fun isAlreadyCurrent(localLatestDate: String?, remoteDate: String): Boolean =
    !localLatestDate.isNullOrBlank() && localLatestDate >= remoteDate

fun chooseAsset(localLatestDate: String?, hasLocalDailyRows: Boolean, manifest: ReleaseManifestDto): String {
    if (isAlreadyCurrent(localLatestDate, manifest.date)) return ""
    if (!hasLocalDailyRows && manifest.requiresFullPackage) {
        return requireNotNull(manifest.fullAsset) { "需要全量包，但 Release 未提供全量包" }
    }
    return manifest.deltaAsset
}

fun sha256(bytes: ByteArray): String {
    val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
    return digest.joinToString("") { "%02x".format(it) }
}
