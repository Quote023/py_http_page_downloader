import argparse
import logging
from threading import Thread
from crawler import baixar
from utils import pegar_info_conexao

cache = set()

parser = argparse.ArgumentParser(description='Salva o corpo da resposta http')
parser.add_argument('url', type=str, help='o url que vai ser salvo')
parser.add_argument('--log', action='store_const',const=True, help='logar requests')
parser.add_argument('--mt', action='store_const',const=True, help='usar multi-threading')
parser.add_argument('--tc', type=int, default=5, help='usar multi-threading')
parser.add_argument('--rel', action='store_const',const=True, help='substituir caminhos globais por relativos')

args = parser.parse_args()

usar_multi_thread = bool(args.mt)
log = bool(args.log)
thread_qtd = int(args.tc)
rel = bool(args.rel)

def main(url: str):
  hostname,_ = pegar_info_conexao(url)
  urls = baixar(url,log,rel)
  urls = [u for u in urls if hostname in u and u not in cache]
  cache.update(urls)
  if usar_multi_thread: 
    rodar_multi_threaded(urls)
  else: 
    for u in urls: main(u)


def rodar_multi_threaded(urls):
  #transforma a lista em uma matriz, pra só instanciar uma qtd especifica de threads por vez
  matriz: list[list[str]] =  [urls[i:i + thread_qtd] for i in range(0, len(urls), thread_qtd)]
  for us in matriz:
    threads: list[Thread] = []
    for u in us:
        t = Thread(target=main,args=[u])
        t.start()
        threads.append(t)
    for t in threads:
      t.join()

Log_Format = "%(levelname)s - %(message)s"
logging.basicConfig(filename = "logfile.log",filemode = "w", format = Log_Format,  level = logging.DEBUG)

main(str(args.url))
