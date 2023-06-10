#ifndef commands_h
#define commands_h

#include <sys/types.h>

void send_byte(int);
uint64_t file_size(char* filename);

void terminate();
void ls();
void cd();
void download();
void upload();
void sh();
void execute();

typedef void (*f)();
static f command[] = {&terminate, &ls, &cd, &download, &upload, &sh, &execute};

void exec_command(uint8_t index);

#endif
