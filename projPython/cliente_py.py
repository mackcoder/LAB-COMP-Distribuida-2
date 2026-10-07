import grpc
import calculator_pb2
import calculator_pb2_grpc
def run():
# Conecta no servidor Python
    with grpc.insecure_channel('localhost:50052') as channel:
        stub = calculator_pb2_grpc.CalculadoraStub(channel)
        print("Cliente Python -> Chamando Somar(10, 5)")

        request = calculator_pb2.SomaRequest(a=10, b=5)
        response = stub.Somar(request)

        print(f"Cliente Python <- Resultado: {response.resultado}")

if __name__ == '__main__':
    run()
