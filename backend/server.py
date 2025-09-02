import os
import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import bcrypt
import jwt
from pymongo import MongoClient
from bson import ObjectId
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from threading import Thread
import subprocess

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.rituais_db

# Configuração JWT
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Função para serializar ObjectId
def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id' and isinstance(value, ObjectId):
                result['id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

# Modelos Pydantic
class ClienteCreate(BaseModel):
    nome_completo: str
    email: str
    whatsapp: str
    ritual_id: str
    valor_pago: float
    forma_pagamento: str

class Cliente(BaseModel):
    id: str
    nome_completo: str
    email: str
    whatsapp: str
    ritual_id: str
    ritual_nome: str
    valor_pago: float
    forma_pagamento: str
    created_at: datetime

class RitualCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    imagem_url: str = ""
    visivel: bool = True
    desconto_percentual: Optional[float] = None

class Ritual(BaseModel):
    id: str
    nome: str
    descricao: str
    preco: float
    imagem_url: str
    visivel: bool
    desconto_percentual: Optional[float]
    created_at: datetime

class ConfigCreate(BaseModel):
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = "#8B5CF6"
    cor_secundaria: Optional[str] = "#EC4899"
    whatsapp_numero: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None

class Config(BaseModel):
    id: str
    logo_url: Optional[str]
    cor_primaria: str
    cor_secundaria: str
    whatsapp_numero: Optional[str]
    instagram_url: Optional[str]
    facebook_url: Optional[str]
    updated_at: datetime

class RitualSemanaCreate(BaseModel):
    ritual_id: str
    descricao_especial: Optional[str] = None
    preco_promocional: Optional[float] = None
    ativo: bool = True

class RitualSemana(BaseModel):
    id: str
    ritual_id: str
    ritual_nome: str
    descricao_especial: Optional[str]
    preco_promocional: Optional[float]
    ativo: bool
    created_at: datetime

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str = "admin"

class User(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime

class UserLogin(BaseModel):
    username: str
    password: str

class PaymentGatewayCreate(BaseModel):
    nome: str
    ativo: bool
    config: dict

class PaymentGateway(BaseModel):
    id: str
    nome: str
    ativo: bool
    config: dict
    created_at: datetime

class InstagramProfileCreate(BaseModel):
    username: str
    bio: str
    profile_picture_url: str
    followers_count: int
    following_count: int
    posts_count: int

class InstagramProfile(BaseModel):
    id: str
    username: str
    bio: str
    profile_picture_url: str
    followers_count: int
    following_count: int
    posts_count: int
    updated_at: datetime

class InstagramPostCreate(BaseModel):
    image_url: str
    caption: str
    post_url: str
    likes_count: int = 0
    comments_count: int = 0

class InstagramPost(BaseModel):
    id: str
    image_url: str
    caption: str
    post_url: str
    likes_count: int
    comments_count: int
    created_at: datetime

class Dashboard(BaseModel):
    vendas_hoje: dict
    vendas_mes: dict
    meta_mensal: dict

class MetaVendas(BaseModel):
    mes: int
    ano: int
    valor_meta: float

class TipoConsultaCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    duracao_minutos: int
    ativo: bool = True

class TipoConsulta(BaseModel):
    id: str
    nome: str
    descricao: str
    preco: float
    duracao_minutos: int
    ativo: bool
    created_at: datetime

class HorarioDisponivelCreate(BaseModel):
    dia_semana: int  # 0=Segunda, 1=Terça, ..., 6=Domingo
    hora_inicio: str  # "09:00"
    hora_fim: str     # "18:00"
    intervalo_minutos: int = 60
    ativo: bool = True

class HorarioDisponivel(BaseModel):
    id: str
    dia_semana: int
    hora_inicio: str
    hora_fim: str
    intervalo_minutos: int
    ativo: bool
    created_at: datetime

class ConsultaCreate(BaseModel):
    cliente_nome: str
    cliente_whatsapp: str
    tipo_consulta_id: str
    data_hora: datetime
    observacoes: Optional[str] = None

class Consulta(BaseModel):
    id: str
    cliente_nome: str
    cliente_whatsapp: str
    tipo_consulta_id: str
    tipo_consulta_nome: str
    data_hora: datetime
    observacoes: Optional[str]
    status: str  # "agendada", "confirmada", "realizada", "cancelada"
    valor_pago: float
    created_at: datetime

class WhatsappConfigCreate(BaseModel):
    api_token: str
    numero_whatsapp: str
    ativo: bool = True

class WhatsappConfig(BaseModel):
    id: str
    api_token: str
    numero_whatsapp: str
    ativo: bool
    updated_at: datetime

class WhatsappTemplateCreate(BaseModel):
    nome: str
    tipo: str  # "confirmacao_ritual", "confirmacao_consulta", "lembrete_consulta", "relatorio_diario"
    conteudo: str
    variaveis: List[str] = []
    ativo: bool = True

class WhatsappTemplate(BaseModel):
    id: str
    nome: str
    tipo: str
    conteudo: str
    variaveis: List[str]
    ativo: bool
    created_at: datetime

class WhatsappMessageCreate(BaseModel):
    numero_destino: str
    conteudo: str
    template_usado: Optional[str] = None

class WhatsappMessage(BaseModel):
    id: str
    numero_destino: str
    conteudo: str
    template_usado: Optional[str]
    status: str  # "enviada", "entregue", "lida", "falha"
    enviado_em: datetime

class BackupConfigCreate(BaseModel):
    backup_automatico: bool = True
    frequencia_horas: int = 24
    manter_backups: int = 7

class BackupConfig(BaseModel):
    id: str
    backup_automatico: bool
    frequencia_horas: int
    manter_backups: int
    ultimo_backup: Optional[datetime]
    updated_at: datetime

class CupomCreate(BaseModel):
    codigo: str
    descricao: str
    tipo: str  # "percentual" ou "valor_fixo"
    percentual_desconto: Optional[float] = None
    valor_desconto: Optional[float] = None
    valor_minimo: Optional[float] = None
    data_inicio: datetime
    data_fim: datetime
    uso_maximo: Optional[int] = None
    ativo: bool = True

class Cupom(BaseModel):
    id: str
    codigo: str
    descricao: str
    tipo: str
    percentual_desconto: Optional[float]
    valor_desconto: Optional[float]
    valor_minimo: Optional[float]
    data_inicio: datetime
    data_fim: datetime
    uso_maximo: Optional[int]
    uso_atual: int
    ativo: bool
    created_at: datetime

class IndicacaoCreate(BaseModel):
    nome_indicador: str
    whatsapp_indicador: str
    nome_indicado: str
    whatsapp_indicado: str

class Indicacao(BaseModel):
    id: str
    nome_indicador: str
    whatsapp_indicador: str
    nome_indicado: Optional[str]
    whatsapp_indicado: Optional[str]
    codigo_indicacao: str
    status: str  # "pendente", "convertido", "concluida"
    recompensa_liberada: bool
    data_conversao: Optional[datetime]
    created_at: datetime

class FollowUpCreate(BaseModel):
    cliente_id: str
    tipo: str  # "pos_ritual", "pos_consulta", "remarketing"
    agendado_para: datetime
    conteudo: str

class FollowUp(BaseModel):
    id: str
    cliente_id: str
    tipo: str
    agendado_para: datetime
    conteudo: str
    enviado: bool
    enviado_em: Optional[datetime]
    created_at: datetime

class RemarketingCreate(BaseModel):
    segmento_clientes: str  # "inativos", "rituais_baixo_valor", "consultas_canceladas"
    conteudo_mensagem: str
    data_envio: datetime
    ativo: bool = True

class Remarketing(BaseModel):
    id: str
    segmento_clientes: str
    conteudo_mensagem: str
    data_envio: datetime
    enviados: int
    abertos: int
    convertidos: int
    ativo: bool
    created_at: datetime

# Novos modelos para o Editor de Site
class SiteContentCreate(BaseModel):
    secao: str  # "hero", "sobre", "rituais", "faq", "contato"
    titulo: Optional[str] = None
    subtitulo: Optional[str] = None
    conteudo_html: Optional[str] = None
    imagem_url: Optional[str] = None
    configuracoes: Optional[dict] = {}
    ativo: bool = True
    ordem: int = 0

class SiteContent(BaseModel):
    id: str
    secao: str
    titulo: Optional[str]
    subtitulo: Optional[str]
    conteudo_html: Optional[str]
    imagem_url: Optional[str]
    configuracoes: dict
    ativo: bool
    ordem: int
    updated_at: datetime

class SiteConfigCreate(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    cor_primaria: str = "#8B5CF6"
    cor_secundaria: str = "#EC4899"
    fonte_primaria: str = "Inter"
    fonte_secundaria: str = "Playfair Display"
    # SEO
    meta_titulo: Optional[str] = None
    meta_descricao: Optional[str] = None
    meta_palavras_chave: Optional[str] = None
    # Redes sociais
    instagram_username: Optional[str] = None
    facebook_url: Optional[str] = None
    whatsapp_numero: Optional[str] = None

class SiteConfig(BaseModel):
    id: str
    logo_url: Optional[str]
    favicon_url: Optional[str]
    cor_primaria: str
    cor_secundaria: str
    fonte_primaria: str
    fonte_secundaria: str
    meta_titulo: Optional[str]
    meta_descricao: Optional[str]
    meta_palavras_chave: Optional[str]
    instagram_username: Optional[str]
    facebook_url: Optional[str]
    whatsapp_numero: Optional[str]
    updated_at: datetime

class SiteSectionCreate(BaseModel):
    nome: str
    tipo: str  # "hero", "sobre", "rituais", "faq", "contato", "instagram"
    ativo: bool = True
    ordem: int = 0
    configuracoes: Optional[dict] = {}

class SiteSection(BaseModel):
    id: str
    nome: str
    tipo: str
    ativo: bool
    ordem: int
    configuracoes: dict
    updated_at: datetime

# Funções de autenticação
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(username: str = Depends(verify_token)):
    user = db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return serialize_doc(user)

# Função para criar dados padrão
def create_default_data():
    # Criar usuário admin padrão
    if db.users.count_documents({}) == 0:
        hashed_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        admin_user = {
            "_id": ObjectId(),
            "username": "admin",
            "password": hashed_password.decode('utf-8'),
            "email": "admin@ritual.com",
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        db.users.insert_one(admin_user)
        print("✅ Usuário admin padrão criado")

    # Criar rituais padrão
    if db.rituais.count_documents({}) == 0:
        rituais_padrao = [
            {
                "_id": ObjectId(),
                "nome": "Desamarre",
                "descricao": "Ritual para quebrar amarrações e trabalhos negativos",
                "preco": 67.00,
                "imagem_url": "",
                "visivel": True,
                "desconto_percentual": None,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Banho de Limpeza Espiritual",
                "descricao": "Limpeza profunda da aura e energias negativas",
                "preco": 45.00,
                "imagem_url": "",
                "visivel": True,
                "desconto_percentual": None,
                "created_at": datetime.utcnow()
            }
        ]
        db.rituais.insert_many(rituais_padrao)
        print("✅ Rituais padrão criados")

    # Criar configuração padrão
    if db.config.count_documents({}) == 0:
        config_padrao = {
            "_id": ObjectId(),
            "logo_url": None,
            "cor_primaria": "#8B5CF6",
            "cor_secundaria": "#EC4899",
            "whatsapp_numero": None,
            "instagram_url": None,
            "facebook_url": None,
            "updated_at": datetime.utcnow()
        }
        db.config.insert_one(config_padrao)
        print("✅ Configuração padrão criada")

    # Criar tipos de consulta padrão
    if db.tipos_consulta.count_documents({}) == 0:
        tipos_padrao = [
            {
                "_id": ObjectId(),
                "nome": "Consulta de Tarot",
                "descricao": "Leitura completa das cartas do tarot",
                "preco": 80.00,
                "duracao_minutos": 60,
                "ativo": True,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Mapa Astral",
                "descricao": "Análise completa do seu mapa astral",
                "preco": 120.00,
                "duracao_minutos": 90,
                "ativo": True,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Consulta Espiritual",
                "descricao": "Orientação espiritual personalizada",
                "preco": 100.00,
                "duracao_minutos": 60,
                "ativo": True,
                "created_at": datetime.utcnow()
            }
        ]
        db.tipos_consulta.insert_many(tipos_padrao)
        print("✅ Tipos de consulta padrão criados")

    # Criar horários padrão (Segunda a Sexta, 9h às 18h)
    if db.horarios_disponiveis.count_documents({}) == 0:
        horarios_padrao = []
        for dia in range(5):  # Segunda a Sexta
            horarios_padrao.append({
                "_id": ObjectId(),
                "dia_semana": dia,
                "hora_inicio": "09:00",
                "hora_fim": "18:00",
                "intervalo_minutos": 60,
                "ativo": True,
                "created_at": datetime.utcnow()
            })
        db.horarios_disponiveis.insert_many(horarios_padrao)
        print("✅ Horários padrão criados")

    # Criar templates WhatsApp padrão
    if db.whatsapp_templates.count_documents({}) == 0:
        templates_padrao = [
            {
                "_id": ObjectId(),
                "nome": "Confirmação de Ritual",
                "tipo": "confirmacao_ritual",
                "conteudo": "Olá {nome}! Seu ritual '{ritual}' no valor de R$ {valor} foi confirmado. Em breve entraremos em contato. 🙏✨",
                "variaveis": ["nome", "ritual", "valor"],
                "ativo": True,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Confirmação de Consulta",
                "tipo": "confirmacao_consulta",
                "conteudo": "Olá {nome}! Sua consulta está agendada para {data}. Aguardamos você! 🔮",
                "variaveis": ["nome", "data"],
                "ativo": True,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Lembrete de Consulta",
                "tipo": "lembrete_consulta",
                "conteudo": "Olá {nome}! Lembrando que sua consulta é hoje às {hora}. Te esperamos! ⏰",
                "variaveis": ["nome", "hora"],
                "ativo": True,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Relatório Diário",
                "tipo": "relatorio_diario",
                "conteudo": "📊 Relatório do dia: {total_vendas} vendas realizadas, faturamento: R$ {faturamento_total}",
                "variaveis": ["total_vendas", "faturamento_total"],
                "ativo": True,
                "created_at": datetime.utcnow()
            }
        ]
        db.whatsapp_templates.insert_many(templates_padrao)
        print("✅ Templates WhatsApp padrão criados")

    # Criar meta mensal padrão
    if db.metas_vendas.count_documents({}) == 0:
        meta_padrao = {
            "_id": ObjectId(),
            "mes": datetime.utcnow().month,
            "ano": datetime.utcnow().year,
            "valor_meta": 5000.00
        }
        db.metas_vendas.insert_one(meta_padrao)
        print("✅ Meta mensal padrão criada")

    # Criar configuração de site padrão
    if db.site_config.count_documents({}) == 0:
        site_config_padrao = {
            "_id": ObjectId(),
            "logo_url": None,
            "favicon_url": None,
            "cor_primaria": "#8B5CF6",
            "cor_secundaria": "#EC4899",
            "fonte_primaria": "Inter",
            "fonte_secundaria": "Playfair Display",
            "meta_titulo": "Rituais Espirituais - Transforme sua vida",
            "meta_descricao": "Rituais espirituais poderosos para limpeza energética, proteção e prosperidade. Consultas online com especialistas.",
            "meta_palavras_chave": "rituais, espiritual, tarot, consulta, limpeza energética",
            "instagram_username": None,
            "facebook_url": None,
            "whatsapp_numero": None,
            "updated_at": datetime.utcnow()
        }
        db.site_config.insert_one(site_config_padrao)
        print("✅ Configuração de site padrão criada")

    # Criar seções padrão do site
    if db.site_sections.count_documents({}) == 0:
        secoes_padrao = [
            {
                "_id": ObjectId(),
                "nome": "Hero Principal",
                "tipo": "hero",
                "ativo": True,
                "ordem": 1,
                "configuracoes": {
                    "titulo": "Rituais Espirituais",
                    "subtitulo": "Transforme sua vida através do poder dos rituais ancestrais",
                    "botao_texto": "Ver Rituais",
                    "imagem_fundo": ""
                },
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Rituais de Hoje",
                "tipo": "rituais",
                "ativo": True,
                "ordem": 2,
                "configuracoes": {
                    "titulo": "Rituais de Hoje",
                    "subtitulo": "Especiais para hoje, com energia ainda mais poderosa"
                },
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Sobre Nós",
                "tipo": "sobre",
                "ativo": True,
                "ordem": 3,
                "configuracoes": {
                    "titulo": "Família Espiritual",
                    "conteudo": "Há mais de 20 anos ajudando pessoas a transformarem suas vidas através da espiritualidade."
                },
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Instagram Feed",
                "tipo": "instagram",
                "ativo": True,
                "ordem": 4,
                "configuracoes": {
                    "titulo": "Siga no Instagram",
                    "mostrar_posts": True,
                    "numero_posts": 6
                },
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "FAQ",
                "tipo": "faq",
                "ativo": True,
                "ordem": 5,
                "configuracoes": {
                    "titulo": "Perguntas Frequentes",
                    "perguntas": [
                        {
                            "pergunta": "Como funcionam os rituais?",
                            "resposta": "Os rituais são realizados com ingredientes especiais e energias direcionadas para seu objetivo específico."
                        },
                        {
                            "pergunta": "Quanto tempo leva para ver resultados?",
                            "resposta": "Os resultados podem variar, mas geralmente são percebidos entre 7 a 21 dias."
                        }
                    ]
                },
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "nome": "Contato",
                "tipo": "contato",
                "ativo": True,
                "ordem": 6,
                "configuracoes": {
                    "titulo": "Entre em Contato",
                    "subtitulo": "Estamos aqui para ajudar você"
                },
                "updated_at": datetime.utcnow()
            }
        ]
        db.site_sections.insert_many(secoes_padrao)
        print("✅ Seções padrão do site criadas")

    # Criar conteúdos padrão do site
    if db.site_content.count_documents({}) == 0:
        conteudos_padrao = [
            {
                "_id": ObjectId(),
                "secao": "hero",
                "titulo": "Rituais Espirituais",
                "subtitulo": "Transforme sua vida através do poder dos rituais ancestrais",
                "conteudo_html": "<p>Mais de 5.000 clientes atendidos</p>",
                "imagem_url": "",
                "configuracoes": {
                    "botao_principal": "Ver Rituais",
                    "cor_fundo": "gradient"
                },
                "ativo": True,
                "ordem": 1,
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "secao": "sobre",
                "titulo": "Família Espiritual",
                "subtitulo": "Tradição e conhecimento ancestral",
                "conteudo_html": "<p>Há mais de 20 anos ajudando pessoas a transformarem suas vidas através da espiritualidade. Nossa família trabalha com rituais tradicionais, sempre respeitando as tradições ancestrais.</p><p>Cada ritual é único e personalizado para suas necessidades específicas.</p>",
                "imagem_url": "",
                "configuracoes": {},
                "ativo": True,
                "ordem": 1,
                "updated_at": datetime.utcnow()
            }
        ]
        db.site_content.insert_many(conteudos_padrao)
        print("✅ Conteúdos padrão do site criados")

# Inicializar dados padrão ao iniciar o servidor
create_default_data()

# Funções para simulação WhatsApp
def send_whatsapp_message(numero: str, mensagem: str, template_usado: str = None):
    """Simula envio de mensagem WhatsApp"""
    try:
        # Aqui seria a integração real com WhatsApp Business API
        # Por enquanto, apenas salvamos no histórico
        message_doc = {
            "_id": ObjectId(),
            "numero_destino": numero,
            "conteudo": mensagem,
            "template_usado": template_usado,
            "status": "enviada",
            "enviado_em": datetime.utcnow()
        }
        db.whatsapp_messages.insert_one(message_doc)
        logger.info(f"Mensagem WhatsApp simulada para {numero}: {mensagem[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False

def send_ritual_confirmation(cliente_nome: str, whatsapp: str, ritual_nome: str, valor: float):
    """Envia confirmação de ritual via WhatsApp"""
    template = db.whatsapp_templates.find_one({"tipo": "confirmacao_ritual", "ativo": True})
    if template:
        mensagem = template["conteudo"].format(
            nome=cliente_nome,
            ritual=ritual_nome,
            valor=f"{valor:.2f}"
        )
        return send_whatsapp_message(whatsapp, mensagem, "confirmacao_ritual")
    return False

def send_consulta_confirmation(cliente_nome: str, whatsapp: str, data_consulta: str):
    """Envia confirmação de consulta via WhatsApp"""
    template = db.whatsapp_templates.find_one({"tipo": "confirmacao_consulta", "ativo": True})
    if template:
        mensagem = template["conteudo"].format(
            nome=cliente_nome,
            data=data_consulta
        )
        return send_whatsapp_message(whatsapp, mensagem, "confirmacao_consulta")
    return False

# Scheduler para tarefas automáticas
scheduler = BackgroundScheduler()

def backup_database():
    """Realiza backup automático do banco de dados"""
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = f"/tmp/backup_rituais_{timestamp}.json"
        
        # Coletar dados de todas as coleções
        collections = ['clientes', 'rituais', 'config', 'users', 'rituais_semana', 
                      'payment_gateways', 'instagram_profile', 'instagram_posts',
                      'tipos_consulta', 'horarios_disponiveis', 'consultas',
                      'whatsapp_config', 'whatsapp_templates', 'whatsapp_messages',
                      'cupons', 'indicacoes', 'metas_vendas',
                      'site_config', 'site_sections', 'site_content']
        
        backup_data = {}
        for collection_name in collections:
            collection = db[collection_name]
            backup_data[collection_name] = list(collection.find({}, {"_id": 0}))
        
        # Salvar backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Atualizar configuração de backup
        db.backup_config.update_one(
            {},
            {"$set": {"ultimo_backup": datetime.utcnow()}},
            upsert=True
        )
        
        logger.info(f"Backup realizado com sucesso: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Erro no backup automático: {e}")
        return None

def send_daily_report():
    """Envia relatório diário via WhatsApp"""
    try:
        # Calcular estatísticas do dia
        hoje = datetime.utcnow().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        
        vendas_hoje = db.clientes.count_documents({
            "created_at": {"$gte": inicio_dia, "$lte": fim_dia}
        })
        
        pipeline = [
            {"$match": {"created_at": {"$gte": inicio_dia, "$lte": fim_dia}}},
            {"$group": {"_id": None, "total": {"$sum": "$valor_pago"}}}
        ]
        faturamento = list(db.clientes.aggregate(pipeline))
        faturamento_total = faturamento[0]["total"] if faturamento else 0
        
        # Buscar configuração WhatsApp
        whatsapp_config = db.whatsapp_config.find_one({"ativo": True})
        if whatsapp_config:
            template = db.whatsapp_templates.find_one({"tipo": "relatorio_diario", "ativo": True})
            if template:
                mensagem = template["conteudo"].format(
                    total_vendas=vendas_hoje,
                    faturamento_total=f"{faturamento_total:.2f}"
                )
                send_whatsapp_message(whatsapp_config["numero_whatsapp"], mensagem, "relatorio_diario")
        
        logger.info(f"Relatório diário enviado: {vendas_hoje} vendas, R$ {faturamento_total:.2f}")
    except Exception as e:
        logger.error(f"Erro ao enviar relatório diário: {e}")

# Configurar tarefas agendadas
scheduler.add_job(
    backup_database,
    CronTrigger(hour=2, minute=0),  # Todo dia às 02:00
    id='backup_diario',
    replace_existing=True
)

scheduler.add_job(
    send_daily_report,
    CronTrigger(hour=[12, 18, 22], minute=0),  # Às 12h, 18h e 22h
    id='relatorio_diario',
    replace_existing=True
)

scheduler.start()

# Rotas da API

@app.get("/")
async def root():
    return {"message": "API Rituais Espirituais - Rodando"}

# Rotas de autenticação
@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    user = db.users.find_one({"username": user_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    
    if not bcrypt.checkpw(user_data.password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_doc(user)
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

# Rotas de clientes
@app.post("/api/clientes", response_model=Cliente)
async def create_cliente(cliente: ClienteCreate):
    # Buscar informações do ritual
    ritual = db.rituais.find_one({"_id": ObjectId(cliente.ritual_id)})
    if not ritual:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    cliente_doc = {
        "_id": ObjectId(),
        "nome_completo": cliente.nome_completo,
        "email": cliente.email,
        "whatsapp": cliente.whatsapp,
        "ritual_id": cliente.ritual_id,
        "ritual_nome": ritual["nome"],
        "valor_pago": cliente.valor_pago,
        "forma_pagamento": cliente.forma_pagamento,
        "created_at": datetime.utcnow()
    }
    
    result = db.clientes.insert_one(cliente_doc)
    
    # Enviar confirmação via WhatsApp
    send_ritual_confirmation(
        cliente.nome_completo,
        cliente.whatsapp,
        ritual["nome"],
        cliente.valor_pago
    )
    
    return serialize_doc(db.clientes.find_one({"_id": result.inserted_id}))

@app.get("/api/admin/clientes", response_model=List[Cliente])
async def get_clientes(current_user: dict = Depends(get_current_user)):
    clientes = list(db.clientes.find({}))
    return serialize_doc(clientes)

# Rotas de rituais
@app.get("/api/rituais", response_model=List[Ritual])
async def get_rituais():
    rituais = list(db.rituais.find({"visivel": True}))
    return serialize_doc(rituais)

@app.get("/api/admin/rituais", response_model=List[Ritual])
async def get_all_rituais(current_user: dict = Depends(get_current_user)):
    rituais = list(db.rituais.find({}))
    return serialize_doc(rituais)

@app.post("/api/admin/rituais", response_model=Ritual)
async def create_ritual(ritual: RitualCreate, current_user: dict = Depends(get_current_user)):
    ritual_doc = {
        "_id": ObjectId(),
        **ritual.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.rituais.insert_one(ritual_doc)
    return serialize_doc(db.rituais.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/rituais/{ritual_id}", response_model=Ritual)
async def update_ritual(ritual_id: str, ritual: RitualCreate, current_user: dict = Depends(get_current_user)):
    result = db.rituais.update_one(
        {"_id": ObjectId(ritual_id)},
        {"$set": ritual.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    return serialize_doc(db.rituais.find_one({"_id": ObjectId(ritual_id)}))

@app.delete("/api/admin/rituais/{ritual_id}")
async def delete_ritual(ritual_id: str, current_user: dict = Depends(get_current_user)):
    result = db.rituais.delete_one({"_id": ObjectId(ritual_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    return {"message": "Ritual deletado com sucesso"}

# Rotas de configuração
@app.get("/api/config", response_model=Config)
async def get_config():
    config = db.config.find_one({})
    if not config:
        # Criar configuração padrão se não existir
        config_doc = {
            "_id": ObjectId(),
            "logo_url": None,
            "cor_primaria": "#8B5CF6",
            "cor_secundaria": "#EC4899",
            "whatsapp_numero": None,
            "instagram_url": None,
            "facebook_url": None,
            "updated_at": datetime.utcnow()
        }
        db.config.insert_one(config_doc)
        config = config_doc
    
    return serialize_doc(config)

@app.put("/api/admin/config", response_model=Config)
async def update_config(config: ConfigCreate, current_user: dict = Depends(get_current_user)):
    config_doc = {
        **config.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.config.update_one({}, {"$set": config_doc}, upsert=True)
    
    return serialize_doc(db.config.find_one({}))

# Rotas de rituais da semana
@app.get("/api/rituais-semana", response_model=List[RitualSemana])
async def get_rituais_semana():
    pipeline = [
        {"$match": {"ativo": True}},
        {"$lookup": {
            "from": "rituais",
            "localField": "ritual_id",
            "foreignField": "_id",
            "as": "ritual"
        }},
        {"$unwind": "$ritual"},
        {"$addFields": {
            "ritual_nome": "$ritual.nome"
        }}
    ]
    
    rituais_semana = list(db.rituais_semana.aggregate([
        {"$match": {"ativo": True}},
        {"$addFields": {
            "ritual_object_id": {"$toObjectId": "$ritual_id"}
        }},
        {"$lookup": {
            "from": "rituais",
            "localField": "ritual_object_id", 
            "foreignField": "_id",
            "as": "ritual"
        }},
        {"$unwind": "$ritual"},
        {"$addFields": {
            "ritual_nome": "$ritual.nome"
        }}
    ]))
    
    return serialize_doc(rituais_semana)

@app.get("/api/admin/rituais-semana", response_model=List[RitualSemana])
async def get_all_rituais_semana(current_user: dict = Depends(get_current_user)):
    rituais_semana = list(db.rituais_semana.aggregate([
        {"$addFields": {
            "ritual_object_id": {"$toObjectId": "$ritual_id"}
        }},
        {"$lookup": {
            "from": "rituais",
            "localField": "ritual_object_id",
            "foreignField": "_id",
            "as": "ritual"
        }},
        {"$unwind": "$ritual"},
        {"$addFields": {
            "ritual_nome": "$ritual.nome"
        }}
    ]))
    
    return serialize_doc(rituais_semana)

@app.post("/api/admin/rituais-semana", response_model=RitualSemana)
async def create_ritual_semana(ritual_semana: RitualSemanaCreate, current_user: dict = Depends(get_current_user)):
    # Verificar se o ritual existe
    ritual = db.rituais.find_one({"_id": ObjectId(ritual_semana.ritual_id)})
    if not ritual:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    ritual_semana_doc = {
        "_id": ObjectId(),
        **ritual_semana.dict(),
        "ritual_nome": ritual["nome"],
        "created_at": datetime.utcnow()
    }
    
    result = db.rituais_semana.insert_one(ritual_semana_doc)
    return serialize_doc(db.rituais_semana.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/rituais-semana/{ritual_semana_id}", response_model=RitualSemana)
async def update_ritual_semana(ritual_semana_id: str, ritual_semana: RitualSemanaCreate, current_user: dict = Depends(get_current_user)):
    # Verificar se o ritual existe
    ritual = db.rituais.find_one({"_id": ObjectId(ritual_semana.ritual_id)})
    if not ritual:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    update_doc = {
        **ritual_semana.dict(),
        "ritual_nome": ritual["nome"]
    }
    
    result = db.rituais_semana.update_one(
        {"_id": ObjectId(ritual_semana_id)},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ritual da semana não encontrado")
    
    return serialize_doc(db.rituais_semana.find_one({"_id": ObjectId(ritual_semana_id)}))

@app.delete("/api/admin/rituais-semana/{ritual_semana_id}")
async def delete_ritual_semana(ritual_semana_id: str, current_user: dict = Depends(get_current_user)):
    result = db.rituais_semana.delete_one({"_id": ObjectId(ritual_semana_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ritual da semana não encontrado")
    
    return {"message": "Ritual da semana deletado com sucesso"}

# Rotas de usuários
@app.get("/api/admin/users", response_model=List[User])
async def get_users(current_user: dict = Depends(get_current_user)):
    users = list(db.users.find({}, {"password": 0}))  # Não retornar senhas
    return serialize_doc(users)

@app.post("/api/admin/users", response_model=User)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    # Verificar se username já existe
    existing_user = db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username já existe")
    
    # Hash da senha
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    user_doc = {
        "_id": ObjectId(),
        "username": user.username,
        "password": hashed_password.decode('utf-8'),
        "email": user.email,
        "role": user.role,
        "created_at": datetime.utcnow()
    }
    
    result = db.users.insert_one(user_doc)
    created_user = db.users.find_one({"_id": result.inserted_id}, {"password": 0})
    
    return serialize_doc(created_user)

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    # Não permitir deletar a si mesmo
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Não é possível deletar seu próprio usuário")
    
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário deletado com sucesso"}

# Rotas de gateways de pagamento
@app.get("/api/admin/payment-gateways", response_model=List[PaymentGateway])
async def get_payment_gateways(current_user: dict = Depends(get_current_user)):
    gateways = list(db.payment_gateways.find({}))
    return serialize_doc(gateways)

@app.post("/api/admin/payment-gateways", response_model=PaymentGateway)
async def create_payment_gateway(gateway: PaymentGatewayCreate, current_user: dict = Depends(get_current_user)):
    gateway_doc = {
        "_id": ObjectId(),
        **gateway.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.payment_gateways.insert_one(gateway_doc)
    return serialize_doc(db.payment_gateways.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/payment-gateways/{gateway_id}", response_model=PaymentGateway)
async def update_payment_gateway(gateway_id: str, gateway: PaymentGatewayCreate, current_user: dict = Depends(get_current_user)):
    result = db.payment_gateways.update_one(
        {"_id": ObjectId(gateway_id)},
        {"$set": gateway.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gateway não encontrado")
    
    return serialize_doc(db.payment_gateways.find_one({"_id": ObjectId(gateway_id)}))

@app.delete("/api/admin/payment-gateways/{gateway_id}")
async def delete_payment_gateway(gateway_id: str, current_user: dict = Depends(get_current_user)):
    result = db.payment_gateways.delete_one({"_id": ObjectId(gateway_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gateway não encontrado")
    
    return {"message": "Gateway deletado com sucesso"}

# Rotas do Instagram
@app.get("/api/instagram/profile")
async def get_instagram_profile():
    profile = db.instagram_profile.find_one({})
    return serialize_doc(profile) if profile else None

@app.get("/api/instagram/posts")
async def get_instagram_posts():
    posts = list(db.instagram_posts.find({}).sort("created_at", -1).limit(12))
    return serialize_doc(posts)

@app.get("/api/admin/instagram/profile")
async def get_admin_instagram_profile(current_user: dict = Depends(get_current_user)):
    profile = db.instagram_profile.find_one({})
    return serialize_doc(profile) if profile else None

@app.post("/api/admin/instagram/profile")
async def create_or_update_instagram_profile(profile: InstagramProfileCreate, current_user: dict = Depends(get_current_user)):
    profile_doc = {
        **profile.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.instagram_profile.update_one({}, {"$set": profile_doc}, upsert=True)
    
    return serialize_doc(db.instagram_profile.find_one({}))

@app.get("/api/admin/instagram/posts")
async def get_admin_instagram_posts(current_user: dict = Depends(get_current_user)):
    posts = list(db.instagram_posts.find({}).sort("created_at", -1))
    return serialize_doc(posts)

@app.post("/api/admin/instagram/posts")
async def create_instagram_post(post: InstagramPostCreate, current_user: dict = Depends(get_current_user)):
    post_doc = {
        "_id": ObjectId(),
        **post.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.instagram_posts.insert_one(post_doc)
    return serialize_doc(db.instagram_posts.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/instagram/posts/{post_id}")
async def update_instagram_post(post_id: str, post: InstagramPostCreate, current_user: dict = Depends(get_current_user)):
    result = db.instagram_posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": post.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    return serialize_doc(db.instagram_posts.find_one({"_id": ObjectId(post_id)}))

@app.delete("/api/admin/instagram/posts/{post_id}")
async def delete_instagram_post(post_id: str, current_user: dict = Depends(get_current_user)):
    result = db.instagram_posts.delete_one({"_id": ObjectId(post_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    return {"message": "Post deletado com sucesso"}

# Rotas do Dashboard de Vendas
@app.get("/api/admin/dashboard/vendas")
async def get_dashboard_vendas(current_user: dict = Depends(get_current_user)):
    hoje = datetime.utcnow().date()
    inicio_mes = datetime(hoje.year, hoje.month, 1)
    inicio_dia = datetime.combine(hoje, datetime.min.time())
    fim_dia = datetime.combine(hoje, datetime.max.time())
    
    # Vendas de hoje
    vendas_hoje_rituais = db.clientes.count_documents({
        "created_at": {"$gte": inicio_dia, "$lte": fim_dia}
    })
    
    vendas_hoje_consultas = db.consultas.count_documents({
        "created_at": {"$gte": inicio_dia, "$lte": fim_dia},
        "status": {"$in": ["realizada", "confirmada"]}
    })
    
    # Faturamento hoje
    pipeline_rituais_hoje = [
        {"$match": {"created_at": {"$gte": inicio_dia, "$lte": fim_dia}}},
        {"$group": {"_id": None, "total": {"$sum": "$valor_pago"}}}
    ]
    
    pipeline_consultas_hoje = [
        {"$match": {
            "created_at": {"$gte": inicio_dia, "$lte": fim_dia},
            "status": {"$in": ["realizada", "confirmada"]}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$valor_pago"}}}
    ]
    
    faturamento_rituais_hoje = list(db.clientes.aggregate(pipeline_rituais_hoje))
    faturamento_consultas_hoje = list(db.consultas.aggregate(pipeline_consultas_hoje))
    
    valor_rituais_hoje = faturamento_rituais_hoje[0]["total"] if faturamento_rituais_hoje else 0
    valor_consultas_hoje = faturamento_consultas_hoje[0]["total"] if faturamento_consultas_hoje else 0
    
    # Vendas do mês
    vendas_mes_rituais = db.clientes.count_documents({
        "created_at": {"$gte": inicio_mes}
    })
    
    vendas_mes_consultas = db.consultas.count_documents({
        "created_at": {"$gte": inicio_mes},
        "status": {"$in": ["realizada", "confirmada"]}
    })
    
    # Faturamento do mês
    pipeline_rituais_mes = [
        {"$match": {"created_at": {"$gte": inicio_mes}}},
        {"$group": {"_id": None, "total": {"$sum": "$valor_pago"}}}
    ]
    
    pipeline_consultas_mes = [
        {"$match": {
            "created_at": {"$gte": inicio_mes},
            "status": {"$in": ["realizada", "confirmada"]}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$valor_pago"}}}
    ]
    
    faturamento_rituais_mes = list(db.clientes.aggregate(pipeline_rituais_mes))
    faturamento_consultas_mes = list(db.consultas.aggregate(pipeline_consultas_mes))
    
    valor_rituais_mes = faturamento_rituais_mes[0]["total"] if faturamento_rituais_mes else 0
    valor_consultas_mes = faturamento_consultas_mes[0]["total"] if faturamento_consultas_mes else 0
    
    # Meta mensal
    meta = db.metas_vendas.find_one({
        "mes": hoje.month,
        "ano": hoje.year
    })
    
    valor_meta = meta["valor_meta"] if meta else 5000.00
    faturamento_total_mes = valor_rituais_mes + valor_consultas_mes
    percentual_meta = (faturamento_total_mes / valor_meta * 100) if valor_meta > 0 else 0
    
    return {
        "vendas_hoje": {
            "rituais": {
                "quantidade": vendas_hoje_rituais,
                "valor": valor_rituais_hoje
            },
            "consultas": {
                "quantidade": vendas_hoje_consultas,
                "valor": valor_consultas_hoje
            },
            "total": {
                "quantidade": vendas_hoje_rituais + vendas_hoje_consultas,
                "valor": valor_rituais_hoje + valor_consultas_hoje
            }
        },
        "vendas_mes": {
            "rituais": {
                "quantidade": vendas_mes_rituais,
                "valor": valor_rituais_mes
            },
            "consultas": {
                "quantidade": vendas_mes_consultas,
                "valor": valor_consultas_mes
            },
            "total": {
                "quantidade": vendas_mes_rituais + vendas_mes_consultas,
                "valor": faturamento_total_mes
            }
        },
        "meta_mensal": {
            "valor_meta": valor_meta,
            "valor_atual": faturamento_total_mes,
            "percentual": round(percentual_meta, 1),
            "falta": max(0, valor_meta - faturamento_total_mes),
            "mes": hoje.month,
            "ano": hoje.year
        }
    }

@app.get("/api/admin/dashboard/vendas/consultas")
async def get_consultas_vendas(current_user: dict = Depends(get_current_user)):
    consultas = list(db.consultas.aggregate([
        {"$match": {"status": {"$in": ["realizada", "confirmada"]}}},
        {"$addFields": {
            "tipo_consulta_object_id": {"$toObjectId": "$tipo_consulta_id"}
        }},
        {"$lookup": {
            "from": "tipos_consulta",
            "localField": "tipo_consulta_object_id",
            "foreignField": "_id", 
            "as": "tipo_consulta"
        }},
        {"$unwind": "$tipo_consulta"},
        {"$addFields": {
            "tipo_consulta_nome": "$tipo_consulta.nome"
        }},
        {"$sort": {"created_at": -1}}
    ]))
    
    return serialize_doc(consultas)

@app.get("/api/admin/metas/{mes}/{ano}")
async def get_meta_mensal(mes: int, ano: int, current_user: dict = Depends(get_current_user)):
    meta = db.metas_vendas.find_one({"mes": mes, "ano": ano})
    if not meta:
        # Criar meta padrão
        meta_doc = {
            "_id": ObjectId(),
            "mes": mes,
            "ano": ano,
            "valor_meta": 5000.00
        }
        db.metas_vendas.insert_one(meta_doc)
        meta = meta_doc
    
    return serialize_doc(meta)

@app.post("/api/admin/metas")
async def create_or_update_meta(meta: MetaVendas, current_user: dict = Depends(get_current_user)):
    result = db.metas_vendas.update_one(
        {"mes": meta.mes, "ano": meta.ano},
        {"$set": {"valor_meta": meta.valor_meta}},
        upsert=True
    )
    
    updated_meta = db.metas_vendas.find_one({"mes": meta.mes, "ano": meta.ano})
    return serialize_doc(updated_meta)

# Rotas de Agendamento
@app.get("/api/tipos-consulta")
async def get_tipos_consulta():
    tipos = list(db.tipos_consulta.find({"ativo": True}))
    return serialize_doc(tipos)

@app.get("/api/admin/tipos-consulta")
async def get_admin_tipos_consulta(current_user: dict = Depends(get_current_user)):
    tipos = list(db.tipos_consulta.find({}))
    return serialize_doc(tipos)

@app.post("/api/admin/tipos-consulta")
async def create_tipo_consulta(tipo: TipoConsultaCreate, current_user: dict = Depends(get_current_user)):
    tipo_doc = {
        "_id": ObjectId(),
        **tipo.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.tipos_consulta.insert_one(tipo_doc)
    return serialize_doc(db.tipos_consulta.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/tipos-consulta/{tipo_id}")
async def update_tipo_consulta(tipo_id: str, tipo: TipoConsultaCreate, current_user: dict = Depends(get_current_user)):
    result = db.tipos_consulta.update_one(
        {"_id": ObjectId(tipo_id)},
        {"$set": tipo.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tipo de consulta não encontrado")
    
    return serialize_doc(db.tipos_consulta.find_one({"_id": ObjectId(tipo_id)}))

@app.delete("/api/admin/tipos-consulta/{tipo_id}")
async def delete_tipo_consulta(tipo_id: str, current_user: dict = Depends(get_current_user)):
    result = db.tipos_consulta.delete_one({"_id": ObjectId(tipo_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tipo de consulta não encontrado")
    
    return {"message": "Tipo de consulta deletado com sucesso"}

@app.get("/api/admin/horarios-disponiveis")
async def get_admin_horarios_disponiveis(current_user: dict = Depends(get_current_user)):
    horarios = list(db.horarios_disponiveis.find({}))
    return serialize_doc(horarios)

@app.post("/api/admin/horarios-disponiveis")
async def create_horario_disponivel(horario: HorarioDisponivelCreate, current_user: dict = Depends(get_current_user)):
    horario_doc = {
        "_id": ObjectId(),
        **horario.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.horarios_disponiveis.insert_one(horario_doc)
    return serialize_doc(db.horarios_disponiveis.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/horarios-disponiveis/{horario_id}")
async def update_horario_disponivel(horario_id: str, horario: HorarioDisponivelCreate, current_user: dict = Depends(get_current_user)):
    result = db.horarios_disponiveis.update_one(
        {"_id": ObjectId(horario_id)},
        {"$set": horario.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    return serialize_doc(db.horarios_disponiveis.find_one({"_id": ObjectId(horario_id)}))

@app.delete("/api/admin/horarios-disponiveis/{horario_id}")
async def delete_horario_disponivel(horario_id: str, current_user: dict = Depends(get_current_user)):
    result = db.horarios_disponiveis.delete_one({"_id": ObjectId(horario_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Horário não encontrado")
    
    return {"message": "Horário deletado com sucesso"}

@app.get("/api/horarios-disponiveis/{data}")
async def get_horarios_disponiveis_data(data: str):
    # Converter data string para datetime
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        dia_semana = data_obj.weekday()  # 0=Segunda, 6=Domingo
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    # Buscar horários configurados para o dia da semana
    horarios_config = list(db.horarios_disponiveis.find({
        "dia_semana": dia_semana,
        "ativo": True
    }))
    
    # Buscar consultas já agendadas para a data
    inicio_dia = datetime.combine(data_obj.date(), datetime.min.time())
    fim_dia = datetime.combine(data_obj.date(), datetime.max.time())
    
    consultas_agendadas = list(db.consultas.find({
        "data_hora": {"$gte": inicio_dia, "$lte": fim_dia},
        "status": {"$in": ["agendada", "confirmada"]}
    }))
    
    # Gerar lista de horários disponíveis
    horarios_disponiveis = []
    
    for config in horarios_config:
        hora_inicio = datetime.strptime(config["hora_inicio"], "%H:%M").time()
        hora_fim = datetime.strptime(config["hora_fim"], "%H:%M").time()
        intervalo = timedelta(minutes=config["intervalo_minutos"])
        
        current_time = datetime.combine(data_obj.date(), hora_inicio)
        end_time = datetime.combine(data_obj.date(), hora_fim)
        
        while current_time < end_time:
            # Verificar se horário não está ocupado
            ocupado = any(
                consulta["data_hora"].replace(second=0, microsecond=0) == current_time
                for consulta in consultas_agendadas
            )
            
            if not ocupado:
                horarios_disponiveis.append({
                    "horario": current_time.strftime("%H:%M"),
                    "data_hora": current_time.isoformat(),
                    "disponivel": True
                })
            
            current_time += intervalo
    
    return horarios_disponiveis

@app.post("/api/consultas")
async def create_consulta(consulta: ConsultaCreate):
    # Verificar se tipo de consulta existe
    tipo_consulta = db.tipos_consulta.find_one({"_id": ObjectId(consulta.tipo_consulta_id)})
    if not tipo_consulta:
        raise HTTPException(status_code=404, detail="Tipo de consulta não encontrado")
    
    # Verificar se horário está disponível
    consultas_no_horario = db.consultas.count_documents({
        "data_hora": consulta.data_hora,
        "status": {"$in": ["agendada", "confirmada"]}
    })
    
    if consultas_no_horario > 0:
        raise HTTPException(status_code=400, detail="Horário não está disponível")
    
    consulta_doc = {
        "_id": ObjectId(),
        **consulta.dict(),
        "tipo_consulta_nome": tipo_consulta["nome"],
        "status": "agendada",
        "valor_pago": tipo_consulta["preco"],
        "created_at": datetime.utcnow()
    }
    
    result = db.consultas.insert_one(consulta_doc)
    
    # Enviar confirmação via WhatsApp
    data_formatada = consulta.data_hora.strftime("%d/%m/%Y às %H:%M")
    send_consulta_confirmation(
        consulta.cliente_nome,
        consulta.cliente_whatsapp,
        data_formatada
    )
    
    return serialize_doc(db.consultas.find_one({"_id": result.inserted_id}))

@app.get("/api/admin/consultas/agenda/{data}")
async def get_agenda_dia(data: str, current_user: dict = Depends(get_current_user)):
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    inicio_dia = datetime.combine(data_obj.date(), datetime.min.time())
    fim_dia = datetime.combine(data_obj.date(), datetime.max.time())
    
    consultas = list(db.consultas.aggregate([
        {"$match": {
            "data_hora": {"$gte": inicio_dia, "$lte": fim_dia}
        }},
        {"$addFields": {
            "tipo_consulta_object_id": {"$toObjectId": "$tipo_consulta_id"}
        }},
        {"$lookup": {
            "from": "tipos_consulta",
            "localField": "tipo_consulta_object_id",
            "foreignField": "_id",
            "as": "tipo_consulta"
        }},
        {"$unwind": "$tipo_consulta"},
        {"$addFields": {
            "tipo_consulta_nome": "$tipo_consulta.nome"
        }},
        {"$sort": {"data_hora": 1}}
    ]))
    
    return serialize_doc(consultas)

# Rotas de WhatsApp
@app.get("/api/admin/whatsapp/config")
async def get_whatsapp_config(current_user: dict = Depends(get_current_user)):
    config = db.whatsapp_config.find_one({})
    if config:
        # Mascarar token por segurança
        config_safe = serialize_doc(config)
        if config_safe and "api_token" in config_safe:
            config_safe["api_token"] = "*" * (len(config_safe["api_token"]) - 4) + config_safe["api_token"][-4:]
        return config_safe
    return None

@app.post("/api/admin/whatsapp/config")
async def create_or_update_whatsapp_config(config: WhatsappConfigCreate, current_user: dict = Depends(get_current_user)):
    config_doc = {
        **config.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.whatsapp_config.update_one({}, {"$set": config_doc}, upsert=True)
    
    # Retornar config mascarado
    updated_config = serialize_doc(db.whatsapp_config.find_one({}))
    if updated_config and "api_token" in updated_config:
        updated_config["api_token"] = "*" * (len(updated_config["api_token"]) - 4) + updated_config["api_token"][-4:]
    
    return updated_config

@app.get("/api/admin/whatsapp/templates")
async def get_whatsapp_templates(current_user: dict = Depends(get_current_user)):
    templates = list(db.whatsapp_templates.find({}))
    return serialize_doc(templates)

@app.post("/api/admin/whatsapp/templates")
async def create_whatsapp_template(template: WhatsappTemplateCreate, current_user: dict = Depends(get_current_user)):
    template_doc = {
        "_id": ObjectId(),
        **template.dict(),
        "created_at": datetime.utcnow()
    }
    
    result = db.whatsapp_templates.insert_one(template_doc)
    return serialize_doc(db.whatsapp_templates.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/whatsapp/templates/{template_id}")
async def update_whatsapp_template(template_id: str, template: WhatsappTemplateCreate, current_user: dict = Depends(get_current_user)):
    result = db.whatsapp_templates.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": template.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return serialize_doc(db.whatsapp_templates.find_one({"_id": ObjectId(template_id)}))

@app.delete("/api/admin/whatsapp/templates/{template_id}")
async def delete_whatsapp_template(template_id: str, current_user: dict = Depends(get_current_user)):
    result = db.whatsapp_templates.delete_one({"_id": ObjectId(template_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return {"message": "Template deletado com sucesso"}

@app.post("/api/admin/whatsapp/send-test")
async def send_test_whatsapp(message: WhatsappMessageCreate, current_user: dict = Depends(get_current_user)):
    success = send_whatsapp_message(
        message.numero_destino,
        message.conteudo,
        message.template_usado
    )
    
    if success:
        return {"message": "Mensagem enviada com sucesso", "status": "enviada"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem")

@app.get("/api/admin/whatsapp/messages")
async def get_whatsapp_messages(current_user: dict = Depends(get_current_user)):
    messages = list(db.whatsapp_messages.find({}).sort("enviado_em", -1).limit(100))
    return serialize_doc(messages)

# Rotas de Backup
@app.get("/api/admin/backups")
async def get_backups(current_user: dict = Depends(get_current_user)):
    # Lista arquivos de backup
    import glob
    backups = []
    backup_files = glob.glob("/tmp/backup_rituais_*.json")
    
    for file_path in sorted(backup_files, reverse=True):
        import os
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        
        backups.append({
            "filename": filename,
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime)
        })
    
    # Buscar configuração de backup
    config = db.backup_config.find_one({})
    
    return {
        "backups": backups,
        "config": serialize_doc(config) if config else None
    }

@app.post("/api/admin/backups/create")
async def create_manual_backup(current_user: dict = Depends(get_current_user)):
    backup_path = backup_database()
    
    if backup_path:
        return {"message": "Backup criado com sucesso", "path": backup_path}
    else:
        raise HTTPException(status_code=500, detail="Erro ao criar backup")

@app.get("/api/admin/backups/download/{filename}")
async def download_backup(filename: str, current_user: dict = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    file_path = f"/tmp/{filename}"
    
    if not os.path.exists(file_path) or not filename.startswith("backup_rituais_"):
        raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado")
    
    return FileResponse(file_path, filename=filename, media_type='application/json')

# Rotas de Cupons
@app.get("/api/admin/cupons")
async def get_cupons(current_user: dict = Depends(get_current_user)):
    cupons = list(db.cupons.find({}))
    return serialize_doc(cupons)

@app.post("/api/admin/cupons")
async def create_cupom(cupom: CupomCreate, current_user: dict = Depends(get_current_user)):
    # Verificar se código já existe
    existing_cupom = db.cupons.find_one({"codigo": cupom.codigo})
    if existing_cupom:
        raise HTTPException(status_code=400, detail="Código de cupom já existe")
    
    cupom_doc = {
        "_id": ObjectId(),
        **cupom.dict(),
        "uso_atual": 0,
        "created_at": datetime.utcnow()
    }
    
    result = db.cupons.insert_one(cupom_doc)
    return serialize_doc(db.cupons.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/cupons/{cupom_id}")
async def update_cupom(cupom_id: str, cupom: CupomCreate, current_user: dict = Depends(get_current_user)):
    # Verificar se código já existe (exceto o próprio cupom)
    existing_cupom = db.cupons.find_one({
        "codigo": cupom.codigo,
        "_id": {"$ne": ObjectId(cupom_id)}
    })
    if existing_cupom:
        raise HTTPException(status_code=400, detail="Código de cupom já existe")
    
    result = db.cupons.update_one(
        {"_id": ObjectId(cupom_id)},
        {"$set": cupom.dict()}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cupom não encontrado")
    
    return serialize_doc(db.cupons.find_one({"_id": ObjectId(cupom_id)}))

@app.delete("/api/admin/cupons/{cupom_id}")
async def delete_cupom(cupom_id: str, current_user: dict = Depends(get_current_user)):
    result = db.cupons.delete_one({"_id": ObjectId(cupom_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cupom não encontrado")
    
    return {"message": "Cupom deletado com sucesso"}

@app.post("/api/validar-cupom")
async def validar_cupom(codigo: str, valor_pedido: float):
    cupom = db.cupons.find_one({
        "codigo": codigo,
        "ativo": True,
        "data_inicio": {"$lte": datetime.utcnow()},
        "data_fim": {"$gte": datetime.utcnow()}
    })
    
    if not cupom:
        raise HTTPException(status_code=404, detail="Cupom não encontrado ou expirado")
    
    # Verificar valor mínimo
    if cupom.get("valor_minimo") and valor_pedido < cupom["valor_minimo"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Valor mínimo do pedido: R$ {cupom['valor_minimo']:.2f}"
        )
    
    # Verificar limite de uso
    if cupom.get("uso_maximo") and cupom["uso_atual"] >= cupom["uso_maximo"]:
        raise HTTPException(status_code=400, detail="Cupom esgotado")
    
    # Calcular desconto
    if cupom["tipo"] == "percentual":
        desconto = valor_pedido * (cupom["percentual_desconto"] / 100)
    else:  # valor_fixo
        desconto = cupom["valor_desconto"]
    
    # Não pode ser maior que o valor do pedido
    desconto = min(desconto, valor_pedido)
    valor_final = valor_pedido - desconto
    
    return {
        "valido": True,
        "cupom": serialize_doc(cupom),
        "desconto": desconto,
        "valor_original": valor_pedido,
        "valor_final": valor_final
    }

# Rotas de Indicações
@app.get("/api/admin/indicacoes")
async def get_indicacoes(current_user: dict = Depends(get_current_user)):
    indicacoes = list(db.indicacoes.find({}))
    return serialize_doc(indicacoes)

@app.post("/api/indicacao-amigo")
async def create_indicacao(indicacao: IndicacaoCreate):
    # Gerar código único de indicação
    codigo_indicacao = f"IND{secrets.token_hex(4).upper()}"
    
    # Verificar se código já existe (muito improvável)
    while db.indicacoes.find_one({"codigo_indicacao": codigo_indicacao}):
        codigo_indicacao = f"IND{secrets.token_hex(4).upper()}"
    
    indicacao_doc = {
        "_id": ObjectId(),
        **indicacao.dict(),
        "codigo_indicacao": codigo_indicacao,
        "status": "pendente",
        "recompensa_liberada": False,
        "data_conversao": None,
        "created_at": datetime.utcnow()
    }
    
    result = db.indicacoes.insert_one(indicacao_doc)
    
    # Enviar WhatsApp com código de indicação
    mensagem = f"🎉 Obrigado por indicar um amigo! Seu código de indicação é: {codigo_indicacao}. Quando seu amigo fizer a primeira compra, você ganhará uma recompensa especial!"
    send_whatsapp_message(indicacao.whatsapp_indicador, mensagem, "indicacao_amigo")
    
    return serialize_doc(db.indicacoes.find_one({"_id": result.inserted_id}))

# Rotas do Editor de Site
@app.get("/api/admin/site-config")
async def get_site_config(current_user: dict = Depends(get_current_user)):
    config = db.site_config.find_one({})
    return serialize_doc(config) if config else None

@app.post("/api/admin/site-config")
async def create_or_update_site_config(config: SiteConfigCreate, current_user: dict = Depends(get_current_user)):
    config_doc = {
        **config.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.site_config.update_one({}, {"$set": config_doc}, upsert=True)
    return serialize_doc(db.site_config.find_one({}))

@app.get("/api/admin/site-sections")
async def get_site_sections(current_user: dict = Depends(get_current_user)):
    sections = list(db.site_sections.find({}).sort("ordem", 1))
    return serialize_doc(sections)

@app.post("/api/admin/site-sections")
async def create_site_section(section: SiteSectionCreate, current_user: dict = Depends(get_current_user)):
    section_doc = {
        "_id": ObjectId(),
        **section.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.site_sections.insert_one(section_doc)
    return serialize_doc(db.site_sections.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/site-sections/{section_id}")
async def update_site_section(section_id: str, section: SiteSectionCreate, current_user: dict = Depends(get_current_user)):
    result = db.site_sections.update_one(
        {"_id": ObjectId(section_id)},
        {"$set": {**section.dict(), "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    
    return serialize_doc(db.site_sections.find_one({"_id": ObjectId(section_id)}))

@app.delete("/api/admin/site-sections/{section_id}")
async def delete_site_section(section_id: str, current_user: dict = Depends(get_current_user)):
    result = db.site_sections.delete_one({"_id": ObjectId(section_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Seção não encontrada")
    
    return {"message": "Seção deletada com sucesso"}

@app.post("/api/admin/site-sections/reorder")
async def reorder_site_sections(section_ids: List[str], current_user: dict = Depends(get_current_user)):
    for index, section_id in enumerate(section_ids):
        db.site_sections.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"ordem": index + 1, "updated_at": datetime.utcnow()}}
        )
    
    return {"message": "Ordem das seções atualizada com sucesso"}

@app.get("/api/admin/site-content")
async def get_site_content(current_user: dict = Depends(get_current_user)):
    content = list(db.site_content.find({}).sort("ordem", 1))
    return serialize_doc(content)

@app.get("/api/admin/site-content/{secao}")
async def get_site_content_by_section(secao: str, current_user: dict = Depends(get_current_user)):
    content = list(db.site_content.find({"secao": secao}).sort("ordem", 1))
    return serialize_doc(content)

@app.post("/api/admin/site-content")
async def create_site_content(content: SiteContentCreate, current_user: dict = Depends(get_current_user)):
    content_doc = {
        "_id": ObjectId(),
        **content.dict(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.site_content.insert_one(content_doc)
    return serialize_doc(db.site_content.find_one({"_id": result.inserted_id}))

@app.put("/api/admin/site-content/{content_id}")
async def update_site_content(content_id: str, content: SiteContentCreate, current_user: dict = Depends(get_current_user)):
    result = db.site_content.update_one(
        {"_id": ObjectId(content_id)},
        {"$set": {**content.dict(), "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")
    
    return serialize_doc(db.site_content.find_one({"_id": ObjectId(content_id)}))

@app.delete("/api/admin/site-content/{content_id}")
async def delete_site_content(content_id: str, current_user: dict = Depends(get_current_user)):
    result = db.site_content.delete_one({"_id": ObjectId(content_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")
    
    return {"message": "Conteúdo deletado com sucesso"}

# Rota para upload de imagens
@app.post("/api/admin/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    # Verificar se é uma imagem
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    # Gerar nome único para o arquivo
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Criar diretório de uploads se não existir
    upload_dir = "/app/frontend/public/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Salvar arquivo
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Retornar URL relativa
    file_url = f"/uploads/{unique_filename}"
    
    return {
        "url": file_url,
        "filename": unique_filename,
        "original_name": file.filename,
        "size": len(content)
    }

# Rota para obter fontes do Google Fonts
@app.get("/api/admin/google-fonts")
async def get_google_fonts(current_user: dict = Depends(get_current_user)):
    # Lista de fontes populares do Google Fonts para o site
    fonts = [
        {"name": "Inter", "category": "sans-serif"},
        {"name": "Roboto", "category": "sans-serif"},
        {"name": "Open Sans", "category": "sans-serif"},
        {"name": "Lato", "category": "sans-serif"},
        {"name": "Montserrat", "category": "sans-serif"},
        {"name": "Poppins", "category": "sans-serif"},
        {"name": "Nunito", "category": "sans-serif"},
        {"name": "Source Sans Pro", "category": "sans-serif"},
        {"name": "Playfair Display", "category": "serif"},
        {"name": "Merriweather", "category": "serif"},
        {"name": "Lora", "category": "serif"},
        {"name": "Crimson Text", "category": "serif"},
        {"name": "PT Serif", "category": "serif"},
        {"name": "Dancing Script", "category": "handwriting"},
        {"name": "Pacifico", "category": "handwriting"},
        {"name": "Satisfy", "category": "handwriting"}
    ]
    
    return fonts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)