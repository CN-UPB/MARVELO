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

#ifndef HAL_HPP
#define HAL_HPP
#include <alsa/asoundlib.h>
#define MEM_SIZE 50000
#include <stdint.h>

class hal {
  
public:
  //! Constructor of class
  hal(const char* p_pcHardwareInterface);
  
  //! Destructor of class: Clean up of memory and nice killing of threads
  ~hal();

  uint32_t GetDataFrame(char * p_pcData);

private:
  char *buffer;
  int buffer_frames;
  unsigned int rate;
  snd_pcm_t *capture_handle;
  snd_pcm_hw_params_t *hw_params;
  snd_pcm_format_t format;
  unsigned int channels;

  bool InitHardware(const char * p_pcHwInterface);
};

#endif