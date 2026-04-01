package com.ledge.ui.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ledge.data.model.Transaction
import com.ledge.data.repository.LedgeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LedgerDetailViewModel @Inject constructor(
    private val repository: LedgeRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val friendId: Long = savedStateHandle["friendId"]!!

    val transactions = repository.transactionsFor(friendId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val netBalance = repository.netPerFriend.map { nets ->
        nets.find { it.friendId == friendId }?.net ?: 0L
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0L)

    fun deleteTransaction(transaction: Transaction) {
        viewModelScope.launch {
            repository.deleteTransaction(transaction)
        }
    }

    fun reInsertTransaction(transaction: Transaction) {
        viewModelScope.launch {
            repository.logTransaction(
                transaction.friendId,
                transaction.amount,
                transaction.direction,
                transaction.note
            )
        }
    }
}
