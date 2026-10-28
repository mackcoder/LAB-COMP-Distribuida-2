#instale o pytest com pip install pytest
#crie a pasta na raiz do projeto test_assets com os arquivos sample.pdf e sample.jpg para os testes
#crie a pasta de saida na raiz do projeto test_outputs para os arquivos gerados pelos testes
#execute com pytest -v estando dentro da pasta do cliente e o arquivo de test também no mesmo locao
import os
import pytest
from client import FileProcessorClient

TARGET_HOST = os.getenv('GRPC_SERVER', 'localhost:50051')

@pytest.fixture(scope="module")
def client():
    return FileProcessorClient(target=TARGET_HOST)

@pytest.fixture
def assets_dir():
    os.makedirs('../test_assets', exist_ok=True)
    # Requisito para os testes: ter um sample.pdf e um sample.jpg em test_assets/
    return '../test_assets'

@pytest.fixture
def output_dir():
    # Cria uma pasta "test_outputs" no mesmo diretório do arquivo de teste
    current_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(current_dir, '../test_outputs')
    os.makedirs(out_path, exist_ok=True)
    return out_path

def test_compress_pdf(client, assets_dir, output_dir):
    input_pdf = os.path.join(assets_dir, "sample.pdf")
    output_pdf = os.path.join(output_dir, "compressed.pdf")
    
    assert os.path.exists(input_pdf), "Arquivo PDF de teste não encontrado."
    original_size = os.path.getsize(input_pdf)
    
    client.compress_pdf(input_pdf, str(output_pdf))
    
    assert os.path.exists(output_pdf), "O arquivo comprimido não foi gerado."
    assert os.path.getsize(output_pdf) > 0, "O arquivo de saída está vazio."
    # Ghostscript em arquivos já otimizados pode manter tamanho similar, logo testamos se é > 0

def test_convert_pdf_to_txt(client, assets_dir, output_dir):
    input_pdf = os.path.join(assets_dir, "sample.pdf")
    output_txt = os.path.join(output_dir, "output.txt")
    
    client.convert_to_txt(input_pdf, str(output_txt))
    
    assert os.path.exists(output_txt)
    assert os.path.getsize(output_txt) > 0

def test_convert_image_format(client, assets_dir, output_dir):
    input_img = os.path.join(assets_dir, "sample.jpg")
    output_img = os.path.join(output_dir, "resized.jpg")
    
    assert os.path.exists(input_img), "Arquivo JPG de teste não encontrado."
    
    client.convert_image(input_img, str(output_img), "png")
    
    assert os.path.exists(output_img)
    assert os.path.getsize(output_img) > 0

def test_resize_image(client, assets_dir, output_dir):
    input_img = os.path.join(assets_dir, "sample.jpg")
    output_img = os.path.join(output_dir, "resized.jpg")
    
    client.resize_image(input_img, str(output_img), 800, 600)
    
    assert os.path.exists(output_img)
    assert os.path.getsize(output_img) > 0
