package com.sequoiax.app.ui

import java.util.Locale

fun formatPrice(value: Double?): String = value?.let { String.format(Locale.US, "%.2f", it) } ?: "-"

fun formatPct(value: Double?): String = value?.let {
    val sign = if (it > 0) "+" else ""
    "$sign${String.format(Locale.US, "%.2f", it)}%"
} ?: "-"

fun previewText(value: String, maxChars: Int = 64): String =
    if (value.length <= maxChars) value else value.take(maxChars) + "..."
