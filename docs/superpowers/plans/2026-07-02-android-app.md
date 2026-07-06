# Sequoia-X Android App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native Android app that imports `sequoia_app_data_*.zip` and provides a fast mobile stock-selection reader.

**Architecture:** Add an `android-app/` Gradle project beside the Python pipeline. The app uses Kotlin, Jetpack Compose, Room, and a display-row cache so list queries do not scan all historical daily rows. Import runs in a repository transaction and keeps previous data if a package fails validation.

**Tech Stack:** Kotlin, Android Gradle Plugin, Jetpack Compose, Room, Kotlin serialization, coroutines, Android Storage Access Framework, JUnit/Robolectric where available.

## Global Constraints

- Native Android app.
- Kotlin.
- Jetpack Compose for UI.
- Room over SQLite for local storage.
- Kotlin coroutines for import and database work.
- Android Storage Access Framework for choosing the zip file.
- Manual zip import is the first-version update path.
- No accounts, brokerage integration, cloud sync, automatic push notifications, real-time quotes, or order placement in the first version.
- Home list must not load all historical `stock_daily` rows into memory.
- Home screen should show the latest list in about 1 second after launch on a normal Android phone.
- Filtering and sorting should feel immediate for the current result set.
- Import must run off the UI thread and failed import must leave previous data intact.

---

## File Structure

- Create `android-app/settings.gradle.kts`: Android project settings.
- Create `android-app/build.gradle.kts`: root Gradle plugin versions.
- Create `android-app/app/build.gradle.kts`: Android app module dependencies and Compose config.
- Create `android-app/app/src/main/AndroidManifest.xml`: app manifest and main activity declaration.
- Create `android-app/app/src/main/java/com/sequoiax/app/MainActivity.kt`: Compose entry activity.
- Create `android-app/app/src/main/java/com/sequoiax/app/data/Entities.kt`: Room entities.
- Create `android-app/app/src/main/java/com/sequoiax/app/data/Daos.kt`: Room DAO interfaces.
- Create `android-app/app/src/main/java/com/sequoiax/app/data/AppDatabase.kt`: Room database factory.
- Create `android-app/app/src/main/java/com/sequoiax/app/importer/ImportModels.kt`: Kotlin serialization DTOs for zip files.
- Create `android-app/app/src/main/java/com/sequoiax/app/importer/ZipPackageImporter.kt`: streaming zip import and validation.
- Create `android-app/app/src/main/java/com/sequoiax/app/repository/StockRepository.kt`: app data access facade.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/AppViewModel.kt`: UI state and actions.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`: top-level navigation and screens.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/HomeScreen.kt`: result list, filters, sorting.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/DetailScreen.kt`: stock detail.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`: import state and import action.
- Create `android-app/app/src/main/java/com/sequoiax/app/ui/Formatters.kt`: price, percent, and text helpers.
- Create `android-app/app/src/test/java/com/sequoiax/app/importer/ZipPackageImporterTest.kt`: import parser tests.
- Create `android-app/app/src/test/java/com/sequoiax/app/repository/DisplayRowsTest.kt`: display-row and sort tests.
- Create `android-app/README.md`: Android build and import instructions.

---

### Task 1: Android Project Scaffold

**Files:**
- Create: `android-app/settings.gradle.kts`
- Create: `android-app/build.gradle.kts`
- Create: `android-app/app/build.gradle.kts`
- Create: `android-app/app/src/main/AndroidManifest.xml`
- Create: `android-app/app/src/main/java/com/sequoiax/app/MainActivity.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`
- Create: `android-app/README.md`

**Interfaces:**
- Consumes: none.
- Produces: buildable Android app module `:app`; package `com.sequoiax.app`; composable `SequoiaApp()`.

- [ ] **Step 1: Create Gradle settings**

Create `android-app/settings.gradle.kts`:

```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "SequoiaXAndroid"
include(":app")
```

- [ ] **Step 2: Create root Gradle build**

Create `android-app/build.gradle.kts`:

```kotlin
plugins {
    id("com.android.application") version "8.6.1" apply false
    id("org.jetbrains.kotlin.android") version "2.0.20" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.20" apply false
    id("org.jetbrains.kotlin.plugin.serialization") version "2.0.20" apply false
    id("com.google.devtools.ksp") version "2.0.20-1.0.25" apply false
}
```

- [ ] **Step 3: Create app module Gradle build**

Create `android-app/app/build.gradle.kts`:

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.sequoiax.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.sequoiax.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        compose = true
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.10.01")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.6")
    implementation("androidx.navigation:navigation-compose:2.8.2")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    ksp("androidx.room:room-compiler:2.6.1")

    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
    testImplementation("androidx.test:core:1.6.1")
    testImplementation("androidx.room:room-testing:2.6.1")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
}
```

- [ ] **Step 4: Create manifest and entry activity**

Create `android-app/app/src/main/AndroidManifest.xml`:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:allowBackup="true"
        android:label="Sequoia-X"
        android:supportsRtl="true"
        android:theme="@style/AppTheme">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

Create `android-app/app/src/main/res/values/styles.xml`:

```xml
<resources>
    <style name="AppTheme" parent="android:style/Theme.Material.Light.NoActionBar">
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:navigationBarColor">#F6F7F9</item>
        <item name="android:statusBarColor">#FFFFFF</item>
    </style>
</resources>
```

Create `android-app/app/src/main/java/com/sequoiax/app/MainActivity.kt`:

```kotlin
package com.sequoiax.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.sequoiax.app.ui.SequoiaApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SequoiaApp() }
    }
}
```

- [ ] **Step 5: Create a minimal Compose shell**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SequoiaApp() {
    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("Sequoia-X", style = MaterialTheme.typography.headlineSmall)
                Text("导入选股数据包后查看结果")
            }
        }
    }
}
```

- [ ] **Step 6: Add Android README**

Create `android-app/README.md`:

```markdown
# Sequoia-X Android

Native Android reader for Sequoia-X exported zip packages.

## Build

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

## First import target

Use `../exports/app/sequoia_app_data_2026-07-01.zip`.
```

- [ ] **Step 7: Build the scaffold**

Run:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

Expected: build succeeds and creates `android-app/app/build/outputs/apk/debug/app-debug.apk`.

---

### Task 2: Room Schema And Display Query Contracts

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/data/Entities.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/data/Daos.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/data/AppDatabase.kt`
- Create: `android-app/app/src/test/java/com/sequoiax/app/repository/DisplayRowsTest.kt`

**Interfaces:**
- Consumes: package `com.sequoiax.app`.
- Produces: `AppDatabase`, `StockDao`, `DisplayRowDao`, `ResultDisplayRowEntity`, `StockDisplayRow`, `SortMode`.

- [ ] **Step 1: Write the failing display-row sort test**

Create `android-app/app/src/test/java/com/sequoiax/app/repository/DisplayRowsTest.kt`:

```kotlin
package com.sequoiax.app.repository

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

class DisplayRowsTest {
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
    fun displayRowsSortByPriceBothDirections() = runBlocking {
        db.displayRowDao().replaceRows(
            listOf(
                ResultDisplayRowEntity("2026-07-01", "A", "600601", "方正科技", "电子", "信息", 13.97, 5.12, 10.26, 38.87, "13,14"),
                ResultDisplayRowEntity("2026-07-01", "A", "688361", "中科飞测", "设备", "信息", 422.0, 1.0, 2.0, 3.0, "400,422"),
            )
        )

        val highToLow = db.displayRowDao().queryRows("2026-07-01", "", "", SortMode.PriceDesc.value)
        val lowToHigh = db.displayRowDao().queryRows("2026-07-01", "", "", SortMode.PriceAsc.value)

        assertEquals(listOf("688361", "600601"), highToLow.map { it.symbol })
        assertEquals(listOf("600601", "688361"), lowToHigh.map { it.symbol })
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.repository.DisplayRowsTest
```

Expected: FAIL because `AppDatabase`, `ResultDisplayRowEntity`, and `SortMode` do not exist.

- [ ] **Step 3: Implement entities and sort enum**

Create `android-app/app/src/main/java/com/sequoiax/app/data/Entities.kt`:

```kotlin
package com.sequoiax.app.data

import androidx.room.Entity
import androidx.room.Index

@Entity(primaryKeys = ["packageId"])
data class ImportBatchEntity(
    val packageId: String,
    val sourceFileName: String,
    val generatedAt: String,
    val latestDate: String,
    val importedAt: Long,
)

@Entity(primaryKeys = ["symbol"])
data class StockBasicEntity(
    val symbol: String,
    val name: String,
    val exchange: String,
    val status: String,
    val stockType: String,
    val updatedAt: String,
)

@Entity(
    primaryKeys = ["symbol", "date"],
    indices = [Index(["symbol", "date"])],
)
data class StockDailyEntity(
    val symbol: String,
    val date: String,
    val open: Double?,
    val high: Double?,
    val low: Double?,
    val close: Double?,
    val volume: Double?,
    val turnover: Double?,
)

@Entity(
    primaryKeys = ["date", "strategy", "symbol"],
    indices = [Index(["date", "strategy", "symbol"]), Index(["symbol"])],
)
data class StrategyResultEntity(
    val date: String,
    val strategy: String,
    val symbol: String,
)

@Entity(primaryKeys = ["symbol"], indices = [Index(["symbol"])])
data class StockContextEntity(
    val symbol: String,
    val sector: String,
    val majorInfo: String,
    val updatedAt: String,
)

@Entity(primaryKeys = ["strategy"])
data class StrategyNoteEntity(
    val strategy: String,
    val label: String,
    val explain: String,
    val advice: String,
)

@Entity(
    primaryKeys = ["date", "strategy", "symbol"],
    indices = [Index(["date", "strategy"]), Index(["symbol"]), Index(["latestClose"])],
)
data class ResultDisplayRowEntity(
    val date: String,
    val strategy: String,
    val symbol: String,
    val name: String,
    val sector: String,
    val majorInfo: String,
    val latestClose: Double?,
    val change5: Double?,
    val change20: Double?,
    val change60: Double?,
    val sparklineCsv: String,
)

enum class SortMode(val value: String) {
    Strategy("strategy"),
    PriceDesc("price_desc"),
    PriceAsc("price_asc"),
    Change5("change_5"),
    Change20("change_20"),
    Change60("change_60"),
}
```

- [ ] **Step 4: Implement DAOs and database**

Create `android-app/app/src/main/java/com/sequoiax/app/data/Daos.kt`:

```kotlin
package com.sequoiax.app.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction

@Dao
interface ImportDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBatch(batch: ImportBatchEntity)

    @Query("SELECT * FROM ImportBatchEntity ORDER BY importedAt DESC")
    suspend fun batches(): List<ImportBatchEntity>

    @Query("SELECT * FROM ImportBatchEntity ORDER BY importedAt DESC LIMIT 1")
    suspend fun latestBatch(): ImportBatchEntity?
}

@Dao
interface StockDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBasics(rows: List<StockBasicEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDaily(rows: List<StockDailyEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertResults(rows: List<StrategyResultEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertContexts(rows: List<StockContextEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNotes(rows: List<StrategyNoteEntity>)

    @Query("SELECT * FROM StockDailyEntity WHERE symbol = :symbol ORDER BY date DESC LIMIT :limit")
    suspend fun recentDaily(symbol: String, limit: Int): List<StockDailyEntity>

    @Query("SELECT * FROM StrategyResultEntity WHERE symbol = :symbol ORDER BY date DESC")
    suspend fun resultsForSymbol(symbol: String): List<StrategyResultEntity>
}

@Dao
interface DisplayRowDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRows(rows: List<ResultDisplayRowEntity>)

    @Query("DELETE FROM ResultDisplayRowEntity")
    suspend fun clearRows()

    @Transaction
    suspend fun replaceRows(rows: List<ResultDisplayRowEntity>) {
        clearRows()
        insertRows(rows)
    }

    @Query(
        """
        SELECT * FROM ResultDisplayRowEntity
        WHERE date = :date
          AND (:strategy = '' OR strategy = :strategy)
          AND (
            :query = ''
            OR symbol LIKE '%' || :query || '%'
            OR name LIKE '%' || :query || '%'
            OR sector LIKE '%' || :query || '%'
            OR majorInfo LIKE '%' || :query || '%'
          )
        ORDER BY
          CASE WHEN :sort = 'price_asc' THEN latestClose END ASC,
          CASE WHEN :sort = 'price_desc' THEN latestClose END DESC,
          CASE WHEN :sort = 'change_5' THEN change5 END DESC,
          CASE WHEN :sort = 'change_20' THEN change20 END DESC,
          CASE WHEN :sort = 'change_60' THEN change60 END DESC,
          CASE WHEN :sort = 'strategy' THEN strategy END ASC,
          symbol ASC
        """
    )
    suspend fun queryRows(date: String, query: String, strategy: String, sort: String): List<ResultDisplayRowEntity>

    @Query("SELECT DISTINCT strategy FROM ResultDisplayRowEntity WHERE date = :date ORDER BY strategy")
    suspend fun strategies(date: String): List<String>

    @Query("SELECT MAX(date) FROM ResultDisplayRowEntity")
    suspend fun latestDate(): String?

    @Query("SELECT * FROM ResultDisplayRowEntity WHERE symbol = :symbol ORDER BY date DESC, strategy")
    suspend fun rowsForSymbol(symbol: String): List<ResultDisplayRowEntity>
}
```

Create `android-app/app/src/main/java/com/sequoiax/app/data/AppDatabase.kt`:

```kotlin
package com.sequoiax.app.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        ImportBatchEntity::class,
        StockBasicEntity::class,
        StockDailyEntity::class,
        StrategyResultEntity::class,
        StockContextEntity::class,
        StrategyNoteEntity::class,
        ResultDisplayRowEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun importDao(): ImportDao
    abstract fun stockDao(): StockDao
    abstract fun displayRowDao(): DisplayRowDao

    companion object {
        fun create(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "sequoia-x.db").build()
    }
}
```

- [ ] **Step 5: Run display-row tests**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.repository.DisplayRowsTest
```

Expected: PASS.

---

### Task 3: Zip Importer And Display Row Generation

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/importer/ImportModels.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/importer/ZipPackageImporter.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/repository/StockRepository.kt`
- Create: `android-app/app/src/test/java/com/sequoiax/app/importer/ZipPackageImporterTest.kt`

**Interfaces:**
- Consumes: `AppDatabase`, entities from Task 2.
- Produces: `ZipPackageImporter.importPackage(inputStream: InputStream, sourceName: String): ImportSummary`; `StockRepository.queryRows(...)`.

- [ ] **Step 1: Write failing importer test**

Create `android-app/app/src/test/java/com/sequoiax/app/importer/ZipPackageImporterTest.kt`:

```kotlin
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
        val bytes = sampleZip()
        val importer = ZipPackageImporter(db)

        val summary = importer.importPackage(ByteArrayInputStream(bytes), "sample.zip")
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.importer.ZipPackageImporterTest
```

Expected: FAIL because importer models and `ZipPackageImporter` do not exist.

- [ ] **Step 3: Create import DTOs**

Create `android-app/app/src/main/java/com/sequoiax/app/importer/ImportModels.kt`:

```kotlin
package com.sequoiax.app.importer

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ManifestDto(
    @SerialName("format_version") val formatVersion: Int,
    @SerialName("generated_at") val generatedAt: String = "",
    @SerialName("latest_date") val latestDate: String,
)

@Serializable
data class StockBasicDto(
    val symbol: String,
    val name: String = "",
    val exchange: String = "",
    val status: String = "",
    @SerialName("stock_type") val stockType: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class StockDailyDto(
    val symbol: String,
    val date: String,
    val open: Double? = null,
    val high: Double? = null,
    val low: Double? = null,
    val close: Double? = null,
    val volume: Double? = null,
    val turnover: Double? = null,
)

@Serializable
data class StrategyResultDto(
    val date: String,
    val strategy: String,
    val symbol: String,
)

@Serializable
data class StockContextDto(
    val symbol: String,
    val sector: String = "",
    @SerialName("major_info") val majorInfo: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class StrategyNoteValueDto(
    val label: String = "",
    val explain: String = "",
    val advice: String = "",
)

data class ImportSummary(
    val latestDate: String,
    val resultRows: Int,
    val stockDailyRows: Int,
)
```

- [ ] **Step 4: Implement importer**

Create `android-app/app/src/main/java/com/sequoiax/app/importer/ZipPackageImporter.kt`:

```kotlin
package com.sequoiax.app.importer

import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.StockBasicEntity
import com.sequoiax.app.data.StockContextEntity
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.data.StrategyNoteEntity
import com.sequoiax.app.data.StrategyResultEntity
import java.io.BufferedReader
import java.io.InputStream
import java.io.InputStreamReader
import java.util.UUID
import java.util.zip.ZipInputStream
import kotlinx.serialization.json.Json

class ZipPackageImporter(private val db: AppDatabase) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun importPackage(inputStream: InputStream, sourceName: String): ImportSummary {
        val entries = readZip(inputStream)
        val manifest = json.decodeFromString<ManifestDto>(entries.requireText("manifest.json"))
        require(manifest.formatVersion == 1) { "Unsupported format_version: ${manifest.formatVersion}" }

        val basics = entries.requireLines("stock_basic.jsonl").map { json.decodeFromString<StockBasicDto>(it) }
        val daily = entries.requireLines("stock_daily.jsonl").map { json.decodeFromString<StockDailyDto>(it) }
        val results = entries.requireLines("results.jsonl").map { json.decodeFromString<StrategyResultDto>(it) }
        val contexts = entries.requireLines("stock_context.jsonl").map { json.decodeFromString<StockContextDto>(it) }
        val notes = json.decodeFromString<Map<String, StrategyNoteValueDto>>(entries.requireText("strategy_notes.json"))

        db.runInTransaction {
            runBlockingTransaction {
                db.stockDao().insertBasics(basics.map { StockBasicEntity(it.symbol, it.name, it.exchange, it.status, it.stockType, it.updatedAt) })
                db.stockDao().insertDaily(daily.map { StockDailyEntity(it.symbol, it.date, it.open, it.high, it.low, it.close, it.volume, it.turnover) })
                db.stockDao().insertResults(results.map { StrategyResultEntity(it.date, it.strategy, it.symbol) })
                db.stockDao().insertContexts(contexts.map { StockContextEntity(it.symbol, it.sector, it.majorInfo, it.updatedAt) })
                db.stockDao().insertNotes(notes.map { (strategy, note) -> StrategyNoteEntity(strategy, note.label, note.explain, note.advice) })
                db.displayRowDao().replaceRows(buildDisplayRows(manifest.latestDate, basics, daily, results, contexts))
                db.importDao().insertBatch(
                    ImportBatchEntity(
                        packageId = UUID.randomUUID().toString(),
                        sourceFileName = sourceName,
                        generatedAt = manifest.generatedAt,
                        latestDate = manifest.latestDate,
                        importedAt = System.currentTimeMillis(),
                    )
                )
            }
        }
        return ImportSummary(manifest.latestDate, results.size, daily.size)
    }

    private fun buildDisplayRows(
        latestDate: String,
        basics: List<StockBasicDto>,
        daily: List<StockDailyDto>,
        results: List<StrategyResultDto>,
        contexts: List<StockContextDto>,
    ): List<ResultDisplayRowEntity> {
        val names = basics.associate { it.symbol to it.name }
        val contextMap = contexts.associateBy { it.symbol }
        val dailyBySymbol = daily.filter { it.close != null }.groupBy { it.symbol }
            .mapValues { (_, rows) -> rows.sortedBy { it.date } }
        return results.filter { it.date == latestDate }.mapNotNull { result ->
            val history = dailyBySymbol[result.symbol].orEmpty()
            val latest = history.lastOrNull()?.close
            val closes = history.mapNotNull { it.close }
            val context = contextMap[result.symbol]
            ResultDisplayRowEntity(
                date = result.date,
                strategy = result.strategy,
                symbol = result.symbol,
                name = names[result.symbol].orEmpty(),
                sector = context?.sector.orEmpty(),
                majorInfo = context?.majorInfo.orEmpty(),
                latestClose = latest,
                change5 = pctChange(closes, 5),
                change20 = pctChange(closes, 20),
                change60 = pctChange(closes, 60),
                sparklineCsv = closes.takeLast(30).joinToString(","),
            )
        }
    }

    private fun pctChange(closes: List<Double>, sessions: Int): Double? {
        if (closes.size <= sessions) return null
        val base = closes[closes.size - sessions - 1]
        val latest = closes.last()
        if (base == 0.0) return null
        return kotlin.math.round((latest / base - 1.0) * 10000.0) / 100.0
    }

    private fun readZip(inputStream: InputStream): Map<String, String> {
        val out = linkedMapOf<String, String>()
        ZipInputStream(inputStream).use { zip ->
            while (true) {
                val entry = zip.nextEntry ?: break
                if (!entry.isDirectory) {
                    out[entry.name] = BufferedReader(InputStreamReader(zip, Charsets.UTF_8)).readText()
                }
                zip.closeEntry()
            }
        }
        return out
    }

    private fun Map<String, String>.requireText(name: String): String =
        requireNotNull(this[name]) { "Missing $name" }

    private fun Map<String, String>.requireLines(name: String): List<String> =
        requireText(name).lineSequence().map { it.trim() }.filter { it.isNotEmpty() }.toList()
}

private fun runBlockingTransaction(block: suspend () -> Unit) {
    kotlinx.coroutines.runBlocking { block() }
}
```

- [ ] **Step 5: Create repository facade**

Create `android-app/app/src/main/java/com/sequoiax/app/repository/StockRepository.kt`:

```kotlin
package com.sequoiax.app.repository

import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.importer.ImportSummary
import com.sequoiax.app.importer.ZipPackageImporter
import java.io.InputStream

class StockRepository(private val db: AppDatabase) {
    private val importer = ZipPackageImporter(db)

    suspend fun importPackage(inputStream: InputStream, sourceName: String): ImportSummary =
        importer.importPackage(inputStream, sourceName)

    suspend fun latestDate(): String? = db.displayRowDao().latestDate()

    suspend fun queryRows(
        date: String,
        query: String,
        strategy: String,
        sortMode: SortMode,
    ): List<ResultDisplayRowEntity> = db.displayRowDao().queryRows(date, query, strategy, sortMode.value)

    suspend fun strategies(date: String): List<String> = db.displayRowDao().strategies(date)

    suspend fun batches(): List<ImportBatchEntity> = db.importDao().batches()

    suspend fun rowsForSymbol(symbol: String): List<ResultDisplayRowEntity> = db.displayRowDao().rowsForSymbol(symbol)

    suspend fun recentDaily(symbol: String, limit: Int): List<StockDailyEntity> = db.stockDao().recentDaily(symbol, limit)
}
```

- [ ] **Step 6: Run importer tests**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest --tests com.sequoiax.app.importer.ZipPackageImporterTest
```

Expected: PASS.

---

### Task 4: ViewModel And UI State

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/AppViewModel.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/MainActivity.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`

**Interfaces:**
- Consumes: `StockRepository`, `AppDatabase.create(context)`, `SortMode`.
- Produces: `AppViewModel`, `HomeUiState`, `DetailUiState`, import and filter actions.

- [ ] **Step 1: Implement ViewModel state**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/AppViewModel.kt`:

```kotlin
package com.sequoiax.app.ui

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sequoiax.app.data.ImportBatchEntity
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode
import com.sequoiax.app.data.StockDailyEntity
import com.sequoiax.app.repository.StockRepository
import java.io.InputStream
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class HomeUiState(
    val latestDate: String = "",
    val query: String = "",
    val strategy: String = "",
    val sortMode: SortMode = SortMode.Strategy,
    val strategies: List<String> = emptyList(),
    val rows: List<ResultDisplayRowEntity> = emptyList(),
    val batches: List<ImportBatchEntity> = emptyList(),
    val isImporting: Boolean = false,
    val message: String = "",
)

data class DetailUiState(
    val rows: List<ResultDisplayRowEntity> = emptyList(),
    val daily: List<StockDailyEntity> = emptyList(),
)

class AppViewModel(private val repository: StockRepository) : ViewModel() {
    private val _home = MutableStateFlow(HomeUiState())
    val home: StateFlow<HomeUiState> = _home

    private val _detail = MutableStateFlow(DetailUiState())
    val detail: StateFlow<DetailUiState> = _detail

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            val latest = repository.latestDate().orEmpty()
            val strategies = if (latest.isNotEmpty()) repository.strategies(latest) else emptyList()
            val batches = repository.batches()
            _home.update { it.copy(latestDate = latest, strategies = strategies, batches = batches) }
            reloadRows()
        }
    }

    fun setQuery(value: String) {
        _home.update { it.copy(query = value) }
        reloadRows()
    }

    fun setStrategy(value: String) {
        _home.update { it.copy(strategy = value) }
        reloadRows()
    }

    fun setSortMode(value: SortMode) {
        _home.update { it.copy(sortMode = value) }
        reloadRows()
    }

    fun importFrom(uri: Uri, sourceName: String, openInput: suspend () -> InputStream) {
        viewModelScope.launch {
            _home.update { it.copy(isImporting = true, message = "正在导入 $sourceName") }
            try {
                withContext(Dispatchers.IO) {
                    openInput().use { repository.importPackage(it, sourceName) }
                }
                _home.update { it.copy(isImporting = false, message = "导入完成") }
                refresh()
            } catch (exc: Exception) {
                _home.update { it.copy(isImporting = false, message = "导入失败：${exc.message ?: "未知错误"}") }
            }
        }
    }

    fun loadDetail(symbol: String) {
        viewModelScope.launch {
            val rows = repository.rowsForSymbol(symbol)
            val daily = repository.recentDaily(symbol, 120)
            _detail.value = DetailUiState(rows, daily)
        }
    }

    private fun reloadRows() {
        viewModelScope.launch {
            val state = _home.value
            if (state.latestDate.isEmpty()) {
                _home.update { it.copy(rows = emptyList()) }
                return@launch
            }
            val rows = repository.queryRows(state.latestDate, state.query, state.strategy, state.sortMode)
            _home.update { it.copy(rows = rows) }
        }
    }
}
```

- [ ] **Step 2: Wire ViewModel factory in MainActivity**

Modify `android-app/app/src/main/java/com/sequoiax/app/MainActivity.kt`:

```kotlin
package com.sequoiax.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.sequoiax.app.data.AppDatabase
import com.sequoiax.app.repository.StockRepository
import com.sequoiax.app.ui.AppViewModel
import com.sequoiax.app.ui.SequoiaApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val repository = StockRepository(AppDatabase.create(this))
        val factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return AppViewModel(repository) as T
            }
        }
        setContent {
            val appViewModel: AppViewModel = viewModel(factory = factory)
            SequoiaApp(viewModel = appViewModel)
        }
    }
}
```

- [ ] **Step 3: Update app shell signature**

Modify `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt` so it accepts the ViewModel:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable

@Composable
fun SequoiaApp(viewModel: AppViewModel) {
    MaterialTheme {
        HomeScreen(viewModel = viewModel, onOpenDetail = {})
    }
}
```

- [ ] **Step 4: Run unit tests**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest
```

Expected: PASS.

---

### Task 5: Home Screen With Fast List, Filters, And Sorting

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/HomeScreen.kt`
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/Formatters.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`

**Interfaces:**
- Consumes: `AppViewModel`, `HomeUiState`, `ResultDisplayRowEntity`.
- Produces: interactive home list using `LazyColumn`.

- [ ] **Step 1: Implement formatting helpers**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/Formatters.kt`:

```kotlin
package com.sequoiax.app.ui

import java.util.Locale

fun formatPrice(value: Double?): String = value?.let { String.format(Locale.US, "%.2f", it) } ?: "-"

fun formatPct(value: Double?): String = value?.let {
    val sign = if (it > 0) "+" else ""
    "$sign${String.format(Locale.US, "%.2f", it)}%"
} ?: "-"

fun previewText(value: String, maxChars: Int = 64): String =
    if (value.length <= maxChars) value else value.take(maxChars) + "..."
```

- [ ] **Step 2: Implement HomeScreen**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/HomeScreen.kt`:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.sequoiax.app.data.ResultDisplayRowEntity
import com.sequoiax.app.data.SortMode

@Composable
fun HomeScreen(viewModel: AppViewModel, onOpenDetail: (String) -> Unit) {
    val state by viewModel.home.collectAsState()
    Column(
        modifier = Modifier.fillMaxSize().padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text("Sequoia-X", style = MaterialTheme.typography.headlineSmall)
        Text(if (state.latestDate.isEmpty()) "未导入数据" else "数据日期：${state.latestDate}")
        if (state.isImporting) LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        if (state.message.isNotEmpty()) Text(state.message, color = MaterialTheme.colorScheme.primary)
        FilterBar(state = state, viewModel = viewModel)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.rows, key = { "${it.date}-${it.strategy}-${it.symbol}" }) { row ->
                ResultRow(row = row, onClick = { onOpenDetail(row.symbol) })
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FilterBar(state: HomeUiState, viewModel: AppViewModel) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(
            value = state.query,
            onValueChange = viewModel::setQuery,
            label = { Text("搜索代码、名称、板块或信息") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            StrategyMenu(state, viewModel, Modifier.weight(1f))
            SortMenu(state, viewModel, Modifier.weight(1f))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun StrategyMenu(state: HomeUiState, viewModel: AppViewModel, modifier: Modifier) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }, modifier = modifier) {
        OutlinedTextField(
            value = if (state.strategy.isEmpty()) "全部策略" else state.strategy,
            onValueChange = {},
            readOnly = true,
            label = { Text("策略") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            DropdownMenuItem(text = { Text("全部策略") }, onClick = { viewModel.setStrategy(""); expanded = false })
            state.strategies.forEach { strategy ->
                DropdownMenuItem(text = { Text(strategy) }, onClick = { viewModel.setStrategy(strategy); expanded = false })
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SortMenu(state: HomeUiState, viewModel: AppViewModel, modifier: Modifier) {
    var expanded by remember { mutableStateOf(false) }
    val labels = mapOf(
        SortMode.Strategy to "按策略",
        SortMode.PriceDesc to "股价从高到低",
        SortMode.PriceAsc to "股价从低到高",
        SortMode.Change5 to "按5日涨跌幅",
        SortMode.Change20 to "按20日涨跌幅",
        SortMode.Change60 to "按60日涨跌幅",
    )
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }, modifier = modifier) {
        OutlinedTextField(
            value = labels.getValue(state.sortMode),
            onValueChange = {},
            readOnly = true,
            label = { Text("排序") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            labels.forEach { (mode, label) ->
                DropdownMenuItem(text = { Text(label) }, onClick = { viewModel.setSortMode(mode); expanded = false })
            }
        }
    }
}

@Composable
private fun ResultRow(row: ResultDisplayRowEntity, onClick: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("${row.symbol} ${row.name}", style = MaterialTheme.typography.titleMedium)
                Text(formatPrice(row.latestClose), style = MaterialTheme.typography.titleMedium)
            }
            Text(row.strategy, color = MaterialTheme.colorScheme.primary)
            Text("5日 ${formatPct(row.change5)}  20日 ${formatPct(row.change20)}  60日 ${formatPct(row.change60)}")
            Text("板块：${row.sector.ifEmpty { "未缓存" }}")
            Text(previewText(row.majorInfo.ifEmpty { "暂无近期重大信息" }))
        }
    }
}
```

- [ ] **Step 3: Keep top-level app pointing to HomeScreen**

Ensure `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt` contains:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable

@Composable
fun SequoiaApp(viewModel: AppViewModel) {
    MaterialTheme {
        HomeScreen(viewModel = viewModel, onOpenDetail = {})
    }
}
```

- [ ] **Step 4: Build**

Run:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

Expected: PASS.

---

### Task 6: Data Import Screen And File Picker

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`

**Interfaces:**
- Consumes: `AppViewModel.importFrom(uri, sourceName, openInput)`.
- Produces: Data screen with Android file picker import.

- [ ] **Step 1: Implement DataScreen**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/DataScreen.kt`:

```kotlin
package com.sequoiax.app.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

@Composable
fun DataScreen(viewModel: AppViewModel) {
    val state by viewModel.home.collectAsState()
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
            val sourceName = uri.lastPathSegment ?: "sequoia_app_data.zip"
            viewModel.importFrom(uri, sourceName) {
                requireNotNull(context.contentResolver.openInputStream(uri)) { "无法打开文件" }
            }
        }
    }

    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(if (state.latestDate.isEmpty()) "当前无数据" else "当前数据日期：${state.latestDate}")
        Button(onClick = { launcher.launch(arrayOf("application/zip", "application/octet-stream")) }) {
            Text("导入数据包")
        }
        state.batches.forEach { batch ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(batch.sourceFileName)
                    Text("最新日期：${batch.latestDate}")
                    Text("生成时间：${batch.generatedAt}")
                }
            }
        }
    }
}
```

- [ ] **Step 2: Add simple two-tab navigation**

Modify `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue

@Composable
fun SequoiaApp(viewModel: AppViewModel) {
    var tab by remember { mutableStateOf("home") }
    MaterialTheme {
        Scaffold(
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(selected = tab == "home", onClick = { tab = "home" }, label = { Text("选股") }, icon = {})
                    NavigationBarItem(selected = tab == "data", onClick = { tab = "data" }, label = { Text("数据") }, icon = {})
                }
            }
        ) { padding ->
            Column {
                when (tab) {
                    "data" -> DataScreen(viewModel)
                    else -> HomeScreen(viewModel = viewModel, onOpenDetail = {})
                }
            }
        }
    }
}
```

- [ ] **Step 3: Build**

Run:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

Expected: PASS and no Compose compile errors.

---

### Task 7: Detail Screen

**Files:**
- Create: `android-app/app/src/main/java/com/sequoiax/app/ui/DetailScreen.kt`
- Modify: `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`

**Interfaces:**
- Consumes: `AppViewModel.loadDetail(symbol)`, `DetailUiState`.
- Produces: detail screen opened from home row.

- [ ] **Step 1: Implement DetailScreen**

Create `android-app/app/src/main/java/com/sequoiax/app/ui/DetailScreen.kt`:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun DetailScreen(symbol: String, viewModel: AppViewModel, onBack: () -> Unit) {
    val state by viewModel.detail.collectAsState()
    LaunchedEffect(symbol) {
        viewModel.loadDetail(symbol)
    }
    LazyColumn(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text(symbol, style = MaterialTheme.typography.headlineSmall)
                Button(onClick = onBack) { Text("返回") }
            }
        }
        items(state.rows) { row ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("${row.name}  ${formatPrice(row.latestClose)}", style = MaterialTheme.typography.titleMedium)
                    Text("策略：${row.strategy}")
                    Text("板块：${row.sector}")
                    Text("5日 ${formatPct(row.change5)}  20日 ${formatPct(row.change20)}  60日 ${formatPct(row.change60)}")
                    Text(row.majorInfo.ifEmpty { "暂无近期重大信息" })
                }
            }
        }
        item {
            Text("近期价格", style = MaterialTheme.typography.titleMedium)
            Text(state.daily.reversed().joinToString("  ") { "${it.date}:${formatPrice(it.close)}" })
        }
    }
}
```

- [ ] **Step 2: Wire detail navigation**

Modify `android-app/app/src/main/java/com/sequoiax/app/ui/SequoiaApp.kt`:

```kotlin
package com.sequoiax.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue

@Composable
fun SequoiaApp(viewModel: AppViewModel) {
    var tab by remember { mutableStateOf("home") }
    var detailSymbol by remember { mutableStateOf<String?>(null) }
    MaterialTheme {
        Scaffold(
            bottomBar = {
                if (detailSymbol == null) {
                    NavigationBar {
                        NavigationBarItem(selected = tab == "home", onClick = { tab = "home" }, label = { Text("选股") }, icon = {})
                        NavigationBarItem(selected = tab == "data", onClick = { tab = "data" }, label = { Text("数据") }, icon = {})
                    }
                }
            }
        ) { _ ->
            Column {
                val symbol = detailSymbol
                if (symbol != null) {
                    DetailScreen(symbol = symbol, viewModel = viewModel, onBack = { detailSymbol = null })
                } else {
                    when (tab) {
                        "data" -> DataScreen(viewModel)
                        else -> HomeScreen(viewModel = viewModel, onOpenDetail = { detailSymbol = it })
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 3: Build**

Run:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

Expected: PASS.

---

### Task 8: End-To-End Verification And APK Handoff

**Files:**
- Modify: `android-app/README.md`

**Interfaces:**
- Consumes: debug APK, exported zip package.
- Produces: verified APK path and smoke-test notes.

- [ ] **Step 1: Run all Android unit tests**

Run:

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest
```

Expected: PASS.

- [ ] **Step 2: Build debug APK**

Run:

```powershell
cd android-app
.\gradlew.bat :app:assembleDebug
```

Expected: PASS and file exists at `android-app/app/build/outputs/apk/debug/app-debug.apk`.

- [ ] **Step 3: Update Android README with APK and import instructions**

Modify `android-app/README.md`:

```markdown
# Sequoia-X Android

Native Android reader for Sequoia-X exported zip packages.

## Build

```powershell
cd android-app
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

Debug APK:

```text
android-app/app/build/outputs/apk/debug/app-debug.apk
```

## Import Data

1. Copy `exports/app/sequoia_app_data_2026-07-01.zip` to the phone.
2. Install the debug APK.
3. Open Sequoia-X.
4. Go to `数据`.
5. Tap `导入数据包`.
6. Select the zip file.
7. Return to `选股` and browse results.

## Smoke Checks

- `600601 方正科技` should show latest close `13.97` for `2026-07-01`.
- Price high-to-low sort should put the highest-priced result first.
- Price low-to-high sort should put the lowest-priced result first.
```

- [ ] **Step 4: Final verification from repo root**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_data_engine.py tests/test_export_app_data.py -v
cd android-app
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
```

Expected: Python checks PASS, Android unit tests PASS, APK build PASS.

- [ ] **Step 5: Report deliverables**

Report:

```text
APK: C:\Users\63538\Documents\金融APP\Sequoia-X\android-app\app\build\outputs\apk\debug\app-debug.apk
Import package: C:\Users\63538\Documents\金融APP\Sequoia-X\exports\app\sequoia_app_data_2026-07-01.zip
```

## Self-Review

- Spec coverage: Tasks cover native Android scaffold, Room schema, zip import, display-row cache, home list, filter/sort, detail page, data import page, failed import behavior through transaction, performance via display rows and `LazyColumn`, and APK verification.
- Placeholder scan: No `TBD`, `TODO`, or unspecified error-handling steps remain.
- Type consistency: `SortMode`, `ResultDisplayRowEntity`, `AppDatabase`, `ZipPackageImporter`, `StockRepository`, `AppViewModel`, `HomeScreen`, `DetailScreen`, and `DataScreen` names are used consistently across tasks.
