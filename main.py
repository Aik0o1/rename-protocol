import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import os
import re
import shutil
import gc
import logging

# Configuração do logging
logging.basicConfig(
    filename='processamento_pdfs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

def extrair_texto_tesseract(imagens):
    textos_encontrados = []
    for imagem in imagens:
        imagem_preprocessada = preprocessar_imagem(imagem)
        texto = pytesseract.image_to_string(imagem_preprocessada)
        textos_encontrados.append(texto)
    return " ".join(textos_encontrados)

def encontrar_protocolo_no_texto(texto, regex_prioritario, regex_secundario):
    match_prioritario = re.search(regex_prioritario, texto)
    if match_prioritario:
        return match_prioritario.group(0)
    match_secundario = re.search(regex_secundario, texto)
    if match_secundario:
        return match_secundario.group(0)

def processar_pdfs_lote(diretorio_origem, diretorio_destino, regex_prioritario, regex_secundario, tamanho_lote=100):
    os.makedirs(diretorio_destino, exist_ok=True)
    diretorio_nao_encontrado = os.path.join(diretorio_destino, 'naoEncontrado')
    os.makedirs(diretorio_nao_encontrado, exist_ok=True)
    
    arquivos = [f for f in os.listdir(diretorio_origem) if f.endswith('.pdf')]
    
    for i in range(0, len(arquivos), tamanho_lote):
        lote_atual = arquivos[i:i+tamanho_lote]
        logging.info(f"Processando lote {i//tamanho_lote + 1} de {len(arquivos)//tamanho_lote + 1}")
        
        for filename in lote_atual:
            try:
                pdf_path = os.path.join(diretorio_origem, filename)
                imagens = pdf_para_imagens(pdf_path)
                texto = extrair_texto_tesseract(imagens)
                protocolo = encontrar_protocolo_no_texto(texto, regex_prioritario, regex_secundario)

                if protocolo:
                    protocolo = re.sub(r'\W', '', protocolo)
                    novo_nome = f"{protocolo}.pdf"
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
    diretorio_origem = './pdfs'
    diretorio_destino = './renomeadosComTesseract'
    regex_prioritario = r'(PIP|PIN|PIE)\d{10}'
    regex_secundario = r'\b\d{2}/\d{6}-\d\b'

    # Processar PDFs em lotes de 100
    processar_pdfs_lote(diretorio_origem, diretorio_destino, regex_prioritario, regex_secundario, tamanho_lote=100)
