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

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
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
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.6")
    implementation("androidx.navigation:navigation-compose:2.8.2")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    ksp("androidx.room:room-compiler:2.6.1")

    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
    testImplementation("androidx.test:core:1.6.1")
    testImplementation("androidx.room:room-testing:2.6.1")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
    testImplementation("org.robolectric:robolectric:4.13")
}

afterEvaluate {
    tasks.named<Test>("testDebugUnitTest") {
        val asciiTestClassesDir = file("C:/Temp/SequoiaX/android-test-classes/debugUnitTest")
        val asciiMainClassesDir = file("C:/Temp/SequoiaX/android-main-classes/debug")
        val asciiMainJavaClassesDir = file("C:/Temp/SequoiaX/android-main-java-classes/debug")
        testClassesDirs = files(asciiTestClassesDir)
        classpath = files(asciiTestClassesDir, asciiMainClassesDir, asciiMainJavaClassesDir).plus(classpath)
        doFirst {
            delete(asciiTestClassesDir)
            delete(asciiMainClassesDir)
            delete(asciiMainJavaClassesDir)
            copy {
                from(layout.buildDirectory.dir("tmp/kotlin-classes/debugUnitTest"))
                into(asciiTestClassesDir)
            }
            copy {
                from(layout.buildDirectory.dir("tmp/kotlin-classes/debug"))
                into(asciiMainClassesDir)
            }
            copy {
                from(layout.buildDirectory.dir("intermediates/javac/debug/compileDebugJavaWithJavac/classes"))
                into(asciiMainJavaClassesDir)
            }
        }
    }
}
