package com.sequoiax.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance

enum class MarketColorMode(val label: String) {
    RedUp("红涨绿跌"),
    GreenUp("绿涨红跌"),
}

fun nextMarketColorMode(current: MarketColorMode): MarketColorMode =
    when (current) {
        MarketColorMode.RedUp -> MarketColorMode.GreenUp
        MarketColorMode.GreenUp -> MarketColorMode.RedUp
    }

@Composable
fun marketLineColor(isUp: Boolean, mode: MarketColorMode): Color {
    val dark = MaterialTheme.colorScheme.background.luminance() < 0.5f
    val red = MaterialTheme.colorScheme.primary
    val green = if (dark) Color(0xFF6EE7A4) else Color(0xFF168C4A)
    return when (mode) {
        MarketColorMode.RedUp -> if (isUp) red else green
        MarketColorMode.GreenUp -> if (isUp) green else red
    }
}

@Composable
fun marketContainerColor(value: Double?, mode: MarketColorMode): Color {
    return marketTone(value, mode).container
}

data class MarketTone(val container: Color, val content: Color)

@Composable
fun marketTone(value: Double?, mode: MarketColorMode): MarketTone {
    val dark = MaterialTheme.colorScheme.background.luminance() < 0.5f
    val red = MarketTone(
        container = MaterialTheme.colorScheme.primaryContainer,
        content = MaterialTheme.colorScheme.onPrimaryContainer,
    )
    val green = if (dark) {
        MarketTone(container = Color(0xFF0E5F38), content = Color(0xFFB7F5CE))
    } else {
        MarketTone(container = Color(0xFFDDF6E6), content = Color(0xFF00391C))
    }
    val neutral = MarketTone(
        container = MaterialTheme.colorScheme.surfaceVariant,
        content = MaterialTheme.colorScheme.onSurfaceVariant,
    )

    if (value == null || value == 0.0) return neutral
    return when (mode) {
        MarketColorMode.RedUp -> if (value > 0) red else green
        MarketColorMode.GreenUp -> if (value > 0) green else red
    }
}
