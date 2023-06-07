#ifndef commands_h
#define commands_h

#include <sys/types.h>

void send_byte(int);
uint64_t file_size(char* filename);

void ls();
void cd();
void download();
void upload();
void sh();

typedef void (*f)();
static f command[] = {&ls, &cd, &download, &upload, &sh};

void exec_command(uint8_t index);

#endif
