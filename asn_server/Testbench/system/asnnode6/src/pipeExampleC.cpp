#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdio.h>
#define MAX_BUF 1024

#include <alsa/asoundlib.h>
#include "hal.hpp"


#include <syslog.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <iostream>

volatile sig_atomic_t flag = 0;

typedef void (*sighandler_t)(int);
static sighandler_t handle_signal (int sig_nr, sighandler_t signalhandler) {
   struct sigaction neu_sig, alt_sig;
   neu_sig.sa_handler = signalhandler;
   sigemptyset (&neu_sig.sa_mask);
   neu_sig.sa_flags = SA_RESTART;
   if (sigaction (sig_nr, &neu_sig, &alt_sig) < 0)
      return SIG_ERR;
   return alt_sig.sa_handler;
}

void interrupt_handler(int s){
	   flag = 1; 
} 

int main(int argc, char *argv[])
{
    int input;
    int output;
    int param;
    int log;
    int optind;
        printf("size inputs = %d\n",argc);
    for (optind = 1; optind < argc; optind++) {
        if (argv[optind][0] == '-'){

        switch (argv[optind][1]) {
        case 'i': input = atoi(argv[optind+1]); break;
        case 'o': output = atoi( argv[optind+1]); break;
        case 'p': param = atoi(argv[optind+1]); break;
        }   
      }
    }   

        printf("input Pipe=%d\n",input);
        printf("output Pipe=%d\n",output);

/******** End Input Arguments ********/
   long length;
   int fh;
   int buffer[10];
   FILE *fp;
   int packetSize;
   packetSize = 1024;
   int floatValue[packetSize];
   int maxpacketNr = 5;
/******** End Pipe Arguments *********/

        hal* rpihal = new hal("hw:0");	
	
	// Signal handling
	signal(SIGCHLD, SIG_IGN);
	signal(SIGHUP, interrupt_handler);
	signal (SIGINT,interrupt_handler);

	/* writing to a pipe: pipe name can be configured from cmd */
        printf("Openning Pipe\n");
   	if ((fp=fdopen(output, "w")) == NULL) {
	       perror(" File was not created: ");
       	       exit(1);
   	}
        

	
	bool bRunning = true;
	size_t uiDataSize;
	
	char * pcData = new char[MEM_SIZE];
	
	while(bRunning){
	  if (flag == 1){
	     bRunning = false;      
	  }
	  
	  uiDataSize = rpihal->GetDataFrame(pcData);
	  if (uiDataSize>0){
            if(fwrite(pcData, 4, uiDataSize/4, fp) != packetSize)
    		printf("File write error.");   

	  } 
	}
	

        /* remove the FIFO */
        fclose(fp);

    return 0;
}
