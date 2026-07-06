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
