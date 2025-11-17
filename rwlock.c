#include <stdio.h>
#include <stdlib.h>
#include <semaphore.h>
#include "rwlock.h"
#include "utils.h"

// Initialize the reader-writer lock
void rwlock_init(rwlock_t *rw_lock) {
    rw_lock->readers = 0;
    
    // Initialize semaphores
    // lock semaphore protects the readers counter (binary semaphore)
    if (sem_init(&rw_lock->lock, 0, 1) != 0) {
        perror("Failed to initialize lock semaphore");
        exit(1);
    }
    
    // writelock semaphore controls write access (binary semaphore)
    if (sem_init(&rw_lock->writelock, 0, 1) != 0) {
        perror("Failed to initialize writelock semaphore");
        exit(1);
    }
}

// Acquire read lock
// Multiple readers can hold read locks simultaneously
// First reader acquires the write lock to block writers
void rwlock_acquire_readlock(rwlock_t *rw_lock, int priority) {
    // Protect the readers counter
    sem_wait(&rw_lock->lock);
    
    rw_lock->readers++;
    
    // If this is the first reader, acquire the write lock
    // This prevents writers from entering while readers are active
    if (rw_lock->readers == 1) {
        sem_wait(&rw_lock->writelock);
    }
    
    sem_post(&rw_lock->lock);
    
    // Log that read lock was acquired
    log_message("THREAD %d READ LOCK ACQUIRED", priority);
}

// Release read lock
void rwlock_release_readlock(rwlock_t *rw_lock, int priority) {
    // Protect the readers counter
    sem_wait(&rw_lock->lock);
    
    rw_lock->readers--;
    
    // If this is the last reader, release the write lock
    // This allows writers to enter
    if (rw_lock->readers == 0) {
        sem_post(&rw_lock->writelock);
    }
    
    sem_post(&rw_lock->lock);
    
    // Log that read lock was released
    log_message("THREAD %d READ LOCK RELEASED", priority);
}

// Acquire write lock
// Writers need exclusive access - no readers or other writers allowed
void rwlock_acquire_writelock(rwlock_t *rw_lock, int priority) {
    // Acquire the write lock for exclusive access
    sem_wait(&rw_lock->writelock);
    
    // Log that write lock was acquired
    log_message("THREAD %d WRITE LOCK ACQUIRED", priority);
}

// Release write lock
void rwlock_release_writelock(rwlock_t *rw_lock, int priority) {
    // Release the write lock
    sem_post(&rw_lock->writelock);
    
    // Log that write lock was released
    log_message("THREAD %d WRITE LOCK RELEASED", priority);
}

// Cleanup/destroy the lock
void rwlock_destroy(rwlock_t *rw_lock) {
    sem_destroy(&rw_lock->lock);
    sem_destroy(&rw_lock->writelock);
}
