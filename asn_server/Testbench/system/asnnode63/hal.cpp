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

#include "hal.hpp"
#include <iostream>

#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>
#include <syslog.h>

bool hal::InitHardware(const char * p_pcHwInterface){
 int i;
  int err;
  buffer_frames = 128;
  rate = 16000;
  format = SND_PCM_FORMAT_S32_LE;
  channels = 8;

  if ((err = snd_pcm_open (&capture_handle, p_pcHwInterface, SND_PCM_STREAM_CAPTURE, 0)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to open device");
    return false;
  }
		   
  if ((err = snd_pcm_hw_params_malloc (&hw_params)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to allocate hardware parameter structure");
    return false;
  }

  if ((err = snd_pcm_hw_params_any (capture_handle, hw_params)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to initialize hardware parameter structure");
    return false;
  }

  if ((err = snd_pcm_hw_params_set_access (capture_handle, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to set access typ");
    return false;
  }

  if ((err = snd_pcm_hw_params_set_format (capture_handle, hw_params, format)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to set format");
    return false;
  }

  if ((err = snd_pcm_hw_params_set_rate_near (capture_handle, hw_params, &rate, 0)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to set rate");
    return false;
  }

  if ((err = snd_pcm_hw_params_set_channels (capture_handle, hw_params, channels)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to set channels");
    return false;
  }
	
  if ((err = snd_pcm_hw_params (capture_handle, hw_params)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to set parameters");
    return false;
  }

  snd_pcm_hw_params_free (hw_params);

  if ((err = snd_pcm_prepare (capture_handle)) < 0) {
    syslog(LOG_NOTICE, "NTSND: Error - Unable to prepare audio interface");
    return false;
  }

  buffer = new char[buffer_frames * snd_pcm_format_width(format) / 8 * channels];

  syslog(LOG_NOTICE, "NTSND: Success - Audio Interface Prepared");
  return true;
}


uint32_t hal::GetDataFrame(char * p_pcData){
  int err;
    if ((err = snd_pcm_readi (capture_handle, p_pcData, buffer_frames)) != buffer_frames) {
      syslog(LOG_NOTICE, "NTSND: Error - Read from audio interface failed");
      return 0;
    }
  return buffer_frames*channels*snd_pcm_format_width(format) / 8;
}



hal::hal(const char* p_pcHardwareInterface)
{
  syslog(LOG_NOTICE, "NTSND: Init Hardware");
  InitHardware(p_pcHardwareInterface);
}

hal::~hal()
{
  syslog(LOG_NOTICE, "NTSND: Disconnecting from soundcard");
  delete [] buffer;
  snd_pcm_close (capture_handle);
}
