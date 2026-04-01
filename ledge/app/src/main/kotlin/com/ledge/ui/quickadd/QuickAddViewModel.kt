package com.ledge.ui.quickadd

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ledge.data.model.Direction
import com.ledge.data.model.Friend
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

    fun logTransaction(
        friendId: Long,
        amountPaise: Long,
        direction: Direction,
        note: String?,
        onDone: (friendName: String) -> Unit
    ) {
        viewModelScope.launch {
            repository.logTransaction(friendId, amountPaise, direction, note)
            val friendName = friends.value.find { it.id == friendId }?.name ?: ""
            onDone(friendName)
        }
    }
}
