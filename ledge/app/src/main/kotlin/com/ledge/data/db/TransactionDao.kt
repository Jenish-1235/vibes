package com.ledge.data.db

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.Query
import com.ledge.data.model.FriendNet
import com.ledge.data.model.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface TransactionDao {
    @Query("SELECT * FROM transactions WHERE friendId = :friendId ORDER BY createdAt DESC")
    fun getTransactionsForFriend(friendId: Long): Flow<List<Transaction>>

    @Query("""
        SELECT friendId,
               SUM(CASE WHEN direction = 'GAVE' THEN amount ELSE -amount END) as net
        FROM transactions GROUP BY friendId
    """)
    fun getNetPerFriend(): Flow<List<FriendNet>>

    @Query("""
        SELECT SUM(CASE WHEN direction = 'GAVE' THEN amount ELSE -amount END)
        FROM transactions
    """)
    fun getNetTotal(): Flow<Long?>

    @Insert
    suspend fun insert(transaction: Transaction)

    @Query("""
        SELECT SUM(CASE WHEN direction = 'GAVE' THEN amount ELSE -amount END)
        FROM transactions
    """)
    suspend fun getNetTotalSync(): Long?

    @Delete
    suspend fun delete(transaction: Transaction)
}
