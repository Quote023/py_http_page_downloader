import argparse
import logging
import threading
from crawler import baixar
from utils import pegar_info_conexao

cache = set()

parser = argparse.ArgumentParser(description='Salva o corpo da resposta http')
parser.add_argument('url', type=str, help='o url que vai ser salvo')
parser.add_argument('--log', action='store_const',const=True, help='logar requests')
parser.add_argument('--mt', action='store_const',const=True, help='usar multi-threading')
parser.add_argument('--rel', action='store_const',const=True, help='substituir caminhos globais por relativos')

args = parser.parse_args()

usar_multi_thread = bool(args.mt)
log = bool(args.log)
rel = bool(args.rel)

def main(url: str):
  hostname,_ = pegar_info_conexao(url)
  urls = baixar(url,log,rel)
  urls = [u for u in urls if hostname in u and u not in cache]
  cache.update(urls)
  for u in urls:
    if usar_multi_thread:
      t = threading.Thread(target=main,args=[u])
      t.start()
    else:
      main(u)


Log_Format = "%(levelname)s - %(message)s"
logging.basicConfig(filename = "logfile.log",filemode = "w", format = Log_Format,  level = logging.DEBUG)

main(str(args.url))
