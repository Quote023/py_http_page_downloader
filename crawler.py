import logging
import os
from pathlib import Path
import re
import socket
import ssl

from utils import *

def baixar(url: str,log: bool,rel: bool) -> list[str]:
  logger = logging.getLogger()
  url = url.replace(" ","")  #remover espaços em branco na URL
  #colocar protocolo nas urls vazias (assumir que é http caso não tenha nada)
  if not url.startswith("http"): url = "http://" + url 
  
  if "#" in url.split("/")[-1].split("?")[0]:
    return {} #ignorar urls hash (normalmente apenas indicam uma seção da mesma página)
  
  print(f"Baixando: {url}")
  usar_ssl = eh_endereco_seguro(url) #se o endereço tiver "https://" no inicio, usar SSL
  hostname,porta = pegar_info_conexao(url) #função que separa protocolo://hostname:porta/endpoint
  endpoint = pegar_endpoint(url)
  server_address = (hostname.encode(), porta) # tupla de conexão pro socket
  request_header = (f'GET {endpoint} HTTP/1.0\r\nHost: {hostname}\r\nAccept: */*\r\n\r\n') # cabeçalho padrão  
  if log:
    print("-------REQUEST-------")
    print("endpoint:" + endpoint)
    print("hostname:" + hostname)
    print("complete:" + f"{hostname}:{porta}{endpoint}" )
    print("---------------------")
    print(request_header.strip())
  clt_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if usar_ssl: clt_sock = upgrade_ssl(clt_sock,hostname)
  clt_sock.settimeout(10.0) # tempo máximo de resposta do servidor
  try:
    clt_sock.connect(server_address)
    clt_sock.send(request_header.encode())
    response = b''
    while True:
      recv = clt_sock.recv(1024)
      if not recv: break
      response += recv

    clt_sock.close()
  except Exception as e: # se der algum erro: escrever exceção no log e ignorar url
    logger.error(f"Falha ao baixar {url} =>> {str(e)}") 
    return {}

  partes = response.split(b"\r\n\r\n", 1) #separar corpo do cabeçalho
  headers = parse_response_headers(partes[0].decode()) #dicionário com cada parte do cabeçalho como chave:valor
  body = partes[1]
  if log:
    print("------RESPONSE-------")
    print(partes[0].decode())
    print("--------RESULT-------")

  match headers.get("status_code"):
    case 300 | 301 | 302 | 303 | 307 | 308: #redirects
        alvo = headers.get("location")
        print(f"Redirecionando: {alvo}")
        return { str(alvo) }
    case status if status >= 200 and status < 300: #sucessos
        endpoint_base = endpoint.split("?")[0] # limpar parametros opcionais da url "/index.html?pagina=2" => "/index.html"
        file_name = pegar_nome_arquivo(endpoint_base)
        subpasta = endpoint_base.removesuffix(file_name).strip("/")
        path_to_save = os.path.join(os.getcwd(),"out",hostname,subpasta).removesuffix("/") # ./out/<site>/<arquivos>
        Path(path_to_save).mkdir(parents=True, exist_ok=True)
        file_path = path_to_save + "/" + file_name.strip("/")
        file_data = body
        if rel: # caminho relátivo ex: 
          # "host.com.br/pagina2/index.html" faz referencia à "host.com.br/img/bg.jpg" => subpasta: "/pagina2"
          # "host.com.br/img/bg.jpg" vai ser substituido por "../img/bg.jpg"
          rel_path = b"." if subpasta.count("/") <= 0 else ("../"*subpasta.count("/")).strip("/").encode() 
          file_data = re.sub(fr"https?:\/\/(?:www.)?{hostname}".encode(),rel_path,body)
        logger.debug("salvo com sucesso: " + path_to_save[path_to_save.find("out"):] + " >=> " + file_name)
        salvar_arquivo(file_data, file_path)
        if "text/html" in headers.get("content-type"): # baixa o que tiver em tags <img src={url}/> | <a href={url}/> | <div background={url}/>
          return {u for u in pegar_arquivos(body.decode(),url) if u}
        elif "text/css" in headers.get("content-type"): # baixa o que tiver em @import url(<url>)
          return {u for u in pegar_arquivos_css(body.decode(),url) if u}
        else: return {}
    case _: return {}


def pegar_arquivos(html: str,hostname: str):
    regex = re.compile(r'(?:(?:href=)|(?:src=)|(?:background=))(?:\"|\')(.[^">]+?)(?=\"|\')')
    imgs = regex.findall(html)
    return {add_hostname(hostname,src) for src in imgs if not src.startswith("data:")}

def pegar_arquivos_css(css: str,hostname: str):
    regex = re.compile(r'(?:url\()(.[^">]+?)(?=\))')
    imgs: list[str] = regex.findall(css)
    return {add_hostname(hostname,src.strip("'\"")) for src in imgs if not src.startswith("data:")}


def upgrade_ssl(sock: socket.socket, hostname: str):
    return ssl.create_default_context().wrap_socket(sock, server_hostname=hostname)
