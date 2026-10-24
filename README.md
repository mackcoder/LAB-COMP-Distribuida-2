# LAB-COMP-Distribuida-2

Repositório de atividades práticas de **gRPC** da disciplina **Computação Distribuída**. Ele reúne três projetos, cada um avançando um passo em relação ao anterior:

| Pasta | Projeto | O que pratica |
|---|---|---|
| [`projPython/`](projPython) e [`projCpp/`](projCpp) | Calculadora gRPC | RPC unário e **interoperabilidade** entre Python e C++ |
| [`SystemNotas/`](SystemNotas) | Gerenciador de Notas | Serviço CRUD em Python, testes com `pytest` e **server streaming** |
| [`Processamento de Arquivos/`](Processamento%20de%20Arquivos) | Serviço de Processamento de Arquivos | Servidor C++ + cliente Python, **streaming bidirecional** de arquivos, ferramentas Unix, logging e **Docker** |

O ambiente de desenvolvimento usado é o **GitHub Codespaces** (Ubuntu).

---

## Conceitos em comum

Os três projetos seguem o mesmo fluxo do gRPC:

1. **Contrato (`.proto`)**: define as mensagens e os métodos do serviço em Protocol Buffers.
2. **Geração de código**: o `protoc` gera, a partir do `.proto`, as classes das mensagens e os *stubs*. Em Python são os arquivos `*_pb2.py` e `*_pb2_grpc.py`; em C++, `*.pb.h/.cc` e `*.grpc.pb.h/.cc`.
3. **Servidor**: herda a classe base gerada (`...Servicer` em Python, `...::Service` em C++) e implementa cada método.
4. **Cliente**: usa o *stub* gerado para chamar os métodos remotos como se fossem funções locais.

Tipos de RPC usados no repositório:

| Tipo | Assinatura no `.proto` | Onde aparece |
|---|---|---|
| Unário | `rpc M (Req) returns (Resp)` | Calculadora, Notas |
| Server streaming | `rpc M (Req) returns (stream Resp)` | `ListarNotasAluno` (Notas) |
| Bidirecional | `rpc M (stream Req) returns (stream Resp)` | Todos os métodos do Processamento de Arquivos |

---

## 1. Calculadora gRPC (`projPython/` e `projCpp/`)

Serviço mínimo com um único método, `Somar`, que recebe dois números (`SomaRequest { a, b }`) e devolve a soma (`SomaResponse { resultado }`). O mesmo `calculator.proto` (pacote `calculadora`) está nas duas pastas.

O objetivo é mostrar que **cliente e servidor podem estar em linguagens diferentes**, já que o contrato `.proto` é o mesmo. Por isso as portas estão cruzadas:

| Programa | Papel | Porta |
|---|---|---|
| `projPython/servidor_py.py` | Servidor Python | escuta em **50051** |
| `projCpp/servidor_cpp.cpp` | Servidor C++ | escuta em **50052** |
| `projCpp/cliente_cpp.cpp` | Cliente C++ | chama o **servidor Python** (`localhost:50051`) |
| `projPython/cliente_py.py` | Cliente Python | chama o **servidor C++** (`localhost:50052`) |

```
cliente_cpp  ──►  servidor_py  (50051)
cliente_py   ──►  servidor_cpp (50052)
```

### Como rodar

Dependências:
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libgrpc++-dev libprotobuf-dev protobuf-compiler protobuf-compiler-grpc
pip install grpcio grpcio-tools
```

**Python** (gerar o código e subir o servidor):
```bash
cd projPython
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. calculator.proto
python servidor_py.py          # terminal 1
```

**C++** (compilar com CMake e subir o servidor):
```bash
cd projCpp
mkdir -p build && cd build
cmake ..
make
./servidor_cpp                 # terminal 2
```

**Clientes:**
```bash
./servidor_cpp                 # já rodando
cd projCpp/build && ./cliente_cpp     # terminal 3 → Resultado: 150.7
cd projPython && python cliente_py.py # terminal 4 → Resultado: 15.0
```

O `CMakeLists.txt` de `projCpp` gera os stubs C++ com o `protoc` (alvo `generate_proto`) e compila dois executáveis: `servidor_cpp` e `cliente_cpp`. O arquivo `.vscode/settings.json` aponta a extensão CMake Tools do VS Code para essa pasta.

---

## 2. Gerenciador de Notas (`SystemNotas/`)

Serviço gRPC em Python para gerenciar notas de alunos, com armazenamento **em memória** (um dicionário `db_notas` cuja chave é `"<RA>_<disciplina>"`, por exemplo `"123_CIC0001"`).

### Contrato (`notas.proto`, pacote `gerencia_notas`)

| Método | Entrada | Saída | Comportamento |
|---|---|---|---|
| `AdicionarNota` | `AdicionaNotaRequest` | `StatusResponse` | Cria a nota. Falha se já existir nota para aquele RA/disciplina. |
| `AlterarNota` | `AdicionaNotaRequest` | `StatusResponse` | Atualiza nota, ano e semestre. Falha se a nota não existir (não cria uma nova). |
| `ConsultarNota` | `AlunoDisciplinaRequest` | `ConsultaNotaResponse` | Retorna a nota com `sucesso=True`, ou `sucesso=False` + `msg_erro`. |
| `CalcularMedia` | `AlunoRequest` | `MediaResponse` | Média de todas as notas do RA. Falha se o aluno não tiver notas. |
| `ListarNotasAluno` *(desafio)* | `AlunoRequest` | `stream Nota` | **Server streaming:** envia, uma a uma, as notas do RA usando `yield`. Para um aluno sem notas, o stream vem vazio. |

### Arquivos

- `notas.proto`: contrato do serviço.
- `servidor.py`: implementação do `GerenciadorNotasServicer` e função `serve()` (porta **50051**).
- `cliente.py`: adiciona notas para o RA `123`, calcula a média e lista as notas via streaming.
- `test_grpc.py`: suíte `pytest` que sobe o servidor na porta 50053 e valida as regras da tabela acima: duplicidade, alteração de nota inexistente, média ignorando outros alunos, stream só com o RA pedido etc.
- `notas_pb2.py`, `notas_pb2.pyi`, `notas_pb2_grpc.py`: código gerado pelo `protoc`.

### Como rodar

```bash
cd SystemNotas
pip install grpcio grpcio-tools pytest

# (re)gerar o código a partir do .proto
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. notas.proto

python servidor.py     # terminal 1
python cliente.py      # terminal 2

pytest test_grpc.py -v # testes automatizados (não precisa do servidor rodando)
```

> As notas ficam em memória: ao reiniciar o servidor, os dados são apagados. Se o cliente for executado duas vezes com o mesmo servidor, `AdicionarNota` responde "Nota já existe…", e isso é o esperado.

---

## 3. Serviço de Processamento de Arquivos (`Processamento de Arquivos/`)

Atividade principal da disciplina: um **servidor gRPC em C++** que recebe arquivos de um **cliente Python** por streaming, processa esses arquivos com ferramentas de linha de comando do Unix e devolve o resultado também por streaming. Toda a solução roda em **containers Docker**.

### Serviços (`proto/file_processor.proto`, pacote `file_processor`)

Todos os métodos são **bidirecionais** (`stream FileRequest` → `stream FileResponse`). O arquivo trafega em blocos (`FileChunk`) de 1 KB, o que evita carregar arquivos grandes inteiros na memória.

| Método | Ferramenta | Comando | Entrega |
|---|---|---|---|
| `CompressPDF` | Ghostscript | `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook ...` | **Entrega 1** ✅ |
| `ConvertToTXT` | Poppler | `pdftotext input.pdf output.txt` | Entrega 2 |
| `ConvertImageFormat` | ImageMagick | `convert input.jpg output.png` | Entrega 2 |
| `ResizeImage` | ImageMagick | `convert input.jpg -resize 800x600 output.jpg` | Entrega 2 |

Formato das mensagens:
- **`FileRequest`**: na primeira mensagem vão o `file_name` e os parâmetros do serviço, dentro de um `oneof parameters` (`compress_pdf_params`, `convert_image_format_params { output_format }`, `resize_image_params { width, height }` …). As mensagens seguintes levam só o `file_content`.
- **`FileResponse`**: `file_name` do arquivo gerado, `file_content` (um bloco), `status_message` e `success`.
---

<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="660" viewBox="0 0 1140 660" font-family="'Segoe UI', Helvetica, Arial, sans-serif">
  <defs>
    <marker id="aBlue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2563EB"/></marker>
    <marker id="aPurple" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#7C3AED"/></marker>
    <marker id="aAmber" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#B45309"/></marker>
    <style>
      .s  { font-size: 12.5px; fill: #6B7280; }
      .m  { font-family: Consolas, 'Cascadia Code', 'DejaVu Sans Mono', monospace; font-size: 13px; fill: #111827; }
      .h  { font-size: 16px; font-weight: 600; fill: #FFFFFF; }
      .hs { font-size: 12px; fill: #FFFFFF; opacity: .88; }
      .step { font-size: 11px; font-weight: 700; fill: #FFFFFF; }
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="1139" height="659" rx="16" fill="#FFFFFF" stroke="#E5E7EB"/>

  <text x="40" y="46" font-size="21" font-weight="700" fill="#111827">Fluxo de uma requisição <tspan font-family="Consolas, 'Cascadia Code', 'DejaVu Sans Mono', monospace" fill="#7C3AED">CompressPDF</tspan></text>
  <text x="40" y="70" class="s">Streaming bidirecional gRPC · arquivo enviado em blocos (FileChunk) de 1 KB</text>

  <!-- cabeçalhos -->
  <rect x="80"  y="92" width="220" height="56" rx="10" fill="#2563EB"/>
  <text x="190" y="117" text-anchor="middle" class="h">Cliente Python</text>
  <text x="190" y="136" text-anchor="middle" class="hs">client.py</text>

  <rect x="530" y="92" width="220" height="56" rx="10" fill="#7C3AED"/>
  <text x="640" y="117" text-anchor="middle" class="h">Servidor C++</text>
  <text x="640" y="136" text-anchor="middle" class="hs">server.cc · porta 50051</text>

  <rect x="900" y="92" width="220" height="56" rx="10" fill="#D97706"/>
  <text x="1010" y="117" text-anchor="middle" class="h">Ghostscript</text>
  <text x="1010" y="136" text-anchor="middle" class="hs">gs (processo do sistema)</text>

  <!-- linhas de vida -->
  <line x1="190"  y1="148" x2="190"  y2="630" stroke="#BFDBFE" stroke-width="2" stroke-dasharray="6 6"/>
  <line x1="640"  y1="148" x2="640"  y2="630" stroke="#DDD6FE" stroke-width="2" stroke-dasharray="6 6"/>
  <line x1="1010" y1="148" x2="1010" y2="630" stroke="#FDE68A" stroke-width="2" stroke-dasharray="6 6"/>

  <!-- barra de atividade do servidor -->
  <rect x="633" y="176" width="14" height="404" rx="3" fill="#EDE9FE" stroke="#C4B5FD"/>

  <!-- 1 -->
  <circle cx="40" cy="194" r="11" fill="#2563EB"/><text x="40" y="198" text-anchor="middle" class="step">1</text>
  <text x="412" y="184" text-anchor="middle" class="m">FileRequest{ file_name, compress_pdf_params }</text>
  <line x1="194" y1="194" x2="630" y2="194" stroke="#2563EB" stroke-width="2" marker-end="url(#aBlue)"/>
  <text x="412" y="213" text-anchor="middle" class="s">generate_requests() · 1ª mensagem: nome do arquivo + parâmetros</text>

  <!-- 2 -->
  <circle cx="40" cy="254" r="11" fill="#2563EB"/><text x="40" y="258" text-anchor="middle" class="step">2</text>
  <text x="412" y="244" text-anchor="middle" class="m">FileRequest{ file_content } × N</text>
  <line x1="194" y1="254" x2="630" y2="254" stroke="#2563EB" stroke-width="2" marker-end="url(#aBlue)"/>
  <line x1="194" y1="260" x2="624" y2="260" stroke="#2563EB" stroke-width="1" stroke-opacity=".35"/>
  <line x1="194" y1="265" x2="624" y2="265" stroke="#2563EB" stroke-width="1" stroke-opacity=".2"/>

  <!-- 3 -->
  <circle cx="40" cy="314" r="11" fill="#7C3AED"/><text x="40" y="318" text-anchor="middle" class="step">3</text>
  <rect x="664" y="296" width="300" height="36" rx="8" fill="#F5F3FF" stroke="#C4B5FD"/>
  <text x="814" y="319" text-anchor="middle" class="m">ReceiveFile() → /tmp/input_&lt;nome&gt;</text>

  <!-- 4 -->
  <circle cx="40" cy="374" r="11" fill="#D97706"/><text x="40" y="378" text-anchor="middle" class="step">4</text>
  <text x="826" y="364" text-anchor="middle" class="m">std::system("gs -sDEVICE=pdfwrite …")</text>
  <line x1="647" y1="374" x2="1000" y2="374" stroke="#B45309" stroke-width="2" marker-end="url(#aAmber)"/>
  <line x1="1006" y1="410" x2="651" y2="410" stroke="#B45309" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#aAmber)"/>
  <text x="826" y="430" text-anchor="middle" class="s">/tmp/output_&lt;nome&gt; + código de retorno</text>

  <!-- 5 -->
  <circle cx="40" cy="474" r="11" fill="#7C3AED"/><text x="40" y="478" text-anchor="middle" class="step">5</text>
  <rect x="664" y="456" width="300" height="36" rx="8" fill="#F5F3FF" stroke="#C4B5FD"/>
  <text x="814" y="479" text-anchor="middle" class="m">LogOperation() → server.log</text>

  <!-- 6 -->
  <circle cx="40" cy="534" r="11" fill="#7C3AED"/><text x="40" y="538" text-anchor="middle" class="step">6</text>
  <text x="412" y="524" text-anchor="middle" class="m">FileResponse{ file_content } × N</text>
  <line x1="630" y1="534" x2="196" y2="534" stroke="#7C3AED" stroke-width="2" marker-end="url(#aPurple)"/>
  <line x1="630" y1="540" x2="200" y2="540" stroke="#7C3AED" stroke-width="1" stroke-opacity=".35"/>
  <line x1="630" y1="545" x2="200" y2="545" stroke="#7C3AED" stroke-width="1" stroke-opacity=".2"/>
  <text x="412" y="564" text-anchor="middle" class="s">SendFile() · stream de resposta</text>

  <!-- 7 -->
  <circle cx="40" cy="610" r="11" fill="#059669"/><text x="40" y="614" text-anchor="middle" class="step">7</text>
  <rect x="70" y="590" width="360" height="40" rx="8" fill="#EFF6FF" stroke="#BFDBFE"/>
  <text x="250" y="615" text-anchor="middle" class="m">save_response_stream() → <tspan fill="#2563EB" font-weight="700">comprimido.pdf</tspan></text>
  <rect x="664" y="590" width="300" height="40" rx="8" fill="#F5F3FF" stroke="#C4B5FD"/>
  <text x="814" y="615" text-anchor="middle" class="m">remove arquivos de /tmp</text>
</svg>




### Log de operações

Cada requisição é registrada em `server.log` com **timestamp, tipo (INFO/SUCESSO/ERRO), serviço, nome do arquivo e mensagem**:

```
[2026-10-24 15:19:22] [INFO] Servico=CompressPDF | Arquivo=test.pdf | Requisicao recebida
[2026-10-24 15:19:22] [SUCESSO] Servico=CompressPDF | Arquivo=test.pdf | PDF comprimido e enviado como comprimido_test.pdf
```

O arquivo é criado na pasta de onde o `./server` é executado (`server_cpp/build/`).
<img width="1140" height="660" alt="fluxo-compresspdf" src="https://github.com/user-attachments/assets/8907b272-827e-4764-a86c-47240cfb2532" />

### Estrutura

```
Processamento de Arquivos/
├── docker-compose.yml         # sobe os containers servidor-grpc e cliente-python
├── proto/
│   └── file_processor.proto   # contrato compartilhado por C++ e Python
├── server_cpp/
│   ├── server.cc              # FileProcessorServiceImpl + RunServer() (porta 50051)
│   ├── CMakeLists.txt         # versão local ativa; versão Docker comentada com #[[ ]]
│   └── Dockerfile             # Ubuntu 22.04 + gRPC, Ghostscript, Poppler, ImageMagick
└── client_python/
    ├── client.py              # FileProcessorClient + área de teste
    ├── requirements.txt       # grpcio, grpcio-tools, pytest
    ├── Dockerfile             # python:3.10-slim
    └── test.pdf               # PDF usado no teste de compressão
```

### Containers (`docker-compose.yml`)

| Serviço | Imagem | Função |
|---|---|---|
| `servidor-grpc` | `server_cpp/Dockerfile` (Ubuntu 22.04) | Compila e roda o servidor C++. Expõe a porta **50051**. |
| `cliente-python` | `client_python/Dockerfile` (Python 3.10) | Roda o cliente. Usa `host.docker.internal` para alcançar o servidor (contorna timeouts de rede no Codespaces). |

Os dois containers montam a pasta do projeto em `/workspace` (`volumes: - .:/workspace`). Assim, editar o código no VS Code já reflete dentro dos containers, e eles ficam em `sleep infinity` esperando os comandos.

### `CMakeLists.txt`: versão local x versão Docker

O enunciado fornece duas versões do CMake, porque cada ambiente localiza o gRPC de um jeito:

- **Local (Codespaces):** `find_package(gRPC CONFIG)` usa os arquivos de configuração CMake que o gRPC instala.
- **Docker (Ubuntu 22.04):** o gRPC do `apt` é localizado via `pkg-config`, com `protoc` e `grpc_cpp_plugin` em caminhos fixos (`/usr/bin`).

As duas estão no mesmo arquivo. A que não está em uso fica dentro de um comentário de bloco `#[[ ... ]]`. Para trocar de ambiente, mova o `#[[ ]]` de uma versão para a outra e **limpe a pasta `build/`** antes de compilar, porque o cache do CMake guarda os caminhos do ambiente anterior.

### Como rodar: sem Docker (Codespaces)

```bash
# Terminal 1: servidor
sudo apt-get update
sudo apt-get install -y build-essential cmake ghostscript poppler-utils imagemagick \
     libgrpc++-dev libprotobuf-dev protobuf-compiler-grpc protobuf-compiler python3 python3-pip
cd "Processamento de Arquivos/server_cpp"
mkdir -p build && cd build
cmake ..
make
./server
```

```bash
# Terminal 2: cliente
cd "Processamento de Arquivos/client_python"
pip install grpcio grpcio-tools
python3 -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/file_processor.proto
# em client.py, use: FileProcessorClient(target='localhost:50051')
python3 client.py
```

### Como rodar: com Docker

```bash
cd "Processamento de Arquivos"
docker-compose up -d --build
docker ps        # confere o nome dos containers (depende do nome da pasta)
```

```bash
# Terminal 1: servidor
docker exec -it <nome>-servidor-grpc-1 bash
cd server_cpp
mkdir -p build && cd build
rm -rf *
# ative a versão Docker no CMakeLists.txt
cmake ..
make
./server
```

```bash
# Terminal 2: cliente
docker exec -it <nome>-cliente-python-1 bash
cd client_python
python -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/file_processor.proto
python3 client.py
```

Resultado esperado: `Compressão finalizada! Verifique o arquivo comprimido.pdf na sua pasta.` O `comprimido.pdf` aparece em `client_python/`, e a operação fica registrada em `server_cpp/build/server.log`.

Sempre que alterar o código ou os Dockerfiles:
```bash
docker-compose down
docker-compose up -d --build
```

### Tratamento de erros

- O cliente verifica se o arquivo de entrada existe antes de enviar.
- Se o servidor não receber dados, devolve `INVALID_ARGUMENT`. Se o Ghostscript falhar (por exemplo, quando o arquivo não é um PDF válido), devolve `INTERNAL` e registra `[ERRO]` no log.
- No cliente, falhas do servidor são capturadas com `except grpc.RpcError` e exibidas com o código e a mensagem do erro.

---

## Tecnologias

- **gRPC / Protocol Buffers 3**
- **Python 3**: `grpcio`, `grpcio-tools`, `pytest`
- **C++17**: `libgrpc++`, `libprotobuf`, CMake
- **Ghostscript**, **Poppler (`pdftotext`)**, **ImageMagick**
- **Docker** e **Docker Compose**
- **GitHub Codespaces**
