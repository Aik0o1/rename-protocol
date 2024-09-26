import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import os
import re
import shutil
import gc
import logging
from PyPDF2 import PdfReader, PdfWriter

# Configuração do logging
logging.basicConfig(
    filename='logTestes.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def dividir_pdf(pdf_path, max_paginas_por_subdocumento=10):
    reader = PdfReader(pdf_path)
    total_paginas = len(reader.pages)
    subdocumentos = []

    for i in range(0, total_paginas, max_paginas_por_subdocumento):
        writer = PdfWriter()
        for j in range(i, min(i + max_paginas_por_subdocumento, total_paginas)):
            writer.add_page(reader.pages[j])
        
        sub_pdf_path = f"{pdf_path}_parte_{i//max_paginas_por_subdocumento + 1}.pdf"
        with open(sub_pdf_path, "wb") as sub_pdf_file:
            writer.write(sub_pdf_file)
        
        subdocumentos.append(sub_pdf_path)
    
    return subdocumentos

def pdf_para_imagens(pdf_path, dpi=500):
    return convert_from_path(pdf_path, dpi=dpi)

def preprocessar_imagem(imagem):
    imagem_cinza = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2GRAY)
    imagem_suavizada = cv2.medianBlur(imagem_cinza, 3)
    _, imagem_bin = cv2.threshold(imagem_suavizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    imagem_bin = cv2.dilate(imagem_bin, kernel, iterations=1)
    imagem_bin = cv2.erode(imagem_bin, kernel, iterations=1)
    return imagem_bin

def extrair_texto_tesseract_por_pagina(pdf_path, regex_prioritario, regex_secundario):
    imagens = pdf_para_imagens(pdf_path)
    protocolos_encontrados = set()  # Usar um conjunto para evitar duplicatas

    for i, imagem in enumerate(imagens):
        imagem_preprocessada = preprocessar_imagem(imagem)
        texto = pytesseract.image_to_string(imagem_preprocessada)

        # Procurar todos os protocolos
        protocolos_encontrados.update(re.findall(regex_prioritario, texto))
        protocolos_encontrados.update(re.findall(regex_secundario, texto))

        # Limpar a memória após processar a página
        del imagem_preprocessada
        gc.collect()
        
    return list(protocolos_encontrados)  # Retorna uma lista de protocolos encontrados

def processar_pdfs_lote(diretorio_origem, diretorio_destino, regex_prioritario, regex_secundario, tamanho_lote=100, max_paginas_por_subdocumento=10):
    os.makedirs(diretorio_destino, exist_ok=True)
    diretorio_nao_encontrado = os.path.join(diretorio_destino, 'naoEncontrado')
    os.makedirs(diretorio_nao_encontrado, exist_ok=True)
    
    arquivos = [f for f in os.listdir(diretorio_origem) if f.endswith('.pdf')]
    
    for i in range(0, len(arquivos), tamanho_lote):
        lote_atual = arquivos[i:i+tamanho_lote]
        logging.info(f"Processando lote {i//tamanho_lote + 1} de {len(arquivos)//tamanho_lote + 1}")
        
        for filename in lote_atual:
            try:
                logging.info(f"Processando arquivo {filename}")
                pdf_path = os.path.join(diretorio_origem, filename)
                
                # Verificar o número de páginas no PDF
                reader = PdfReader(pdf_path)
                total_paginas = len(reader.pages)
                
                protocolos_encontrados = []
                
                # Se o documento tiver mais de 10 páginas, divida-o em subdocumentos
                if total_paginas > 10:
                    subdocumentos = dividir_pdf(pdf_path, max_paginas_por_subdocumento)
                    
                    # Processar cada subdocumento
                    for subdocumento in subdocumentos:
                        protocolos_encontrados.extend(extrair_texto_tesseract_por_pagina(subdocumento, regex_prioritario, regex_secundario))

                    # Excluir todos os subdocumentos gerados
                    for subdocumento in subdocumentos:
                        os.remove(subdocumento)
                        logging.info(f"Subdocumento {subdocumento} excluído")

                else:
                    # Processar PDF normalmente se tiver 10 páginas ou menos
                    protocolos_encontrados = extrair_texto_tesseract_por_pagina(pdf_path, regex_prioritario, regex_secundario)
                
                if protocolos_encontrados:
                    protocolos_unicos = sorted(set(protocolos_encontrados))
                    novo_nome = " ".join(re.sub(r'\W', '', protocolo) for protocolo in protocolos_unicos) + ".pdf"
                    novo_caminho = os.path.join(diretorio_destino, novo_nome)
                    shutil.move(pdf_path, novo_caminho)
                    logging.info(f"Arquivo {filename} movido e renomeado para {novo_nome}")
                else:
                    destino_nao_encontrado = os.path.join(diretorio_nao_encontrado, filename)
                    shutil.move(pdf_path, destino_nao_encontrado)
                    logging.info(f"Protocolo não encontrado no arquivo {filename}, movido para {diretorio_nao_encontrado}")

                gc.collect()
            except Exception as e:
                logging.error(f"Erro ao processar arquivo {filename}: {e}")

if __name__ == "__main__":
    diretorio_origem = './testes'
    diretorio_destino = './testesRenomeados'
    regex_prioritario = r'(PIP|PIN|PIE)\d{10}'
    regex_secundario = r'\b\d{2}/\d{6}-\d\b'

    # Processar PDFs em lotes de 10
    processar_pdfs_lote(diretorio_origem, diretorio_destino, regex_prioritario, regex_secundario, tamanho_lote=10, max_paginas_por_subdocumento=10)
