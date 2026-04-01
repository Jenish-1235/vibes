package com.ledge.ui.home

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.ledge.R
import com.ledge.data.model.FriendWithBalance
import com.ledge.databinding.ItemFriendBinding

class FriendAdapter(
    private val onClick: (FriendWithBalance) -> Unit
) : ListAdapter<FriendWithBalance, FriendAdapter.ViewHolder>(DIFF) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemFriendBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(private val binding: ItemFriendBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: FriendWithBalance) {
            binding.friendName.text = item.friend.name
            val net = item.net
            val context = binding.root.context

            val formatted = formatPaise(net)
            binding.friendBalance.text = formatted

            val colorRes = when {
                net > 0 -> R.color.green_positive
                net < 0 -> R.color.red_negative
                else -> R.color.text_secondary
            }
            binding.friendBalance.setTextColor(ContextCompat.getColor(context, colorRes))

            binding.root.setOnClickListener { onClick(item) }
        }
    }

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<FriendWithBalance>() {
            override fun areItemsTheSame(a: FriendWithBalance, b: FriendWithBalance) =
                a.friend.id == b.friend.id

            override fun areContentsTheSame(a: FriendWithBalance, b: FriendWithBalance) = a == b
        }

        fun formatPaise(paise: Long): String {
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
