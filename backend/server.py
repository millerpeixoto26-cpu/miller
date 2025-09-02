from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
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
import requests
import secrets

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

# Modelos de Gateway de Pagamento
class PaymentGateway(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # stripe, pagbank, mercadopago
    display_name: str  # Nome amigável
    is_active: bool = False
    is_default: bool = False
    config: Dict[str, str] = Field(default_factory=dict)  # API keys, etc
    supported_methods: List[str] = Field(default_factory=list)  # credit_card, pix, boleto
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentGatewayCreate(BaseModel):
    name: str
    display_name: str
    is_active: bool = True
    is_default: bool = False
    config: Dict[str, str] = Field(default_factory=dict)
    supported_methods: List[str] = Field(default_factory=list)

class PaymentGatewayUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    config: Optional[Dict[str, str]] = None
    supported_methods: Optional[List[str]] = None

# Modelos Instagram
class InstagramProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    display_name: str
    bio: str
    profile_image_url: str
    instagram_url: str
    followers_count: Optional[int] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InstagramPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_url: str
    caption: str
    post_url: Optional[str] = None
    is_active: bool = True
    order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Novos modelos para API Integration
class InstagramApiConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    app_id: str
    app_secret: str
    redirect_uri: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InstagramApiToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    instagram_user_id: Optional[str] = None
    instagram_username: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InstagramApiSync(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sync_type: str  # "profile", "posts", "both"
    status: str  # "pending", "in_progress", "completed", "failed"
    items_synced: int = 0
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class InstagramProfileCreate(BaseModel):
    username: str
    display_name: str
    bio: str
    profile_image_url: str
    instagram_url: str
    followers_count: Optional[int] = None
    is_active: bool = True

class InstagramProfileUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    instagram_url: Optional[str] = None
    followers_count: Optional[int] = None
    is_active: Optional[bool] = None

class InstagramPostCreate(BaseModel):
    image_url: str
    caption: str
    post_url: Optional[str] = None
    is_active: bool = True
    order: int = 0

class InstagramPostUpdate(BaseModel):
    image_url: Optional[str] = None
    caption: Optional[str] = None
    post_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

# Novos modelos para API Integration
class InstagramApiConfigCreate(BaseModel):
    app_id: str
    app_secret: str
    redirect_uri: str
    is_active: bool = True

class InstagramApiConfigUpdate(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    is_active: Optional[bool] = None

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

# Gateways de pagamento padrão
GATEWAYS_PADRAO = [
    {
        "id": "stripe",
        "name": "stripe",
        "display_name": "Stripe",
        "is_active": True,
        "is_default": True,
        "config": {
            "api_key": "",
            "webhook_secret": "",
            "currency": "brl"
        },
        "supported_methods": ["credit_card", "pix"]
    },
    {
        "id": "pagbank",
        "name": "pagbank",
        "display_name": "PagBank (PagSeguro)",
        "is_active": False,
        "is_default": False,
        "config": {
            "client_id": "",
            "client_secret": "",
            "sandbox": "true"
        },
        "supported_methods": ["credit_card", "pix", "boleto"]
    },
    {
        "id": "mercadopago",
        "name": "mercadopago", 
        "display_name": "Mercado Pago",
        "is_active": False,
        "is_default": False,
        "config": {
            "access_token": "",
            "public_key": "",
            "sandbox": "true"
        },
        "supported_methods": ["credit_card", "pix", "boleto"]
    }
]
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

# Função para criar gateways padrão
async def create_default_gateways():
    existing_gateways = await db.payment_gateways.count_documents({})
    if existing_gateways == 0:
        for gateway_data in GATEWAYS_PADRAO:
            await db.payment_gateways.insert_one(gateway_data)
        print("✅ Gateways de pagamento padrão criados")
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

# APIs de Gateways de Pagamento
@api_router.get("/payment-gateways", response_model=List[dict])
async def get_payment_gateways(current_user: User = Depends(get_current_active_user)):
    """Retorna todos os gateways de pagamento"""
    gateways = await db.payment_gateways.find().to_list(1000)
    
    # Remove o _id do MongoDB
    for gateway in gateways:
        if "_id" in gateway:
            del gateway["_id"]
    
    return gateways

@api_router.get("/payment-gateways/active", response_model=List[dict])
async def get_active_payment_gateways():
    """Retorna apenas gateways ativos (para uso público)"""
    gateways = await db.payment_gateways.find({"is_active": True}).to_list(1000)
    
    # Remove dados sensíveis e _id
    for gateway in gateways:
        if "_id" in gateway:
            del gateway["_id"]
        # Remove config para não expor chaves de API
        if "config" in gateway:
            del gateway["config"]
    
    return gateways

@api_router.get("/payment-gateways/default", response_model=dict)
async def get_default_payment_gateway():
    """Retorna o gateway padrão"""
    gateway = await db.payment_gateways.find_one({"is_default": True, "is_active": True})
    
    if not gateway:
        # Se não há gateway padrão, pega o primeiro ativo
        gateway = await db.payment_gateways.find_one({"is_active": True})
    
    if not gateway:
        raise HTTPException(status_code=404, detail="Nenhum gateway de pagamento ativo encontrado")
    
    # Remove _id
    if "_id" in gateway:
        del gateway["_id"]
    
    return gateway

@api_router.put("/payment-gateways/{gateway_id}", response_model=dict)
async def update_payment_gateway(
    gateway_id: str, 
    gateway_update: PaymentGatewayUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um gateway de pagamento"""
    existing_gateway = await db.payment_gateways.find_one({"id": gateway_id})
    if not existing_gateway:
        raise HTTPException(status_code=404, detail="Gateway não encontrado")
    
    update_data = gateway_update.dict(exclude_unset=True)
    
    # Se está definindo como padrão, remove o padrão dos outros
    if update_data.get("is_default") == True:
        await db.payment_gateways.update_many(
            {"id": {"$ne": gateway_id}},
            {"$set": {"is_default": False}}
        )
    
    # Atualiza o gateway
    await db.payment_gateways.update_one(
        {"id": gateway_id},
        {"$set": update_data}
    )
    
    # Retorna o gateway atualizado
    updated_gateway = await db.payment_gateways.find_one({"id": gateway_id})
    if "_id" in updated_gateway:
        del updated_gateway["_id"]
    
    return updated_gateway

@api_router.post("/payment-gateways/{gateway_id}/test", response_model=dict)
async def test_payment_gateway(
    gateway_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Testa conexão com o gateway de pagamento"""
    gateway = await db.payment_gateways.find_one({"id": gateway_id})
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway não encontrado")
    
    # Aqui você implementaria a lógica de teste para cada gateway
    # Por enquanto, vamos simular um teste básico
    
    gateway_name = gateway["name"]
    config = gateway.get("config", {})
    
    # Verifica se as configurações básicas estão preenchidas
    if gateway_name == "stripe":
        if not config.get("api_key"):
            return {"success": False, "message": "API Key do Stripe não configurada"}
    elif gateway_name == "pagbank":
        if not config.get("client_id") or not config.get("client_secret"):
            return {"success": False, "message": "Client ID ou Client Secret do PagBank não configurados"}
    elif gateway_name == "mercadopago":
        if not config.get("access_token"):
            return {"success": False, "message": "Access Token do Mercado Pago não configurado"}
    
    return {
        "success": True, 
        "message": f"Configurações do {gateway['display_name']} validadas com sucesso"
    }

# APIs Instagram (Manual)
@api_router.get("/instagram/profile")
async def get_instagram_profile():
    """Retorna o perfil Instagram (público)"""
    profile = await db.instagram_profile.find_one({"is_active": True})
    if not profile:
        return {"message": "Perfil não encontrado", "profile": None}
    
    if "_id" in profile:
        del profile["_id"]
    
    return profile

@api_router.get("/admin/instagram/profile")
async def get_instagram_profile_admin(current_user: User = Depends(get_current_active_user)):
    """Retorna o perfil Instagram para admin"""
    profile = await db.instagram_profile.find_one()
    if not profile:
        return {"message": "Perfil não encontrado", "profile": None}
    
    if "_id" in profile:
        del profile["_id"]
    
    return profile

@api_router.post("/admin/instagram/profile", response_model=dict)
async def create_or_update_instagram_profile(
    profile_data: InstagramProfileCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """Cria ou atualiza o perfil Instagram"""
    existing_profile = await db.instagram_profile.find_one()
    
    profile_dict = profile_data.dict()
    
    if existing_profile:
        # Atualiza perfil existente
        await db.instagram_profile.update_one(
            {"id": existing_profile["id"]},
            {"$set": profile_dict}
        )
        profile_dict["id"] = existing_profile["id"]
    else:
        # Cria novo perfil
        profile_obj = InstagramProfile(**profile_dict)
        await db.instagram_profile.insert_one(profile_obj.dict())
        profile_dict = profile_obj.dict()
    
    return profile_dict

@api_router.get("/instagram/posts", response_model=List[dict])
async def get_instagram_posts():
    """Retorna posts Instagram ativos (público)"""
    posts = await db.instagram_posts.find(
        {"is_active": True}
    ).sort("order", 1).limit(9).to_list(9)
    
    for post in posts:
        if "_id" in post:
            del post["_id"]
    
    return posts

@api_router.get("/admin/instagram/posts", response_model=List[dict])
async def get_instagram_posts_admin(current_user: User = Depends(get_current_active_user)):
    """Retorna todos os posts Instagram para admin"""
    posts = await db.instagram_posts.find().sort("order", 1).to_list(1000)
    
    for post in posts:
        if "_id" in post:
            del post["_id"]
    
    return posts

@api_router.post("/admin/instagram/posts", response_model=dict)
async def create_instagram_post(
    post_data: InstagramPostCreate, 
    current_user: User = Depends(get_current_active_user)
):
    """Cria um novo post Instagram"""
    post_dict = post_data.dict()
    post_obj = InstagramPost(**post_dict)
    
    await db.instagram_posts.insert_one(post_obj.dict())
    
    return post_obj.dict()

@api_router.put("/admin/instagram/posts/{post_id}", response_model=dict)
async def update_instagram_post(
    post_id: str, 
    post_update: InstagramPostUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Atualiza um post Instagram"""
    existing_post = await db.instagram_posts.find_one({"id": post_id})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    update_data = post_update.dict(exclude_unset=True)
    
    await db.instagram_posts.update_one(
        {"id": post_id},
        {"$set": update_data}
    )
    
    updated_post = await db.instagram_posts.find_one({"id": post_id})
    if "_id" in updated_post:
        del updated_post["_id"]
    
    return updated_post

@api_router.delete("/admin/instagram/posts/{post_id}")
async def delete_instagram_post(
    post_id: str, 
    current_user: User = Depends(get_current_active_user)
):
    """Remove um post Instagram"""
    result = await db.instagram_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    return {"message": "Post removido com sucesso"}

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar o router API
app.include_router(api_router)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Função para criar configuração padrão do Instagram API
async def create_default_instagram_config():
    config_exists = await db.instagram_api_config.find_one()
    if not config_exists:
        # Criar configuração vazia para ser preenchida pelo admin
        default_config = InstagramApiConfig(
            app_id="",
            app_secret="",
            redirect_uri=f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/admin/instagram/callback",
            is_active=False
        )
        await db.instagram_api_config.insert_one(default_config.dict())
        print("✅ Configuração padrão do Instagram API criada")

@app.on_event("startup")
async def startup_event():
    await create_default_admin()
    await create_default_gateways()
    await create_default_instagram_config()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Novas APIs para Instagram API Integration
@api_router.get("/admin/instagram/api/config")
async def get_instagram_api_config(current_user: User = Depends(get_current_active_user)):
    """Retorna configuração da API do Instagram"""
    config = await db.instagram_api_config.find_one()
    if not config:
        return {"message": "Configuração não encontrada", "config": None}
    
    if "_id" in config:
        del config["_id"]
    
    # Não retornar app_secret por segurança
    if "app_secret" in config:
        config["app_secret"] = "***" if config["app_secret"] else ""
    
    return config

@api_router.post("/admin/instagram/api/config")
async def create_or_update_instagram_api_config(
    config_data: InstagramApiConfigCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Cria ou atualiza configuração da API do Instagram"""
    existing_config = await db.instagram_api_config.find_one()
    
    config_dict = config_data.dict()
    config_dict["id"] = str(uuid.uuid4()) if not existing_config else existing_config["id"]
    config_dict["created_at"] = datetime.now(timezone.utc)
    
    if existing_config:
        # Atualiza configuração existente
        await db.instagram_api_config.replace_one(
            {"id": existing_config["id"]},
            config_dict
        )
    else:
        # Cria nova configuração
        await db.instagram_api_config.insert_one(config_dict)
    
    # Remove app_secret da resposta
    config_dict["app_secret"] = "***"
    if "_id" in config_dict:
        del config_dict["_id"]
    
    return config_dict

@api_router.get("/admin/instagram/api/connect")
async def instagram_api_connect(current_user: User = Depends(get_current_active_user)):
    """Inicia processo de conexão com Instagram API"""
    config = await db.instagram_api_config.find_one({"is_active": True})
    if not config or not config.get("app_id") or not config.get("app_secret"):
        raise HTTPException(
            status_code=400, 
            detail="Configuração da API do Instagram não encontrada ou incompleta"
        )
    
    # Gerar state para CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Salvar state no banco temporariamente (expira em 10 minutos)
    await db.instagram_oauth_states.insert_one({
        "state": state,
        "user_id": current_user.id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })
    
    # URL de autorização do Instagram
    auth_url = (
        "https://api.instagram.com/oauth/authorize"
        f"?client_id={config['app_id']}"
        f"&redirect_uri={config['redirect_uri']}"
        "&scope=user_profile,user_media"
        "&response_type=code"
        f"&state={state}"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Redirecione o usuário para auth_url para completar a autenticação"
    }

@api_router.get("/admin/instagram/api/callback")
async def instagram_api_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Callback da autenticação OAuth2 do Instagram"""
    
    # Verificar se houve erro na autenticação
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Erro na autenticação Instagram: {error} - {error_description or 'Erro desconhecido'}"
        )
    
    # Validar parâmetros obrigatórios
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Código de autorização ou state não recebidos"
        )
    
    # Validar state (CSRF protection)
    oauth_state = await db.instagram_oauth_states.find_one({
        "state": state,
        "user_id": current_user.id
    })
    
    if not oauth_state:
        raise HTTPException(status_code=400, detail="State inválido ou expirado")
    
    # Verificar se state não expirou
    if datetime.now(timezone.utc) > oauth_state["expires_at"]:
        raise HTTPException(status_code=400, detail="State expirado")
    
    # Remover state usado
    await db.instagram_oauth_states.delete_one({"state": state})
    
    # Obter configuração da API
    config = await db.instagram_api_config.find_one({"is_active": True})
    if not config:
        raise HTTPException(status_code=500, detail="Configuração da API não encontrada")
    
    try:
        # Trocar código por access token
        token_url = "https://api.instagram.com/oauth/access_token"
        token_data = {
            'client_id': config['app_id'],
            'client_secret': config['app_secret'],
            'grant_type': 'authorization_code',
            'redirect_uri': config['redirect_uri'],
            'code': code
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            raise HTTPException(status_code=400, detail="Falha ao obter access token")
        
        # Salvar token no banco
        token_obj = InstagramApiToken(
            user_id=current_user.id,
            access_token=token_json['access_token'],
            instagram_user_id=str(token_json.get('user_id', '')),
            is_active=True
        )
        
        # Remover tokens antigos do usuário
        await db.instagram_api_tokens.delete_many({"user_id": current_user.id})
        
        # Inserir novo token
        await db.instagram_api_tokens.insert_one(token_obj.dict())
        
        return {
            "message": "Conta Instagram conectada com sucesso",
            "instagram_user_id": token_json.get('user_id'),
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao conectar com Instagram API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@api_router.get("/admin/instagram/api/status")
async def instagram_api_status(current_user: User = Depends(get_current_active_user)):
    """Verifica status da conexão com Instagram API"""
    token = await db.instagram_api_tokens.find_one({
        "user_id": current_user.id,
        "is_active": True
    })
    
    if not token:
        return {
            "connected": False,
            "message": "Conta Instagram não conectada"
        }
    
    # Verificar se token ainda é válido fazendo uma chamada para a API
    try:
        user_url = f"https://graph.instagram.com/me?fields=id,username&access_token={token['access_token']}"
        response = requests.get(user_url)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "connected": True,
                "instagram_user_id": user_data.get('id'),
                "instagram_username": user_data.get('username'),
                "connected_at": token['created_at']
            }
        else:
            # Token inválido, marcar como inativo
            await db.instagram_api_tokens.update_one(
                {"id": token["id"]},
                {"$set": {"is_active": False}}
            )
            return {
                "connected": False,
                "message": "Token expirado ou inválido"
            }
            
    except Exception as e:
        return {
            "connected": False,
            "message": f"Erro ao verificar conexão: {str(e)}"
        }

@api_router.post("/admin/instagram/api/sync")
async def instagram_api_sync(
    sync_type: str = "both",  # "profile", "posts", "both"
    current_user: User = Depends(get_current_active_user)
):
    """Sincroniza dados do Instagram via API"""
    
    # Verificar se há token ativo
    token = await db.instagram_api_tokens.find_one({
        "user_id": current_user.id,
        "is_active": True
    })
    
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Conta Instagram não conectada"
        )
    
    # Criar registro de sincronização
    sync_record = InstagramApiSync(
        sync_type=sync_type,
        status="in_progress"
    )
    sync_result = await db.instagram_api_syncs.insert_one(sync_record.dict())
    sync_id = sync_result.inserted_id
    
    try:
        items_synced = 0
        
        # Sincronizar perfil
        if sync_type in ["profile", "both"]:
            user_url = f"https://graph.instagram.com/me?fields=id,username,account_type,media_count&access_token={token['access_token']}"
            response = requests.get(user_url)
            response.raise_for_status()
            
            user_data = response.json()
            
            # Atualizar perfil no banco
            profile_data = {
                "username": user_data.get('username', ''),
                "display_name": user_data.get('username', ''),
                "bio": f"Conta conectada via API - {user_data.get('account_type', 'PERSONAL')}",
                "profile_image_url": f"https://via.placeholder.com/150?text={user_data.get('username', 'IG')}",
                "instagram_url": f"https://instagram.com/{user_data.get('username', '')}",
                "followers_count": None,  # Basic Display API não fornece followers
                "is_active": True
            }
            
            # Remover perfil existente e criar novo
            await db.instagram_profile.delete_many({})
            profile_obj = InstagramProfile(**profile_data)
            await db.instagram_profile.insert_one(profile_obj.dict())
            items_synced += 1
        
        # Sincronizar posts
        if sync_type in ["posts", "both"]:
            media_url = f"https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,permalink,thumbnail_url,timestamp&access_token={token['access_token']}"
            response = requests.get(media_url)
            response.raise_for_status()
            
            media_data = response.json()
            
            # Remover posts existentes
            await db.instagram_posts.delete_many({})
            
            # Inserir novos posts
            for i, item in enumerate(media_data.get('data', [])[:6]):  # Limitar a 6 posts
                post_data = {
                    "image_url": item.get('media_url', item.get('thumbnail_url', '')),
                    "caption": item.get('caption', '')[:200] if item.get('caption') else '',  # Limitar caption
                    "post_url": item.get('permalink', ''),
                    "is_active": True,
                    "order": i
                }
                
                post_obj = InstagramPost(**post_data)
                await db.instagram_posts.insert_one(post_obj.dict())
                items_synced += 1
        
        # Atualizar registro de sincronização
        await db.instagram_api_syncs.update_one(
            {"_id": sync_id},
            {
                "$set": {
                    "status": "completed",
                    "items_synced": items_synced,
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "message": f"Sincronização concluída com sucesso",
            "sync_type": sync_type,
            "items_synced": items_synced,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except requests.RequestException as e:
        # Atualizar registro com erro
        await db.instagram_api_syncs.update_one(
            {"_id": sync_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao sincronizar com Instagram: {str(e)}"
        )
    except Exception as e:
        # Atualizar registro com erro
        await db.instagram_api_syncs.update_one(
            {"_id": sync_id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.now(timezone.utc)
                }
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@api_router.delete("/admin/instagram/api/disconnect")
async def instagram_api_disconnect(current_user: User = Depends(get_current_active_user)):
    """Desconecta conta Instagram"""
    result = await db.instagram_api_tokens.update_many(
        {"user_id": current_user.id},
        {"$set": {"is_active": False}}
    )
    
    return {
        "message": "Conta Instagram desconectada com sucesso",
        "tokens_deactivated": result.modified_count
    }

@api_router.get("/admin/instagram/api/sync/history")
async def instagram_api_sync_history(current_user: User = Depends(get_current_active_user)):
    """Retorna histórico de sincronizações"""
    syncs = await db.instagram_api_syncs.find().sort("started_at", -1).limit(10).to_list(10)
    
    for sync in syncs:
        if "_id" in sync:
            del sync["_id"]
    
    return syncs