#include <iostream>
#include <memory>
#include <grpcpp/grpcpp.h>
#include "calculator.grpc.pb.h"

class CalculadoraImpl final : public calculadora::Calculadora::Service {
    grpc::Status Somar(grpc::ServerContext* context,
            const calculadora::SomaRequest* request,
            calculadora::SomaResponse* response) override {
                std::cout << "Servidor C++: Recebido " << request->a() << " + " << request->b() << std::endl;
        double resultado = request->a() + request->b();
        response->set_resultado(resultado);
        return grpc::Status::OK;
    }
};
void RunServer() {
    std::string server_address("0.0.0.0:50052"); // Porta diferente!
    CalculadoraImpl service;
    grpc::ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);
    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    std::cout << "Servidor C++ escutando em " << server_address << std::endl;
    server->Wait();
}
int main() {
    RunServer();
    return 0;
}
