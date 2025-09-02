from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Stripe setup
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# JWT setup
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class Ritual(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    descricao: str
    preco: float
    imagem_url: Optional[str] = None
    visivel: bool = True
    tem_desconto: bool = False
    desconto_valor: Optional[float] = None
    desconto_percentual: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RitualCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    imagem_url: Optional[str] = None
    visivel: bool = True
    tem_desconto: bool = False
    desconto_valor: Optional[float] = None
    desconto_percentual: Optional[float] = None

class RitualUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    imagem_url: Optional[str] = None
    visivel: Optional[bool] = None
    tem_desconto: Optional[bool] = None
    desconto_valor: Optional[float] = None
    desconto_percentual: Optional[float] = None

class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome_completo: str
    email: str
    telefone: str
    nome_pessoa_amada: str
    data_nascimento: str
    informacoes_adicionais: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClienteCreate(BaseModel):
    nome_completo: str
    email: str
    telefone: str
    nome_pessoa_amada: str
    data_nascimento: str
    informacoes_adicionais: Optional[str] = None

class Pedido(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ritual_id: str
    cliente_id: str
    valor_total: float
    status_pagamento: str
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Configuracao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    logo_url: Optional[str] = None
    whatsapp_numero: Optional[str] = None
    cores: Dict[str, str] = Field(default_factory=lambda: {
        "primary": "#8b5cf6",
        "secondary": "#ec4899", 
        "background": "#1a1a2e",
        "text": "#ffffff"
    })
    layout_sections: List[str] = Field(default_factory=lambda: [
        "hero", "rituais", "testimonials", "footer"
    ])
    stripe_snippet_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RitualSemana(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dia_semana: str  # segunda, terca, quarta, quinta, sexta, sabado, domingo
    ritual_id: str
    imagem_destaque: Optional[str] = None
    ativo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConfiguracaoUpdate(BaseModel):
    logo_url: Optional[str] = None
    whatsapp_numero: Optional[str] = None
    cores: Optional[Dict[str, str]] = None
    layout_sections: Optional[List[str]] = None
    stripe_snippet_id: Optional[str] = None

class RitualSemanaCreate(BaseModel):
    dia_semana: str
    ritual_id: str
    imagem_destaque: Optional[str] = None
    ativo: bool = True

# Modelos de Autenticação
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float
    currency: str
    metadata: Dict[str, str]
    session_id: str
    payment_id: Optional[str] = None
    payment_status: str = "initiated"
    ritual_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CheckoutRequest(BaseModel):
    ritual_id: str
    host_url: str

# Rituais predefinidos
RITUAIS_PADRAO = [
    {
        "id": "amarracao-forte",
        "nome": "Amarração Forte",
        "descricao": "Ritual poderoso para unir duas pessoas através de laços espirituais profundos",
        "preco": 97.0,
        "imagem_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop"
    },
    {
        "id": "volta-do-amor",
        "nome": "Volta do Amor",
        "descricao": "Ritual especializado para reconquistar a pessoa amada",
        "preco": 127.0,
        "imagem_url": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=300&fit=crop"
    },
    {
        "id": "desamarre",
        "nome": "Desamarre",
        "descricao": "Ritual para quebrar amarrações e trabalhos negativos",
        "preco": 87.0,
        "imagem_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop"
    },
    {
        "id": "protecao-espiritual",
        "nome": "Proteção Espiritual",
        "descricao": "Ritual de proteção contra energias negativas e olho grande",
        "preco": 67.0,
        "imagem_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=300&fit=crop"
    }
]

async def get_stripe_checkout():
    """Dependency to get Stripe checkout instance"""
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")

# Funções de Autenticação
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    
    # Remove _id do MongoDB
    if "_id" in user:
        del user["_id"]
    
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Função para criar usuário admin padrão
async def create_default_admin():
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        default_admin = User(
            username="admin",
            email="admin@ritual.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        await db.users.insert_one(default_admin.dict())
        print("✅ Usuário admin padrão criado - Login: admin / Senha: admin123")
@api_router.get("/")
async def root():
    return {"message": "Sistema de Rituais API"}

# Rotas de Autenticação
@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login de usuário"""
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Username ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # Remove _id e hashed_password
    if "_id" in user:
        del user["_id"]
    if "hashed_password" in user:
        del user["hashed_password"]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user: User = Depends(get_current_active_user)):
    """Registra um novo usuário (apenas admins podem fazer isso)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar usuários")
    
    # Verifica se o usuário já existe
    existing_user = await db.users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username ou email já existe")
    
    # Cria novo usuário
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )
    
    await db.users.insert_one(new_user.dict())
    
    # Retorna usuário sem senha
    user_dict = new_user.dict()
    del user_dict["hashed_password"]
    return UserResponse(**user_dict)

@api_router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retorna informações do usuário atual"""
    user_dict = current_user.dict()
    del user_dict["hashed_password"]
    return UserResponse(**user_dict)

@api_router.get("/auth/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_active_user)):
    """Lista todos os usuários (apenas para admins)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem listar usuários")
    
    users = await db.users.find().to_list(1000)
    users_response = []
    for user in users:
        if "_id" in user:
            del user["_id"]
        if "hashed_password" in user:
            del user["hashed_password"]
        users_response.append(UserResponse(**user))
    
    return users_response

@api_router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_active_user)):
    """Remove um usuário (apenas para admins, não pode remover a si mesmo)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Apenas administradores podem remover usuários")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode remover sua própria conta")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário removido com sucesso"}

@api_router.get("/rituais", response_model=List[dict])
async def get_rituais():
    """Retorna todos os rituais disponíveis (apenas visíveis para o público)"""
    rituais = await db.rituais.find({"visivel": True}).to_list(1000)
    if not rituais:
        # Se não há rituais no banco, insere os padrão
        for ritual_data in RITUAIS_PADRAO:
            ritual_data["visivel"] = True
            ritual_data["tem_desconto"] = False
            await db.rituais.insert_one(ritual_data)
        return RITUAIS_PADRAO
    
    # Remove o _id do MongoDB para evitar erro de serialização
    for ritual in rituais:
        if "_id" in ritual:
            del ritual["_id"]
    
    return rituais

@api_router.get("/admin/rituais", response_model=List[dict])
async def get_all_rituais(current_user: User = Depends(get_current_active_user)):
    """Retorna todos os rituais (incluindo ocultos) para o admin"""
    rituais = await db.rituais.find().to_list(1000)
    if not rituais:
        # Se não há rituais no banco, insere os padrão
        for ritual_data in RITUAIS_PADRAO:
            ritual_data["visivel"] = True
            ritual_data["tem_desconto"] = False
            await db.rituais.insert_one(ritual_data)
        return RITUAIS_PADRAO
    
    # Remove o _id do MongoDB para evitar erro de serialização
    for ritual in rituais:
        if "_id" in ritual:
            del ritual["_id"]
    
    return rituais

@api_router.post("/rituais", response_model=dict)
async def create_ritual(ritual: RitualCreate, current_user: User = Depends(get_current_active_user)):
    """Cria um novo ritual"""
    ritual_dict = ritual.dict()
    ritual_dict["id"] = str(uuid.uuid4())
    ritual_dict["created_at"] = datetime.now(timezone.utc)
    await db.rituais.insert_one(ritual_dict)
    return ritual_dict

@api_router.put("/rituais/{ritual_id}", response_model=dict)
async def update_ritual(ritual_id: str, ritual_update: RitualUpdate, current_user: User = Depends(get_current_active_user)):
    """Atualiza um ritual existente"""
    existing_ritual = await db.rituais.find_one({"id": ritual_id})
    if not existing_ritual:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    # Atualiza apenas os campos fornecidos
    update_data = ritual_update.dict(exclude_unset=True)
    
    # Atualiza no banco
    await db.rituais.update_one(
        {"id": ritual_id},
        {"$set": update_data}
    )
    
    # Busca e retorna o ritual atualizado
    updated_ritual = await db.rituais.find_one({"id": ritual_id})
    if "_id" in updated_ritual:
        del updated_ritual["_id"]
    
    return updated_ritual

@api_router.delete("/rituais/{ritual_id}")
async def delete_ritual(ritual_id: str, current_user: User = Depends(get_current_active_user)):
    """Remove um ritual"""
    result = await db.rituais.delete_one({"id": ritual_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    return {"message": "Ritual removido com sucesso"}

@api_router.get("/rituais/{ritual_id}", response_model=dict)
async def get_ritual(ritual_id: str):
    """Retorna um ritual específico"""
    ritual = await db.rituais.find_one({"id": ritual_id})
    if not ritual:
        # Se não encontrou no banco, verifica nos padrão
        for r in RITUAIS_PADRAO:
            if r["id"] == ritual_id:
                return r
        raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    # Remove o _id do MongoDB
    if "_id" in ritual:
        del ritual["_id"]
    
    return ritual

@api_router.post("/checkout")
async def create_checkout_session(request: CheckoutRequest):
    """Cria uma sessão de pagamento no Stripe"""
    ritual = await db.rituais.find_one({"id": request.ritual_id})
    if not ritual:
        # Verifica nos rituais padrão
        ritual = next((r for r in RITUAIS_PADRAO if r["id"] == request.ritual_id), None)
        if not ritual:
            raise HTTPException(status_code=404, detail="Ritual não encontrado")
    
    # Inicializa Stripe
    webhook_url = f"{request.host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # URLs de sucesso e cancelamento
    success_url = f"{request.host_url}/sucesso?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.host_url}/"
    
    # Metadata
    metadata = {
        "ritual_id": request.ritual_id,
        "ritual_nome": ritual["nome"]
    }
    
    # Cria sessão de checkout
    checkout_request = CheckoutSessionRequest(
        amount=ritual["preco"],
        currency="brl",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Salva transação no banco
    transaction = PaymentTransaction(
        amount=ritual["preco"],
        currency="brl",
        metadata=metadata,
        session_id=session.session_id,
        ritual_id=request.ritual_id,
        payment_status="initiated"
    )
    
    await db.payment_transactions.insert_one(transaction.dict())
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    """Verifica o status do pagamento"""
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    
    # Verifica status no Stripe
    checkout_status = await stripe_checkout.get_checkout_status(session_id)
    
    # Atualiza status no banco
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": checkout_status.payment_status}}
    )
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "amount_total": checkout_status.amount_total,
        "currency": checkout_status.currency,
        "metadata": checkout_status.metadata
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Webhook do Stripe"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Atualiza status da transação
        await db.payment_transactions.update_one(
            {"session_id": webhook_response.session_id},
            {"$set": {"payment_status": webhook_response.payment_status}}
        )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/clientes", response_model=Cliente)
async def create_cliente(cliente: ClienteCreate, session_id: str):
    """Cria um novo cliente após pagamento confirmado"""
    # Verifica se o pagamento foi bem-sucedido
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction or transaction["payment_status"] != "paid":
        raise HTTPException(status_code=400, detail="Pagamento não confirmado")
    
    cliente_dict = cliente.dict()
    cliente_obj = Cliente(**cliente_dict)
    
    await db.clientes.insert_one(cliente_obj.dict())
    
    # Cria o pedido
    pedido = Pedido(
        ritual_id=transaction["ritual_id"],
        cliente_id=cliente_obj.id,
        valor_total=transaction["amount"],
        status_pagamento="paid",
        session_id=session_id
    )
    
    await db.pedidos.insert_one(pedido.dict())
    
    return cliente_obj

@api_router.get("/admin/pedidos", response_model=List[dict])
async def get_pedidos(current_user: User = Depends(get_current_active_user)):
    """Retorna todos os pedidos para o painel admin"""
    pipeline = [
        {
            "$lookup": {
                "from": "clientes",
                "localField": "cliente_id",
                "foreignField": "id",
                "as": "cliente"
            }
        },
        {
            "$lookup": {
                "from": "rituais",
                "localField": "ritual_id",
                "foreignField": "id",
                "as": "ritual"
            }
        },
        {
            "$unwind": "$cliente"
        },
        {
            "$unwind": "$ritual"
        },
        {
            "$match": {
                "status_pagamento": "paid"
            }
        },
        {
            "$sort": {
                "created_at": -1
            }
        }
    ]
    
    pedidos = await db.pedidos.aggregate(pipeline).to_list(1000)
    
    # Se não encontrou no banco, busca nos rituais padrão
    for pedido in pedidos:
        if not pedido.get("ritual"):
            ritual_padrao = next((r for r in RITUAIS_PADRAO if r["id"] == pedido["ritual_id"]), None)
            if ritual_padrao:
                pedido["ritual"] = ritual_padrao
    
    return pedidos

# APIs de Configuração
@api_router.get("/config", response_model=dict)
async def get_configuracao(current_user: User = Depends(get_current_active_user)):
    """Retorna as configurações do site"""
    config = await db.configuracoes.find_one()
    if not config:
        # Cria configuração padrão se não existir
        config_padrao = Configuracao()
        await db.configuracoes.insert_one(config_padrao.dict())
        return config_padrao.dict()
    
    # Remove o _id do MongoDB
    if "_id" in config:
        del config["_id"]
    
    return config

@api_router.put("/config", response_model=dict)
async def update_configuracao(config_update: ConfiguracaoUpdate, current_user: User = Depends(get_current_active_user)):
    """Atualiza as configurações do site"""
    existing_config = await db.configuracoes.find_one()
    
    if not existing_config:
        # Cria configuração padrão se não existir
        config_padrao = Configuracao()
        config_data = config_padrao.dict()
    else:
        config_data = existing_config
    
    # Atualiza apenas os campos fornecidos
    update_data = config_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        config_data[key] = value
    
    # Atualiza no banco
    await db.configuracoes.replace_one(
        {"id": config_data.get("id")}, 
        config_data, 
        upsert=True
    )
    
    # Remove o _id do MongoDB
    if "_id" in config_data:
        del config_data["_id"]
    
    return config_data

# APIs de Rituais da Semana
@api_router.get("/rituais-semana", response_model=List[dict])
async def get_rituais_semana(current_user: User = Depends(get_current_active_user)):
    """Retorna os rituais configurados para cada dia da semana"""
    rituais_semana = await db.rituais_semana.find({"ativo": True}).to_list(1000)
    
    # Remove o _id do MongoDB
    for ritual in rituais_semana:
        if "_id" in ritual:
            del ritual["_id"]
    
    # Busca dados completos dos rituais
    for rs in rituais_semana:
        ritual = await db.rituais.find_one({"id": rs["ritual_id"]})
        if not ritual:
            # Verifica nos rituais padrão
            ritual = next((r for r in RITUAIS_PADRAO if r["id"] == rs["ritual_id"]), None)
        
        if ritual and "_id" in ritual:
            del ritual["_id"]
        
        rs["ritual"] = ritual
    
    return rituais_semana

@api_router.post("/rituais-semana", response_model=dict)
async def create_ritual_semana(ritual_semana: RitualSemanaCreate, current_user: User = Depends(get_current_active_user)):
    """Cria ou atualiza ritual da semana para um dia específico"""
    # Remove ritual existente para o mesmo dia
    await db.rituais_semana.delete_many({"dia_semana": ritual_semana.dia_semana})
    
    # Cria novo ritual da semana
    ritual_dict = ritual_semana.dict()
    ritual_obj = RitualSemana(**ritual_dict)
    
    await db.rituais_semana.insert_one(ritual_obj.dict())
    
    return ritual_obj.dict()

@api_router.get("/rituais-semana/hoje", response_model=List[dict])
async def get_rituais_hoje():
    """Retorna os rituais de hoje baseado no dia da semana"""
    from datetime import datetime
    import locale
    
    # Mapeamento dos dias da semana
    dias_semana = {
        0: "segunda",  # Monday
        1: "terca",    # Tuesday  
        2: "quarta",   # Wednesday
        3: "quinta",   # Thursday
        4: "sexta",    # Friday
        5: "sabado",   # Saturday
        6: "domingo"   # Sunday
    }
    
    hoje = datetime.now().weekday()
    dia_hoje = dias_semana[hoje]
    
    rituais_hoje = await db.rituais_semana.find({
        "dia_semana": dia_hoje, 
        "ativo": True
    }).to_list(1000)
    
    # Remove o _id do MongoDB e busca dados completos
    for ritual in rituais_hoje:
        if "_id" in ritual:
            del ritual["_id"]
        
        # Busca dados completos do ritual
        ritual_data = await db.rituais.find_one({"id": ritual["ritual_id"]})
        if not ritual_data:
            ritual_data = next((r for r in RITUAIS_PADRAO if r["id"] == ritual["ritual_id"]), None)
        
        if ritual_data and "_id" in ritual_data:
            del ritual_data["_id"]
        
        ritual["ritual"] = ritual_data
    
    return rituais_hoje

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()