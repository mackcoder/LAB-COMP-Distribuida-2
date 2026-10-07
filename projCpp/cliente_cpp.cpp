#include <iostream>
#include <memory>
#include <grpcpp/grpcpp.h>
#include "calculator.grpc.pb.h"
class CalculadoraClient {
public:
    CalculadoraClient(std::shared_ptr<grpc::Channel> channel)
        : stub_(calculadora::Calculadora::NewStub(channel)) {}
    void Somar(double a, double b) {
        calculadora::SomaRequest request;
        request.set_a(a);
        request.set_b(b);
        calculadora::SomaResponse response;
        grpc::ClientContext context;
        std::cout << "Cliente C++ -> Chamando Somar(" << a << ", " << b << ")" <<
    std::endl;
        grpc::Status status = stub_->Somar(&context, request, &response);
        if (status.ok()) {
            std::cout << "Cliente C++ <- Resultado: " << response.resultado() <<
    std::endl;
        } else {
            std::cout << "RPC falhou" << std::endl;
        }
    }
private:
    std::unique_ptr<calculadora::Calculadora::Stub> stub_;
};
int main() {
    // Conecta no servidor C++
    std::string target_str = "localhost:50051";
    CalculadoraClient client(grpc::CreateChannel(target_str,
    grpc::InsecureChannelCredentials()));
    client.Somar(100.5, 50.2);
    return 0;
}