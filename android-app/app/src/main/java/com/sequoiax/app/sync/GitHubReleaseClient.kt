package com.sequoiax.app.sync

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request

data class RemoteManifest(
    val manifest: ReleaseManifestDto,
    val assets: Map<String, String>,
)

interface ReleaseClient {
    suspend fun fetchLatestManifest(): RemoteManifest
    suspend fun downloadAsset(assetName: String, assets: Map<String, String>): ByteArray
}

@Serializable
private data class ReleaseAssetDto(
    val name: String,
    @SerialName("browser_download_url") val browserDownloadUrl: String,
)

@Serializable
private data class ReleaseDto(
    @SerialName("tag_name") val tagName: String,
    val assets: List<ReleaseAssetDto> = emptyList(),
)

class GitHubReleaseClient(
    private val repository: String = "635389202/Sequoia-X-app",
    private val httpClient: OkHttpClient = OkHttpClient(),
) : ReleaseClient {
    private val json = Json { ignoreUnknownKeys = true }

    override suspend fun fetchLatestManifest(): RemoteManifest {
        val releaseText = getText("https://api.github.com/repos/$repository/releases/latest")
        val release = json.decodeFromString(ReleaseDto.serializer(), releaseText)
        val assets = release.assets.associate { it.name to it.browserDownloadUrl }
        val manifestUrl = requireNotNull(assets["manifest.json"]) { "最新 Release 缺少 manifest.json" }
        val manifest = parseReleaseManifest(getText(manifestUrl))
        return RemoteManifest(manifest, assets)
    }

    override suspend fun downloadAsset(assetName: String, assets: Map<String, String>): ByteArray {
        val url = requireNotNull(assets[assetName]) { "Release 缺少资产 $assetName" }
        return getBytes(url)
    }

    private fun getText(url: String): String = getBytes(url).decodeToString()

    private fun getBytes(url: String): ByteArray {
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", "Sequoia-X-Android")
            .build()
        httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) error("GitHub 请求失败：HTTP ${response.code}")
            return requireNotNull(response.body) { "GitHub 返回空响应" }.bytes()
        }
    }
}
