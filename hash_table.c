#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hash_table.h"
#include "utils.h"

// Jenkins one-at-a-time hash function
uint32_t jenkins_hash(const char *key) {
    uint32_t hash = 0;
    size_t len = strlen(key);
    
    for (size_t i = 0; i < len; i++) {
        hash += key[i];
        hash += (hash << 10);
        hash ^= (hash >> 6);
    }
    
    hash += (hash << 3);
    hash ^= (hash >> 11);
    hash += (hash << 15);
    
    return hash;
}

// Initialize the hash table
void hash_table_init(hashTable *table) {
    table->head = NULL;
    rwlock_init(&table->lock);
}

// Insert a new record into the hash table
int hash_table_insert(hashTable *table, const char *name, uint32_t salary, int priority) {
    uint32_t hash = jenkins_hash(name);
    
    log_message("THREAD %d INSERT,%u,%s,%u", priority, hash, name, salary);
    
    // Acquire write lock
    rwlock_acquire_writelock(&table->lock, priority);
    
    // Check if entry already exists
    hashRecord *current = table->head;
    while (current != NULL) {
        if (current->hash == hash) {
            // Duplicate found
            rwlock_release_writelock(&table->lock, priority);
            printf("Insert failed. Entry %u is a duplicate.\n", hash);
            return -1;
        }
        current = current->next;
    }
    
    // Create new record
    hashRecord *new_record = (hashRecord *)malloc(sizeof(hashRecord));
    if (!new_record) {
        perror("Failed to allocate memory for new record");
        rwlock_release_writelock(&table->lock, priority);
        return -1;
    }
    
    new_record->hash = hash;
    strncpy(new_record->name, name, 49);
    new_record->name[49] = '\0';
    new_record->salary = salary;
    new_record->next = table->head;
    table->head = new_record;
    
    // Release write lock
    rwlock_release_writelock(&table->lock, priority);
    
    printf("Inserted %u,%s,%u\n", hash, name, salary);
    return 0;
}

// Delete a record from the hash table
int hash_table_delete(hashTable *table, const char *name, int priority) {
    uint32_t hash = jenkins_hash(name);
    
    log_message("THREAD %d DELETE,%u,%s", priority, hash, name);
    
    // Acquire write lock
    rwlock_acquire_writelock(&table->lock, priority);
    
    hashRecord *current = table->head;
    hashRecord *prev = NULL;
    
    // Search for the record
    while (current != NULL) {
        if (current->hash == hash) {
            // Found - remove it
            if (prev == NULL) {
                // First node
                table->head = current->next;
            } else {
                prev->next = current->next;
            }
            
            printf("Deleted record for %u,%s,%u\n", current->hash, current->name, current->salary);
            free(current);
            
            rwlock_release_writelock(&table->lock, priority);
            return 0;
        }
        prev = current;
        current = current->next;
    }
    
    // Not found
    rwlock_release_writelock(&table->lock, priority);
    printf("Entry %u not deleted. Not in database.\n", hash);
    return -1;
}

// Update the salary of a record
int hash_table_update(hashTable *table, const char *name, uint32_t new_salary, int priority) {
    uint32_t hash = jenkins_hash(name);
    
    log_message("THREAD %d UPDATE,%u,%s,%u", priority, hash, name, new_salary);
    
    // Acquire write lock
    rwlock_acquire_writelock(&table->lock, priority);
    
    hashRecord *current = table->head;
    
    // Search for the record
    while (current != NULL) {
        if (current->hash == hash) {
            // Found - update it
            uint32_t old_salary = current->salary;
            current->salary = new_salary;
            
            printf("Updated record %u from %u,%s,%u to %u,%s,%u\n",
                   hash, hash, name, old_salary, hash, name, new_salary);
            
            rwlock_release_writelock(&table->lock, priority);
            return 0;
        }
        current = current->next;
    }
    
    // Not found
    rwlock_release_writelock(&table->lock, priority);
    printf("Update failed. Entry %u not found.\n", hash);
    return -1;
}

// Search for a record in the hash table
hashRecord* hash_table_search(hashTable *table, const char *name, int priority) {
    uint32_t hash = jenkins_hash(name);
    
    log_message("THREAD %d SEARCH,%u,%s", priority, hash, name);
    
    // Acquire read lock
    rwlock_acquire_readlock(&table->lock, priority);
    
    hashRecord *current = table->head;
    hashRecord *result = NULL;
    
    // Search for the record
    while (current != NULL) {
        if (current->hash == hash) {
            result = current;
            break;
        }
        current = current->next;
    }
    
    // Release read lock
    rwlock_release_readlock(&table->lock, priority);
    
    // Print result
    if (result) {
        printf("Found: %u,%s,%u\n", result->hash, result->name, result->salary);
    } else {
        printf("%s not found.\n", name);
    }
    
    return result;
}

// Comparison function for qsort
static int compare_records(const void *a, const void *b) {
    const hashRecord *rec_a = *(const hashRecord **)a;
    const hashRecord *rec_b = *(const hashRecord **)b;
    
    if (rec_a->hash < rec_b->hash) return -1;
    if (rec_a->hash > rec_b->hash) return 1;
    return 0;
}

// Print all records in the hash table (sorted by hash)
void hash_table_print(hashTable *table, int priority) {
    log_message("THREAD %d PRINT", priority);
    
    // Acquire read lock
    rwlock_acquire_readlock(&table->lock, priority);
    
    // Count records
    int count = 0;
    hashRecord *current = table->head;
    while (current != NULL) {
        count++;
        current = current->next;
    }
    
    if (count == 0) {
        printf("Current Database:\n(empty)\n");
        rwlock_release_readlock(&table->lock, priority);
        return;
    }
    
    // Create array of pointers for sorting
    hashRecord **records = (hashRecord **)malloc(count * sizeof(hashRecord *));
    if (!records) {
        perror("Failed to allocate memory for sorting");
        rwlock_release_readlock(&table->lock, priority);
        return;
    }
    
    // Fill array
    current = table->head;
    for (int i = 0; i < count; i++) {
        records[i] = current;
        current = current->next;
    }
    
    // Sort by hash
    qsort(records, count, sizeof(hashRecord *), compare_records);
    
    // Print sorted records
    printf("Current Database:\n");
    for (int i = 0; i < count; i++) {
        printf("%u,%s,%u\n", records[i]->hash, records[i]->name, records[i]->salary);
    }
    
    free(records);
    
    // Release read lock
    rwlock_release_readlock(&table->lock, priority);
}

// Clean up and free all memory
void hash_table_destroy(hashTable *table) {
    hashRecord *current = table->head;
    hashRecord *next;
    
    while (current != NULL) {
        next = current->next;
        free(current);
        current = next;
    }
    
    rwlock_destroy(&table->lock);
}