#ifndef __RWLOCK_H__
#define __RWLOCK_H__

#include <semaphore.h>

// Reader-Writer Lock Structure
typedef struct _rwlock_t {
    sem_t writelock;    // Semaphore for write lock
    sem_t lock;         // Semaphore for protecting readers counter
    int readers;        // Count of active readers
} rwlock_t;

// Initialize the reader-writer lock
void rwlock_init(rwlock_t *rw_lock);

// Acquire read lock (multiple readers allowed)
void rwlock_acquire_readlock(rwlock_t *rw_lock, int priority);

// Release read lock
void rwlock_release_readlock(rwlock_t *rw_lock, int priority);

// Acquire write lock (exclusive access)
void rwlock_acquire_writelock(rwlock_t *rw_lock, int priority);

// Release write lock
void rwlock_release_writelock(rwlock_t *rw_lock, int priority);

// Destroy/cleanup the lock (optional, for good practice)
void rwlock_destroy(rwlock_t *rw_lock);

#endif // __RWLOCK_H__
