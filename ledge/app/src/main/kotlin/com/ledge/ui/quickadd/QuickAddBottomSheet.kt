package com.ledge.ui.quickadd

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.google.android.material.chip.Chip
import com.google.android.material.snackbar.Snackbar
import com.ledge.R
import com.ledge.data.model.Direction
import com.ledge.data.model.Friend
import com.ledge.databinding.SheetQuickAddBinding
import com.ledge.ui.home.FriendAdapter
import com.ledge.widget.LedgeWidget
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class QuickAddBottomSheet : BottomSheetDialogFragment() {

    private var _binding: SheetQuickAddBinding? = null
    private val binding get() = _binding!!
    private val viewModel: QuickAddViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = SheetQuickAddBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.btnGave.setOnClickListener { submit(Direction.GAVE) }
        binding.btnOwe.setOnClickListener { submit(Direction.OWE) }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.friends.collect { friends ->
                    populateChips(friends)
                }
            }
        }

        binding.amountInput.requestFocus()
    }

    private fun populateChips(friends: List<Friend>) {
        binding.chipGroupFriends.removeAllViews()
        friends.forEach { friend ->
            val chip = Chip(requireContext()).apply {
                text = friend.name
                isCheckable = true
                tag = friend.id
            }
            binding.chipGroupFriends.addView(chip)
        }
        if (friends.size == 1) {
            (binding.chipGroupFriends.getChildAt(0) as? Chip)?.isChecked = true
        }
    }

    private fun getSelectedFriendIds(): List<Long> {
        val ids = mutableListOf<Long>()
        for (i in 0 until binding.chipGroupFriends.childCount) {
            val chip = binding.chipGroupFriends.getChildAt(i) as? Chip ?: continue
            if (chip.isChecked) {
                ids.add(chip.tag as Long)
            }
        }
        return ids
    }

    private fun submit(direction: Direction) {
        val selectedIds = getSelectedFriendIds()
        if (selectedIds.isEmpty()) return

        val amountText = binding.amountInput.text.toString().trim()
        if (amountText.isEmpty()) return

        val amountPaise = parseToPaise(amountText) ?: return
        if (amountPaise <= 0) return

        val note = binding.noteInput.text?.toString()?.trim()?.ifEmpty { null }

        viewModel.logTransactionForMultiple(selectedIds, amountPaise, direction, note) { names ->
            activity?.let { act ->
                val formatted = FriendAdapter.formatPaise(amountPaise)
                val namesStr = names.joinToString(", ")
                Snackbar.make(
                    act.findViewById(android.R.id.content),
                    getString(R.string.logged_snackbar, formatted.removePrefix("+"), namesStr),
                    Snackbar.LENGTH_SHORT
                ).show()
            }
            LedgeWidget.triggerUpdate(requireContext())
            dismiss()
        }
    }

    private fun parseToPaise(text: String): Long? {
        return try {
            val parts = text.split(".")
            val rupees = parts[0].toLongOrNull() ?: return null
            val paise = if (parts.size > 1) {
                val p = parts[1].take(2).padEnd(2, '0')
                p.toLongOrNull() ?: 0L
            } else 0L
            rupees * 100 + paise
        } catch (_: Exception) {
            null
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
