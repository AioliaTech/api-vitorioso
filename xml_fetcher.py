import requests
import xmltodict
import json
import os
import re
from datetime import datetime
from unidecode import unidecode
from typing import Dict, List, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod

# =================== CONFIGURAÇÕES GLOBAIS =======================

JSON_FILE = "data.json"

# =================== MAPEAMENTOS DE VEÍCULOS =======================

MAPEAMENTO_CATEGORIAS = {}
OPCIONAL_CHAVE_HATCH = "limpador traseiro"

# --- Listas de Modelos por Categoria ---

hatch_models = ["gol", "uno", "palio", "celta", "march", "sandero", "i30", "golf", "fox", "up", "fit", "etios", "bravo", "punto", "208", "argo", "mobi", "c3", "picanto", "stilo", "c4 vtr", "kwid", "soul", "agile", "fusca", "a1", "new beetle", "116i", "118i", "120i", "125i", "m135i", "m140i"]
for model in hatch_models: MAPEAMENTO_CATEGORIAS[model] = "Hatch"

sedan_models = ["civic", "a6", "sentra", "jetta", "voyage", "siena", "grand siena", "cobalt", "logan", "fluence", "cerato", "elantra", "virtus", "accord", "altima", "fusion", "passat", "vectra sedan", "classic", "cronos", "linea", "408", "c4 pallas", "bora", "hb20s", "lancer", "camry", "onix plus", "azera", "malibu", "318i", "320d", "320i", "328i", "330d", "330i", "335i", "520d", "528i", "530d", "530i", "535i", "540i", "550i", "740i", "750i", "c180", "c200", "c250", "c300", "e250", "e350", "m3", "m5", "s4", "classe c", "classe e", "classe s", "eqe", "eqs"]
for model in sedan_models: MAPEAMENTO_CATEGORIAS[model] = "Sedan"

hatch_sedan_models = ["onix", "hb20", "yaris", "city", "a3", "corolla", "focus", "fiesta", "corsa", "astra", "vectra", "cruze", "clio", "megane", "206", "207", "307", "tiida", "ka", "versa", "prisma", "polo", "c4", "sonic", "série 1", "série 2", "série 3", "série 4", "série 5", "série 6", "série 7", "classe a", "cla"]
for model in hatch_sedan_models: MAPEAMENTO_CATEGORIAS[model] = "hatch,sedan"

suv_models = ["xc60", "tiggo", "edge", "outlander", "range rover evoque", "song plus", "duster", "ecosport", "hrv", "hr-v", "compass", "renegade", "tracker", "kicks", "captur", "creta", "tucson", "santa fe", "sorento", "sportage", "pajero", "tr4", "aircross", "tiguan", "t-cross", "tcross", "rav4", "land cruiser", "cherokee", "grand cherokee", "trailblazer", "pulse", "fastback", "territory", "bronco sport", "2008", "3008", "5008", "c4 cactus", "taos", "crv", "cr-v", "corolla cross", "hilux sw4", "sw4", "pajero sport", "commander", "nivus", "equinox", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "ix", "ix1", "ix2", "ix3", "gla", "glb", "glc", "gle", "gls", "classe g", "eqa", "eqb", "eqc", "q2", "q3", "q5", "q7", "q8", "q6 e-tron", "e-tron", "q4 e-tron", "q4etron", "wrx", "xv"]
for model in suv_models: MAPEAMENTO_CATEGORIAS[model] = "SUV"

caminhonete_models = ["duster oroch", "d20", "hilux", "ranger", "s10", "s-10", "l200", "triton", "toro", "frontier", "amarok", "maverick", "montana", "ram 1500", "rampage", "f-250", "f250", "courier", "dakota", "gladiator", "hoggar"]
for model in caminhonete_models: MAPEAMENTO_CATEGORIAS[model] = "Caminhonete"

utilitario_models = ["saveiro", "strada", "oroch", "kangoo", "partner", "doblo", "fiorino", "kombi", "doblo cargo", "berlingo", "combo", "express", "hr"]
for model in utilitario_models: MAPEAMENTO_CATEGORIAS[model] = "Utilitário"

furgao_models = ["boxer", "daily", "ducato", "expert", "jumper", "jumpy", "master", "scudo", "sprinter", "trafic", "transit", "vito"]
for model in furgao_models: MAPEAMENTO_CATEGORIAS[model] = "Furgão"

coupe_models = ["370z", "brz", "camaro", "challenger", "corvette", "gt86", "mustang", "r8", "rcz", "rx8", "supra", "tt", "tts", "veloster", "m2", "m4", "m8", "s5", "amg gt"]
for model in coupe_models: MAPEAMENTO_CATEGORIAS[model] = "Coupe"

conversivel_models = ["911 cabrio", "beetle cabriolet", "boxster", "eos", "miata", "mini cabrio", "slk", "z4", "série 8", "slc", "sl"]
for model in conversivel_models: MAPEAMENTO_CATEGORIAS[model] = "Conversível"

station_wagon_models = ["a4 avant", "fielder", "golf variant", "palio weekend", "parati", "quantum", "spacefox", "rs2", "rs4", "rs6"]
for model in station_wagon_models: MAPEAMENTO_CATEGORIAS[model] = "Station Wagon"

minivan_models = ["caravan", "carnival", "grand c4", "idea", "livina", "meriva", "picasso", "scenic", "sharan", "spin", "touran", "xsara picasso", "zafira", "série 2 active tourer", "classe b", "classe t", "classe r", "classe v"]
for model in minivan_models: MAPEAMENTO_CATEGORIAS[model] = "Minivan"

offroad_models = ["bandeirante", "bronco", "defender", "grand vitara", "jimny", "samurai", "troller", "wrangler"]
for model in offroad_models: MAPEAMENTO_CATEGORIAS[model] = "Off-road"

# =================== UTILS =======================

def normalizar_texto(texto: str) -> str:
    if not texto: return ""
    texto_norm = unidecode(str(texto)).lower()
    texto_norm = re.sub(r'[^a-z0-9\s]', '', texto_norm)
    texto_norm = re.sub(r'\s+', ' ', texto_norm).strip()
    return texto_norm

def definir_categoria_veiculo(modelo: str, carroceria: str = "", opcionais: str = "") -> Optional[str]:
    """
    Define a categoria de um veículo usando busca EXATA no mapeamento.
    Para modelos ambíguos ("hatch,sedan"), usa a carroceria ou opcionais para decidir.
    """
    if not modelo: return None
    
    # Normaliza o modelo do feed para uma busca exata
    modelo_norm = normalizar_texto(modelo)
    
    # Busca pela chave exata no mapeamento
    categoria_result = MAPEAMENTO_CATEGORIAS.get(modelo_norm)
    
    # Se encontrou uma correspondência exata
    if categoria_result:
        if categoria_result == "hatch,sedan":
            # Primeiro tenta usar a carroceria
            if carroceria:
                carroceria_norm = normalizar_texto(carroceria)
                if "hatch" in carroceria_norm or "hatchback" in carroceria_norm:
                    return "Hatch"
                elif "sedan" in carroceria_norm:
                    return "Sedan"
            
            # Se não conseguiu pela carroceria, usa os opcionais
            opcionais_norm = normalizar_texto(opcionais)
            opcional_chave_norm = normalizar_texto(OPCIONAL_CHAVE_HATCH)
            if opcional_chave_norm in opcionais_norm:
                return "Hatch"
            else:
                return "Sedan"
        else:
            # Para todos os outros casos (SUV, Caminhonete, etc.)
            return categoria_result
            
    # Se não encontrou correspondência exata, verifica os modelos ambíguos
    # Isso é útil para casos como "Onix LTZ" corresponder a "onix"
    for modelo_ambiguo, categoria_ambigua in MAPEAMENTO_CATEGORIAS.items():
        if categoria_ambigua == "hatch,sedan":
            if normalizar_texto(modelo_ambiguo) in modelo_norm:
                # Primeiro tenta usar a carroceria
                if carroceria:
                    carroceria_norm = normalizar_texto(carroceria)
                    if "hatch" in carroceria_norm or "hatchback" in carroceria_norm:
                        return "Hatch"
                    elif "sedan" in carroceria_norm:
                        return "Sedan"
                
                # Se não conseguiu pela carroceria, usa os opcionais
                opcionais_norm = normalizar_texto(opcionais)
                opcional_chave_norm = normalizar_texto(OPCIONAL_CHAVE_HATCH)
                if opcional_chave_norm in opcionais_norm:
                    return "Hatch"
                else:
                    return "Sedan"

    return None # Nenhuma correspondência encontrada

def converter_preco(valor: Any) -> float:
    if not valor: return 0.0
    try:
        if isinstance(valor, (int, float)): return float(valor)
        valor_str = str(valor)
        valor_str = re.sub(r'[^\d,.]', '', valor_str).replace(',', '.')
        parts = valor_str.split('.')
        if len(parts) > 2: valor_str = ''.join(parts[:-1]) + '.' + parts[-1]
        return float(valor_str) if valor_str else 0.0
    except (ValueError, TypeError): return 0.0

def safe_get(data: Dict, keys: Union[str, List[str]], default: Any = None) -> Any:
    if isinstance(keys, str): keys = [keys]
    for key in keys:
        if isinstance(data, dict) and key in data and data[key] is not None:
            return data[key]
    return default

def normalize_fotos(fotos_data: Any) -> List[str]:
    """
    Normaliza diferentes estruturas de fotos para uma lista simples de URLs.
    
    Entrada aceitas:
    - Lista simples de URLs: ["url1", "url2"]  
    - Lista aninhada: [["url1", "url2"], ["url3"]]
    - Lista de objetos: [{"url": "url1"}, {"IMAGE_URL": "url2"}]
    - Objeto único: {"url": "url1"}
    - String única: "url1"
    - String com separador pipe: "url1|url2|url3"
    - String com separador vírgula: "url1,url2,url3"
    
    Retorna sempre: ["url1", "url2", "url3"]
    """
    if not fotos_data:
        return []
    
    result = []
    
    def extract_url_from_item(item):
        """Extrai URL de um item que pode ser string, dict ou outro tipo"""
        if isinstance(item, str):
            url = item.strip()
            if not url:
                return []
            
            # Se a string contém pipes, divide por pipe
            if "|" in url:
                return [u.strip() for u in url.split("|") if u.strip()]
            # Se a string contém vírgulas, divide por vírgula
            elif "," in url:
                urls = [u.strip() for u in url.split(",") if u.strip()]
                # Filtra apenas URLs válidas (que contêm http ou começam com /)
                valid_urls = []
                for u in urls:
                    if ("http" in u or u.startswith("/")) and len(u) > 10:
                        valid_urls.append(u)
                return valid_urls
            else:
                return [url] if url else []
                
        elif isinstance(item, dict):
            # Tenta várias chaves possíveis para URL
            for key in ["url", "URL", "src", "IMAGE_URL", "path", "link", "href"]:
                if key in item and item[key]:
                    url = str(item[key]).strip()
                    # Remove parâmetros de query se houver
                    clean_url = url.split("?")[0] if "?" in url else url
                    return [clean_url] if clean_url else []
        return []
    
    def process_item(item):
        """Processa um item que pode ser string, lista ou dict"""
        if isinstance(item, str):
            urls = extract_url_from_item(item)
            result.extend(urls)
        elif isinstance(item, list):
            # Lista aninhada - processa cada subitem
            for subitem in item:
                process_item(subitem)
        elif isinstance(item, dict):
            urls = extract_url_from_item(item)
            result.extend(urls)
    
    # Processa a estrutura principal
    if isinstance(fotos_data, list):
        for item in fotos_data:
            process_item(item)
    else:
        process_item(fotos_data)
    
    # Remove duplicatas e URLs vazias, mantém a ordem
    seen = set()
    normalized = []
    for url in result:
        if url and url not in seen and url.strip() and len(url) > 10:
            seen.add(url)
            normalized.append(url.strip())
    
    # Ordena as fotos pelo número que aparece antes da extensão
    def extract_number_from_url(url):
        """Extrai o número do final da URL antes da extensão"""
        # Procura por padrão como CRETA-12.avif, NIVUS-5.avif, etc.
        match = re.search(r'-(\d+)\.(?:avif|jpg|jpeg|png|webp)$', url, re.IGNORECASE)

# =================== PARSER WORDPRESS =======================

class WordPressParser:
    """
    Parser específico para estruturas XML do WordPress/WooCommerce de veículos
    Processa estruturas no formato <data><post>...</post></data>
    """
    
    def can_parse(self, data: Any, url: str) -> bool:
        """
        Verifica se os dados são do formato WordPress
        """
        # Verifica estrutura básica
        if not isinstance(data, dict):
            return False
        
        # Procura pela estrutura <data><post> ou similar
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                return True
        
        # Verifica se é uma lista de posts diretamente
        if "post" in data:
            return True
            
        return False
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """
        Processa dados do WordPress
        """
        # Extrai os posts da estrutura
        posts = self._extract_posts(data)
        
        parsed_vehicles = []
        
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            # Debug: mostra os campos disponíveis (apenas para o primeiro post)
            if len(parsed_vehicles) == 0:
                print(f"[DEBUG] Campos disponíveis no XML:")
                for key in sorted(post.keys()):
                    value = post[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {key}: {value}")
                print()
            
            # Extrai dados básicos do veículo
            marca = self._safe_get_post_field(post, ["Marca", "marca", "_marca"])
            modelo = self._safe_get_post_field(post, ["Modelo", "modelo", "_modelo"])
            versao = self._safe_get_post_field(post, ["Verso", "versao", "_versao", "Version"])
            carroceria = self._safe_get_post_field(post, ["_carroceria", "carroceria", "Carroceria"])
            opcionais = self._safe_get_post_field(post, ["Opcionais", "opcionais", "_opcionais"])
            
            # Campos específicos do XML fornecido
            cor = self._safe_get_post_field(post, ["Cores", "cor", "_cor", "Color"])
            ano_campo = self._safe_get_post_field(post, ["_ano", "ano", "Ano", "Year"])
            km = self._safe_get_post_field(post, ["_quilometragem", "quilometragem", "KM", "km"])
            combustivel = self._safe_get_post_field(post, ["_combustivel", "combustivel", "Combustivel"])
            cambio = self._safe_get_post_field(post, ["_cambio", "cambio", "Cambio"])
            preco = self._safe_get_post_field(post, ["_valor", "valor", "preco", "Preco", "Price"])
            
            # Processa o campo ano que pode vir como "2024/2025"
            ano_fabricacao, ano_modelo = self._extract_anos(ano_campo)
            
            # Determina categoria
            categoria_final = definir_categoria_veiculo(modelo, carroceria, opcionais)
            
            # Extrai motor da versão
            motor_info = self._extract_motor_info(versao or "")
            
            # Processa fotos
            fotos = self._extract_photos_wordpress(post)
            
            # Monta o veículo normalizado
            parsed = self._normalize_vehicle({
                "id": self._safe_get_post_field(post, ["ID", "id", "_id"]),
                "tipo": "carro",  # Por padrão, assume carro
                "titulo": self._safe_get_post_field(post, ["Title", "titulo", "_titulo", "_subtitulo"]),
                "versao": self._clean_version(versao or ""),
                "marca": marca,
                "modelo": modelo,
                "ano": ano_modelo,
                "ano_fabricacao": ano_fabricacao,
                "km": km,
                "cor": cor,
                "combustivel": combustivel,
                "cambio": cambio,
                "motor": motor_info,
                "portas": None,  # Geralmente não disponível
                "categoria": categoria_final,
                "cilindrada": None,  # Para carros, geralmente não usado
                "preco": converter_preco(preco),
                "opcionais": opcionais or "",
                "fotos": fotos
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_posts(self, data: Dict) -> List[Dict]:
        """
        Extrai os posts da estrutura XML
        """
        posts = []
        
        # Tenta várias estruturas possíveis
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                post_content = post_data["post"]
                if isinstance(post_content, list):
                    posts.extend(post_content)
                elif isinstance(post_content, dict):
                    posts.append(post_content)
        
        # Verifica se há posts diretamente na raiz
        elif "post" in data:
            post_content = data["post"]
            if isinstance(post_content, list):
                posts.extend(post_content)
            elif isinstance(post_content, dict):
                posts.append(post_content)
        
        # Se ainda não encontrou, procura por qualquer chave que contenha "post"
        if not posts:
            for key, value in data.items():
                if "post" in key.lower() and isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        posts.extend(value)
                    else:
                        posts.append(value)
        
        return posts
    
    def _safe_get_post_field(self, post: Dict, fields: List[str]) -> Optional[str]:
        """
        Busca um campo no post, tentando várias variações de nome
        """
        for field in fields:
            if field in post and post[field] is not None:
                value = post[field]
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # Converte para string e remove espaços
                if value is not None:
                    str_value = str(value).strip()
                    # Retorna None se for string vazia
                    return str_value if str_value else None
        return None
    
    def _extract_photos_wordpress(self, post: Dict) -> List[str]:
        """
        Extrai fotos do post do WordPress
        Prioriza campos específicos para evitar mistura de fotos
        """
        # Ordem de prioridade dos campos de foto
        foto_fields_priority = [
            "_galeria",      # Campo principal com todas as fotos
            "ImageURL",      # URLs das imagens 
            "ImageFeatured", # Imagem destacada
        ]
        
        # Tenta cada campo por ordem de prioridade
        for field in foto_fields_priority:
            if field in post and post[field]:
                value = post[field]
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # Processa as fotos encontradas
                fotos_normalizadas = normalize_fotos(value)
                
                # Se encontrou fotos válidas, retorna (não mistura campos)
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        # Se não encontrou em campos prioritários, busca em outros
        outros_campos = ["galeria", "_imagens", "imagens", "fotos", "_fotos", "images", "_images"]
        for field in outros_campos:
            if field in post and post[field]:
                value = post[field]
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                fotos_normalizadas = normalize_fotos(value)
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo alternativo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        print(f"[DEBUG] Nenhuma foto encontrada para este veículo")
        return []
    
    def _extract_anos(self, ano_campo: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai ano de fabricação e ano do modelo do campo _ano
        Exemplo: "2024/2025" -> (ano_fabricacao="2024", ano_modelo="2025")
        """
        if not ano_campo:
            return None, None
        
        # Se contém barra, separa
        if "/" in ano_campo:
            partes = ano_campo.split("/")
            if len(partes) == 2:
                ano_fabricacao = partes[0].strip()
                ano_modelo = partes[1].strip()
                return ano_fabricacao, ano_modelo
        
        # Se não tem barra, usa o mesmo valor para ambos
        ano_limpo = ano_campo.strip()
        return ano_limpo, ano_limpo
    
    def _extract_motor_info(self, versao: str) -> Optional[str]:
        """
        Extrai informações do motor da versão
        Exemplo: "1.0 Flex" -> "1.0"
        """
        if not versao:
            return None
        
        # Busca padrão de cilindrada (ex: 1.0, 1.4, 2.0)
        motor_match = re.search(r'\b(\d+\.\d+)\b', versao)
        return motor_match.group(1) if motor_match else None
    
    def _clean_version(self, versao: str) -> str:
        """
        Limpa a versão removendo informações técnicas redundantes
        """
        if not versao:
            return ""
        
        # Remove padrões técnicos comuns
        versao_limpa = re.sub(r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', '', versao, flags=re.IGNORECASE)
        # Remove espaços extras
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa
    
    def _normalize_vehicle(self, vehicle: Dict) -> Dict:
        """
        Normaliza os dados do veículo
        """
        # Aplica normalização nas fotos antes de retornar
        fotos = vehicle.get("fotos", [])
        vehicle["fotos"] = normalize_fotos(fotos)
        
        return {
            "id": vehicle.get("id"), 
            "tipo": vehicle.get("tipo"), 
            "titulo": vehicle.get("titulo"),
            "versao": vehicle.get("versao"), 
            "marca": vehicle.get("marca"), 
            "modelo": vehicle.get("modelo"),
            "ano": vehicle.get("ano"), 
            "ano_fabricacao": vehicle.get("ano_fabricacao"), 
            "km": vehicle.get("km"),
            "cor": vehicle.get("cor"), 
            "combustivel": vehicle.get("combustivel"), 
            "cambio": vehicle.get("cambio"),
            "motor": vehicle.get("motor"), 
            "portas": vehicle.get("portas"), 
            "categoria": vehicle.get("categoria"),
            "cilindrada": vehicle.get("cilindrada"), 
            "preco": vehicle.get("preco", 0.0),
            "opcionais": vehicle.get("opcionais", ""), 
            "fotos": vehicle.get("fotos", [])
        }

# =================== SISTEMA PRINCIPAL =======================

class SimplifiedVehicleFetcher:
    def __init__(self):
        self.parser = WordPressParser()
        print("[INFO] Sistema simplificado iniciado - Parser WordPress ativo")
    
    def get_urls(self) -> List[str]: 
        return list({val for var, val in os.environ.items() if var.startswith("XML_URL") and val})
    
    def detect_format(self, content: bytes, url: str) -> tuple[Any, str]:
        content_str = content.decode('utf-8', errors='ignore')
        try: 
            return json.loads(content_str), "json"
        except json.JSONDecodeError:
            try: 
                return xmltodict.parse(content_str), "xml"
            except Exception: 
                raise ValueError(f"Formato não reconhecido para URL: {url}")
    
    def process_url(self, url: str) -> List[Dict]:
        print(f"[INFO] Processando URL: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data, format_type = self.detect_format(response.content, url)
            print(f"[INFO] Formato detectado: {format_type}")
            
            if self.parser.can_parse(data, url):
                print(f"[INFO] Usando parser: {self.parser.__class__.__name__}")
                return self.parser.parse(data, url)
            else:
                print(f"[AVISO] Parser não conseguiu processar URL: {url}")
                return []
                
        except requests.RequestException as e: 
            print(f"[ERRO] Erro de requisição para URL {url}: {e}")
            return []
        except Exception as e: 
            print(f"[ERRO] Erro crítico ao processar URL {url}: {e}")
            return []
    
    def fetch_all(self) -> Dict:
        urls = self.get_urls()
        if not urls:
            print("[AVISO] Nenhuma variável de ambiente 'XML_URL' foi encontrada.")
            return {}
        
        print(f"[INFO] {len(urls)} URL(s) encontrada(s) para processar")
        all_vehicles = [vehicle for url in urls for vehicle in self.process_url(url)]
        
        # Estatísticas
        stats = self._generate_stats(all_vehicles)
        
        result = {
            "veiculos": all_vehicles, 
            "_updated_at": datetime.now().isoformat(), 
            "_total_count": len(all_vehicles), 
            "_sources_processed": len(urls),
            "_statistics": stats
        }
        
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f: 
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[OK] Arquivo {JSON_FILE} salvo com sucesso!")
        except Exception as e: 
            print(f"[ERRO] Erro ao salvar arquivo JSON: {e}")
        
        print(f"[OK] Total de veículos processados: {len(all_vehicles)}")
        self._print_stats(stats)
        return result
    
    def _generate_stats(self, vehicles: List[Dict]) -> Dict:
        """Gera estatísticas dos veículos processados"""
        stats = {
            "por_tipo": {},
            "por_categoria": {},
            "top_marcas": {},
            "faixa_preco": {"ate_30k": 0, "30k_60k": 0, "60k_100k": 0, "acima_100k": 0}
        }
        
        for vehicle in vehicles:
            # Estatísticas por tipo
            tipo = vehicle.get("tipo", "indefinido")
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            
            # Estatísticas por categoria
            categoria = vehicle.get("categoria", "indefinido")
            stats["por_categoria"][categoria] = stats["por_categoria"].get(categoria, 0) + 1
            
            # Top marcas
            marca = vehicle.get("marca", "indefinido")
            stats["top_marcas"][marca] = stats["top_marcas"].get(marca, 0) + 1
            
            # Faixa de preço
            preco = vehicle.get("preco", 0)
            if preco <= 30000:
                stats["faixa_preco"]["ate_30k"] += 1
            elif preco <= 60000:
                stats["faixa_preco"]["30k_60k"] += 1
            elif preco <= 100000:
                stats["faixa_preco"]["60k_100k"] += 1
            else:
                stats["faixa_preco"]["acima_100k"] += 1
        
        return stats
    
    def _print_stats(self, stats: Dict):
        """Imprime estatísticas formatadas"""
        print(f"\n{'='*60}\nESTATÍSTICAS DO PROCESSAMENTO\n{'='*60}")
        
        print(f"\n📊 Distribuição por Tipo:")
        for tipo, count in sorted(stats["por_tipo"].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {tipo}: {count}")
        
        print(f"\n🚗 Distribuição por Categoria:")
        for categoria, count in sorted(stats["por_categoria"].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {categoria}: {count}")
        
        print(f"\n🏭 Top 5 Marcas:")
        for marca, count in sorted(stats["top_marcas"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {marca}: {count}")
        
        print(f"\n💰 Faixa de Preços:")
        faixas = stats["faixa_preco"]
        print(f"  • Até R$ 30.000: {faixas['ate_30k']}")
        print(f"  • R$ 30.001 - R$ 60.000: {faixas['30k_60k']}")
        print(f"  • R$ 60.001 - R$ 100.000: {faixas['60k_100k']}")
        print(f"  • Acima de R$ 100.000: {faixas['acima_100k']}")

# =================== FUNÇÃO PARA IMPORTAÇÃO =======================

def fetch_and_convert_xml():
    """Função de alto nível para ser importada por outros módulos."""
    fetcher = SimplifiedVehicleFetcher()
    return fetcher.fetch_all()

# =================== EXECUÇÃO PRINCIPAL (SE RODADO DIRETAMENTE) =======================

if __name__ == "__main__":
    result = fetch_and_convert_xml()
    
    if result and 'veiculos' in result:
        total = result.get('_total_count', 0)
        print(f"\n{'='*50}\nRESUMO DO PROCESSAMENTO\n{'='*50}")
        print(f"Total de veículos: {total}")
        print(f"Atualizado em: {result.get('_updated_at', 'N/A')}")
        print(f"Fontes processadas: {result.get('_sources_processed', 0)}")
        
        if total > 0:
            print(f"\nExemplo dos primeiros 5 veículos:")
            for i, v in enumerate(result['veiculos'][:5], 1):
                categoria = v.get('categoria', 'N/A')
                print(f"{i}. {v.get('marca', 'N/A')} {v.get('modelo', 'N/A')} ({categoria}) {v.get('ano', 'N/A')} - R$ {v.get('preco', 0.0):,.2f}")
            
            # Demonstração da normalização de fotos
            print(f"\nExemplos de fotos normalizadas:")
            vehicles_with_photos = [v for v in result['veiculos'] if v.get('fotos')][:3]
            for i, vehicle in enumerate(vehicles_with_photos, 1):
                fotos = vehicle.get('fotos', [])
                print(f"{i}. {vehicle.get('marca', 'N/A')} {vehicle.get('modelo', 'N/A')} - {len(fotos)} foto(s)")
                if fotos:
                    print(f"   Primeira foto: {fotos[0]}")
                    if len(fotos) > 1:
                        print(f"   Total de fotos: {len(fotos)}")
        
        print(f"\n{'='*50}")
        print("Sistema WordPress Parser - Processamento concluído!")
        print(f"{'='*50}")
    else:
        print("[ERRO] Nenhum veículo foi processado ou houve erro no processamento."), url, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Se não encontrou número, coloca no final
        return 999999
    
    # Ordena pela numeração
    normalized.sort(key=extract_number_from_url)
    
    return normalized

# =================== PARSER WORDPRESS =======================

class WordPressParser:
    """
    Parser específico para estruturas XML do WordPress/WooCommerce de veículos
    Processa estruturas no formato <data><post>...</post></data>
    """
    
    def can_parse(self, data: Any, url: str) -> bool:
        """
        Verifica se os dados são do formato WordPress
        """
        # Verifica estrutura básica
        if not isinstance(data, dict):
            return False
        
        # Procura pela estrutura <data><post> ou similar
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                return True
        
        # Verifica se é uma lista de posts diretamente
        if "post" in data:
            return True
            
        return False
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """
        Processa dados do WordPress
        """
        # Extrai os posts da estrutura
        posts = self._extract_posts(data)
        
        parsed_vehicles = []
        
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            # Debug: mostra os campos disponíveis (apenas para o primeiro post)
            if len(parsed_vehicles) == 0:
                print(f"[DEBUG] Campos disponíveis no XML:")
                for key in sorted(post.keys()):
                    value = post[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {key}: {value}")
                print()
            
            # Extrai dados básicos do veículo
            marca = self._safe_get_post_field(post, ["Marca", "marca", "_marca"])
            modelo = self._safe_get_post_field(post, ["Modelo", "modelo", "_modelo"])
            versao = self._safe_get_post_field(post, ["Verso", "versao", "_versao", "Version"])
            carroceria = self._safe_get_post_field(post, ["_carroceria", "carroceria", "Carroceria"])
            opcionais = self._safe_get_post_field(post, ["Opcionais", "opcionais", "_opcionais"])
            
            # Campos específicos do XML fornecido
            cor = self._safe_get_post_field(post, ["Cores", "cor", "_cor", "Color"])
            ano_campo = self._safe_get_post_field(post, ["_ano", "ano", "Ano", "Year"])
            km = self._safe_get_post_field(post, ["_quilometragem", "quilometragem", "KM", "km"])
            combustivel = self._safe_get_post_field(post, ["_combustivel", "combustivel", "Combustivel"])
            cambio = self._safe_get_post_field(post, ["_cambio", "cambio", "Cambio"])
            preco = self._safe_get_post_field(post, ["_valor", "valor", "preco", "Preco", "Price"])
            
            # Processa o campo ano que pode vir como "2024/2025"
            ano_fabricacao, ano_modelo = self._extract_anos(ano_campo)
            
            # Determina categoria
            categoria_final = definir_categoria_veiculo(modelo, carroceria, opcionais)
            
            # Extrai motor da versão
            motor_info = self._extract_motor_info(versao or "")
            
            # Processa fotos
            fotos = self._extract_photos_wordpress(post)
            
            # Monta o veículo normalizado
            parsed = self._normalize_vehicle({
                "id": self._safe_get_post_field(post, ["ID", "id", "_id"]),
                "tipo": "carro",  # Por padrão, assume carro
                "titulo": self._safe_get_post_field(post, ["Title", "titulo", "_titulo", "_subtitulo"]),
                "versao": self._clean_version(versao or ""),
                "marca": marca,
                "modelo": modelo,
                "ano": ano_modelo,
                "ano_fabricacao": ano_fabricacao,
                "km": km,
                "cor": cor,
                "combustivel": combustivel,
                "cambio": cambio,
                "motor": motor_info,
                "portas": None,  # Geralmente não disponível
                "categoria": categoria_final,
                "cilindrada": None,  # Para carros, geralmente não usado
                "preco": converter_preco(preco),
                "opcionais": opcionais or "",
                "fotos": fotos
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_posts(self, data: Dict) -> List[Dict]:
        """
        Extrai os posts da estrutura XML
        """
        posts = []
        
        # Tenta várias estruturas possíveis
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                post_content = post_data["post"]
                if isinstance(post_content, list):
                    posts.extend(post_content)
                elif isinstance(post_content, dict):
                    posts.append(post_content)
        
        # Verifica se há posts diretamente na raiz
        elif "post" in data:
            post_content = data["post"]
            if isinstance(post_content, list):
                posts.extend(post_content)
            elif isinstance(post_content, dict):
                posts.append(post_content)
        
        # Se ainda não encontrou, procura por qualquer chave que contenha "post"
        if not posts:
            for key, value in data.items():
                if "post" in key.lower() and isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        posts.extend(value)
                    else:
                        posts.append(value)
        
        return posts
    
    def _safe_get_post_field(self, post: Dict, fields: List[str]) -> Optional[str]:
        """
        Busca um campo no post, tentando várias variações de nome
        """
        for field in fields:
            if field in post and post[field] is not None:
                value = post[field]
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # Converte para string e remove espaços
                if value is not None:
                    str_value = str(value).strip()
                    # Retorna None se for string vazia
                    return str_value if str_value else None
        return None
    
    def _extract_photos_wordpress(self, post: Dict) -> List[str]:
        """
        Extrai fotos do post do WordPress
        Prioriza campos específicos para evitar mistura de fotos
        """
        # Ordem de prioridade dos campos de foto
        foto_fields_priority = [
            "_galeria",      # Campo principal com todas as fotos
            "ImageURL",      # URLs das imagens 
            "ImageFeatured", # Imagem destacada
        ]
        
        # Tenta cada campo por ordem de prioridade
        for field in foto_fields_priority:
            if field in post and post[field]:
                value = post[field]
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                # Processa as fotos encontradas
                fotos_normalizadas = normalize_fotos(value)
                
                # Se encontrou fotos válidas, retorna (não mistura campos)
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        # Se não encontrou em campos prioritários, busca em outros
        outros_campos = ["galeria", "_imagens", "imagens", "fotos", "_fotos", "images", "_images"]
        for field in outros_campos:
            if field in post and post[field]:
                value = post[field]
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                fotos_normalizadas = normalize_fotos(value)
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo alternativo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        print(f"[DEBUG] Nenhuma foto encontrada para este veículo")
        return []
    
    def _extract_anos(self, ano_campo: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai ano de fabricação e ano do modelo do campo _ano
        Exemplo: "2024/2025" -> (ano_fabricacao="2024", ano_modelo="2025")
        """
        if not ano_campo:
            return None, None
        
        # Se contém barra, separa
        if "/" in ano_campo:
            partes = ano_campo.split("/")
            if len(partes) == 2:
                ano_fabricacao = partes[0].strip()
                ano_modelo = partes[1].strip()
                return ano_fabricacao, ano_modelo
        
        # Se não tem barra, usa o mesmo valor para ambos
        ano_limpo = ano_campo.strip()
        return ano_limpo, ano_limpo
    
    def _extract_motor_info(self, versao: str) -> Optional[str]:
        """
        Extrai informações do motor da versão
        Exemplo: "1.0 Flex" -> "1.0"
        """
        if not versao:
            return None
        
        # Busca padrão de cilindrada (ex: 1.0, 1.4, 2.0)
        motor_match = re.search(r'\b(\d+\.\d+)\b', versao)
        return motor_match.group(1) if motor_match else None
    
    def _clean_version(self, versao: str) -> str:
        """
        Limpa a versão removendo informações técnicas redundantes
        """
        if not versao:
            return ""
        
        # Remove padrões técnicos comuns
        versao_limpa = re.sub(r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', '', versao, flags=re.IGNORECASE)
        # Remove espaços extras
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa
    
    def _normalize_vehicle(self, vehicle: Dict) -> Dict:
        """
        Normaliza os dados do veículo
        """
        # Aplica normalização nas fotos antes de retornar
        fotos = vehicle.get("fotos", [])
        vehicle["fotos"] = normalize_fotos(fotos)
        
        return {
            "id": vehicle.get("id"), 
            "tipo": vehicle.get("tipo"), 
            "titulo": vehicle.get("titulo"),
            "versao": vehicle.get("versao"), 
            "marca": vehicle.get("marca"), 
            "modelo": vehicle.get("modelo"),
            "ano": vehicle.get("ano"), 
            "ano_fabricacao": vehicle.get("ano_fabricacao"), 
            "km": vehicle.get("km"),
            "cor": vehicle.get("cor"), 
            "combustivel": vehicle.get("combustivel"), 
            "cambio": vehicle.get("cambio"),
            "motor": vehicle.get("motor"), 
            "portas": vehicle.get("portas"), 
            "categoria": vehicle.get("categoria"),
            "cilindrada": vehicle.get("cilindrada"), 
            "preco": vehicle.get("preco", 0.0),
            "opcionais": vehicle.get("opcionais", ""), 
            "fotos": vehicle.get("fotos", [])
        }

# =================== SISTEMA PRINCIPAL =======================

class SimplifiedVehicleFetcher:
    def __init__(self):
        self.parser = WordPressParser()
        print("[INFO] Sistema simplificado iniciado - Parser WordPress ativo")
    
    def get_urls(self) -> List[str]: 
        return list({val for var, val in os.environ.items() if var.startswith("XML_URL") and val})
    
    def detect_format(self, content: bytes, url: str) -> tuple[Any, str]:
        content_str = content.decode('utf-8', errors='ignore')
        try: 
            return json.loads(content_str), "json"
        except json.JSONDecodeError:
            try: 
                return xmltodict.parse(content_str), "xml"
            except Exception: 
                raise ValueError(f"Formato não reconhecido para URL: {url}")
    
    def process_url(self, url: str) -> List[Dict]:
        print(f"[INFO] Processando URL: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data, format_type = self.detect_format(response.content, url)
            print(f"[INFO] Formato detectado: {format_type}")
            
            if self.parser.can_parse(data, url):
                print(f"[INFO] Usando parser: {self.parser.__class__.__name__}")
                return self.parser.parse(data, url)
            else:
                print(f"[AVISO] Parser não conseguiu processar URL: {url}")
                return []
                
        except requests.RequestException as e: 
            print(f"[ERRO] Erro de requisição para URL {url}: {e}")
            return []
        except Exception as e: 
            print(f"[ERRO] Erro crítico ao processar URL {url}: {e}")
            return []
    
    def fetch_all(self) -> Dict:
        urls = self.get_urls()
        if not urls:
            print("[AVISO] Nenhuma variável de ambiente 'XML_URL' foi encontrada.")
            return {}
        
        print(f"[INFO] {len(urls)} URL(s) encontrada(s) para processar")
        all_vehicles = [vehicle for url in urls for vehicle in self.process_url(url)]
        
        # Estatísticas
        stats = self._generate_stats(all_vehicles)
        
        result = {
            "veiculos": all_vehicles, 
            "_updated_at": datetime.now().isoformat(), 
            "_total_count": len(all_vehicles), 
            "_sources_processed": len(urls),
            "_statistics": stats
        }
        
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f: 
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[OK] Arquivo {JSON_FILE} salvo com sucesso!")
        except Exception as e: 
            print(f"[ERRO] Erro ao salvar arquivo JSON: {e}")
        
        print(f"[OK] Total de veículos processados: {len(all_vehicles)}")
        self._print_stats(stats)
        return result
    
    def _generate_stats(self, vehicles: List[Dict]) -> Dict:
        """Gera estatísticas dos veículos processados"""
        stats = {
            "por_tipo": {},
            "por_categoria": {},
            "top_marcas": {},
            "faixa_preco": {"ate_30k": 0, "30k_60k": 0, "60k_100k": 0, "acima_100k": 0}
        }
        
        for vehicle in vehicles:
            # Estatísticas por tipo
            tipo = vehicle.get("tipo", "indefinido")
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            
            # Estatísticas por categoria
            categoria = vehicle.get("categoria", "indefinido")
            stats["por_categoria"][categoria] = stats["por_categoria"].get(categoria, 0) + 1
            
            # Top marcas
            marca = vehicle.get("marca", "indefinido")
            stats["top_marcas"][marca] = stats["top_marcas"].get(marca, 0) + 1
            
            # Faixa de preço
            preco = vehicle.get("preco", 0)
            if preco <= 30000:
                stats["faixa_preco"]["ate_30k"] += 1
            elif preco <= 60000:
                stats["faixa_preco"]["30k_60k"] += 1
            elif preco <= 100000:
                stats["faixa_preco"]["60k_100k"] += 1
            else:
                stats["faixa_preco"]["acima_100k"] += 1
        
        return stats
    
    def _print_stats(self, stats: Dict):
        """Imprime estatísticas formatadas"""
        print(f"\n{'='*60}\nESTATÍSTICAS DO PROCESSAMENTO\n{'='*60}")
        
        print(f"\n📊 Distribuição por Tipo:")
        for tipo, count in sorted(stats["por_tipo"].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {tipo}: {count}")
        
        print(f"\n🚗 Distribuição por Categoria:")
        for categoria, count in sorted(stats["por_categoria"].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {categoria}: {count}")
        
        print(f"\n🏭 Top 5 Marcas:")
        for marca, count in sorted(stats["top_marcas"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {marca}: {count}")
        
        print(f"\n💰 Faixa de Preços:")
        faixas = stats["faixa_preco"]
        print(f"  • Até R$ 30.000: {faixas['ate_30k']}")
        print(f"  • R$ 30.001 - R$ 60.000: {faixas['30k_60k']}")
        print(f"  • R$ 60.001 - R$ 100.000: {faixas['60k_100k']}")
        print(f"  • Acima de R$ 100.000: {faixas['acima_100k']}")

# =================== FUNÇÃO PARA IMPORTAÇÃO =======================

def fetch_and_convert_xml():
    """Função de alto nível para ser importada por outros módulos."""
    fetcher = SimplifiedVehicleFetcher()
    return fetcher.fetch_all()

# =================== EXECUÇÃO PRINCIPAL (SE RODADO DIRETAMENTE) =======================

if __name__ == "__main__":
    result = fetch_and_convert_xml()
    
    if result and 'veiculos' in result:
        total = result.get('_total_count', 0)
        print(f"\n{'='*50}\nRESUMO DO PROCESSAMENTO\n{'='*50}")
        print(f"Total de veículos: {total}")
        print(f"Atualizado em: {result.get('_updated_at', 'N/A')}")
        print(f"Fontes processadas: {result.get('_sources_processed', 0)}")
        
        if total > 0:
            print(f"\nExemplo dos primeiros 5 veículos:")
            for i, v in enumerate(result['veiculos'][:5], 1):
                categoria = v.get('categoria', 'N/A')
                print(f"{i}. {v.get('marca', 'N/A')} {v.get('modelo', 'N/A')} ({categoria}) {v.get('ano', 'N/A')} - R$ {v.get('preco', 0.0):,.2f}")
            
            # Demonstração da normalização de fotos
            print(f"\nExemplos de fotos normalizadas:")
            vehicles_with_photos = [v for v in result['veiculos'] if v.get('fotos')][:3]
            for i, vehicle in enumerate(vehicles_with_photos, 1):
                fotos = vehicle.get('fotos', [])
                print(f"{i}. {vehicle.get('marca', 'N/A')} {vehicle.get('modelo', 'N/A')} - {len(fotos)} foto(s)")
                if fotos:
                    print(f"   Primeira foto: {fotos[0]}")
                    if len(fotos) > 1:
                        print(f"   Total de fotos: {len(fotos)}")
        
        print(f"\n{'='*50}")
        print("Sistema WordPress Parser - Processamento concluído!")
        print(f"{'='*50}")
    else:
        print("[ERRO] Nenhum veículo foi processado ou houve erro no processamento.")
