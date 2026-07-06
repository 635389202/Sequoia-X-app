package com.sequoiax.app.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.SwapHoriz
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.Button
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun DataScreen(
    viewModel: AppViewModel,
    marketColorMode: MarketColorMode,
    onToggleMarketColorMode: () -> Unit,
) {
    val state by viewModel.home.collectAsState()
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
            runCatching {
                context.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            val sourceName = uri.lastPathSegment ?: "sequoia_app_data.zip"
            viewModel.importFrom(sourceName) {
                requireNotNull(context.contentResolver.openInputStream(uri)) { "无法打开文件" }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("数据管理", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(
                    if (state.latestDate.isEmpty()) "当前无数据，请先导入全量数据包。"
                    else "当前数据日期：${state.latestDate}",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    "首次使用导入全量包，之后每天导入增量包即可。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Button(onClick = {
                    launcher.launch(
                        arrayOf(
                            "application/zip",
                            "application/x-zip",
                            "application/x-zip-compressed",
                            "application/octet-stream",
                        ),
                    )
                }) {
                    Icon(Icons.Filled.UploadFile, contentDescription = null)
                    Text("导入数据包")
                }
                if (state.isImporting) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                }
                if (state.message.isNotEmpty()) {
                    Text(
                        text = state.message,
                        color = if (state.message.startsWith("导入失败")) {
                            MaterialTheme.colorScheme.error
                        } else {
                            MaterialTheme.colorScheme.primary
                        },
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("显示设置", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text(
                    "当前涨跌配色：${marketColorMode.label}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                OutlinedButton(onClick = onToggleMarketColorMode) {
                    Icon(Icons.Filled.SwapHoriz, contentDescription = null)
                    Text("一键切换涨跌颜色")
                }
            }
        }
        Text("导入记录", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        state.batches.forEach { batch ->
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(batch.sourceFileName, fontWeight = FontWeight.SemiBold)
                    Text("最新日期：${batch.latestDate}")
                    Text("生成时间：${batch.generatedAt}", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}
