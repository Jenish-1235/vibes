# Ledge

Minimal friend money ledger with a home screen widget. Track who owes whom without opening Splitwise for small amounts.

## Status: 🚧 In progress

## What it does

- Maintain a simple per-friend balance (positive = they owe you, negative = you owe them)
- Log transactions in under 10 seconds via home screen widget → Quick Add sheet
- Review per-friend transaction history with swipe-to-delete

## Tech Stack

- Kotlin, Views + ViewBinding, Room, Hilt, Navigation Component
- Classic AppWidgetProvider for the 2×1 widget
- Min SDK 26, Target SDK 34

## Building

```bash
cd ledge/
./gradlew assembleDebug
```

## Project Structure

See [TRD.md](TRD.md) for full architecture details.
