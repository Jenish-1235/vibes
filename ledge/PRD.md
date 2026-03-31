# Ledge — Product Requirements Document

## Problem Statement

Friends split money constantly in small informal contexts — chai, autos, groceries, trips. Nobody opens Splitwise for a ₹150 debt. WhatsApp messages get buried. Mental math drifts. The cost of logging must be near zero or the behavior won't stick.

## Target User

Small friend group (2–8 people), Indian college or young professional context, cash + UPI informal splits. No formal settlement cycles, no group accounting needed.

## Core Mental Model

One number per friend. Positive = they owe you (green). Negative = you owe them (red). The widget shows one total number — your net position across everyone. That's the entire product.

## User Flows

### Primary flow — logging a transaction
Widget visible on home screen → tap → Quick Add sheet appears → pick friend → enter amount → tap Gave or Owe → optional note → confirm. Done in under 10 seconds without ever opening the app.

### Secondary flow — reviewing
Long press widget → Home screen → tap a friend → see their full chronological ledger with notes.

### Tertiary flow — setup
Open app normally → Home → FAB → add friend name → done.

## Screens

### Home
- List of friends, each row shows name + net balance + green/red color
- One FAB: + Friend
- Tap friend row → Ledger Detail
- No navigation bar, no tabs, no hamburger menu

### Quick Add Sheet (Bottom Sheet)
- Friend picker — horizontal pill chips, scrollable
- Large numeric amount input, auto-focused on open
- Two full-width buttons: I Gave (green) / I Owe (red)
- Note field — hidden by default, small "add note" text link below buttons
- Confirm closes the sheet, shows a brief snackbar: "Logged ₹X with [Name]"

### Ledger Detail
- Friend name + net balance as header
- Chronological list of transactions: amount, direction arrow, date, note if present
- Swipe left on entry → delete with undo snackbar
- No edit. Delete and re-add. Keeps the log honest.

### Widget
- Size: 2×1 (small), single widget type
- Tap → Opens Quick Add sheet directly
- Long press → Opens Home screen
- Display: Net total across all friends. One number. One color. Nothing else.

## Explicit Non-Goals
- No cloud sync or auth
- No multi-currency
- No group splits (log per person individually)
- No payment integration
- No notifications or reminders
- No edit transaction (delete + re-add only)
- No export or backup
- No iOS

## Success Criteria
Used instead of WhatsApp notes within one week. Friends ask for it. Splitwise never opened for sub-₹500 things again.
