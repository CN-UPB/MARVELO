// ---------------------------------------------------------------------------
// (c) 2017 by
// University of Paderborn,
// Department of electrical engineering and information technology,
// Pohlweg 47-49,
// D-33098 Paderborn,
// Germany/Allemagne
//
// URL: http://nt.uni-paderborn.de
//
// We provide absolute NO WARRANTY for this code. Use it on your own risk!
// Please report any bugs to: spark@nt.upb.de
// ---------------------------------------------------------------------------

#ifndef PIPEINTERFACE_HPP
#define PIPEINTERFACE_HPP

#include "stdint.h"
#include <pthread.h>
#include <vector>
#include <string>

// Definition of constants
#define MAX_BUFFER_SIZE 20000 // Maximum buffer size for one packet to be transported via udp
#define MIN_MESSAGE_SIZE 6 //

// Protocol Messages
#define MAX_MESSAGE_MEMORY 50

typedef struct {
  //! Thread id of data server thread (responsible for communication with nodes / receiving data)
  pthread_t *thread_id_Server;
  //! Mutexguarding all communication between threads and class
  pthread_mutex_t *ServerCommMutex; 
  //! Conditional signal for waiting: Occures if new data becomes available
  pthread_cond_t * CondSignalData;
  //! running flag for data server thread
  bool bRunningServer;
  const char * pcPipeName;
  uint32_t uiBytesPerFrame;
  //! Message Memory as FIFO
  char ** MessageFIFO;
  //! Amount of data on stack
  uint32_t uiMessagesOnStack;
} threadinfo_t;

class pipeinterface {
  
public:
  //! Constructor of class
  pipeinterface();
      
    
  //! Constructor of class
  pipeinterface(const char* p_pcPipeName, uint32_t p_uiBytesPerFrame);
  
  //! Destructor of class: Clean up of memory and nice killing of threads
  ~pipeinterface();

  //! Get data from receiver stack with optional waiting (WaitSeconds=0 means immediate return)
  uint32_t GetDataWithTimeout(char* p_pcData, uint32_t p_uiTimeToWaitSeconds);
  
protected:
  //! Entry point for starting the Server Thread
  static void *EntryPointServer(void *);
  //! Entry point for starting the Node Discovery Thread
  static void *EntryPointDiscovery(void *);  
    
private:

  //! object class struct hosting all information about the threads (is distributed to all threads)
  threadinfo_t threadinfo;
  
  //! Our receiver/sender buffer: only used by public methods to send data/commands via the m_iSendSocket
  char * m_RxTxBuffer;
  
  //! Server Thread ID
  pthread_t mServerId;
  //! static method to start server thread
  static void RunServerThread(void *p_threadinfo);
  //! Conditional signal to wait for data (gently sleep)
  pthread_cond_t *mCondSignalData;
  // Mutex to guard all communication/interaction on common variable between class and threads
  pthread_mutex_t * mServerCommMutex;
  //! Get a message from the fifo
  uint32_t FrontPopMessageFIFO(threadinfo_t* TInfo, char* p_pcData);
};

#endif