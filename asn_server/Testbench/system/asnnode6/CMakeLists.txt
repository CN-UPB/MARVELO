cmake_minimum_required(VERSION 2.6.2)

Project(asn6pipe)

find_package(PkgConfig)
pkg_check_modules(ALSA REQUIRED alsa)


add_subdirectory (
  src
  )





