package com.ledge.data.db

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.Query
import com.ledge.data.model.Friend
import kotlinx.coroutines.flow.Flow

@Dao
interface FriendDao {
    @Query("SELECT * FROM friends ORDER BY name ASC")
    fun getAllFriends(): Flow<List<Friend>>

    @Insert
    suspend fun insert(friend: Friend): Long

    @Delete
    suspend fun delete(friend: Friend)
}
