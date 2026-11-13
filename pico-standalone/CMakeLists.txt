cmake_minimum_required(VERSION 3.13)
if(NOT PICO_SDK_PATH)
    if(DEFINED ENV{PICO_SDK_PATH})
        set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}")
    else()
        set(PICO_SDK_PATH "C:/Tools/Embedded/pico-sdk")
    endif()
endif()
# Normal production candidate uses Flash XIP. Override explicitly for RAM tests.
if(NOT DEFINED PICO_NO_FLASH)
    set(PICO_NO_FLASH OFF CACHE BOOL "Build a nonpersistent SRAM-only test image")
endif()
include("${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
project(pico_gap_standalone C CXX ASM)
option(GAP_INTEGER_FFT "Experimental integer FFT backend; validate before deployment" OFF)
option(GAP_INTEGER_FAST "Bit-equivalent integer conversion/shift optimization; requires integer FFT" OFF)
option(GAP_WHITEN_FLOAT "Experimental float exp/log whitening; validate before deployment" OFF)
option(GAP_MAG_CACHE "Reuse FFT scratch bins for band magnitudes; validate before deployment" OFF)
if(GAP_INTEGER_FAST AND NOT GAP_INTEGER_FFT)
    message(FATAL_ERROR "GAP_INTEGER_FAST requires GAP_INTEGER_FFT=ON")
endif()
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
if(NOT EXISTS "${CMAKE_CURRENT_LIST_DIR}/dsp/gap_dsp.c")
    message(FATAL_ERROR "Real dsp/gap_dsp.c is required; no estimator stub is permitted")
endif()
add_executable(pico_gap_standalone main.c dsp/gap_dsp.c)
target_include_directories(pico_gap_standalone PRIVATE ${CMAKE_CURRENT_LIST_DIR})
target_compile_options(pico_gap_standalone PRIVATE -O3 -Wall -Wextra -fstack-usage)
target_compile_definitions(pico_gap_standalone PRIVATE
    GAP_INTEGER_FFT=$<BOOL:${GAP_INTEGER_FFT}>
    GAP_INTEGER_FAST=$<BOOL:${GAP_INTEGER_FAST}>
    GAP_WHITEN_FLOAT=$<BOOL:${GAP_WHITEN_FLOAT}>
    GAP_MAG_CACHE=$<BOOL:${GAP_MAG_CACHE}>
    PICO_STACK_SIZE=4096
    CFG_TUD_CDC_TX_BUFSIZE=2048
    CFG_TUD_CDC_RX_BUFSIZE=256
    CFG_TUD_CDC_EP_BUFSIZE=64
    CFG_TUSB_DEBUG=0
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE=1)
pico_set_program_name(pico_gap_standalone "PICO_GAP_STANDALONE")
pico_set_program_version(pico_gap_standalone "0.2-link_diag")
pico_generate_pio_header(pico_gap_standalone ${CMAKE_CURRENT_LIST_DIR}/sen0325_i2s.pio)
target_link_libraries(pico_gap_standalone pico_stdlib pico_rand pico_unique_id
    hardware_pio hardware_dma hardware_irq hardware_clocks hardware_uart m)
pico_enable_stdio_usb(pico_gap_standalone 1)
pico_enable_stdio_uart(pico_gap_standalone 0)
pico_add_extra_outputs(pico_gap_standalone)
