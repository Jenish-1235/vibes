package com.ledge.data.db

import androidx.room.Database
import androidx.room.RoomDatabase
import com.ledge.data.model.Friend
import com.ledge.data.model.Transaction

@Database(entities = [Friend::class, Transaction::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun friendDao(): FriendDao
    abstract fun transactionDao(): TransactionDao
}
