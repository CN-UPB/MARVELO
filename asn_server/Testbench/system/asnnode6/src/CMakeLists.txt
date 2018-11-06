include_directories("${PROJECT_SOURCE_DIR}/src")
link_directories(${ALSA_LIBRARY_DIRS})
include_directories(${ALSA_INCLUDE_DIRS})

add_executable(asn6pipe 
	hal.cpp
	hal.hpp
	pipeExampleC.cpp
  )

target_link_libraries(asn6pipe
    ${ALSA_LIBRARIES}
  )  
  
install (TARGETS asn6pipe DESTINATION bin)
 






