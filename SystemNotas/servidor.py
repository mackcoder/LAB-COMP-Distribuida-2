# servidor.py (esqueleto)
import grpc
from concurrent import futures
import notas_pb2
import notas_pb2_grpc
# Armazenamento em memória (simulando um banco de dados)
db_notas = {} # Ex: { "123_DISC1": Nota(...), "123_DISC2": Nota(...) }
class GerenciadorNotasServicer(notas_pb2_grpc.GerenciadorNotasServicer):

    def AdicionarNota(self, request, context):
        print(f"Adicionando nota para RA {request.ra} na disciplina {request.cod_disciplina}")
        chave = f"{request.ra}_{request.cod_disciplina}"
        if chave in db_notas:
            return notas_pb2.StatusResponse(sucesso=False, msg="Nota já existe para este aluno/disciplina. Use AlterarNota.")
    # Lógica para criar e armazenar o objeto Nota

        db_notas[chave] = notas_pb2.Nota(ra = request.ra, cod_disciplina = request.cod_disciplina, ano = request.ano, semestre = request.semestre, nota=request.nota)

        return notas_pb2.StatusResponse(sucesso=True, msg="Nota adicionada com sucesso!")

    def AlternarNota(self, request, context):
        print(f"Alterando nota do RA {request.ra} na disciplina {request.cod_disciplina}")
        chave = f"{request.ra}_{request.cod_disciplina}"
        if chave not in db_notas:
            return notas_pb2.StatusResponse(sucesso=False, msg="Nota não encontrada para este aluno/disciplina. Use AdicionarNota.")

        db_notas[chave] = notas_pb2.Nota(ra = request.ra, cod_disciplina = request.cod_disciplina, ano = request.ano, semestre = request.semestre, nota=request.nota)
        
        return notas_pb2.StatusResponse(sucesso=True, msg="Nota alterado com sucesso!")
            

    def ConsultarNota(self, request, context):
        print(f"Consultando nota para RA {request.ra} na disciplina {request.cod_disciplina}")
        chave = f"{request.ra}_{request.cod_disciplina}"
        if chave not in db_notas:
            return notas_pb2.ConsultaNotaResponse(sucesso=False, msg_erro="Nota não existe para este aluno/disciplina.")

        return notas_pb2.ConsultaNotaResponse(sucesso=True, nota=db_notas[chave])

    def CalcularMedia(self, request, context):
        print(f"Calculando média do RA {request.ra}")
        notas_aluno = [n.nota for n in db_notas.values() if n.ra == request.ra]
        if not notas_aluno:
            return notas_pb2.MediaResponse(sucesso=False, msg_erro="Nenhuma nota encontrada para este RA.")

        media = sum(notas_aluno) / len(notas_aluno)
        return notas_pb2.MediaResponse(sucesso=True, media=media)

    def ListarNotasAluno(self, request, context):
        encontrou = False

        print(f"Listando notas para o RA {request.ra}")
        
        for nota in db_notas.values():
            if nota.ra == request.ra:
                encontrou = True
                yield nota

        if not encontrou:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details('Método não implementado!')
            

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    notas_pb2_grpc.add_GerenciadorNotasServicer_to_server(GerenciadorNotasServicer(),
    server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC rodando na porta 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()