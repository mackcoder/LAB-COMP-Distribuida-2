# cliente.py
import grpc
import notas_pb2
import notas_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = notas_pb2_grpc.GerenciadorNotasStub(channel)

        # Exemplo de chamada: Adicionar Nota
        response = stub.AdicionarNota(notas_pb2.AdicionaNotaRequest(ra="123", cod_disciplina="CIC0001", ano=2025, semestre=2, nota=9.5))
        response = stub.AdicionarNota(notas_pb2.AdicionaNotaRequest(ra="123", cod_disciplina="CIC0002", ano=2025, semestre=2, nota=6.5))
        response = stub.AdicionarNota(notas_pb2.AdicionaNotaRequest(ra="123", cod_disciplina="CIC0003", ano=2025, semestre=2, nota=10))
        response = stub.AdicionarNota(notas_pb2.AdicionaNotaRequest(ra="123", cod_disciplina="CIC0004", ano=2025, semestre=2, nota=5.0))
        print(f"Resposta do servidor: {response.msg}")
    
        # Exemplo de chamada: Calcular Média
        media_response = stub.CalcularMedia(notas_pb2.AlunoRequest(ra="123"))
        if media_response.sucesso:
            print(f"Média do aluno 123: {media_response.media}")
        else:
            print(f"Erro ao calcular média: {media_response.msg_erro}")

        # --- CHAMADA DO DESAFIO (STREAMING) ---
        # Itera sobre o stream de respostas recebido do servidor e imprime cada nota.
        print("\n--- Listando todas as notas do aluno 123 (DESAFIO) ---")
        try:
            notas_stream = stub.ListarNotasAluno(notas_pb2.AlunoRequest(ra="123"))
            for nota in notas_stream:
                print(f" - Disciplina: {nota.cod_disciplina}, Nota: {nota.nota}")
        except grpc.RpcError as e:
            print(f"Erro ao chamar ListarNotasAluno: {e.details()}")


if __name__ == '__main__':
    run()