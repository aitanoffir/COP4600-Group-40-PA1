#ifndef __UTILS_H__
#define __UTILS_H__

#include <stdio.h>

// Get current timestamp in microseconds
long long current_timestamp();

// Initialize the log file (hash.log)
void init_log();

// Log a message to hash.log with timestamp
void log_message(const char *format, ...);

// Close the log file
void close_log();

// Global log file pointer (defined in utils.c)
extern FILE *log_file;

#endif // __UTILS_H__
