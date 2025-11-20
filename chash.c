#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <stdint.h>
#include <ctype.h>      // Required for toupper()
#include "hash_table.h"
#include "utils.h"      // Logging utilities

// The project explicitly requires the command file name to be hardcoded.
#define COMMANDS_FILENAME "commands.txt" 

// --- Synchronization Primitives for Priority Ordering ---
pthread_mutex_t turn_mutex; 
pthread_cond_t turn_cond; 
int current_turn = 1; // Starts at 1 for the first thread

// --- Thread Argument Structure ---
typedef struct {
    char command[10];
    char name[50];
    uint32_t salary; 
    hashTable *table;
    int priority;    // The unique priority ID (1, 2, 3...)
} ThreadArgs;


// --- Helper Function: Priority Ordering Logic (Condition Variables) ---
void wait_and_signal_next(int my_priority) {
    // 1. Lock the mutex to check the shared condition
    pthread_mutex_lock(&turn_mutex);

    // WAIT: Wait until it's our turn (current_turn == my_priority)
    // The 'while' loop is essential to guard against spurious wakeups.
    while (current_turn != my_priority) {
        //Spin
        pthread_cond_wait(&turn_cond, &turn_mutex);
    }
    
    // SIGNAL: Increment turn counter and signal the next thread
    current_turn++;
    
    // Notify all waiting threads to re-check the new 'current_turn' value.
    pthread_cond_broadcast(&turn_cond);
    
    // 2. Unlock the mutex
    pthread_mutex_unlock(&turn_mutex);
}

// --- The Core Thread Function ---
void *thread_routine(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;
    hashTable *table = args->table;

    // 1. Enforce Priority Order
    wait_and_signal_next(args->priority);

    // 2. Execute Command
    // The command string is guaranteed to be UPPERCASE due to parsing normalization.
    if (strcmp(args->command, "INSERT") == 0) {
        hash_table_insert(table, args->name, args->salary, args->priority);
    } else if (strcmp(args->command, "DELETE") == 0) {
        hash_table_delete(table, args->name, args->priority);
    } else if (strcmp(args->command, "UPDATE") == 0) {
        hash_table_update(table, args->name, args->salary, args->priority);
    } else if (strcmp(args->command, "SEARCH") == 0) {
        hash_table_search(table, args->name, args->priority);
    } else if (strcmp(args->command, "PRINT") == 0) {
        hash_table_print(table, args->priority);
    }

    // Free the dynamically allocated arguments structure
    free(args);
    return NULL;
}

// --- Main Driver Function ---
int main(void) {
    // 1. SETUP & INITIALIZATION
    
    init_log(); 

    hashTable table;
    hash_table_init(&table);
    
    // Initialize Condition Variable Synchronization
    pthread_mutex_init(&turn_mutex, NULL);
    pthread_cond_init(&turn_cond, NULL);

    // 2. FILE READING AND COMMAND PARSING (Using hardcoded filename)
    FILE *fp = fopen(COMMANDS_FILENAME, "r");
    if (!fp) {
        fprintf(stderr, "Error: Failed to open %s. Please ensure the file is in the current directory.\n", COMMANDS_FILENAME);
        close_log();
        return 1;
    }

    char line[1024];
    ThreadArgs **all_args = NULL; 
    pthread_t *threads = NULL;    
    int command_count = 0;
    
    // Read the file line by line
    while (fgets(line, sizeof(line), fp)) {
        // Skip empty lines or configuration lines (e.g., "threads,60,0")
        if (line[0] == '\n' || line[0] == '\r' || strspn(line, " \t\n\r") == strlen(line) || strncmp(line, "threads", 7) == 0) {
            continue;
        }

        // Allocate memory for the new command's arguments and thread ID
        all_args = realloc(all_args, (command_count + 1) * sizeof(ThreadArgs *));
        threads = realloc(threads, (command_count + 1) * sizeof(pthread_t));
        
        ThreadArgs *args = (ThreadArgs *)malloc(sizeof(ThreadArgs));
        if (!args || !all_args || !threads) {
            perror("Memory allocation failed");
            // NOTE: Robust error handling would clean up all threads/memory here
            return 1;
        }
        
        args->table = &table;
        args->priority = command_count + 1; // Priority is 1-indexed
        
        char name_buffer[50];
        uint32_t salary_buffer = 0;
        
        // sscanf to parse: COMMAND,Name,Salary. %*[^\n] is used to discard any extra fields on the line.
        int items_read = sscanf(line, "%[^,],%[^,],%u%*[^\n]", 
                                args->command, name_buffer, &salary_buffer);
        
        // FIX: CONVERT COMMAND TO UPPERCASE FOR NORMALIZATION
        for (int i = 0; args->command[i]; i++) {
            args->command[i] = toupper((unsigned char)args->command[i]);
        }

        // Standardize input based on command type
        if (items_read >= 2) {
            strncpy(args->name, name_buffer, 50);
            args->name[49] = '\0';
        } else {
            args->name[0] = '\0'; 
        }
        
        if (items_read == 3) {
            args->salary = salary_buffer;
        } else {
            args->salary = 0;
        }
        
        all_args[command_count] = args;
        command_count++;
    }
    
    fclose(fp);
    
    // 3. THREAD CREATION AND EXECUTION
    printf("Starting %d threads from %s...\n", command_count, COMMANDS_FILENAME);
    
    for (int i = 0; i < command_count; i++) {
        if (pthread_create(&threads[i], NULL, thread_routine, all_args[i]) != 0) {
            perror("Failed to create thread");
            return 1;
        }
    }

    // 4. WAIT FOR THREADS TO COMPLETE
    for (int i = 0; i < command_count; i++) {
        pthread_join(threads[i], NULL);
    }

    // 5. FINAL CLEANUP
    printf("All threads finished. Final database state:\n");
    hash_table_print(&table, 0); 
    
    hash_table_destroy(&table);
    pthread_mutex_destroy(&turn_mutex);
    pthread_cond_destroy(&turn_cond);
    free(threads);
    
    close_log();
    
    return 0;
}
