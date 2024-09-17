# Rename-PDFs-Protocol-Script

## Visão Geral
Esse script tem finalidade de ler PDFs em busca do número de protocolo presente no mesmo a fim de renomear e tornar mais simples a sua busca.

O script possui as seguintes características:
**-**


# Processador de PDFs com Tesseract e Regex

Este projeto é um script Python que processa arquivos PDF em lotes, extrai texto utilizando OCR (Tesseract) e busca por padrões de protocolo em formatos específicos, utilizando expressões regulares (regex). Os arquivos PDF são renomeados de acordo com o protocolo encontrado e organizados em pastas.

## Funcionalidades

- **Conversão de PDFs para imagens**: Utiliza a biblioteca `pdf2image` para converter arquivos PDF em imagens.
- **Processamento de imagens**: Aplica pré-processamento nas imagens usando a biblioteca `OpenCV` para melhorar a extração de texto.
- **Extração de texto via OCR**: Utiliza o Tesseract OCR para extrair texto das imagens.
- **Busca de protocolos no texto**: Busca por dois tipos de padrões de protocolo utilizando expressões regulares. Caso um protocolo seja encontrado, o arquivo PDF é renomeado.
- **Organização dos PDFs**: Os PDFs são movidos para uma pasta de saída. Se um protocolo for encontrado, o arquivo é renomeado. Se nenhum protocolo for encontrado, o arquivo é movido para uma subpasta chamada `naoEncontrado`.
- **Processamento em lotes**: Os arquivos PDF são processados em lotes, permitindo lidar com grandes volumes de documentos.

## Pré-requisitos

Para executar o script, certifique-se de ter as seguintes bibliotecas Python instaladas:

```bash
pip install pytesseract pdf2image opencv-python numpy
```
Além disso, você precisará ter o Tesseract OCR  e o Poppler instalados. Para instalar:
No Linux (Ubuntu):
```bash
sudo apt install tesseract-ocr
sudo apt install poppler-utils
```
No Windows, baixe e instale o Tesseract e o Poppler a partir do site oficial: https://github.com/tesseract-ocr/tesseract.
https://github.com/oschwartz10612/poppler-windows/releases/tag/v24.07.0-0

## Estrutura do Projeto
* main.py: Script principal que processa os PDFs.
* processamento_pdfs.log: Arquivo de log que armazena informações sobre os PDFs processados.

## Como usar
1. Coloque seus arquivos PDF na pasta ./pdfs.
2. Execute o script:
```bash
python3 main.py
```
3. O script processará os PDFs em lotes (com tamanho configurável) e salvará os arquivos processados na pasta ./renomeadosComTesseract. Caso não seja encontrado um protocolo, o arquivo será movido para a subpasta ./renomeadosComTesseract/naoEncontrado.

## Configuração
Você pode alterar o comportamento do script modificando as seguintes variáveis:
* regex_prioritario: Expressão regular para protocolos prioritários. O padrão é (PIP|PIN|PIE)\d{10}.
* regex_secundario: Expressão regular para protocolos secundários. O padrão é \b\d{2}/\d{6}-\d\b.
* tamanho_lote: Define quantos PDFs serão processados por vez. O padrão é 5.

## Log de Execução
O script gera um arquivo de log (processamento_pdfs.log) que armazena:
* Mensagens de informação sobre o andamento do processamento.
* Erros que possam ocorrer durante o processamento dos arquivos.

```log
2024-09-13 10:12:45 - INFO - Processando lote 1 de 2
2024-09-13 10:12:45 - INFO - Arquivo documento1.pdf copiado e renomeado para PIP1234567890.pdf
2024-09-13 10:12:50 - INFO - Protocolo não encontrado no arquivo documento2.pdf, copiado para ./renomeadosComTesseract/naoEncontrado
``
