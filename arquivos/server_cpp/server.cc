#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <chrono>
#include <ctime>
#include <cstdlib>
#include <cstdio>
#include <iomanip>
#include <mutex>
#include <grpcpp/grpcpp.h>
#include "file_processor.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerReaderWriter;
using grpc::Status;
using namespace file_processor;

class FileProcessorServiceImpl final : public FileProcessorService::Service {
private:

    std::mutex log_mutex_;  // o servidor atende várias requisições em paralelo

    void LogOperation(const std::string& type, const std::string& service, const std::string& file, const std::string& msg) {
        // 1. Data e hora atual do sistema
        auto now = std::chrono::system_clock::now();
        std::time_t t = std::chrono::system_clock::to_time_t(now);
        std::tm tm_local{};
        localtime_r(&t, &tm_local);

        std::lock_guard<std::mutex> lock(log_mutex_);

        // 2. Abre o server.log em modo de adição
        std::ofstream log("server.log", std::ios::app);
        if (!log) {
            std::cerr << "Falha ao abrir server.log" << std::endl;
            return;
        }

        // 3. Escreve a linha: timestamp, tipo, serviço, arquivo e mensagem
        log << "[" << std::put_time(&tm_local, "%Y-%m-%d %H:%M:%S") << "] "
            << "[" << type << "] "
            << "Servico=" << service << " | "
            << "Arquivo=" << (file.empty() ? "-" : file) << " | "
            << msg << std::endl;

        // Também mostra no terminal
        std::cout << "[" << type << "] " << service << " | " << file << " | " << msg << std::endl;

        // 4. O arquivo é fechado automaticamente ao sair do escopo
    }

    // =========================================================================
    // MÉTODOS AUXILIARES FORNECIDOS (NÃO ALTERAR)
    // =========================================================================

    bool ReceiveFile(ServerReaderWriter<FileResponse, FileRequest>* stream, std::string& filepath, std::string& original_name, FileRequest& last_req) {
        FileRequest req;
        std::ofstream outfile;
        bool first = true;
        while (stream->Read(&req)) {
            if (first) {
                original_name = req.file_name();
                filepath = "/tmp/input_" + original_name;
                outfile.open(filepath, std::ios::binary);
                last_req = req;
                first = false;
            }
            if (req.has_file_content()) {
                outfile.write(req.file_content().content().c_str(), req.file_content().content().size());
            }
        }
        if (outfile.is_open()) outfile.close();
        return !first;
    }

    Status SendFile(ServerReaderWriter<FileResponse, FileRequest>* stream, const std::string& out_filepath, const std::string& out_filename) {
        std::ifstream infile(out_filepath, std::ios::binary);
        if (!infile) return Status(grpc::StatusCode::INTERNAL, "Falha ao ler output");

        FileResponse resp;
        resp.set_success(true);
        resp.set_file_name(out_filename);
        resp.set_status_message("Sucesso");

        char buffer[1024];
        while (infile.read(buffer, sizeof(buffer)) || infile.gcount() > 0) {
            FileChunk* chunk = new FileChunk();
            chunk->set_content(buffer, infile.gcount());
            resp.set_allocated_file_content(chunk);
            stream->Write(resp);
            resp.clear_file_content();
        }
        return Status::OK;
    }

public:
    // =========================================================================
    // IMPLEMENTAÇÃO SUA (SERVIÇOS gRPC)
    // =========================================================================

    Status CompressPDF(ServerContext* context, ServerReaderWriter<FileResponse, FileRequest>* stream) override {
        const std::string service = "CompressPDF";
        std::string in_path, original_name;
        FileRequest first_req;

        // 1. Recebe o arquivo enviado pelo cliente
        if (!ReceiveFile(stream, in_path, original_name, first_req)) {
            LogOperation("ERRO", service, "", "Nenhum dado recebido do cliente");
            return Status(grpc::StatusCode::INVALID_ARGUMENT, "Nenhum arquivo recebido");
        }
        LogOperation("INFO", service, original_name, "Requisicao recebida");

        // 2. Monta o comando do Ghostscript
        std::string out_name = "comprimido_" + original_name;
        std::string out_path = "/tmp/output_" + original_name;
        std::string cmd = "gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook "
                          "-dNOPAUSE -dQUIET -dBATCH -sOutputFile=\"" + out_path + "\" \"" + in_path + "\"";

        // 3. Executa o comando
        int ret = std::system(cmd.c_str());

        if (ret != 0) {
            // 4. Registra a falha e limpa os temporários
            LogOperation("ERRO", service, original_name, "Ghostscript falhou (codigo " + std::to_string(ret) + ")");
            std::remove(in_path.c_str());
            std::remove(out_path.c_str());
            return Status(grpc::StatusCode::INTERNAL, "Falha ao comprimir o PDF");
        }

        // 5. Devolve o arquivo comprimido ao cliente
        Status status = SendFile(stream, out_path, out_name);
        if (status.ok()) {
            LogOperation("SUCESSO", service, original_name, "PDF comprimido e enviado como " + out_name);
        } else {
            LogOperation("ERRO", service, original_name, "Falha ao enviar: " + status.error_message());
        }

        // 6. Remove os arquivos temporários
        std::remove(in_path.c_str());
        std::remove(out_path.c_str());

        return status;
    }

    // =========================================================================
    // MÉTODOS IGNORADOS PARA ESTA ENTREGA
    // =========================================================================

    Status ConvertToTXT(ServerContext* /*context*/, ServerReaderWriter<FileResponse, FileRequest>* /*stream*/) override {
        // Não é necessário implementar para esta atividade.
        return Status::OK;
    }

    Status ConvertImageFormat(ServerContext* /*context*/, ServerReaderWriter<FileResponse, FileRequest>* /*stream*/) override {
        // Não é necessário implementar para esta atividade.
        return Status::OK;
    }

    Status ResizeImage(ServerContext* /*context*/, ServerReaderWriter<FileResponse, FileRequest>* /*stream*/) override {
        // Não é necessário implementar para esta atividade.
        return Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    FileProcessorServiceImpl service;

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Servidor gRPC operacional em " << server_address << std::endl;
    server->Wait();
}

int main() {
    RunServer();
    return 0;
}
