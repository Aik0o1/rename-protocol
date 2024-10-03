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
from collections import Counter

# Configuração do logging
logging.basicConfig(
    filename='logs.log',
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

def pdf_para_imagens(pdf_path, dpi=800):
    return convert_from_path(pdf_path, dpi=dpi)

def preprocessar_imagem(imagem):
    imagem_cinza = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2GRAY)
    imagem_suavizada = cv2.medianBlur(imagem_cinza, 3)
    _, imagem_bin = cv2.threshold(imagem_suavizada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    imagem_bin = cv2.dilate(imagem_bin, kernel, iterations=1)
    imagem_bin = cv2.erode(imagem_bin, kernel, iterations=1)
    return imagem_bin

def rotacionar_imagem(imagem, angulo):
    (h, w) = imagem.shape[:2]
    centro = (w // 2, h // 2)
    matriz_rotacao = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    return cv2.warpAffine(imagem, matriz_rotacao, (w, h))

def verificar_protocolo_semelhante(protocolos):
    contagem = Counter(protocolos)
    protocolos_mais_comuns = contagem.most_common()
    
    # Lista final de protocolos únicos
    protocolos_unicos = []

    while protocolos_mais_comuns:
        protocolo_atual, _ = protocolos_mais_comuns.pop(0)
        protocolo_similar = False

        # Verifica se há protocolos semelhantes na lista final
        for prot in protocolos_unicos:
            dif = sum(1 for a, b in zip(prot, protocolo_atual) if a != b)
            if dif == 1 and  protocolo_atual[0] != prot[0]:  # Se diferir por apenas um dígito
                protocolo_similar = True
                break

        if not protocolo_similar:
            protocolos_unicos.append(protocolo_atual)

    return protocolos_unicos


def extrair_texto_tesseract_por_pagina(pdf_path, regex_prioritario, regex_secundario):
    imagens = pdf_para_imagens(pdf_path)
    protocolos_encontrados = []

    angulos = list(range(1, 20)) + list(range(175, 186)) + list(range(225, 242)) + list(range(265, 271))

    for i, imagem in enumerate(imagens):
        imagem_preprocessada = preprocessar_imagem(imagem)
        
        for angulo in angulos:
            imagem_rotacionada = rotacionar_imagem(imagem_preprocessada, angulo)
            texto = pytesseract.image_to_string(imagem_rotacionada)
            
            encontrados_prioritario = re.findall(regex_prioritario, texto)
            encontrados_secundario = re.findall(regex_secundario, texto)

            if encontrados_prioritario:
                logging.info(f"Protocolo(s) prioritário(s) encontrado(s) no ângulo {angulo}: {encontrados_prioritario}")
                print(f"Protocolo(s) prioritário(s) encontrado(s) no ângulo {angulo}: {encontrados_prioritario}")

            if encontrados_secundario:
                logging.info(f"Protocolo(s) secundário(s) encontrado(s) no ângulo {angulo}: {encontrados_secundario}")
                print(f"Protocolo(s) secundário(s) encontrado(s) no ângulo {angulo}: {encontrados_secundario}")

            # Adiciona os protocolos encontrados à lista geral
            protocolos_encontrados.extend(encontrados_prioritario)
            protocolos_encontrados.extend(encontrados_secundario)

            del imagem_rotacionada
            gc.collect()
        
        del imagem_preprocessada
        gc.collect()
    
    if protocolos_encontrados:
        protocolos_finais = verificar_protocolo_semelhante(protocolos_encontrados)
        return protocolos_finais
    else:
        return []


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
                
                reader = PdfReader(pdf_path)
                total_paginas = len(reader.pages)
                
                protocolos_encontrados = []
                
                if total_paginas > 10:
                    subdocumentos = dividir_pdf(pdf_path, max_paginas_por_subdocumento)
                    
                    for subdocumento in subdocumentos:
                        protocolos_encontrados.extend(extrair_texto_tesseract_por_pagina(subdocumento, regex_prioritario, regex_secundario))

                    for subdocumento in subdocumentos:
                        os.remove(subdocumento)
                        logging.info(f"Subdocumento {subdocumento} excluído")

                else:
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
    diretorio_origem = './DOCUMENTOS'
    diretorio_destino = './Documentos-Renomeados'
    regex_prioritario = r'\b(?:PIP|PIN|PIE)(?=\d{10})\d{10}\b'
    regex_secundario = r'\b\d{2}/\d{6}-\d\b'

    # Processar PDFs em lotes de 10
    processar_pdfs_lote(diretorio_origem, diretorio_destino, regex_prioritario, regex_secundario, tamanho_lote=10, max_paginas_por_subdocumento=2)
