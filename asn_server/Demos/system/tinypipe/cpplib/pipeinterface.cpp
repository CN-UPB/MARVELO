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

#include "pipeinterface.hpp"
#include <cstring>
#include <strings.h>
#include <stdio.h>
#include <iostream>
#include <pthread.h>
#include <unistd.h>
#include <sys/time.h>
#include <cstdio>
#include <fcntl.h>

#include <cmath>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdio.h>

// Definition of inline helper functions for speedup and thread security


//! Function to drop move all messages on stack up front and drop first one
inline uint32_t ShiftFIFO(char ** MessageFIFO, uint32_t p_msgOnStack){
  uint32_t DataLength=0;
  for (uint32_t k=1; k<p_msgOnStack; ++k){
    // Get the size of Data in the FIFO slot FIFO[k] = [Size, Data];
    DataLength = 0;
    memcpy(reinterpret_cast<char*>(&DataLength), MessageFIFO[k] ,4);
    // move the data upfront if size makes sense
    if ((DataLength>MIN_MESSAGE_SIZE)&&(DataLength<MAX_BUFFER_SIZE)){
	memcpy(MessageFIFO[k-1],MessageFIFO[k] ,DataLength+4);
    }else{
        std::cout << "Data on stack corrupted: Size" << DataLength << " exeeeds ["<< MIN_MESSAGE_SIZE << ", "<<MAX_BUFFER_SIZE<< "]" << std::endl;
    }
  }
   return (p_msgOnStack-1);
}

//! Function to push data to back of FIFO, drops data if full
inline uint32_t PushBackFIFO(char ** MessageFIFO, uint32_t p_msgOnStack, char * p_pcData, uint32_t p_DataLength){
  uint32_t DataLength=p_DataLength;
  // Check if full, if yes drop
  if (p_msgOnStack>=MAX_MESSAGE_MEMORY){
     // std::cout << "ERROR - Buffer full -> Drop Data" << std::endl;
     p_msgOnStack = ShiftFIFO(MessageFIFO, p_msgOnStack); // we drop the first (oldest) one
  }
  // Add new data
  memcpy(MessageFIFO[ p_msgOnStack], reinterpret_cast<char*>(&DataLength),4);
  memcpy(&MessageFIFO[ p_msgOnStack][4],p_pcData ,p_DataLength);
  return (p_msgOnStack+1);
}

pipeinterface::pipeinterface(){
};

//! standard Constructor of class
pipeinterface::pipeinterface(const char* p_pcPipeName, uint32_t p_uiBytesPerFrame){
   
  // create Server
  mServerCommMutex = new pthread_mutex_t();
  pthread_mutex_init(mServerCommMutex, NULL);
  mCondSignalData = new pthread_cond_t();
  pthread_cond_init(mCondSignalData,NULL);

  // store all information in threadinfo and share it with threads  
  threadinfo.ServerCommMutex = mServerCommMutex;
  threadinfo.CondSignalData = mCondSignalData;
  threadinfo.bRunningServer = true;
  threadinfo.pcPipeName = p_pcPipeName;
  threadinfo.thread_id_Server = &mServerId;
  threadinfo.MessageFIFO = new char*[MAX_MESSAGE_MEMORY];
  threadinfo.uiBytesPerFrame = p_uiBytesPerFrame;
  // Pre-Allocate mem for FIFO
  for (uint32_t k=0; k< MAX_MESSAGE_MEMORY; ++k){
    threadinfo.MessageFIFO[k] = new char[MAX_BUFFER_SIZE] ;
    memset(threadinfo.MessageFIFO[k],0,MAX_BUFFER_SIZE);
  }
  threadinfo.uiMessagesOnStack = 0;
  // pass the pointer to the lists to the threads

  // Fire up the thread for serving data 
  pthread_create(&mServerId, NULL, pipeinterface::EntryPointServer, reinterpret_cast<void *>(&threadinfo));
 
}

//! Lovely destructor for cleaning up the mess
pipeinterface::~pipeinterface(){
  // Inform the threads gently that they have to come to an end
  ::pthread_mutex_lock(threadinfo.ServerCommMutex);
  threadinfo.bRunningServer = false;
  ::pthread_mutex_unlock(threadinfo.ServerCommMutex);

  // close the sockets to get the threads out of receive-sleep

  // join the threads == Wait until their death
  pthread_join(mServerId,NULL);
  
  // clean up the memory: FIFO, etc.
  for (uint32_t k=0; k< MAX_MESSAGE_MEMORY; ++k){
    delete [] threadinfo.MessageFIFO[k];
  }
  delete [] threadinfo.MessageFIFO;
  delete [] m_RxTxBuffer;
  // destroy the cond signals and the mutex
  pthread_cond_destroy(mCondSignalData);
  pthread_mutex_destroy(mServerCommMutex);
}

//! Entry Point for starting the server thread
void *pipeinterface::EntryPointServer(void *p_threadinfo)
{
  pipeinterface::RunServerThread(p_threadinfo);
  return NULL;
}


void pipeinterface::RunServerThread(void *p_threadinfo){
  threadinfo_t * TInfo = reinterpret_cast<threadinfo_t *> (p_threadinfo);
  bool bRunning = TInfo->bRunningServer;
  
  int input = atoi( TInfo->pcPipeName);
  std::cout << "Opening pipe for reading data: " << TInfo->pcPipeName << " "<< input << std::flush << std::endl;
  FILE * m_iPipeIn = fdopen(input, "r");
  
  char Buffer[MAX_BUFFER_SIZE];
  size_t MsgLen = 0;
  while (bRunning){  
    
    MsgLen = ::fread(Buffer, 1, TInfo->uiBytesPerFrame, m_iPipeIn);
    
    if (MsgLen == static_cast<size_t>(TInfo->uiBytesPerFrame)){
      ::pthread_mutex_lock(TInfo->ServerCommMutex);
      TInfo->uiMessagesOnStack = PushBackFIFO(TInfo->MessageFIFO, TInfo->uiMessagesOnStack, Buffer, MsgLen);
      ::pthread_mutex_unlock(TInfo->ServerCommMutex);
      // Inform about data
      pthread_cond_signal(TInfo->CondSignalData);
    }    
    
    ::pthread_mutex_lock(TInfo->ServerCommMutex);
    bRunning = TInfo->bRunningServer;
    ::pthread_mutex_unlock(TInfo->ServerCommMutex);
    
  }
  
  fclose(m_iPipeIn);
}




//! Get the first message from the FIFO: Memory has to be provided by caller!
uint32_t pipeinterface::FrontPopMessageFIFO(threadinfo_t* TInfo, char * p_pcData){
  ::pthread_mutex_lock(TInfo->ServerCommMutex);
  //std::cout << "Pop: "<< TInfo->InstanceName << " : "<< TInfo->uiMessagesOnStack << std::endl;
  char* Prime;
  uint32_t Len = 0;
  if ( TInfo->uiMessagesOnStack>0){
    memcpy(reinterpret_cast<char*>(&Len),&TInfo->MessageFIFO[0][0],4);
    if ((Len>MIN_MESSAGE_SIZE)&&(Len<=MAX_BUFFER_SIZE)){
      Prime = TInfo->MessageFIFO[0]+4;
      memcpy(p_pcData,Prime,Len);
      // shift the fifo to drop first element
      TInfo->uiMessagesOnStack = ShiftFIFO(TInfo->MessageFIFO ,TInfo->uiMessagesOnStack);
      ::pthread_mutex_unlock(TInfo->ServerCommMutex);
      return Len;
    }else{
      std::cout << " ERROR - Invalid Packet on stack " << Len << std::endl;
      TInfo->uiMessagesOnStack = ShiftFIFO(TInfo->MessageFIFO ,TInfo->uiMessagesOnStack);
    }
  }
  ::pthread_mutex_unlock(TInfo->ServerCommMutex);
  return 0;
}

//! Get data from node, if no data wait until timeout
uint32_t pipeinterface::GetDataWithTimeout(char* p_pcData, uint32_t p_uiTimeToWaitSeconds){
  uint32_t MsgSize =  FrontPopMessageFIFO(&threadinfo, p_pcData);
  
  if ((MsgSize>0) || (p_uiTimeToWaitSeconds<1)){
    return MsgSize;
  }
  
  struct timeval ActualTime;
  struct timespec DeadlineTimeForWaiting;
  gettimeofday(&ActualTime,NULL);
  DeadlineTimeForWaiting.tv_sec = ActualTime.tv_sec+p_uiTimeToWaitSeconds;
  DeadlineTimeForWaiting.tv_nsec = (ActualTime.tv_usec)*1000UL;
  while ((MsgSize<1) && (ActualTime.tv_sec<DeadlineTimeForWaiting.tv_sec)){
    pthread_mutex_lock(threadinfo.ServerCommMutex);
    pthread_cond_timedwait(threadinfo.CondSignalData, threadinfo.ServerCommMutex, &DeadlineTimeForWaiting);
    pthread_mutex_unlock(threadinfo.ServerCommMutex);
    MsgSize =  FrontPopMessageFIFO(&threadinfo, p_pcData);
    gettimeofday(&ActualTime,NULL);
  }
  return MsgSize;
}


extern "C" {
    pipeinterface* pipeinterface_new(char * a, uint32_t b){ return new pipeinterface(a,b); }
    uint32_t pipeinterface_GetDataWithTimeout(pipeinterface* mypipeinterface, char* p_pcData, uint32_t p_uiTimeToWaitSeconds){return mypipeinterface->GetDataWithTimeout(p_pcData, p_uiTimeToWaitSeconds); }
}



