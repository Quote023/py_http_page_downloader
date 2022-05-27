import argparse
import os
import re
import socket
import ssl
from pathlib import Path
# Funções úteis


def pegarHostname(url: str) -> str:
    spltAr = url.split("://")
    i = (0, 1)[len(spltAr) > 1]
    # remover query params, endpoint etc
    return spltAr[i].split("?")[0].split('/')[0].split(':')[0].lower()


def pegarEndpoint(url: str) -> str:
    spltAr = url.split("://")
    i = (0, 1)[len(spltAr) > 1]
    spltAr = spltAr[i].split('/', 1)
    if(len(spltAr) <= 1):
        return "/"
    else:
        return ("/" + spltAr[1].lower())


parser = argparse.ArgumentParser(description='Salva o corpo da resposta http')
parser.add_argument('url', type=str, help='o url que vai ser salvo')
parser.add_argument('--log', action='store_const',
                    const=True, help='logar requests')

args = parser.parse_args()
url = str(args.url)
log = bool(args.log)


def baixar(url):
    if log and not str(args.url) == url:
        print("\r\n")

    print(f"Baixando: {url}")

    usarSsl = url.startswith("https")
    porta = 443 if usarSsl else 80

    hostname = pegarHostname(url)
    endpoint = pegarEndpoint(url)

    server_address = (hostname.encode(), porta)
    request_header = (f'GET {endpoint} HTTP/1.0\r\n'
                      f'Host: {hostname}\r\n'
                      f'Accept: */*\r\n\r\n')

    if log:
        print("-------REQUEST-------")
        print("endpoint:" + endpoint)
        print("hostname:" + hostname)
        print("---------------------")
        print(request_header.strip())

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if usarSsl:
        ctx = ssl.create_default_context()
        client_socket = ctx.wrap_socket(
            client_socket, server_hostname=hostname)

    client_socket.connect(server_address)

    client_socket.send(request_header.encode())

    response = b''
    while True:
        recv = client_socket.recv(4096)
        if not recv:
            break
        response += recv

    client_socket.close()

    partes = response.split(b"\r\n\r\n", 1)
    headers = partes[0].decode().split("\r\n")
    status_code = int(headers[0].split(" ")[1])
    body = partes[1]
    if log:
        print("------RESPONSE-------")
        print(partes[0].decode())
        print("--------RESULT-------")

    match status_code:
        case 301:
            alvo = (
                [s for s in headers if "location:" in s]
                [0].split('location:')
                [1].strip()
            )
            print(f"Redirecionando: {alvo}")
            baixar(alvo)
        case _ if status_code >= 200 and status_code < 300:
            site_folder = hostname.replace(".", "_")
            file_name = endpoint.split("/")[-1]
            file_name = file_name if "." in file_name else "index.html"
            path_to_save = Path(
                f"out/{site_folder}" + endpoint.removesuffix(file_name))
            path_to_save.mkdir(parents=True, exist_ok=True)
            file_path = os.getcwd() + "/" + str(path_to_save) + "/" + file_name
            if log:
                print("salvando em:" + file_path)
            if "content-type: text/html" in partes[0].decode().lower():
              baixar_imagens(body.decode(),hostname)
            salvar(body, file_path)


def baixar_imagens(html: str,hostname: str):
    rgx_imgs = re.compile('<img[^>]+src=(?:\"|\')(.[^">]+?)(?=\"|\')')
    for src in rgx_imgs.findall(html):
        if(src.startswith("data:")): continue
        is_url_valida = "http" in src
        url = src if is_url_valida else add_hostname(hostname, src)
        baixar(url)


def add_hostname(hostname: str, path: str):
    hostname + "/" + path.removeprefix("./").removeprefix("/")


def baixar_arquivos(html: str):
    pass


def salvar(data: bytes, path: str):
    file = open(path, 'wb')
    file.write(data)
    file.close()


baixar(url)
