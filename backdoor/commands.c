#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dirent.h>
#include <unistd.h>
#include <string.h>
#include <sys/sendfile.h>
#include <sys/stat.h>

#define BUFFER_SIZE 1024

#include "commands.h"

void exec_command(uint8_t index) { command[index](); }

uint64_t file_size(char* filename) {
    struct stat st;
    stat(filename, &st);
    return st.st_size;
}

void send_byte(int byte) {
    printf("%c", byte);
    fflush(0);
}


void ls() {
    struct dirent *de;
    DIR *dr = opendir(".");
    if (dr == NULL) {
        send_byte(0);
        return;
    }

    while ((de = readdir(dr)) != NULL)
        printf("%c%s",  strlen(de->d_name), de->d_name);
    closedir(dr);
    send_byte(0);  // end of list
}

void cd() {
    uint8_t path_length;
    char path[256];
    read(0, &path_length, 1);
    read(0, &path, path_length);
    path[path_length] = 0;
    chdir(path);
}

void download() {
    uint8_t path_length;
    char filename[256];
    read(0, &path_length, 1);
    read(0, &filename, path_length);
    filename[path_length] = 0;

    FILE* file = fopen(filename, "r");
    if (!file) {
        send_byte(0);
        return;
    }
    uint64_t size = file_size(filename);
    write(1, &size, 8);
    if (sendfile(1, fileno(file), 0, size) < 0) perror("sendfile");
    fflush(0);
    fclose(file);
}

void upload() {
    uint8_t path_length;
    char filename[256];
    read(0, &path_length, 1);
    read(0, &filename, path_length);
    filename[path_length] = 0;

    FILE* file = fopen(filename, "w");
    if (!file) {
        send_byte(0);  // fail
        return;
    } else {
        send_byte(1);  // success
    }

    uint64_t size;
    read(0, &size, 8);

    char buffer[BUFFER_SIZE];
    int received;
    while (size > 0) {
        received = read(0, buffer, BUFFER_SIZE);
        fwrite(buffer, sizeof(char), received, file);
        size -= received;
    }
    fclose(file);
}

void sh() {
    uint8_t command_length;
    char command[256];
    read(0, &command_length, 1);
    read(0, &command, command_length);
    command[command_length] = 0;
    system(command);
    send_byte(0x4); // end of transmission
}
