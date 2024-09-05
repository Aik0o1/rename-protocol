import os
import re
import shutil
from PyPDF2 import PdfReader

def encontrar_protocolo_no_pdf(pdf_path, regex_protocolo):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()

        # Buscar o número do protocolo no texto extraído
        match = re.search(regex_protocolo, text)
        if match:
            return match.group(0)  # Retorna o grupo que corresponde ao protocolo completo
    return None

def processar_pdfs(diretorio_origem, diretorio_destino, regex_protocolo):
    # Garantir que o diretório de destino e o diretório de 'naoEncontrado' existam
    os.makedirs(diretorio_destino, exist_ok=True)
    diretorio_nao_encontrado = os.path.join(diretorio_destino, './naoEncontrado')
    os.makedirs(diretorio_nao_encontrado, exist_ok=True)

    # Iterar sobre todos os arquivos no diretório de origem
    for filename in os.listdir(diretorio_origem):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(diretorio_origem, filename)
            protocolo = encontrar_protocolo_no_pdf(pdf_path, regex_protocolo)

            if protocolo:
                # Remover todos os caracteres que não são dígitos ou letras do protocolo
                protocolo = re.sub(r'\W', '', protocolo)
                
                # Criar uma cópia do arquivo PDF e renomear com o número do protocolo
                novo_nome = f"{protocolo}.pdf"
                novo_caminho = os.path.join(diretorio_destino, novo_nome)
                shutil.copy(pdf_path, novo_caminho)
                print(f"Arquivo {filename} copiado e renomeado para {novo_nome}")
            else:
                # Mover o arquivo para a pasta 'naoEncontrado' se o protocolo não for encontrado
                destino_nao_encontrado = os.path.join(diretorio_nao_encontrado, filename)
                shutil.copy(pdf_path, destino_nao_encontrado)
                print(f"Protocolo não encontrado no arquivo {filename}, copiado para {diretorio_nao_encontrado}")

if __name__ == "__main__":
    # Diretório de origem dos PDFs
    diretorio_origem = './teste'

    # Diretório de destino para salvar os PDFs renomeados
    diretorio_destino = './renomeados'

    # Expressão regular para encontrar o número do protocolo nos formatos "10/003229-0" ou "PIP1902094449"
    regex_protocolo = r'(\d{2}/\d{6}-\d{1})|([A-Z]{3}\d{10})|Protocolo:\s*(\d{2}/\d{6}-\d{1})'
    
    
    # Processar os PDFs
    processar_pdfs(diretorio_origem, diretorio_destino, regex_protocolo)
    