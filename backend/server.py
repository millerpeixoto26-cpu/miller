from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Stripe setup
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RitualCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    imagem_url: Optional[str] = None

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

# Routes
@api_router.get("/")
async def root():
    return {"message": "Sistema de Rituais API"}

@api_router.get("/rituais", response_model=List[dict])
async def get_rituais():
    """Retorna todos os rituais disponíveis"""
    rituais = await db.rituais.find().to_list(1000)
    if not rituais:
        # Se não há rituais no banco, insere os padrão
        for ritual_data in RITUAIS_PADRAO:
            await db.rituais.insert_one(ritual_data)
        return RITUAIS_PADRAO
    
    # Remove o _id do MongoDB para evitar erro de serialização
    for ritual in rituais:
        if "_id" in ritual:
            del ritual["_id"]
    
    return rituais

@api_router.post("/rituais", response_model=dict)
async def create_ritual(ritual: RitualCreate):
    """Cria um novo ritual"""
    ritual_dict = ritual.dict()
    ritual_dict["id"] = str(uuid.uuid4())
    ritual_dict["created_at"] = datetime.now(timezone.utc)
    await db.rituais.insert_one(ritual_dict)
    return ritual_dict

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
async def get_pedidos():
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