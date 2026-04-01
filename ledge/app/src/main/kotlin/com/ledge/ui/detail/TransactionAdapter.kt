package com.ledge.ui.detail

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.ledge.R
import com.ledge.data.model.Direction
import com.ledge.data.model.Transaction
import com.ledge.databinding.ItemTransactionBinding
import com.ledge.ui.home.FriendAdapter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class TransactionAdapter : ListAdapter<Transaction, TransactionAdapter.ViewHolder>(DIFF) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemTransactionBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ViewHolder(private val binding: ItemTransactionBinding) :
        RecyclerView.ViewHolder(binding.root) {

        private val dateFormat = SimpleDateFormat("dd MMM, hh:mm a", Locale.getDefault())

        fun bind(txn: Transaction) {
            val context = binding.root.context
            val isGave = txn.direction == Direction.GAVE
            val sign = if (isGave) "+" else "-"
            val formatted = FriendAdapter.formatPaise(if (isGave) txn.amount else -txn.amount)

            binding.txnAmount.text = formatted
            binding.txnAmount.setTextColor(
                ContextCompat.getColor(
                    context,
                    if (isGave) R.color.green_positive else R.color.red_negative
                )
            )

            binding.txnDirection.text = if (isGave) "↑ Gave" else "↓ Owe"
            binding.txnDirection.setTextColor(
                ContextCompat.getColor(
                    context,
                    if (isGave) R.color.green_positive else R.color.red_negative
                )
            )

            binding.txnDate.text = dateFormat.format(Date(txn.createdAt))

            binding.txnNote.isVisible = !txn.note.isNullOrEmpty()
            binding.txnNote.text = txn.note
        }
    }

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<Transaction>() {
            override fun areItemsTheSame(a: Transaction, b: Transaction) = a.id == b.id
            override fun areContentsTheSame(a: Transaction, b: Transaction) = a == b
        }
    }
}
