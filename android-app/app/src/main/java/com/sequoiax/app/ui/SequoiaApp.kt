package com.sequoiax.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.activity.compose.BackHandler
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.Dataset
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.SettingsSuggest
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.sequoiax.app.ui.theme.SequoiaTheme
import com.sequoiax.app.ui.theme.ThemeMode

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SequoiaApp(viewModel: AppViewModel) {
    var tab by rememberSaveable { mutableStateOf("home") }
    var detailSymbol by remember { mutableStateOf<String?>(null) }
    var themeMode by rememberSaveable { mutableStateOf(ThemeMode.System) }
    var marketColorMode by rememberSaveable { mutableStateOf(MarketColorMode.RedUp) }

    SequoiaTheme(themeMode = themeMode) {
        BackHandler(enabled = detailSymbol != null) {
            detailSymbol = null
        }
        Scaffold(
            topBar = {
                if (detailSymbol != null) {
                    TopAppBar(
                        title = { Text("股票详情") },
                        navigationIcon = {
                            IconButton(onClick = { detailSymbol = null }) {
                                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                            }
                        },
                        actions = {
                            IconButton(onClick = { themeMode = nextThemeMode(themeMode) }) {
                                Icon(themeIcon(themeMode), contentDescription = "切换主题：${themeMode.label}")
                            }
                        },
                    )
                }
            },
            bottomBar = {
                if (detailSymbol == null) {
                    NavigationBar {
                        NavigationBarItem(
                            selected = tab == "home",
                            onClick = { tab = "home" },
                            label = { Text("选股") },
                            icon = { Icon(Icons.Filled.BarChart, contentDescription = null) },
                        )
                        NavigationBarItem(
                            selected = tab == "data",
                            onClick = { tab = "data" },
                            label = { Text("数据") },
                            icon = { Icon(Icons.Filled.Dataset, contentDescription = null) },
                        )
                    }
                }
            },
        ) { innerPadding ->
            Column(modifier = Modifier.padding(innerPadding)) {
                val symbol = detailSymbol
                if (symbol != null) {
                    DetailScreen(symbol = symbol, viewModel = viewModel, marketColorMode = marketColorMode)
                } else {
                    when (tab) {
                        "data" -> DataScreen(
                            viewModel = viewModel,
                            marketColorMode = marketColorMode,
                            onToggleMarketColorMode = { marketColorMode = nextMarketColorMode(marketColorMode) },
                        )
                        else -> HomeScreen(
                            viewModel = viewModel,
                            onOpenDetail = { detailSymbol = it },
                            themeMode = themeMode,
                            onToggleTheme = { themeMode = nextThemeMode(themeMode) },
                            marketColorMode = marketColorMode,
                        )
                    }
                }
            }
        }
    }
}

private fun nextThemeMode(current: ThemeMode): ThemeMode =
    when (current) {
        ThemeMode.System -> ThemeMode.Light
        ThemeMode.Light -> ThemeMode.Dark
        ThemeMode.Dark -> ThemeMode.System
    }

private fun themeIcon(themeMode: ThemeMode) =
    when (themeMode) {
        ThemeMode.System -> Icons.Filled.SettingsSuggest
        ThemeMode.Light -> Icons.Filled.LightMode
        ThemeMode.Dark -> Icons.Filled.DarkMode
    }
