import os
from typing import Dict

def eh_endereco_seguro(url: str):
  return url.startswith("https")

def pegar_info_conexao(url: str) -> tuple[str, int]:
    spltAr = url.split("://")
    i = (0, 1)[len(spltAr) > 1]
    host_port = spltAr[i].split("?")[0].split('/')[0].lower().split(':')
    if len(host_port) < 2 or not host_port[1].isnumeric(): 
      return (host_port[0],porta_padrao(url)) 
    else: 
      return (host_port[0],int(host_port[1])) 

def porta_padrao(url: str):
    return 443 if url.startswith("https") else 80

def pegar_endpoint(url: str) -> str:
    spltAr = url.split("://")
    i = (0, 1)[len(spltAr) > 1]
    spltAr = spltAr[i].split('/', 1)
    if len(spltAr) <= 1: return "/"
    else: return ("/" + spltAr[1].lower())

def pegar_nome_arquivo(path: str):
  file_name = path.strip("/").split("?")[0].split("/")[-1]
  return file_name if "." in file_name else "index.html"

def add_hostname(hostname: str, path: str):
  hostname = hostname.split("?")[0].strip("/")
  path = path.strip('./')

  if hostname.endswith((".html",".php",".jsp",".css",".js",".xml",".json")):
    hostname = os.path.dirname(hostname) #remove arquivos pra não salvar coisas tipo "pagina2/index.html/imgs/foto.jpg" e sim "pagina2/imgs/foto.jpg"
    
  if ".." in path: #voltar 1 pasta
    hostname = hostname[:hostname.rfind("/")]

  return path if "http" in path else f"{hostname}/{path}"


def salvar_arquivo(data: bytes, path: str):
  file = open(path, 'wb')
  file.write(data)
  file.close()

def parse_response_headers(h_txt: str):
  linha_1, *linhas = h_txt.split("\n")
  protocolo, status, mensagem = linha_1.split(" ",2)
  h_dict: Dict[str, str | float | int] = {
    "status_code": int(status), 
    "message": mensagem, 
    "protocol": protocolo
  }
  for linha in linhas:
    chave,valor =  linha.lower().strip("\r\n").split(":",1)
    h_dict[chave] = valor.strip() if not valor.isnumeric()\
      else float(valor) if "." in valor\
      else int(valor) 
  return h_dict
