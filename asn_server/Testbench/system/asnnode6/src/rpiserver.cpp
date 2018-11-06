/* 
  A Minimal Capture Program
  This program opens an audio interface for capture, configures it for
  stereo, 16 bit, 44.1kHz, interleaved conventional read/write
  access. Then its reads a chunk of random data from it, and exits. It
  isn't meant to be a real program.
  From on Paul David's tutorial : http://equalarea.com/paul/alsa-audio.html
  Fixes rate and buffer problems
  sudo apt-get install libasound2-dev
  gcc -o alsa-record-example -lasound alsa-record-example.c && ./alsa-record-example hw:0
*/

#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>
#include "hal.hpp"
#include <iostream>
#include <../../cpplib/ddn.hpp>
#include <stdint.h>
	   
#include <signal.h>
#include <unistd.h>
#include <limits.h>
#include <syslog.h>

#include <unistd.h>
#include <syslog.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>

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

static void start_daemon (const char *log_name) {
   int i;
   pid_t pid = fork ();
   // Kill parent process to become infant
   if (pid < 0){
      exit (EXIT_FAILURE);
   }
   if (pid > 0){
      exit (EXIT_SUCCESS);
   }
   
   // Try to become session leader
   if (setsid() < 0) {
      syslog(LOG_EMERG, "NTSND: Failed to become session leader %s", log_name);
      exit (EXIT_FAILURE);
   }
   
   signal(SIGCHLD, SIG_IGN);
   signal(SIGHUP, interrupt_handler);
   signal (SIGINT,interrupt_handler);
   
   // handle signal sighup
   // handle_signal (SIGHUP, SIG_IGN);
   // Terminate child
   pid = fork ();
   
   if (pid < 0){
      exit (EXIT_FAILURE);
   }
   if (pid > 0){
      exit (EXIT_SUCCESS);
   }
   
   umask (0);
}

	   
main (int argc, char *argv[])
{
  char hostname[HOST_NAME_MAX];
  gethostname(hostname, HOST_NAME_MAX);
  
  // Become a daemon, so kill the parents and become an infant
  openlog( "logging", LOG_PID|LOG_CONS, LOG_LOCAL0 );
  syslog(LOG_NOTICE, "NTSND: Starting NTSoundDeamon (Build %s)\n",__TIMESTAMP__);
  start_daemon ("NTSoundDeamon");
  
  
  // create new hardware abstraction layer
  hal* rpihal = new hal("hw:0");
  ddn* ddnserver = new ddn(hostname,"asn");
  char * pcData = new char[MEM_SIZE];
  uint32_t uiDataSize;
  uint32_t uiMsgNumber = 0;
  
  bool bRunning = true;
  while(bRunning){
    if (flag == 1){
      bRunning = false;      
    }
    uiDataSize = rpihal->GetDataFrame(pcData);
    if (uiDataSize>0){
      ddnserver->SendData(pcData,uiMsgNumber,uiDataSize);
      uiMsgNumber++;
    }        
  }

  delete rpihal;
  delete ddnserver;
  syslog(LOG_NOTICE, "NTSND: NTSoundDeamon retires ...");
  
}