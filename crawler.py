from asyncio.log import logger
import os
from pathlib import Path
import re
import socket
import ssl

from utils import *

def baixar(url: str,log: bool,rel: bool) -> list[str]:
  print(f"Baixando: {url}")
  usar_ssl = eh_endereco_seguro(url)
  hostname,porta = pegar_info_conexao(url)
  endpoint = pegar_endpoint(url)
  server_address = (hostname.encode(), porta)
  request_header = (f'GET {endpoint} HTTP/1.0\r\nHost: {hostname}\r\nAccept: */*\r\n\r\n')
    
  if log:
    print("-------REQUEST-------")
    print("endpoint:" + endpoint)
    print("hostname:" + hostname)
    print("complete:" + f"{hostname}:{porta}{endpoint}" )
    print("---------------------")
    print(request_header.strip())

  clt_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if usar_ssl: clt_sock = upgrade_ssl(clt_sock,hostname)

  clt_sock.connect(server_address)
  clt_sock.send(request_header.encode())

  response = b''
  while True:
    recv = clt_sock.recv(1024)
    if not recv: break
    response += recv

  clt_sock.close()

  partes = response.split(b"\r\n\r\n", 1)
  headers = parse_response_headers(partes[0].decode())
  body = partes[1]
  if log:
    print("------RESPONSE-------")
    print(partes[0].decode())
    print("--------RESULT-------")

  match headers.get("status_code"):
    case 300 | 301 | 302 | 303 | 307 | 308:
        alvo = headers.get("location")
        print(f"Redirecionando: {alvo}")
        return [ str(alvo) ]
    case status if status >= 200 and status < 300:
        file_name = pegar_nome_arquivo(endpoint)
        subpasta = endpoint.removesuffix(file_name).strip("/")
        path_to_save = os.path.join(os.getcwd(),"out",hostname,subpasta).removesuffix("/")
        Path(path_to_save).mkdir(parents=True, exist_ok=True)
        file_path = path_to_save + "/" + file_name.strip("/")
        file_data = body
        if rel: file_data = re.sub(fr"https?:\/\/(?:www.)?{hostname}".encode(),b".",body)
        salvar_arquivo(file_data, file_path)
        if "text/html" in headers.get("content-type"):
          return [u for u in pegar_arquivos(body.decode(),url) if u]
        else: return []
    case _:
        return []


def pegar_arquivos(html: str,hostname: str):
    regex = re.compile(r'(?:(?:href=)|(?:src=)|(?:background=))(?:\"|\')(.[^">]+?)(?=\"|\')')
    imgs = regex.findall(html)
    return {add_hostname(hostname,src) for src in imgs if not src.startswith("data:")}


def upgrade_ssl(sock: socket.socket, hostname: str):
    return ssl.create_default_context().wrap_socket(sock, server_hostname=hostname)

def test_socket(sock: socket.socket, default: socket.socket = None):
  if not sock: return (False, default)
  try:
    data = sock.recv(1)
    if data: print(data)
    return (True, sock)
  except Exception as e:
    print(e)
    return (False, default)