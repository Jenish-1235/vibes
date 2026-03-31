# Ledge — Technical Requirements Document

## Platform
Native Android only. Minimum SDK 26 (Android 8.0). Target SDK 34. Language: Kotlin. Build: Gradle with version catalogs.

## Architecture
MVVM + Repository pattern. Single Activity (MainActivity) with Navigation Component managing fragments. Bottom sheet lives outside nav graph, invoked directly.

### Package Structure
```
com.ledge/
├── MainActivity.kt
├── ui/
│   ├── home/         HomeFragment + HomeViewModel
│   ├── quickadd/     QuickAddBottomSheet + QuickAddViewModel
│   └── detail/       LedgerDetailFragment + LedgerDetailViewModel
├── data/
│   ├── db/           AppDatabase, DAOs
│   ├── model/        Friend, Transaction (Room entities)
│   └── repository/   LedgeRepository
├── widget/
│   └── LedgeWidget   AppWidgetProvider
└── di/
    └── AppModule     Hilt module
```

## Tech Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Kotlin | Standard, concise |
| UI | Views + ViewBinding | No Compose — simpler for a 3-screen app |
| Navigation | Navigation Component | Single activity, handles back stack cleanly |
| Database | Room + SQLite | Local only, type-safe, zero setup |
| DI | Hilt | Minimal boilerplate |
| Async | Kotlin Coroutines + Flow | Room emits Flow, ViewModels collect |
| Widget | Classic AppWidgetProvider + RemoteViews | Glance adds Compose dependency, overkill here |
| Build | Gradle + libs.versions.toml | Standard version catalog |

## Data Model

- **Amount stored as Long in paise** (multiply display value by 100). No Float or Double anywhere near money.
- **Direction enum**: `GAVE` or `OWE`
- Room database name: `ledge.db`

## Key Constraints
- All DB operations on background dispatcher, never main thread
- Amount always in paise internally, format to ₹ only at display layer
- Widget PendingIntent uses FLAG_IMMUTABLE (required API 31+)
- No internet permission in manifest
- Widget updates triggered by: app launch, any transaction logged, onEnabled. No polling.
