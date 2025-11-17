#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <sys/time.h>
#include "utils.h"

// Global log file pointer
FILE *log_file = NULL;

// Get current timestamp in microseconds
long long current_timestamp() {
    struct timeval te;
    gettimeofday(&te, NULL); // get current time
    long long microseconds = (te.tv_sec * 1000000LL) + te.tv_usec;
    return microseconds;
}

// Initialize the log file
void init_log() {
    log_file = fopen("hash.log", "w");
    if (!log_file) {
        perror("Failed to open hash.log");
        exit(1);
    }
}

// Log a message with timestamp to hash.log
void log_message(const char *format, ...) {
    if (!log_file) {
        fprintf(stderr, "Error: Log file not initialized\n");
        return;
    }
    
    // Write timestamp
    fprintf(log_file, "%lld: ", current_timestamp());
    
    // Write the formatted message
    va_list args;
    va_start(args, format);
    vfprintf(log_file, format, args);
    va_end(args);
    
    // Add newline
    fprintf(log_file, "\n");
    
    // Flush to ensure immediate write
    fflush(log_file);
}

// Close the log file
void close_log() {
    if (log_file) {
        fclose(log_file);
        log_file = NULL;
    }
}
