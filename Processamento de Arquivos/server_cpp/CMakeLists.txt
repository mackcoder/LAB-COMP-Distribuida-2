# VERSÃO LOCAL

#cd server_cpp
#mkdir build
#cd build
#cmake ..
#make
#./server

cmake_minimum_required(VERSION 3.15)
project(FileProcessorServer CXX)

# O gRPC requer C++17 nas versões mais recentes
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Localizar os pacotes do gRPC e Protobuf no sistema
find_package(gRPC CONFIG REQUIRED)
find_package(Protobuf REQUIRED)

# Diretório onde está o arquivo proto
set(PROTO_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../proto")
set(PROTO_FILE "${PROTO_DIR}/file_processor.proto")

# Variáveis com os nomes dos arquivos gerados automaticamente
set(PROTO_SRC "${CMAKE_CURRENT_BINARY_DIR}/file_processor.pb.cc")
set(PROTO_HDR "${CMAKE_CURRENT_BINARY_DIR}/file_processor.pb.h")
set(GRPC_SRC "${CMAKE_CURRENT_BINARY_DIR}/file_processor.grpc.pb.cc")
set(GRPC_HDR "${CMAKE_CURRENT_BINARY_DIR}/file_processor.grpc.pb.h")

# Comando customizado para compilar o .proto e gerar o código C++
add_custom_command(
    OUTPUT ${PROTO_SRC} ${PROTO_HDR} ${GRPC_SRC} ${GRPC_HDR}
    COMMAND protobuf::protoc
    ARGS --grpc_out="${CMAKE_CURRENT_BINARY_DIR}"
        --cpp_out="${CMAKE_CURRENT_BINARY_DIR}"
        -I "${PROTO_DIR}"
        --plugin=protoc-gen-grpc=$<TARGET_FILE:gRPC::grpc_cpp_plugin>
        "${PROTO_FILE}"
    DEPENDS "${PROTO_FILE}"
)

# Incluir o diretório onde os arquivos de cabeçalho (.h) foram gerados
include_directories("${CMAKE_CURRENT_BINARY_DIR}")

# Declarar o executável do servidor, incluindo os arquivos gerados pelo protoc
add_executable(server
    server.cc
    ${PROTO_SRC}
    ${GRPC_SRC}
)

# Vincular (link) as bibliotecas do gRPC e Protobuf ao executável
target_link_libraries(server
    gRPC::grpc++
    gRPC::grpc
    protobuf::libprotobuf
)




# VERSÃO DOCKER
#[[
cmake_minimum_required(VERSION 3.15)
project(FileProcessorServer CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Usa a pkg-config do Ubuntu para localizar o gRPC e Protobuf
find_package(PkgConfig REQUIRED)
pkg_check_modules(GRPC REQUIRED grpc++)
pkg_check_modules(PROTOBUF REQUIRED protobuf)

set(PROTO_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../proto")
set(PROTO_FILE "${PROTO_DIR}/file_processor.proto")

set(PROTO_SRC "${CMAKE_CURRENT_BINARY_DIR}/file_processor.pb.cc")
set(PROTO_HDR "${CMAKE_CURRENT_BINARY_DIR}/file_processor.pb.h")
set(GRPC_SRC "${CMAKE_CURRENT_BINARY_DIR}/file_processor.grpc.pb.cc")
set(GRPC_HDR "${CMAKE_CURRENT_BINARY_DIR}/file_processor.grpc.pb.h")

# No Ubuntu, o apt-get instala o compilador e o plugin nestes caminhos fixos
set(PROTOC_COMPILER "/usr/bin/protoc")
set(GRPC_CPP_PLUGIN "/usr/bin/grpc_cpp_plugin")

add_custom_command(
    OUTPUT ${PROTO_SRC} ${PROTO_HDR} ${GRPC_SRC} ${GRPC_HDR}
    COMMAND ${PROTOC_COMPILER}
    ARGS --grpc_out="${CMAKE_CURRENT_BINARY_DIR}"
        --cpp_out="${CMAKE_CURRENT_BINARY_DIR}"
        -I "${PROTO_DIR}"
        --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN}
        "${PROTO_FILE}"
    DEPENDS "${PROTO_FILE}"
)

include_directories("${CMAKE_CURRENT_BINARY_DIR}")

add_executable(server
    server.cc
    ${PROTO_SRC}
    ${GRPC_SRC}
)

# Link direto com as bibliotecas do sistema
target_link_libraries(server
    grpc++
    grpc
    protobuf
)
]]
