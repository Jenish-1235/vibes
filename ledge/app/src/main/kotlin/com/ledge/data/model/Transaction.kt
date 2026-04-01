package com.ledge.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "transactions",
    foreignKeys = [
        ForeignKey(
            entity = Friend::class,
            parentColumns = ["id"],
            childColumns = ["friendId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("friendId")]
)
data class Transaction(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val friendId: Long,
    val amount: Long,           // stored in paise, no floating point
    val direction: Direction,   // GAVE | OWE
    val note: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)

enum class Direction { GAVE, OWE }
