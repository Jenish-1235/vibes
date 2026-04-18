package com.ledge.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.ledge.R
import com.ledge.databinding.FragmentHomeBinding
import com.ledge.ui.quickadd.QuickAddBottomSheet
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HomeViewModel by viewModels()

    private val adapter = FriendAdapter { item ->
        val action = HomeFragmentDirections.actionHomeToDetail(
            friendId = item.friend.id,
            friendName = item.friend.name
        )
        findNavController().navigate(action)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.friendsList.layoutManager = LinearLayoutManager(requireContext())
        binding.friendsList.adapter = adapter

        binding.fabAddFriend.setOnClickListener { showAddFriendDialog() }
        binding.fabQuickAdd.setOnClickListener {
            QuickAddBottomSheet().show(parentFragmentManager, "quick_add")
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.friendsWithBalance.collect { list ->
                    adapter.submitList(list)
                    binding.emptyState.isVisible = list.isEmpty()
                    binding.friendsList.isVisible = list.isNotEmpty()
                }
            }
        }
    }

    private fun showAddFriendDialog() {
        val input = EditText(requireContext()).apply {
            hint = getString(R.string.friend_name_hint)
            setPadding(64, 32, 64, 32)
        }
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.add_friend)
            .setView(input)
            .setPositiveButton(R.string.add) { _, _ ->
                val name = input.text.toString().trim()
                if (name.isNotEmpty()) {
                    viewModel.addFriend(name)
                }
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
