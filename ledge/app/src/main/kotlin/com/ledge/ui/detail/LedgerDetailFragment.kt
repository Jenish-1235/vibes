package com.ledge.ui.detail

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.ItemTouchHelper
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.snackbar.Snackbar
import com.ledge.R
import com.ledge.databinding.FragmentLedgerDetailBinding
import com.ledge.ui.home.FriendAdapter
import com.ledge.widget.LedgeWidget
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class LedgerDetailFragment : Fragment() {

    private var _binding: FragmentLedgerDetailBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LedgerDetailViewModel by viewModels()
    private val args: LedgerDetailFragmentArgs by navArgs()
    private val adapter = TransactionAdapter()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLedgerDetailBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.detailFriendName.text = args.friendName
        binding.transactionsList.layoutManager = LinearLayoutManager(requireContext())
        binding.transactionsList.adapter = adapter

        setupSwipeToDelete()

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.transactions.collect { list ->
                        adapter.submitList(list)
                        binding.emptyTransactions.isVisible = list.isEmpty()
                        binding.transactionsList.isVisible = list.isNotEmpty()
                    }
                }
                launch {
                    viewModel.netBalance.collect { net ->
                        binding.detailNetBalance.text = FriendAdapter.formatPaise(net)
                        val colorRes = when {
                            net > 0 -> R.color.green_positive
                            net < 0 -> R.color.red_negative
                            else -> R.color.text_secondary
                        }
                        binding.detailNetBalance.setTextColor(
                            ContextCompat.getColor(requireContext(), colorRes)
                        )
                    }
                }
            }
        }
    }

    private fun setupSwipeToDelete() {
        val callback = object : ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.LEFT) {
            override fun onMove(
                rv: RecyclerView, vh: RecyclerView.ViewHolder, target: RecyclerView.ViewHolder
            ) = false

            override fun onSwiped(viewHolder: RecyclerView.ViewHolder, direction: Int) {
                val position = viewHolder.adapterPosition
                val txn = adapter.currentList[position]
                viewModel.deleteTransaction(txn)
                LedgeWidget.triggerUpdate(requireContext())

                Snackbar.make(binding.root, R.string.transaction_deleted, Snackbar.LENGTH_LONG)
                    .setAction(R.string.undo) {
                        viewModel.reInsertTransaction(txn)
                        LedgeWidget.triggerUpdate(requireContext())
                    }
                    .show()
            }
        }
        ItemTouchHelper(callback).attachToRecyclerView(binding.transactionsList)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
