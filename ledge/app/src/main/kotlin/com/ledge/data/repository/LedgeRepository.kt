package com.ledge.data.repository

import com.ledge.data.db.FriendDao
import com.ledge.data.db.TransactionDao
import com.ledge.data.model.Direction
import com.ledge.data.model.Friend
import com.ledge.data.model.FriendNet
import com.ledge.data.model.Transaction
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LedgeRepository @Inject constructor(
    private val friendDao: FriendDao,
    private val transactionDao: TransactionDao
) {
    val friends: Flow<List<Friend>> = friendDao.getAllFriends()
    val netPerFriend: Flow<List<FriendNet>> = transactionDao.getNetPerFriend()
    val netTotal: Flow<Long?> = transactionDao.getNetTotal()

    fun transactionsFor(friendId: Long): Flow<List<Transaction>> =
        transactionDao.getTransactionsForFriend(friendId)

    suspend fun addFriend(name: String): Long =
        friendDao.insert(Friend(name = name))

    suspend fun deleteFriend(friend: Friend) =
        friendDao.delete(friend)

    suspend fun logTransaction(friendId: Long, amount: Long, direction: Direction, note: String?) =
        transactionDao.insert(
            Transaction(friendId = friendId, amount = amount, direction = direction, note = note)
        )

    suspend fun deleteTransaction(transaction: Transaction) =
        transactionDao.delete(transaction)
}
