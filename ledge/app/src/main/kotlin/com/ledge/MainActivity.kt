package com.ledge

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.ledge.ui.quickadd.QuickAddBottomSheet
import com.ledge.widget.LedgeWidget
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        handleQuickAddIntent(intent)
        LedgeWidget.triggerUpdate(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleQuickAddIntent(intent)
    }

    private fun handleQuickAddIntent(intent: Intent?) {
        if (intent?.action == LedgeWidget.ACTION_OPEN_QUICK_ADD) {
            QuickAddBottomSheet().show(supportFragmentManager, "quick_add")
        }
    }
}
