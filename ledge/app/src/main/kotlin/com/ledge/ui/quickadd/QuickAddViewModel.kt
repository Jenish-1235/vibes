package com.ledge.ui.quickadd

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ledge.data.model.Direction
import com.ledge.data.repository.LedgeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class QuickAddViewModel @Inject constructor(
    private val repository: LedgeRepository
) : ViewModel() {

    val friends = repository.friends
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun logTransactionForMultiple(
        friendIds: List<Long>,
        amountPaise: Long,
        direction: Direction,
        note: String?,
        onDone: (friendNames: List<String>) -> Unit
    ) {
        viewModelScope.launch {
            val friendMap = friends.value.associate { it.id to it.name }
            for (id in friendIds) {
                repository.logTransaction(id, amountPaise, direction, note)
            }
            val names = friendIds.mapNotNull { friendMap[it] }
            onDone(names)
        }
    }
}
