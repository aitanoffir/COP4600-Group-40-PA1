#ifndef __HASH_TABLE_H__
#define __HASH_TABLE_H__

#include <stdint.h>
#include "rwlock.h"

// Hash table record structure
typedef struct hash_struct {
    uint32_t hash;
    char name[50];
    uint32_t salary;
    struct hash_struct *next;
} hashRecord;

// Hash table structure
typedef struct {
    hashRecord *head;
    rwlock_t lock;
} hashTable;

// Jenkins one-at-a-time hash function
uint32_t jenkins_hash(const char *key);

// Initialize the hash table
void hash_table_init(hashTable *table);

// Insert a new record into the hash table
// Returns 0 on success, -1 if duplicate exists
int hash_table_insert(hashTable *table, const char *name, uint32_t salary, int priority);

// Delete a record from the hash table
// Returns 0 on success, -1 if not found
int hash_table_delete(hashTable *table, const char *name, int priority);

// Update the salary of a record
// Returns 0 on success, -1 if not found
int hash_table_update(hashTable *table, const char *name, uint32_t new_salary, int priority);

// Search for a record in the hash table
// Returns the record if found, NULL otherwise
hashRecord* hash_table_search(hashTable *table, const char *name, int priority);

// Print all records in the hash table (sorted by hash)
void hash_table_print(hashTable *table, int priority);

// Clean up and free all memory
void hash_table_destroy(hashTable *table);

#endif // __HASH_TABLE_H__
