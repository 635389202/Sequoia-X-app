# Android Material UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dark mode, Chinese strategy labels, sorting, and Material Design polish to the Android app.

**Architecture:** Keep the database and import package format unchanged. Add UI-only mapping helpers for strategy labels/notes, a Material3 theme layer, and update Compose screens to use top app bars, cards, chips/dropdowns, and clear Chinese copy.

**Tech Stack:** Kotlin, Jetpack Compose, Material3, Room, Gradle Android Plugin.

## Global Constraints

- Do not change the Android import zip schema.
- Keep strategy filtering by original English strategy id.
- Show Chinese labels copied from the web dashboard where available.
- Rebuild the debug APK after implementation.

---

### Task 1: Theme And Mode Toggle

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/theme/Theme.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`

**Interfaces:**
- Produces: `enum class ThemeMode`, `@Composable fun SequoiaTheme(themeMode: ThemeMode, content: @Composable () -> Unit)`
- Consumes: Android system dark theme via `isSystemInDarkTheme()`.

- [ ] Add light/dark color schemes.
- [ ] Add `ThemeMode.System`, `ThemeMode.Light`, `ThemeMode.Dark`.
- [ ] Add a top app bar action in `SequoiaApp` to cycle theme mode.
- [ ] Verify `:app:assembleDebug` compiles.

### Task 2: Strategy Chinese Labels And Notes

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/StrategyText.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/HomeScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/DetailScreen.kt`

**Interfaces:**
- Produces: `fun strategyLabel(id: String): String`, `fun strategyNote(id: String): StrategyDisplayNote`
- Consumes: `ResultDisplayRowEntity.strategy` original id.

- [ ] Add strategy labels and notes copied from `export_app_data.py`.
- [ ] Use labels in filter menu, result cards, and detail rows.
- [ ] Keep selected filter value as original strategy id.
- [ ] Verify English strategy ids no longer show in normal UI.

### Task 3: Material Screen Polish

**Files:**
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/HomeScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/DetailScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/Formatters.kt`

**Interfaces:**
- Consumes: existing `HomeUiState`, `DetailUiState`, `SortMode`.
- Produces: readable Chinese UI with Material3 cards, buttons, text fields, and navigation.

- [ ] Replace garbled Chinese text with valid UTF-8 Chinese copy.
- [ ] Keep sorting menu visible and translated.
- [ ] Use Material3 `ElevatedCard`, `AssistChip`/text hierarchy, `TopAppBar`, `NavigationBar`.
- [ ] Rebuild debug APK and export updated app package.
