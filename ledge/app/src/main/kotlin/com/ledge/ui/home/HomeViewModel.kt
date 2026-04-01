package com.ledge.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ledge.data.model.Friend
import com.ledge.data.model.FriendWithBalance
import com.ledge.data.repository.LedgeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: LedgeRepository
) : ViewModel() {

    val friendsWithBalance = combine(
        repository.friends,
        repository.netPerFriend
    ) { friends, nets ->
        val netMap = nets.associate { it.friendId to it.net }
        friends.map { friend ->
            FriendWithBalance(friend, netMap[friend.id] ?: 0L)
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addFriend(name: String) {
        viewModelScope.launch {
            repository.addFriend(name.trim())
        }
    }

    fun deleteFriend(friend: Friend) {
        viewModelScope.launch {
            repository.deleteFriend(friend)
        }
    }
}
