import grpc
from concurrent import futures
import calculator_pb2
import calculator_pb2_grpc
#grpc → biblioteca principal
#futures → permite atender várias requisições ao mesmo tempo
#calculator_pb2 → mensagens (request/response)
#calculator_pb2_grpc → estrutura do serviço
class ServicoCalculadora(calculator_pb2_grpc.CalculadoraServicer):
# CalculadoraServicer vem do .proto
    def Somar(self, request, context):
        print(f"Servidor Python: Recebido {request.a} + {request.b}")
        resultado = request.a + request.b
        return calculator_pb2.SomaResponse(resultado=resultado)
    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calculator_pb2_grpc.add_CalculadoraServicer_to_server(ServicoCalculadora(),
    server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor Python escutando na porta 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
