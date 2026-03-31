package com.ledge.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import androidx.core.content.ContextCompat
import androidx.room.Room
import com.ledge.MainActivity
import com.ledge.R
import com.ledge.data.db.AppDatabase
import kotlinx.coroutines.runBlocking

class LedgeWidget : AppWidgetProvider() {

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        appWidgetIds.forEach { widgetId ->
            updateWidget(context, appWidgetManager, widgetId)
        }
    }

    companion object {
        const val ACTION_OPEN_QUICK_ADD = "com.ledge.OPEN_QUICK_ADD"

        fun triggerUpdate(context: Context) {
            val manager = AppWidgetManager.getInstance(context)
            val ids = manager.getAppWidgetIds(
                ComponentName(context, LedgeWidget::class.java)
            )
            val intent = Intent(context, LedgeWidget::class.java).apply {
                action = AppWidgetManager.ACTION_APPWIDGET_UPDATE
                putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, ids)
            }
            context.sendBroadcast(intent)
        }

        private fun updateWidget(
            context: Context,
            manager: AppWidgetManager,
            widgetId: Int
        ) {
            val views = RemoteViews(context.packageName, R.layout.widget_ledge)

            // Fetch net total synchronously (widget updates run briefly)
            val netTotal = try {
                val db = Room.databaseBuilder(
                    context.applicationContext, AppDatabase::class.java, "ledge.db"
                ).build()
                val total = runBlocking {
                    db.transactionDao().getNetTotalSync()
                }
                db.close()
                total ?: 0L
            } catch (_: Exception) {
                0L
            }

            val formatted = formatPaiseWidget(netTotal)
            views.setTextViewText(R.id.widget_amount, formatted)

            val color = when {
                netTotal > 0 -> ContextCompat.getColor(context, R.color.green_positive)
                netTotal < 0 -> ContextCompat.getColor(context, R.color.red_negative)
                else -> ContextCompat.getColor(context, R.color.text_secondary)
            }
            views.setTextColor(R.id.widget_amount, color)

            // Tap → Quick Add
            val tapIntent = PendingIntent.getActivity(
                context, 0,
                Intent(context, MainActivity::class.java).apply {
                    action = ACTION_OPEN_QUICK_ADD
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                },
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_root, tapIntent)

            manager.updateAppWidget(widgetId, views)
        }

        private fun formatPaiseWidget(paise: Long): String {
            val absAmount = kotlin.math.abs(paise)
            val rupees = absAmount / 100
            val paisePart = absAmount % 100
            val sign = when {
                paise > 0 -> "+"
                paise < 0 -> "-"
                else -> ""
            }
            return if (paisePart == 0L) {
                "${sign}₹$rupees"
            } else {
                "${sign}₹$rupees.${paisePart.toString().padStart(2, '0')}"
            }
        }
    }
}
