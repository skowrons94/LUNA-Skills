cmake_minimum_required(VERSION 3.16)
project(ncounter CXX)

# Serial application without visualisation or UI sessions: builds against a minimal Geant4.
find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})

add_executable(ncounter src/ncounter.cc)
target_compile_features(ncounter PRIVATE cxx_std_17)
target_link_libraries(ncounter PRIVATE ${Geant4_LIBRARIES})

# Copy the macros next to the executable so that a build directory can run them directly.
# configure_file re-copies a macro whenever it changes (file(COPY) would copy only once).
file(GLOB NC_MACROS CONFIGURE_DEPENDS ${PROJECT_SOURCE_DIR}/macros/*.mac)
foreach(mac ${NC_MACROS})
  get_filename_component(name ${mac} NAME)
  configure_file(${mac} ${PROJECT_BINARY_DIR}/macros/${name} COPYONLY)
endforeach()
