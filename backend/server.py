from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import mercadopago
from emergentintegrations.llm.chat import LlmChat, UserMessage
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.responses import StreamingResponse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Mercado Pago SDK
sdk = mercadopago.SDK(os.environ.get('MERCADO_PAGO_ACCESS_TOKEN'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ========== MODELS ==========

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password: str
    role: str = "user"  # user ou admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyCreate(BaseModel):
    user_id: str
    name: str
    segment: str
    # Dados da empresa
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    # Endereço
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    # Contatos
    telefone_fixo: Optional[str] = None
    celular_whatsapp: Optional[str] = None
    email_empresa: Optional[str] = None
    site: Optional[str] = None
    contato_principal: Optional[str] = None

class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    segment: str
    # Dados da empresa
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None
    # Endereço
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    # Contatos
    telefone_fixo: Optional[str] = None
    celular_whatsapp: Optional[str] = None
    email_empresa: Optional[str] = None
    site: Optional[str] = None
    contato_principal: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: str  # trial, active, expired, cancelled
    trial_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trial_end: datetime
    subscription_start: Optional[datetime] = None
    payment_id: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    company_id: str
    user_id: str
    type: str  # receita, custo, despesa
    description: str
    amount: float
    category: str
    date: str
    status: str = "previsto"  # previsto, realizado
    notes: Optional[str] = None

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: str
    type: str
    description: str
    amount: float
    category: str
    date: str
    status: str = "previsto"
    notes: Optional[str] = None
    origem: str = "manual"  # manual ou conta (vindo de contas a pagar/receber)
    conta_id: Optional[str] = None  # ID da conta vinculada (se origem = conta)
    cancelled: bool = False  # Indica se o lançamento foi cancelado
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MonthlyGoalCreate(BaseModel):
    company_id: str
    month: str  # formato: 2025-12
    goal_amount: float

class MonthlyGoal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    month: str
    goal_amount: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========== MODELS DE CONTAS A PAGAR/RECEBER ==========

class ContaCreate(BaseModel):
    company_id: str
    user_id: str
    tipo: str  # PAGAR ou RECEBER
    descricao: str
    categoria: str
    data_emissao: str  # formato: YYYY-MM-DD
    data_vencimento: str  # formato: YYYY-MM-DD
    valor: float
    forma_pagamento: str  # PIX, Boleto, Cartão, Dinheiro, Transferência
    observacoes: Optional[str] = None

class Conta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    user_id: str
    tipo: str  # PAGAR ou RECEBER
    descricao: str
    categoria: str
    data_emissao: str
    data_vencimento: str
    data_pagamento: Optional[str] = None
    valor: float
    status: str = "PENDENTE"  # PENDENTE, PAGO, ATRASADO, PARCIAL
    forma_pagamento: str
    observacoes: Optional[str] = None
    lancamento_id: Optional[str] = None  # ID do lançamento vinculado
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContaStatusUpdate(BaseModel):
    status: str  # PAGO, RECEBIDO, PENDENTE, ATRASADO, PARCIAL
    data_pagamento: Optional[str] = None

# ========== MODELS DE CATEGORIAS PERSONALIZADAS ==========

class CustomCategoryCreate(BaseModel):
    company_id: str
    tipo: str  # receita, custo, despesa
    nome: str

class CustomCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    tipo: str  # receita, custo, despesa
    nome: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========== MODELS DE ORÇAMENTOS ==========

class OrcamentoCreate(BaseModel):
    empresa_id: str
    usuario_id: str
    # Cliente
    cliente_nome: str
    cliente_documento: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_telefone: Optional[str] = None
    cliente_whatsapp: Optional[str] = None
    cliente_endereco: Optional[str] = None
    # Dados do orçamento
    tipo: str  # produto, servico_hora, servico_m2, valor_fechado
    descricao_servico_ou_produto: str
    area_m2: Optional[float] = None
    quantidade: Optional[float] = None
    detalhes_itens: Optional[dict] = None
    custo_total: float
    preco_minimo: float
    preco_sugerido: float
    preco_praticado: float
    # Condições comerciais
    validade_proposta: str  # data no formato YYYY-MM-DD
    condicoes_pagamento: str
    prazo_execucao: str
    observacoes: Optional[str] = None

class Orcamento(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero_orcamento: str  # Será gerado automaticamente
    empresa_id: str
    usuario_id: str
    # Cliente
    cliente_nome: str
    cliente_documento: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_telefone: Optional[str] = None
    cliente_whatsapp: Optional[str] = None
    cliente_endereco: Optional[str] = None
    # Dados do orçamento
    tipo: str
    descricao_servico_ou_produto: str
    area_m2: Optional[float] = None
    quantidade: Optional[float] = None
    detalhes_itens: Optional[dict] = None
    custo_total: float
    preco_minimo: float
    preco_sugerido: float
    preco_praticado: float
    # Condições comerciais
    validade_proposta: str
    condicoes_pagamento: str
    prazo_execucao: str
    observacoes: Optional[str] = None
    # Status e envio
    status: str = "RASCUNHO"  # RASCUNHO, ENVIADO, APROVADO, NAO_APROVADO
    enviado_em: Optional[datetime] = None
    aprovado_em: Optional[datetime] = None
    nao_aprovado_em: Optional[datetime] = None
    canal_envio: Optional[str] = None
    # Auditoria
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrcamentoStatusUpdate(BaseModel):
    status: str  # ENVIADO, APROVADO, NAO_APROVADO
    canal_envio: Optional[str] = None

# ========== MODELS: MATERIAIS ==========

class MaterialCreate(BaseModel):
    nome_item: str
    descricao: Optional[str] = None
    unidade: str
    preco_compra_base: float

class Material(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome_item: str
    descricao: Optional[str] = None
    unidade: str
    preco_compra_base: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrcamentoMaterialCreate(BaseModel):
    id_orcamento: str
    id_material: Optional[str] = None  # Se None, é um material novo
    nome_item: str
    descricao_customizada: Optional[str] = None
    unidade: str
    preco_compra_fornecedor: float
    percentual_acrescimo: float
    quantidade: float

class OrcamentoMaterial(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    id_orcamento: str
    id_material: Optional[str] = None
    nome_item: str
    descricao_customizada: Optional[str] = None
    unidade: str
    preco_compra_fornecedor: float
    percentual_acrescimo: float
    preco_unitario_final: float
    quantidade: float
    preco_total_item: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========== STARTUP: CRIAR PRIMEIRO ADMIN ==========

@app.on_event("startup")
async def create_first_admin():
    """Criar primeiro admin automaticamente se não existir"""
    try:
        admin_email = "admin@lucroliquido.com"
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if not existing_admin:
            admin = User(
                name="Administrador",
                email=admin_email,
                password="admin123",
                role="admin"
            )
            doc = admin.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.users.insert_one(doc)
            logger.info("✅ Primeiro admin criado com sucesso!")
        else:
            logger.info("✅ Admin já existe no sistema")
    except Exception as e:
        logger.error(f"⚠️ Erro ao criar admin: {e}")
        # Não falha o startup se não conseguir criar admin
        # Pode ser um problema temporário de conexão com MongoDB

# ========== ROTAS DE AUTENTICAÇÃO ==========

@api_router.get("/")
async def api_root():
    """Root endpoint for API - useful for health checks"""
    return {"status": "ok", "message": "API funcionando!", "version": "1.0"}

@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Verificar se email já existe
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Criar usuário
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role="user"
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Criar trial de 7 dias automaticamente
    trial_start = datetime.now(timezone.utc)
    trial_end = trial_start + timedelta(days=7)
    
    subscription = Subscription(
        user_id=user.id,
        status="trial",
        trial_start=trial_start,
        trial_end=trial_end
    )
    
    sub_doc = subscription.model_dump()
    sub_doc['trial_start'] = sub_doc['trial_start'].isoformat()
    sub_doc['trial_end'] = sub_doc['trial_end'].isoformat()
    sub_doc['created_at'] = sub_doc['created_at'].isoformat()
    await db.subscriptions.insert_one(sub_doc)
    
    return {
        "message": "Usuário registrado com sucesso!",
        "user_id": user.id,
        "name": user.name,
        "role": user.role,
        "trial_days": 7
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or user['password'] != credentials.password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    return {
        "user_id": user['id'],
        "name": user['name'],
        "email": user['email'],
        "role": user['role']
    }

# ========== ROTAS DE EMPRESAS ==========

@api_router.post("/companies")
async def create_company(company_data: CompanyCreate):
    company = Company(
        user_id=company_data.user_id,
        name=company_data.name,
        segment=company_data.segment
    )
    
    doc = company.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.companies.insert_one(doc)
    
    return {"message": "Empresa criada com sucesso!", "company_id": company.id}

@api_router.get("/companies/{user_id}")
async def get_companies(user_id: str):
    # Adicionar projeção para buscar apenas campos necessários e limitar a 50
    companies = await db.companies.find(
        {"user_id": user_id}, 
        {"_id": 0, "id": 1, "name": 1, "segment": 1, "created_at": 1}
    ).to_list(50)
    return companies

@api_router.get("/company/{company_id}")
async def get_company_detail(company_id: str):
    """Buscar detalhes completos da empresa"""
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    return company

@api_router.put("/company/{company_id}")
async def update_company(company_id: str, company_data: CompanyCreate):
    """Atualizar dados da empresa"""
    update_doc = company_data.model_dump()
    update_doc['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.companies.update_one(
        {"id": company_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    return {"message": "Empresa atualizada com sucesso!"}

# ========== ROTAS DE LANÇAMENTOS ==========

@api_router.post("/transactions")
async def create_transaction(transaction_data: TransactionCreate):
    transaction = Transaction(**transaction_data.model_dump())
    
    doc = transaction.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.transactions.insert_one(doc)
    
    return {"message": "Lançamento criado com sucesso!", "transaction_id": transaction.id}

@api_router.get("/transactions/{company_id}")
async def get_transactions(company_id: str, month: Optional[str] = None):
    query = {"company_id": company_id}
    
    if month:
        query["date"] = {"$regex": f"^{month}"}
    
    # Limitar a 500 transações e ordenar por data decrescente
    transactions = await db.transactions.find(
        query, 
        {"_id": 0}
    ).sort("date", -1).limit(500).to_list(None)
    return transactions

@api_router.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, transaction_data: TransactionCreate):
    update_doc = transaction_data.model_dump()
    
    result = await db.transactions.update_one(
        {"id": transaction_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    
    return {"message": "Lançamento atualizado com sucesso!"}

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    result = await db.transactions.delete_one({"id": transaction_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    
    return {"message": "Lançamento excluído com sucesso!"}

# ========== ROTAS DE MÉTRICAS ==========

@api_router.get("/metrics/{company_id}/{month}")
async def get_metrics(company_id: str, month: str):
    # Usar aggregation para calcular no banco ao invés de em Python
    # Excluir lançamentos cancelados
    pipeline = [
        {"$match": {
            "company_id": company_id,
            "date": {"$regex": f"^{month}"},
            "status": "realizado",
            "cancelled": {"$ne": True}  # Excluir cancelados
        }},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"}
        }}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(None)
    
    metrics = {"faturamento": 0, "custos": 0, "despesas": 0, "lucro_liquido": 0}
    
    for result in results:
        if result['_id'] == 'receita':
            metrics['faturamento'] = result['total']
        elif result['_id'] == 'custo':
            metrics['custos'] = result['total']
        elif result['_id'] == 'despesa':
            metrics['despesas'] = result['total']
    
    metrics['lucro_liquido'] = metrics['faturamento'] - metrics['custos'] - metrics['despesas']
    
    return metrics

# ========== ROTAS DE META MENSAL ==========

@api_router.post("/monthly-goal")
async def create_monthly_goal(goal_data: MonthlyGoalCreate):
    # Verificar se já existe meta para o mês
    existing = await db.monthly_goals.find_one({
        "company_id": goal_data.company_id,
        "month": goal_data.month
    })
    
    if existing:
        # Atualizar
        await db.monthly_goals.update_one(
            {"id": existing['id']},
            {"$set": {"goal_amount": goal_data.goal_amount}}
        )
        return {"message": "Meta atualizada com sucesso!"}
    
    # Criar nova
    goal = MonthlyGoal(**goal_data.model_dump())
    doc = goal.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.monthly_goals.insert_one(doc)
    
    return {"message": "Meta criada com sucesso!", "goal_id": goal.id}

@api_router.get("/monthly-goal/{company_id}/{month}")
async def get_monthly_goal(company_id: str, month: str):
    goal = await db.monthly_goals.find_one({
        "company_id": company_id,
        "month": month
    }, {"_id": 0})
    
    if not goal:
        return {"goal_amount": 0}
    
    return goal

# ========== ROTAS DE CATEGORIAS ==========

# Categorias padrão do sistema organizadas por tipo
CATEGORIAS_PADRAO = {
    "receita": [
        "Vendas de produtos",
        "Vendas de serviços",
        "Mensalidades / Assinaturas",
        "Honorários / Consultoria",
        "Comissões recebidas",
        "Receitas recorrentes (planos, contratos)",
        "Receitas eventuais (jobs pontuais, extras)",
        "Receitas financeiras (juros, rendimentos)",
        "Descontos obtidos",
        "Outras receitas operacionais"
    ],
    "custo": [
        "Matéria-prima",
        "Embalagens",
        "Frete de compras",
        "Frete de vendas / entrega",
        "Mão de obra direta (produção/serviço)",
        "Insumos de produção (peças, químicos, materiais)",
        "Terceirização de produção / serviços",
        "Energia elétrica da produção",
        "Impostos sobre vendas",
        "Comissões sobre vendas",
        "Taxas de plataformas de venda (marketplaces, apps etc.)",
        "Outros custos operacionais diretos"
    ],
    "despesa": [
        # Administrativas / estruturais
        "Aluguel e condomínio",
        "Água, luz, telefone e internet",
        "Salários administrativos",
        "Encargos trabalhistas (INSS, FGTS, benefícios)",
        "Contabilidade e assessoria",
        "Licenças, alvarás e taxas",
        "Seguros (empresa, veículos, responsabilidade civil)",
        "Material de escritório e limpeza",
        # Comerciais / marketing
        "Marketing e anúncios (Google, Meta, etc.)",
        "Materiais promocionais e brindes",
        "Viagens e representação comercial",
        "Comissões de representantes",
        # Tecnologia / operação
        "Softwares e sistemas (SaaS em geral)",
        "Hospedagem de site / e-mail",
        "Manutenção de máquinas, equipamentos e TI",
        "Manutenção de veículos",
        # Financeiras / tributos
        "Tarifas bancárias",
        "Juros bancários",
        "Taxas de cartão de crédito/débito",
        "Multas e encargos",
        "Tributos fixos (Simples, ISS, ICMS fixo etc.)",
        # Coringa
        "Outras despesas operacionais"
    ]
}

@api_router.get("/categories")
async def get_categories(company_id: Optional[str] = None):
    """
    Retorna categorias padrão + personalizadas (se company_id fornecido)
    Organizado por tipo: receita, custo, despesa
    """
    categories = {
        "receita": CATEGORIAS_PADRAO["receita"].copy(),
        "custo": CATEGORIAS_PADRAO["custo"].copy(),
        "despesa": CATEGORIAS_PADRAO["despesa"].copy()
    }
    
    # Buscar categorias personalizadas da empresa
    if company_id:
        custom_cats = await db.custom_categories.find(
            {"company_id": company_id},
            {"_id": 0}
        ).to_list(None)
        
        for cat in custom_cats:
            tipo = cat['tipo']
            if tipo in categories:
                categories[tipo].append(cat['nome'])
    
    return categories

# ========== ROTAS DE CATEGORIAS PERSONALIZADAS ==========

@api_router.get("/custom-categories/{company_id}")
async def get_custom_categories(company_id: str):
    """Listar todas as categorias personalizadas de uma empresa"""
    categories = await db.custom_categories.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("nome", 1).to_list(None)
    return categories

@api_router.post("/custom-categories")
async def create_custom_category(category_data: CustomCategoryCreate):
    """Criar nova categoria personalizada"""
    # Validar tipo
    if category_data.tipo not in ["receita", "custo", "despesa"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser: receita, custo ou despesa")
    
    # Verificar se já existe categoria com mesmo nome e tipo para essa empresa
    existing = await db.custom_categories.find_one({
        "company_id": category_data.company_id,
        "tipo": category_data.tipo,
        "nome": category_data.nome
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Categoria já existe para este tipo")
    
    category = CustomCategory(**category_data.model_dump())
    doc = category.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.custom_categories.insert_one(doc)
    
    return {"message": "Categoria criada com sucesso!", "category_id": category.id}

@api_router.put("/custom-categories/{category_id}")
async def update_custom_category(category_id: str, category_data: CustomCategoryCreate):
    """Atualizar categoria personalizada"""
    # Validar tipo
    if category_data.tipo not in ["receita", "custo", "despesa"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser: receita, custo ou despesa")
    
    result = await db.custom_categories.update_one(
        {"id": category_id},
        {"$set": {
            "tipo": category_data.tipo,
            "nome": category_data.nome
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    return {"message": "Categoria atualizada com sucesso!"}

@api_router.delete("/custom-categories/{category_id}")
async def delete_custom_category(category_id: str):
    """Deletar categoria personalizada"""
    result = await db.custom_categories.delete_one({"id": category_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    return {"message": "Categoria excluída com sucesso!"}

# ========== ROTAS DE ORÇAMENTOS ==========

async def gerar_numero_orcamento(empresa_id: str):
    """Gerar número sequencial de orçamento (formato: LL-YYYY-NNNN)"""
    ano_atual = datetime.now().year
    
    # Buscar último orçamento do ano
    ultimo_orcamento = await db.orcamentos.find_one(
        {
            "empresa_id": empresa_id,
            "numero_orcamento": {"$regex": f"^LL-{ano_atual}-"}
        },
        sort=[("created_at", -1)]
    )
    
    if ultimo_orcamento:
        # Extrair número do último orçamento
        try:
            ultimo_numero = int(ultimo_orcamento['numero_orcamento'].split('-')[-1])
            proximo_numero = ultimo_numero + 1
        except:
            proximo_numero = 1
    else:
        proximo_numero = 1
    
    return f"LL-{ano_atual}-{proximo_numero:04d}"

@api_router.post("/orcamentos")
async def create_orcamento(orcamento_data: OrcamentoCreate):
    """Criar novo orçamento"""
    # Gerar número do orçamento
    numero_orcamento = await gerar_numero_orcamento(orcamento_data.empresa_id)
    
    orcamento = Orcamento(
        numero_orcamento=numero_orcamento,
        **orcamento_data.model_dump()
    )
    
    doc = orcamento.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.orcamentos.insert_one(doc)
    
    return {"message": "Orçamento criado com sucesso!", "orcamento_id": orcamento.id, "numero_orcamento": numero_orcamento}

@api_router.get("/orcamentos/{empresa_id}")
async def get_orcamentos(
    empresa_id: str,
    status: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    cliente: Optional[str] = None
):
    """Listar orçamentos com filtros"""
    query = {"empresa_id": empresa_id}
    
    if status:
        query["status"] = status
    if cliente:
        query["cliente_nome"] = {"$regex": cliente, "$options": "i"}
    if data_inicio and data_fim:
        query["created_at"] = {
            "$gte": data_inicio,
            "$lte": data_fim
        }
    
    orcamentos = await db.orcamentos.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(None)
    return orcamentos

@api_router.get("/orcamento/{orcamento_id}")
async def get_orcamento_detail(orcamento_id: str):
    """Buscar detalhes de um orçamento específico"""
    orcamento = await db.orcamentos.find_one({"id": orcamento_id}, {"_id": 0})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    return orcamento

@api_router.put("/orcamento/{orcamento_id}")
async def update_orcamento(orcamento_id: str, orcamento_data: OrcamentoCreate):
    """Atualizar orçamento"""
    update_doc = orcamento_data.model_dump()
    update_doc['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.orcamentos.update_one(
        {"id": orcamento_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    return {"message": "Orçamento atualizado com sucesso!"}

@api_router.delete("/orcamento/{orcamento_id}")
async def delete_orcamento(orcamento_id: str):
    """Deletar orçamento"""
    result = await db.orcamentos.delete_one({"id": orcamento_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    return {"message": "Orçamento excluído com sucesso!"}

@api_router.patch("/orcamento/{orcamento_id}/status")
async def update_orcamento_status(orcamento_id: str, status_data: OrcamentoStatusUpdate):
    """Atualizar status do orçamento"""
    orcamento = await db.orcamentos.find_one({"id": orcamento_id})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    update_fields = {
        "status": status_data.status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Atualizar datas específicas baseado no status
    if status_data.status == "ENVIADO":
        update_fields['enviado_em'] = datetime.now(timezone.utc).isoformat()
        if status_data.canal_envio:
            update_fields['canal_envio'] = status_data.canal_envio
    elif status_data.status == "APROVADO":
        update_fields['aprovado_em'] = datetime.now(timezone.utc).isoformat()
    elif status_data.status == "NAO_APROVADO":
        update_fields['nao_aprovado_em'] = datetime.now(timezone.utc).isoformat()
    
    await db.orcamentos.update_one({"id": orcamento_id}, {"$set": update_fields})
    
    return {"message": f"Status atualizado para {status_data.status}!"}

def generate_pdf_with_reportlab(orcamento: dict, empresa: dict, materiais: list = None) -> bytes:
    """Fallback: Gerar PDF usando ReportLab (sem dependências do sistema)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.colors import HexColor
    from datetime import datetime as dt
    
    if materiais is None:
        materiais = []
    
    buffer = BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Cores
    primary_color = HexColor('#7C3AED')
    text_color = HexColor('#444444')
    
    # Header com gradiente (simulado com retângulo)
    c.setFillColor(primary_color)
    c.rect(0, height - 80*mm, width, 80*mm, fill=True, stroke=False)
    
    # Logo/Nome da Empresa
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(20*mm, height - 30*mm, empresa.get('razao_social') or empresa.get('name', 'EMPRESA'))
    
    # Título ORÇAMENTO
    c.setFont("Helvetica-Bold", 28)
    c.drawRightString(width - 20*mm, height - 30*mm, "ORÇAMENTO")
    
    # Número do orçamento
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 20*mm, height - 40*mm, f"Nº {orcamento.get('numero_orcamento', 'N/A')}")
    
    # Data
    data_emissao = orcamento.get('created_at', '')
    if isinstance(data_emissao, str) and len(data_emissao) >= 10:
        try:
            data_emissao = dt.fromisoformat(data_emissao.replace('Z', '+00:00'))
            data_emissao = data_emissao.strftime("%d/%m/%Y")
        except:
            data_emissao = data_emissao[:10]
    c.drawRightString(width - 20*mm, height - 50*mm, f"Data: {data_emissao}")
    
    # Status
    status = orcamento.get('status', 'RASCUNHO')
    status_map = {'RASCUNHO': 'Rascunho', 'ENVIADO': 'Enviado', 'APROVADO': 'Aprovado', 'NAO_APROVADO': 'Não Aprovado'}
    c.drawRightString(width - 20*mm, height - 60*mm, status_map.get(status, status))
    
    # Dados do Cliente
    y = height - 100*mm
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "DADOS DO CLIENTE")
    y -= 10*mm
    
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Nome: {orcamento.get('cliente_nome', '')}")
    y -= 5*mm
    if orcamento.get('cliente_documento'):
        c.drawString(20*mm, y, f"CPF/CNPJ: {orcamento.get('cliente_documento')}")
        y -= 5*mm
    if orcamento.get('cliente_whatsapp'):
        c.drawString(20*mm, y, f"WhatsApp: {orcamento.get('cliente_whatsapp')}")
        y -= 5*mm
    if orcamento.get('cliente_email'):
        c.drawString(20*mm, y, f"E-mail: {orcamento.get('cliente_email')}")
        y -= 5*mm
    
    # Descrição do Serviço
    y -= 10*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "DESCRIÇÃO DO SERVIÇO")
    y -= 10*mm
    
    c.setFont("Helvetica", 10)
    descricao = orcamento.get('descricao_servico_ou_produto', '')
    # Quebrar texto longo em múltiplas linhas
    max_width = width - 40*mm
    words = descricao.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if c.stringWidth(test_line, "Helvetica", 10) < max_width:
            line = test_line
        else:
            c.drawString(20*mm, y, line)
            y -= 5*mm
            line = word + " "
    if line:
        c.drawString(20*mm, y, line)
        y -= 5*mm
    
    # Materiais (se houver)
    if materiais and len(materiais) > 0:
        y -= 10*mm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20*mm, y, "MATERIAIS UTILIZADOS")
        y -= 10*mm
        
        # Cabeçalho da tabela
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, y, "Item")
        c.drawString(70*mm, y, "Unid.")
        c.drawString(90*mm, y, "Qtd.")
        c.drawString(110*mm, y, "Preço Unit.")
        c.drawString(140*mm, y, "Total")
        y -= 5*mm
        
        # Linha separadora
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.line(20*mm, y, width - 20*mm, y)
        y -= 5*mm
        
        # Listar materiais
        c.setFont("Helvetica", 9)
        total_materiais = 0
        for material in materiais:
            # Verificar se precisa de nova página
            if y < 50*mm:
                c.showPage()
                y = height - 30*mm
                c.setFont("Helvetica", 9)
            
            # Item (com quebra de linha se necessário)
            nome_item = material.get('nome_item', '')
            if len(nome_item) > 30:
                nome_item = nome_item[:27] + "..."
            c.drawString(20*mm, y, nome_item)
            
            # Unidade
            c.drawString(70*mm, y, material.get('unidade', ''))
            
            # Quantidade
            c.drawString(90*mm, y, f"{material.get('quantidade', 0):.2f}")
            
            # Preço unitário final (formatado)
            preco_unit = material.get('preco_unitario_final', 0)
            preco_unit_fmt = f"R$ {preco_unit:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            c.drawString(110*mm, y, preco_unit_fmt)
            
            # Total do item (formatado)
            total_item = material.get('preco_total_item', 0)
            total_item_fmt = f"R$ {total_item:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            c.drawString(140*mm, y, total_item_fmt)
            
            total_materiais += total_item
            y -= 5*mm
        
        # Linha separadora
        y -= 2*mm
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.line(20*mm, y, width - 20*mm, y)
        y -= 5*mm
        
        # Total de materiais
        c.setFont("Helvetica-Bold", 10)
        total_mat_fmt = f"R$ {total_materiais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        c.drawString(110*mm, y, "TOTAL MATERIAIS:")
        c.drawString(140*mm, y, total_mat_fmt)
        y -= 5*mm
    
    # Valores
    y -= 10*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "VALORES")
    y -= 10*mm
    
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Custo Total: R$ {orcamento.get('custo_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 5*mm
    c.drawString(20*mm, y, f"Preço Mínimo: R$ {orcamento.get('preco_minimo', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 5*mm
    
    # Valor da Proposta em destaque
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, f"VALOR DA PROPOSTA: R$ {orcamento.get('preco_praticado', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 10*mm
    
    # Condições Comerciais
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "CONDIÇÕES COMERCIAIS")
    y -= 10*mm
    
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Validade: {orcamento.get('validade_proposta', '')}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Prazo: {orcamento.get('prazo_execucao', '')}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Pagamento: {orcamento.get('condicoes_pagamento', '')}")
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width/2, 20*mm, f"Gerado automaticamente pelo sistema Lucro Líquido em {dt.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()

@api_router.get("/orcamento/{orcamento_id}/pdf")
async def generate_orcamento_pdf(orcamento_id: str):
    """Gerar PDF do orçamento - usa WeasyPrint se disponível, senão usa ReportLab"""
    from datetime import datetime as dt
    
    # Buscar orçamento
    orcamento = await db.orcamentos.find_one({"id": orcamento_id}, {"_id": 0})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Buscar dados da empresa
    empresa = await db.companies.find_one({"id": orcamento['empresa_id']}, {"_id": 0})
    
    if not empresa:
        empresa = {"name": "Empresa"}
    
    # Buscar materiais do orçamento
    materiais = await db.orcamento_materiais.find(
        {"id_orcamento": orcamento_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Tentar usar WeasyPrint primeiro (template profissional)
    try:
        from weasyprint import HTML
        from jinja2 import Environment, FileSystemLoader
        import os
        
        # Preparar dados para o template
        data_emissao = orcamento.get('created_at', '')
        if isinstance(data_emissao, str) and len(data_emissao) >= 10:
            try:
                data_emissao = dt.fromisoformat(data_emissao.replace('Z', '+00:00'))
                data_emissao = data_emissao.strftime("%d/%m/%Y")
            except:
                data_emissao = data_emissao[:10]
        
        data_geracao = dt.now().strftime("%d/%m/%Y %H:%M")
        
        # Formatar status
        status = orcamento.get('status', 'RASCUNHO')
        status_label_map = {
            'RASCUNHO': 'Rascunho',
            'ENVIADO': 'Enviado',
            'APROVADO': 'Aprovado',
            'NAO_APROVADO': 'Não Aprovado'
        }
        status_label = status_label_map.get(status, status)
        
        context = {
            'numero_orcamento': orcamento.get('numero_orcamento', 'N/A'),
            'data_emissao': data_emissao,
            'data_geracao': data_geracao,
            'status': status_label,
            'empresa': empresa,
            'cliente_nome': orcamento.get('cliente_nome', ''),
            'cliente_documento': orcamento.get('cliente_documento'),
            'cliente_whatsapp': orcamento.get('cliente_whatsapp'),
            'cliente_telefone': orcamento.get('cliente_telefone'),
            'cliente_email': orcamento.get('cliente_email'),
            'cliente_endereco': orcamento.get('cliente_endereco'),
            'tipo': orcamento.get('tipo', ''),
            'descricao_servico_ou_produto': orcamento.get('descricao_servico_ou_produto', ''),
            'area_m2': orcamento.get('area_m2'),
            'quantidade': orcamento.get('quantidade'),
            'custo_total': orcamento.get('custo_total', 0),
            'preco_minimo': orcamento.get('preco_minimo', 0),
            'preco_sugerido': orcamento.get('preco_sugerido', 0),
            'preco_praticado': orcamento.get('preco_praticado', 0),
            'validade_proposta': orcamento.get('validade_proposta', ''),
            'condicoes_pagamento': orcamento.get('condicoes_pagamento', ''),
            'prazo_execucao': orcamento.get('prazo_execucao', ''),
            'observacoes': orcamento.get('observacoes'),
        }
        
        # Carregar template
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('orcamento.html')
        
        # Renderizar HTML
        html_content = template.render(**context)
        
        # Converter para PDF
        pdf_file = HTML(string=html_content).write_pdf()
        
        return StreamingResponse(
            BytesIO(pdf_file),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=orcamento_{orcamento.get('numero_orcamento', orcamento_id)}.pdf"}
        )
        
    except (OSError, ImportError) as e:
        # Fallback: usar ReportLab se WeasyPrint não estiver disponível
        logger.warning(f"WeasyPrint não disponível, usando ReportLab como fallback: {str(e)}")
        pdf_bytes = generate_pdf_with_reportlab(orcamento, empresa, materiais)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=orcamento_{orcamento.get('numero_orcamento', orcamento_id)}.pdf"}
        )

# ========== ANÁLISE IA (CHATGPT) ==========

@api_router.post("/orcamento/{orcamento_id}/whatsapp")
async def enviar_orcamento_whatsapp(orcamento_id: str):
    """
    Prepara o orçamento para envio via WhatsApp
    Retorna uma URL pública temporária do PDF
    """
    import secrets
    import time
    
    # Buscar orçamento
    orcamento = await db.orcamentos.find_one({"id": orcamento_id}, {"_id": 0})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Gerar token único para este PDF
    token = secrets.token_urlsafe(32)
    expiration = int(time.time()) + (24 * 3600)  # Expira em 24 horas
    
    # Salvar token no banco
    await db.orcamentos.update_one(
        {"id": orcamento_id},
        {"$set": {
            "pdf_share_token": token,
            "pdf_share_expiration": expiration
        }}
    )
    
    # Retornar URL pública
    # Em produção, use a URL da aplicação
    base_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001/api')
    pdf_url = f"{base_url}/orcamento/share/{token}"
    
    # Preparar dados para WhatsApp
    import re
    from urllib.parse import quote
    
    whatsapp_number = re.sub(r'\D', '', orcamento.get('cliente_whatsapp', ''))
    
    # Formatar valor monetário
    valor_formatado = f"R$ {float(orcamento.get('preco_praticado', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    mensagem = f"""Olá {orcamento.get('cliente_nome')}!

Segue o orçamento {orcamento.get('numero_orcamento')} para sua análise.

*{orcamento.get('descricao_servico_ou_produto')}*

💰 Valor: {valor_formatado}

Validade: {orcamento.get('validade_proposta')}
Prazo: {orcamento.get('prazo_execucao')}

📄 Ver orçamento completo (PDF): {pdf_url}

Qualquer dúvida, estou à disposição!"""
    
    return {
        "pdf_url": pdf_url,
        "whatsapp_url": f"https://wa.me/55{whatsapp_number}?text={quote(mensagem)}",
        "token": token,
        "expires_in": "24 horas"
    }

@api_router.get("/orcamento/share/{token}")
async def share_orcamento_pdf(token: str):
    """Endpoint público para compartilhar PDF via token temporário"""
    import time
    
    # Buscar orçamento pelo token
    orcamento = await db.orcamentos.find_one({
        "pdf_share_token": token
    }, {"_id": 0})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Link inválido ou expirado")
    
    # Verificar se o token ainda é válido
    expiration = orcamento.get('pdf_share_expiration', 0)
    if int(time.time()) > expiration:
        raise HTTPException(status_code=410, detail="Link expirado. Solicite um novo ao vendedor.")
    
    # Buscar empresa
    empresa = await db.companies.find_one({"id": orcamento['empresa_id']}, {"_id": 0})
    if not empresa:
        empresa = {"name": "Empresa"}
    
    # Buscar materiais do orçamento
    materiais = await db.orcamento_materiais.find(
        {"id_orcamento": orcamento['id']},
        {"_id": 0}
    ).to_list(1000)
    
    # Gerar PDF
    try:
        from weasyprint import HTML
        from jinja2 import Environment, FileSystemLoader
        import os
        from datetime import datetime as dt
        
        # Preparar dados para o template
        data_emissao = orcamento.get('created_at', '')
        if isinstance(data_emissao, str) and len(data_emissao) >= 10:
            try:
                data_emissao = dt.fromisoformat(data_emissao.replace('Z', '+00:00'))
                data_emissao = data_emissao.strftime("%d/%m/%Y")
            except:
                data_emissao = data_emissao[:10]
        
        data_geracao = dt.now().strftime("%d/%m/%Y %H:%M")
        
        status = orcamento.get('status', 'RASCUNHO')
        status_label_map = {
            'RASCUNHO': 'Rascunho',
            'ENVIADO': 'Enviado',
            'APROVADO': 'Aprovado',
            'NAO_APROVADO': 'Não Aprovado'
        }
        status_label = status_label_map.get(status, status)
        
        context = {
            'numero_orcamento': orcamento.get('numero_orcamento', 'N/A'),
            'data_emissao': data_emissao,
            'data_geracao': data_geracao,
            'status': status_label,
            'empresa': empresa,
            'cliente_nome': orcamento.get('cliente_nome', ''),
            'cliente_documento': orcamento.get('cliente_documento'),
            'cliente_whatsapp': orcamento.get('cliente_whatsapp'),
            'cliente_telefone': orcamento.get('cliente_telefone'),
            'cliente_email': orcamento.get('cliente_email'),
            'cliente_endereco': orcamento.get('cliente_endereco'),
            'tipo': orcamento.get('tipo', ''),
            'descricao_servico_ou_produto': orcamento.get('descricao_servico_ou_produto', ''),
            'area_m2': orcamento.get('area_m2'),
            'quantidade': orcamento.get('quantidade'),
            'custo_total': orcamento.get('custo_total', 0),
            'preco_minimo': orcamento.get('preco_minimo', 0),
            'preco_sugerido': orcamento.get('preco_sugerido', 0),
            'preco_praticado': orcamento.get('preco_praticado', 0),
            'validade_proposta': orcamento.get('validade_proposta', ''),
            'condicoes_pagamento': orcamento.get('condicoes_pagamento', ''),
            'prazo_execucao': orcamento.get('prazo_execucao', ''),
            'observacoes': orcamento.get('observacoes'),
        }
        
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('orcamento.html')
        html_content = template.render(**context)
        pdf_file = HTML(string=html_content).write_pdf()
        
        return StreamingResponse(
            BytesIO(pdf_file),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=orcamento_{orcamento.get('numero_orcamento', token)}.pdf",
                "Cache-Control": "no-cache"
            }
        )
        
    except (OSError, ImportError) as e:
        # Fallback: usar ReportLab
        logger.warning(f"WeasyPrint não disponível, usando ReportLab: {str(e)}")
        pdf_bytes = generate_pdf_with_reportlab(orcamento, empresa)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=orcamento_{orcamento.get('numero_orcamento', token)}.pdf",
                "Cache-Control": "no-cache"
            }
        )

# ========== ENDPOINTS: MATERIAIS ==========

@api_router.post("/materiais")
async def create_material(material_data: MaterialCreate):
    """Criar novo material no catálogo"""
    material = Material(**material_data.model_dump())
    
    doc = material.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.materiais.insert_one(doc)
    
    return {"message": "Material criado com sucesso!", "material_id": material.id}

@api_router.get("/materiais")
async def get_materiais():
    """Listar todos os materiais cadastrados"""
    materiais = await db.materiais.find({}, {"_id": 0}).sort("nome_item", 1).to_list(1000)
    return materiais

@api_router.get("/materiais/buscar")
async def buscar_materiais(q: str):
    """Buscar materiais por nome (autocomplete)"""
    materiais = await db.materiais.find(
        {"nome_item": {"$regex": q, "$options": "i"}},
        {"_id": 0}
    ).limit(20).to_list(None)
    return materiais

@api_router.get("/materiais/{material_id}")
async def get_material_detail(material_id: str):
    """Buscar detalhes de um material específico"""
    material = await db.materiais.find_one({"id": material_id}, {"_id": 0})
    
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    return material

@api_router.put("/materiais/{material_id}")
async def update_material(material_id: str, material_data: MaterialCreate):
    """Atualizar material"""
    update_doc = material_data.model_dump()
    update_doc['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.materiais.update_one(
        {"id": material_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    return {"message": "Material atualizado com sucesso!"}

@api_router.delete("/materiais/{material_id}")
async def delete_material(material_id: str):
    """Deletar material do catálogo"""
    result = await db.materiais.delete_one({"id": material_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    return {"message": "Material excluído com sucesso!"}

# ========== ENDPOINTS: MATERIAIS NO ORÇAMENTO ==========

@api_router.post("/orcamentos/{orcamento_id}/materiais")
async def add_material_to_orcamento(orcamento_id: str, material_data: OrcamentoMaterialCreate):
    """Adicionar material ao orçamento"""
    # Verificar se o orçamento existe
    orcamento = await db.orcamentos.find_one({"id": orcamento_id}, {"_id": 0})
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    # Calcular valores
    preco_unitario_final = material_data.preco_compra_fornecedor * (1 + (material_data.percentual_acrescimo / 100))
    preco_total_item = preco_unitario_final * material_data.quantidade
    
    # Criar OrcamentoMaterial
    orcamento_material = OrcamentoMaterial(
        id_orcamento=orcamento_id,
        id_material=material_data.id_material,
        nome_item=material_data.nome_item,
        descricao_customizada=material_data.descricao_customizada,
        unidade=material_data.unidade,
        preco_compra_fornecedor=material_data.preco_compra_fornecedor,
        percentual_acrescimo=material_data.percentual_acrescimo,
        preco_unitario_final=preco_unitario_final,
        quantidade=material_data.quantidade,
        preco_total_item=preco_total_item
    )
    
    doc = orcamento_material.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.orcamento_materiais.insert_one(doc)
    
    # Se id_material não existe (material novo), criar material no catálogo
    if not material_data.id_material:
        novo_material = Material(
            nome_item=material_data.nome_item,
            descricao=material_data.descricao_customizada,
            unidade=material_data.unidade,
            preco_compra_base=material_data.preco_compra_fornecedor
        )
        material_doc = novo_material.model_dump()
        material_doc['created_at'] = material_doc['created_at'].isoformat()
        material_doc['updated_at'] = material_doc['updated_at'].isoformat()
        await db.materiais.insert_one(material_doc)
    
    return {
        "message": "Material adicionado ao orçamento com sucesso!",
        "orcamento_material_id": orcamento_material.id,
        "preco_unitario_final": preco_unitario_final,
        "preco_total_item": preco_total_item
    }

@api_router.get("/orcamentos/{orcamento_id}/materiais")
async def get_orcamento_materiais(orcamento_id: str):
    """Listar materiais de um orçamento"""
    materiais = await db.orcamento_materiais.find(
        {"id_orcamento": orcamento_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Calcular total de materiais
    total_materiais = sum(m['preco_total_item'] for m in materiais)
    
    return {
        "materiais": materiais,
        "total_materiais": total_materiais
    }

@api_router.delete("/orcamentos/{orcamento_id}/materiais/{orcamento_material_id}")
async def remove_material_from_orcamento(orcamento_id: str, orcamento_material_id: str):
    """Remover material do orçamento"""
    result = await db.orcamento_materiais.delete_one({
        "id": orcamento_material_id,
        "id_orcamento": orcamento_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Material não encontrado no orçamento")
    
    return {"message": "Material removido do orçamento com sucesso!"}

@api_router.post("/ai-analysis")
async def ai_analysis(data: dict):
    try:
        company_id = data['company_id']
        month = data['month']
        
        # Usar aggregation para calcular métricas
        pipeline = [
            {"$match": {
                "company_id": company_id,
                "date": {"$regex": f"^{month}"},
                "status": "realizado"
            }},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        results = await db.transactions.aggregate(pipeline).to_list(None)
        
        faturamento = 0
        custos = 0
        despesas = 0
        
        for result in results:
            if result['_id'] == 'receita':
                faturamento = result['total']
            elif result['_id'] == 'custo':
                custos = result['total']
            elif result['_id'] == 'despesa':
                despesas = result['total']
        
        lucro = faturamento - custos - despesas
        
        # Prompt para ChatGPT
        prompt = f"""
        Analise os seguintes dados financeiros de uma empresa no mês {month}:
        
        - Faturamento Total: R$ {faturamento:,.2f}
        - Custos Totais: R$ {custos:,.2f}
        - Despesas Totais: R$ {despesas:,.2f}
        - Lucro Líquido: R$ {lucro:,.2f}
        
        Por favor, forneça:
        1. Pontos de atenção nos números apresentados
        2. Oportunidades de economia
        3. Sugestões para melhorar a gestão financeira
        4. Insights sobre o negócio
        
        Seja objetivo e prático nas recomendações.
        """
        
        # Usar Emergent LLM Chat
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"analysis-{company_id}-{month}",
            system_message="Você é um especialista em análise financeira empresarial."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        analysis = await chat.send_message(user_message)
        
        return {"analysis": analysis}
    
    except Exception as e:
        logger.error(f"Erro na análise IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar: {str(e)}")

# ========== EXPLICAÇÃO DE TERMOS FINANCEIROS ==========

@api_router.post("/financial-term-explanation")
async def explain_financial_term(data: dict):
    """Explicar termo financeiro usando IA"""
    try:
        term = data['term']
        business_sector = data.get('business_sector', None)
        
        if not business_sector:
            # Explicação geral do termo
            prompt = f"""
            Explique de forma clara, objetiva e didática o conceito financeiro: "{term}"
            
            Sua explicação deve:
            - Ser acessível para empresários sem formação financeira
            - Incluir exemplos práticos
            - Ter no máximo 4 parágrafos
            - Usar linguagem simples e direta
            
            Não use jargões técnicos desnecessários.
            """
        else:
            # Explicação personalizada para o setor
            prompt = f"""
            Explique como o conceito financeiro "{term}" se aplica especificamente ao setor de {business_sector}.
            
            Sua explicação deve:
            - Conectar o conceito com a realidade desse setor
            - Dar exemplos práticos do dia a dia desse negócio
            - Explicar a importância desse conceito para esse tipo de empresa
            - Ser em no máximo 4 parágrafos
            - Usar linguagem acessível
            
            Seja específico e prático, ajudando o empresário a entender como aplicar isso no seu negócio.
            """
        
        # Usar Emergent LLM Chat
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"term-explanation-{term}",
            system_message="Você é um consultor financeiro especializado em educação empresarial. Seu objetivo é explicar conceitos financeiros de forma clara e aplicada à realidade das empresas."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        explanation = await chat.send_message(user_message)
        
        return {"explanation": explanation, "term": term}
    
    except Exception as e:
        logger.error(f"Erro ao explicar termo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao explicar: {str(e)}")

# ========== ANÁLISE INTELIGENTE COM IA ==========

@api_router.post("/business-health-score")
async def calculate_business_health_score(data: dict):
    """Calcular Score de Saúde do Negócio (0-100)"""
    try:
        company_id = data['company_id']
        month = data.get('month', datetime.now(timezone.utc).strftime('%Y-%m'))
        
        # Usar aggregation para calcular métricas
        pipeline = [
            {"$match": {
                "company_id": company_id,
                "date": {"$regex": f"^{month}"},
                "status": "realizado"
            }},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        results = await db.transactions.aggregate(pipeline).to_list(None)
        
        faturamento = 0
        custos = 0
        despesas = 0
        
        for result in results:
            if result['_id'] == 'receita':
                faturamento = result['total']
            elif result['_id'] == 'custo':
                custos = result['total']
            elif result['_id'] == 'despesa':
                despesas = result['total']
        
        lucro = faturamento - custos - despesas
        
        # Calcular métricas para o score
        margem_liquida = (lucro / faturamento * 100) if faturamento > 0 else 0
        taxa_custos = (custos / faturamento * 100) if faturamento > 0 else 0
        taxa_despesas = (despesas / faturamento * 100) if faturamento > 0 else 0
        
        # Buscar meta (apenas campos necessários)
        goal = await db.monthly_goals.find_one({
            "company_id": company_id,
            "month": month
        }, {"_id": 0, "goal_amount": 1})
        
        atingimento_meta = 0
        if goal and goal.get('goal_amount', 0) > 0:
            atingimento_meta = min((lucro / goal['goal_amount']) * 100, 100)
        
        # Prompt para IA calcular score e interpretar
        prompt = f"""
        Analise a saúde financeira desta empresa com base nos dados do mês {month}:
        
        - Faturamento: R$ {faturamento:,.2f}
        - Custos: R$ {custos:,.2f} ({taxa_custos:.1f}% do faturamento)
        - Despesas: R$ {despesas:,.2f} ({taxa_despesas:.1f}% do faturamento)
        - Lucro Líquido: R$ {lucro:,.2f}
        - Margem Líquida: {margem_liquida:.1f}%
        - Atingimento de Meta: {atingimento_meta:.1f}%
        
        Com base nisso:
        
        1. Calcule um SCORE DE SAÚDE de 0 a 100 considerando:
           - Lucratividade (peso 30%)
           - Margem líquida (peso 25%)
           - Controle de custos (peso 20%)
           - Controle de despesas (peso 15%)
           - Atingimento de meta (peso 10%)
        
        2. Classifique como: Excelente (85-100), Bom (70-84), Atenção (50-69), Crítico (0-49)
        
        3. Liste os 3 PRINCIPAIS PROBLEMAS detectados
        
        4. Dê 3 AÇÕES RECOMENDADAS práticas e objetivas
        
        Formato da resposta:
        SCORE: [número]
        CLASSIFICAÇÃO: [classificação]
        
        PROBLEMAS:
        1. [problema]
        2. [problema]
        3. [problema]
        
        AÇÕES:
        1. [ação]
        2. [ação]
        3. [ação]
        
        Seja objetivo e prático.
        """
        
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"health-score-{company_id}-{month}",
            system_message="Você é um consultor financeiro especializado em análise de saúde empresarial."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        analysis = await chat.send_message(user_message)
        
        return {
            "score_analysis": analysis,
            "raw_data": {
                "faturamento": faturamento,
                "custos": custos,
                "despesas": despesas,
                "lucro": lucro,
                "margem_liquida": margem_liquida,
                "atingimento_meta": atingimento_meta
            }
        }
    
    except Exception as e:
        logger.error(f"Erro ao calcular score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@api_router.post("/intelligent-alerts")
async def generate_intelligent_alerts(data: dict):
    """Gerar Alertas Inteligentes sobre anomalias"""
    try:
        company_id = data['company_id']
        month = data.get('month', datetime.now(timezone.utc).strftime('%Y-%m'))
        
        # Calcular mês anterior
        date_obj = datetime.strptime(month, '%Y-%m')
        previous_month = (date_obj.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        # Buscar dados de ambos os meses em uma query com aggregation
        pipeline = [
            {"$match": {
                "company_id": company_id,
                "date": {"$regex": f"^({month}|{previous_month})"},
                "status": "realizado"
            }},
            {"$project": {
                "month": {"$substr": ["$date", 0, 7]},
                "type": 1,
                "amount": 1
            }},
            {"$group": {
                "_id": {
                    "month": "$month",
                    "type": "$type"
                },
                "total": {"$sum": "$amount"}
            }}
        ]
        
        results = await db.transactions.aggregate(pipeline).to_list(None)
        
        # Processar resultados da aggregation
        current_metrics = {"receita": 0, "custo": 0, "despesa": 0}
        previous_metrics = {"receita": 0, "custo": 0, "despesa": 0}
        
        for result in results:
            month_type = result['_id']['month']
            transaction_type = result['_id']['type']
            total = result['total']
            
            if month_type == month:
                current_metrics[transaction_type] = total
            elif month_type == previous_month:
                previous_metrics[transaction_type] = total
        
        # Métricas atuais
        faturamento_atual = current_metrics['receita']
        custos_atual = current_metrics['custo']
        despesas_atual = current_metrics['despesa']
        lucro_atual = faturamento_atual - custos_atual - despesas_atual
        
        # Métricas anteriores
        faturamento_anterior = previous_metrics['receita']
        custos_anterior = previous_metrics['custo']
        despesas_anterior = previous_metrics['despesa']
        lucro_anterior = faturamento_anterior - custos_anterior - despesas_anterior
        
        # Buscar top 5 categorias de custos/despesas do mês atual
        category_pipeline = [
            {"$match": {
                "company_id": company_id,
                "date": {"$regex": f"^{month}"},
                "status": "realizado",
                "type": {"$in": ["custo", "despesa"]}
            }},
            {"$group": {
                "_id": "$category",
                "total": {"$sum": "$amount"}
            }},
            {"$sort": {"total": -1}},
            {"$limit": 5}
        ]
        
        top_expenses_result = await db.transactions.aggregate(category_pipeline).to_list(None)
        top_expenses = [(r['_id'], r['total']) for r in top_expenses_result]
        
        # Prompt para IA detectar alertas
        prompt = f"""
        Você é um sistema de detecção de anomalias financeiras.
        
        Analise os dados e gere ALERTAS INTELIGENTES para o empresário:
        
        MÊS ATUAL ({month}):
        - Faturamento: R$ {faturamento_atual:,.2f}
        - Custos: R$ {custos_atual:,.2f}
        - Despesas: R$ {despesas_atual:,.2f}
        - Lucro: R$ {lucro_atual:,.2f}
        
        MÊS ANTERIOR ({previous_month}):
        - Faturamento: R$ {faturamento_anterior:,.2f}
        - Custos: R$ {custos_anterior:,.2f}
        - Despesas: R$ {despesas_anterior:,.2f}
        - Lucro: R$ {lucro_anterior:,.2f}
        
        TOP 5 MAIORES GASTOS ATUAIS:
        {chr(10).join([f"- {cat}: R$ {val:,.2f}" for cat, val in top_expenses])}
        
        Detecte e gere até 5 ALERTAS se houver:
        
        1. Despesas muito acima da média
        2. Aumento significativo de custos
        3. Queda de faturamento
        4. Queda de lucro
        5. Margem perigosa
        6. Dependência excessiva de categorias
        
        Para cada alerta, forneça:
        - TÍTULO curto
        - TIPO: crítico, atenção ou info
        - MOTIVO claro
        - IMPACTO no negócio
        - AÇÃO RECOMENDADA imediata
        
        Formato:
        ALERTA 1:
        Título: [título]
        Tipo: [tipo]
        Motivo: [motivo]
        Impacto: [impacto]
        Ação: [ação]
        
        Se não houver alertas críticos, diga "SEM ALERTAS CRÍTICOS" e dê 2 dicas preventivas.
        
        Seja direto e prático.
        """
        
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"alerts-{company_id}-{month}",
            system_message="Você é um sistema de alerta financeiro inteligente."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        alerts_analysis = await chat.send_message(user_message)
        
        return {"alerts": alerts_analysis}
    
    except Exception as e:
        logger.error(f"Erro ao gerar alertas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@api_router.post("/complete-business-analysis")
async def generate_complete_analysis(data: dict):
    """Gerar Análise Completa do Negócio com IA"""
    try:
        company_id = data['company_id']
        month = data.get('month', datetime.now(timezone.utc).strftime('%Y-%m'))
        business_sector = data.get('business_sector', 'não informado')
        
        # Buscar todos os dados necessários
        transactions = await db.transactions.find({
            "company_id": company_id,
            "date": {"$regex": f"^{month}"},
            "status": "realizado"
        }, {"_id": 0}).to_list(1000)
        
        company = await db.companies.find_one({"id": company_id}, {"_id": 0})
        
        # Calcular métricas
        faturamento = sum([t['amount'] for t in transactions if t['type'] == 'receita'])
        custos = sum([t['amount'] for t in transactions if t['type'] == 'custo'])
        despesas = sum([t['amount'] for t in transactions if t['type'] == 'despesa'])
        lucro = faturamento - custos - despesas
        
        margem_liquida = (lucro / faturamento * 100) if faturamento > 0 else 0
        margem_bruta = ((faturamento - custos) / faturamento * 100) if faturamento > 0 else 0
        
        # Análise por categoria
        category_analysis = {}
        for t in transactions:
            cat = t['category']
            if cat not in category_analysis:
                category_analysis[cat] = {'receita': 0, 'custo': 0, 'despesa': 0}
            category_analysis[cat][t['type']] += t['amount']
        
        # Buscar últimos 6 meses para tendência (query única otimizada)
        months_list = []
        for i in range(6):
            m = (datetime.strptime(month, '%Y-%m').replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m')
            months_list.append(m)
        
        # Usar aggregation para calcular métricas de todos os meses em uma query
        pipeline = [
            {"$match": {
                "company_id": company_id,
                "status": "realizado",
                "date": {"$regex": f"^({'|'.join(months_list)})"}
            }},
            {"$project": {
                "month": {"$substr": ["$date", 0, 7]},
                "type": 1,
                "amount": 1
            }},
            {"$group": {
                "_id": {
                    "month": "$month",
                    "type": "$type"
                },
                "total": {"$sum": "$amount"}
            }},
            {"$group": {
                "_id": "$_id.month",
                "data": {
                    "$push": {
                        "type": "$_id.type",
                        "amount": "$total"
                    }
                }
            }},
            {"$sort": {"_id": -1}}
        ]
        
        months_agg = await db.transactions.aggregate(pipeline).to_list(None)
        
        # Processar resultados
        all_months_data = []
        for month_data in months_agg:
            m = month_data['_id']
            faturamento = sum([d['amount'] for d in month_data['data'] if d['type'] == 'receita'])
            custos_despesas = sum([d['amount'] for d in month_data['data'] if d['type'] in ['custo', 'despesa']])
            lucro = faturamento - custos_despesas
            all_months_data.append({"month": m, "faturamento": faturamento, "lucro": lucro})
        
        # Prompt completo para análise detalhada
        prompt = f"""
        Você é um CONSULTOR FINANCEIRO SÊNIOR analisando a empresa {company.get('name', 'Cliente')} do setor {business_sector}.
        
        Gere uma ANÁLISE FINANCEIRA COMPLETA E PROFUNDA baseada nos dados:
        
        📊 MÉTRICAS DO MÊS {month}:
        - Faturamento: R$ {faturamento:,.2f}
        - Custos: R$ {custos:,.2f}
        - Despesas: R$ {despesas:,.2f}
        - Lucro Líquido: R$ {lucro:,.2f}
        - Margem Bruta: {margem_bruta:.1f}%
        - Margem Líquida: {margem_liquida:.1f}%
        
        📈 TENDÊNCIA (6 MESES):
        {chr(10).join([f"- {m['month']}: Fat R$ {m['faturamento']:,.2f} | Lucro R$ {m['lucro']:,.2f}" for m in all_months_data])}
        
        Sua análise DEVE incluir:
        
        ## 1. DIAGNÓSTICO GERAL
        - Visão geral da saúde financeira
        - Pontos fortes
        - Pontos fracos
        
        ## 2. ANÁLISE DE MARGENS
        - Interpretação das margens
        - Comparação com setor {business_sector}
        - Se está saudável ou perigoso
        
        ## 3. GARGALOS IDENTIFICADOS
        - Principais problemas
        - Impacto no lucro
        - Risco para o negócio
        
        ## 4. TENDÊNCIAS
        - Crescimento ou queda
        - Sazonalidade detectada
        - Padrões importantes
        
        ## 5. PREVISÃO (30/60/90 DIAS)
        - Projeção de faturamento
        - Projeção de lucro
        - Probabilidade de atingir meta
        
        ## 6. RECOMENDAÇÕES ESTRATÉGICAS
        - 5 ações prioritárias
        - Ordem de importância
        - Impacto esperado
        
        ## 7. OPORTUNIDADES
        - Onde pode melhorar
        - Como aumentar lucro
        - Otimizações possíveis
        
        Seja PROFUNDO, ESPECÍFICO para o setor {business_sector} e PRÁTICO.
        Use linguagem clara mas profissional.
        """
        
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"complete-analysis-{company_id}-{month}",
            system_message="Você é um consultor financeiro sênior com 20 anos de experiência. Suas análises são profundas, práticas e adaptadas ao setor do cliente."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=prompt)
        complete_analysis = await chat.send_message(user_message)
        
        return {
            "analysis": complete_analysis,
            "metrics": {
                "faturamento": faturamento,
                "custos": custos,
                "despesas": despesas,
                "lucro": lucro,
                "margem_liquida": margem_liquida,
                "margem_bruta": margem_bruta
            }
        }
    
    except Exception as e:
        logger.error(f"Erro na análise completa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

# ========== ASSINATURA E PAGAMENTO ==========

@api_router.get("/subscription/status/{user_id}")
async def get_subscription_status(user_id: str):
    subscription = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    # Calcular dias restantes do trial
    if subscription['status'] == 'trial':
        trial_end = datetime.fromisoformat(subscription['trial_end'])
        now = datetime.now(timezone.utc)
        days_remaining = (trial_end - now).days
        subscription['days_remaining'] = max(0, days_remaining)
    
    return subscription

@api_router.post("/subscription/create-payment")
async def create_payment(data: dict):
    try:
        # user_id será usado no futuro para tracking
        # user_id = data['user_id']
        
        # Criar preferência de pagamento PIX
        payment_data = {
            "transaction_amount": 49.90,
            "description": "Assinatura Mensal - Lucro Líquido",
            "payment_method_id": "pix",
            "payer": {
                "email": data.get('email', 'usuario@email.com')
            }
        }
        
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]
        
        # Extrair QR Code
        qr_code = payment.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code', '')
        qr_code_base64 = payment.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64', '')
        
        return {
            "payment_id": payment['id'],
            "qr_code": qr_code,
            "qr_code_base64": qr_code_base64,
            "amount": 49.90
        }
    
    except Exception as e:
        logger.error(f"Erro ao criar pagamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar pagamento: {str(e)}")

@api_router.post("/subscription/webhook")
async def webhook(data: dict):
    """Webhook para receber notificações do Mercado Pago"""
    try:
        if data.get('type') == 'payment':
            payment_id = data['data']['id']
            
            # Buscar informações do pagamento
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info['response']
            
            if payment['status'] == 'approved':
                # Atualizar assinatura para ativa
                # Aqui você precisaria identificar o usuário pelo payment_id
                logger.info(f"Pagamento aprovado: {payment_id}")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return {"status": "error"}

# ========== CONTAS A PAGAR E RECEBER ==========

async def create_lancamento_from_conta(conta: dict, tipo_lancamento: str):
    """Criar lançamento financeiro automaticamente quando conta é paga/recebida"""
    transaction = Transaction(
        company_id=conta['company_id'],
        user_id=conta['user_id'],
        type=tipo_lancamento,  # despesa (para PAGAR) ou receita (para RECEBER)
        description=conta['descricao'],
        amount=conta['valor'],
        category=conta['categoria'],
        date=conta['data_pagamento'] or conta['data_vencimento'],
        status="realizado",
        notes=f"Lançamento automático de conta {conta['tipo'].lower()}",
        origem="conta",
        conta_id=conta['id'],
        cancelled=False
    )
    
    doc = transaction.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.transactions.insert_one(doc)
    
    return transaction.id

async def cancel_lancamento_from_conta(conta_id: str):
    """Marcar lançamento como cancelado quando conta volta para PENDENTE"""
    result = await db.transactions.update_one(
        {"conta_id": conta_id},
        {"$set": {"cancelled": True}}
    )
    return result.modified_count > 0

@api_router.get("/contas/categorias")
async def get_categorias_contas():
    """Retorna categorias de contas a pagar e receber"""
    return {
        "pagar": [
            "Aluguel",
            "Folha de Pagamento",
            "Impostos",
            "Fornecedores",
            "Água",
            "Luz",
            "Internet",
            "Telefone",
            "Manutenção",
            "Seguros",
            "Empréstimos",
            "Marketing",
            "Contador",
            "Outros"
        ],
        "receber": [
            "Cliente",
            "Contrato",
            "Plano Mensalidade",
            "Serviço Prestado",
            "Venda Produto",
            "Projeto",
            "Consultoria",
            "Parceria",
            "Outros"
        ]
    }

# ===== CONTAS A PAGAR =====

@api_router.post("/contas/pagar")
async def create_conta_pagar(conta_data: ContaCreate):
    """Criar nova conta a pagar"""
    if conta_data.tipo != "PAGAR":
        raise HTTPException(status_code=400, detail="Tipo deve ser PAGAR")
    
    conta = Conta(**conta_data.model_dump())
    
    # Verificar se está atrasada
    from datetime import datetime as dt
    hoje = dt.now().strftime("%Y-%m-%d")
    if conta.data_vencimento < hoje and conta.status == "PENDENTE":
        conta.status = "ATRASADO"
    
    doc = conta.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.contas.insert_one(doc)
    
    return {"message": "Conta a pagar criada com sucesso!", "conta_id": conta.id}

@api_router.get("/contas/pagar")
async def get_contas_pagar(
    company_id: str,
    status: Optional[str] = None,
    mes: Optional[str] = None,
    categoria: Optional[str] = None
):
    """Listar contas a pagar com filtros"""
    query = {"company_id": company_id, "tipo": "PAGAR"}
    
    if status:
        query["status"] = status
    if mes:
        query["data_vencimento"] = {"$regex": f"^{mes}"}
    if categoria:
        query["categoria"] = categoria
    
    contas = await db.contas.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(500)
    return contas

@api_router.get("/contas/pagar/{conta_id}")
async def get_conta_pagar(conta_id: str):
    """Buscar conta a pagar por ID"""
    conta = await db.contas.find_one({"id": conta_id, "tipo": "PAGAR"}, {"_id": 0})
    
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return conta

@api_router.put("/contas/pagar/{conta_id}")
async def update_conta_pagar(conta_id: str, conta_data: ContaCreate):
    """Atualizar conta a pagar"""
    if conta_data.tipo != "PAGAR":
        raise HTTPException(status_code=400, detail="Tipo deve ser PAGAR")
    
    from datetime import datetime as dt
    update_doc = conta_data.model_dump()
    update_doc['updated_at'] = dt.now(timezone.utc).isoformat()
    
    result = await db.contas.update_one(
        {"id": conta_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return {"message": "Conta atualizada com sucesso!"}

@api_router.delete("/contas/pagar/{conta_id}")
async def delete_conta_pagar(conta_id: str):
    """Deletar conta a pagar"""
    # Verificar se tem lançamento vinculado
    conta = await db.contas.find_one({"id": conta_id})
    if conta and conta.get('lancamento_id'):
        # Cancelar lançamento vinculado
        await cancel_lancamento_from_conta(conta_id)
    
    result = await db.contas.delete_one({"id": conta_id, "tipo": "PAGAR"})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return {"message": "Conta excluída com sucesso!"}

@api_router.patch("/contas/pagar/{conta_id}/status")
async def update_status_conta_pagar(conta_id: str, status_data: ContaStatusUpdate):
    """Atualizar status da conta a pagar"""
    conta = await db.contas.find_one({"id": conta_id, "tipo": "PAGAR"})
    
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    from datetime import datetime as dt
    update_fields = {
        "status": status_data.status,
        "updated_at": dt.now(timezone.utc).isoformat()
    }
    
    # Se marcar como PAGO, criar lançamento automático
    if status_data.status == "PAGO" and not conta.get('lancamento_id'):
        data_pagamento = status_data.data_pagamento or dt.now().strftime("%Y-%m-%d")
        update_fields['data_pagamento'] = data_pagamento
        
        # Atualizar conta primeiro
        await db.contas.update_one({"id": conta_id}, {"$set": update_fields})
        
        # Criar lançamento de despesa
        conta_atualizada = await db.contas.find_one({"id": conta_id})
        lancamento_id = await create_lancamento_from_conta(conta_atualizada, "despesa")
        
        # Vincular lançamento à conta
        await db.contas.update_one(
            {"id": conta_id},
            {"$set": {"lancamento_id": lancamento_id}}
        )
        
        return {"message": "Conta marcada como PAGA e lançamento criado!", "lancamento_id": lancamento_id}
    
    # Se voltar para PENDENTE, cancelar lançamento
    elif status_data.status == "PENDENTE" and conta.get('lancamento_id'):
        await cancel_lancamento_from_conta(conta_id)
        update_fields['data_pagamento'] = None
        update_fields['lancamento_id'] = None
    
    await db.contas.update_one({"id": conta_id}, {"$set": update_fields})
    
    return {"message": "Status atualizado com sucesso!"}

# ===== CONTAS A RECEBER =====

@api_router.post("/contas/receber")
async def create_conta_receber(conta_data: ContaCreate):
    """Criar nova conta a receber"""
    if conta_data.tipo != "RECEBER":
        raise HTTPException(status_code=400, detail="Tipo deve ser RECEBER")
    
    conta = Conta(**conta_data.model_dump())
    
    # Verificar se está atrasada
    from datetime import datetime as dt
    hoje = dt.now().strftime("%Y-%m-%d")
    if conta.data_vencimento < hoje and conta.status == "PENDENTE":
        conta.status = "ATRASADO"
    
    doc = conta.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.contas.insert_one(doc)
    
    return {"message": "Conta a receber criada com sucesso!", "conta_id": conta.id}

@api_router.get("/contas/receber")
async def get_contas_receber(
    company_id: str,
    status: Optional[str] = None,
    mes: Optional[str] = None,
    categoria: Optional[str] = None
):
    """Listar contas a receber com filtros"""
    query = {"company_id": company_id, "tipo": "RECEBER"}
    
    if status:
        query["status"] = status
    if mes:
        query["data_vencimento"] = {"$regex": f"^{mes}"}
    if categoria:
        query["categoria"] = categoria
    
    contas = await db.contas.find(query, {"_id": 0}).sort("data_vencimento", 1).to_list(500)
    return contas

@api_router.get("/contas/receber/{conta_id}")
async def get_conta_receber(conta_id: str):
    """Buscar conta a receber por ID"""
    conta = await db.contas.find_one({"id": conta_id, "tipo": "RECEBER"}, {"_id": 0})
    
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return conta

@api_router.put("/contas/receber/{conta_id}")
async def update_conta_receber(conta_id: str, conta_data: ContaCreate):
    """Atualizar conta a receber"""
    if conta_data.tipo != "RECEBER":
        raise HTTPException(status_code=400, detail="Tipo deve ser RECEBER")
    
    from datetime import datetime as dt
    update_doc = conta_data.model_dump()
    update_doc['updated_at'] = dt.now(timezone.utc).isoformat()
    
    result = await db.contas.update_one(
        {"id": conta_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return {"message": "Conta atualizada com sucesso!"}

@api_router.delete("/contas/receber/{conta_id}")
async def delete_conta_receber(conta_id: str):
    """Deletar conta a receber"""
    # Verificar se tem lançamento vinculado
    conta = await db.contas.find_one({"id": conta_id})
    if conta and conta.get('lancamento_id'):
        # Cancelar lançamento vinculado
        await cancel_lancamento_from_conta(conta_id)
    
    result = await db.contas.delete_one({"id": conta_id, "tipo": "RECEBER"})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    return {"message": "Conta excluída com sucesso!"}

@api_router.patch("/contas/receber/{conta_id}/status")
async def update_status_conta_receber(conta_id: str, status_data: ContaStatusUpdate):
    """Atualizar status da conta a receber"""
    conta = await db.contas.find_one({"id": conta_id, "tipo": "RECEBER"})
    
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    from datetime import datetime as dt
    update_fields = {
        "status": status_data.status,
        "updated_at": dt.now(timezone.utc).isoformat()
    }
    
    # Se marcar como RECEBIDO, criar lançamento automático
    if status_data.status == "RECEBIDO" and not conta.get('lancamento_id'):
        data_pagamento = status_data.data_pagamento or dt.now().strftime("%Y-%m-%d")
        update_fields['data_pagamento'] = data_pagamento
        
        # Atualizar conta primeiro
        await db.contas.update_one({"id": conta_id}, {"$set": update_fields})
        
        # Criar lançamento de receita
        conta_atualizada = await db.contas.find_one({"id": conta_id})
        lancamento_id = await create_lancamento_from_conta(conta_atualizada, "receita")
        
        # Vincular lançamento à conta
        await db.contas.update_one(
            {"id": conta_id},
            {"$set": {"lancamento_id": lancamento_id}}
        )
        
        return {"message": "Conta marcada como RECEBIDA e lançamento criado!", "lancamento_id": lancamento_id}
    
    # Se voltar para PENDENTE, cancelar lançamento
    elif status_data.status == "PENDENTE" and conta.get('lancamento_id'):
        await cancel_lancamento_from_conta(conta_id)
        update_fields['data_pagamento'] = None
        update_fields['lancamento_id'] = None
    
    await db.contas.update_one({"id": conta_id}, {"$set": update_fields})
    
    return {"message": "Status atualizado com sucesso!"}

# ===== RESUMOS E CONSULTAS =====

@api_router.get("/contas/resumo-mensal")
async def get_resumo_mensal(company_id: str, mes: str):
    """Resumo mensal de contas a pagar e receber"""
    # Aggregation para contas a pagar
    pipeline_pagar = [
        {"$match": {
            "company_id": company_id,
            "tipo": "PAGAR",
            "data_vencimento": {"$regex": f"^{mes}"}
        }},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$valor"},
            "quantidade": {"$sum": 1}
        }}
    ]
    
    # Aggregation para contas a receber
    pipeline_receber = [
        {"$match": {
            "company_id": company_id,
            "tipo": "RECEBER",
            "data_vencimento": {"$regex": f"^{mes}"}
        }},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$valor"},
            "quantidade": {"$sum": 1}
        }}
    ]
    
    results_pagar = await db.contas.aggregate(pipeline_pagar).to_list(None)
    results_receber = await db.contas.aggregate(pipeline_receber).to_list(None)
    
    # Processar resultados
    pagar = {"pendente": 0, "pago": 0, "atrasado": 0, "total": 0, "quantidade_total": 0}
    receber = {"pendente": 0, "recebido": 0, "atrasado": 0, "total": 0, "quantidade_total": 0}
    
    for r in results_pagar:
        status = r['_id'].lower()
        if status == "pendente":
            pagar['pendente'] = r['total']
        elif status == "pago":
            pagar['pago'] = r['total']
        elif status == "atrasado":
            pagar['atrasado'] = r['total']
        pagar['total'] += r['total']
        pagar['quantidade_total'] += r['quantidade']
    
    for r in results_receber:
        status = r['_id'].lower()
        if status == "pendente":
            receber['pendente'] = r['total']
        elif status in ["recebido", "pago"]:
            receber['recebido'] = r['total']
        elif status == "atrasado":
            receber['atrasado'] = r['total']
        receber['total'] += r['total']
        receber['quantidade_total'] += r['quantidade']
    
    # Calcular saldo projetado
    saldo_projetado = receber['pendente'] - pagar['pendente']
    
    return {
        "pagar": pagar,
        "receber": receber,
        "saldo_projetado": saldo_projetado,
        "contas_atrasadas": {
            "pagar": pagar['atrasado'],
            "receber": receber['atrasado'],
            "total": pagar['atrasado'] + receber['atrasado']
        }
    }

@api_router.get("/contas/proximos-vencimentos")
async def get_proximos_vencimentos(company_id: str, dias: int = 7):
    """Listar próximas contas a vencer nos próximos N dias"""
    from datetime import datetime as dt, timedelta
    
    hoje = dt.now()
    data_limite = hoje + timedelta(days=dias)
    
    # Buscar contas pendentes ou atrasadas que vencem nos próximos N dias
    pipeline = [
        {"$match": {
            "company_id": company_id,
            "status": {"$in": ["PENDENTE", "ATRASADO"]},
            "data_vencimento": {
                "$gte": hoje.strftime("%Y-%m-%d"),
                "$lte": data_limite.strftime("%Y-%m-%d")
            }
        }},
        {"$sort": {"data_vencimento": 1}},
        {"$project": {"_id": 0}}
    ]
    
    contas = await db.contas.aggregate(pipeline).to_list(100)
    
    return {
        "periodo": f"{dias} dias",
        "quantidade": len(contas),
        "contas": contas
    }


@api_router.get("/contas/fluxo-caixa-projetado")
async def get_fluxo_caixa_projetado(company_id: str, meses: int = 6):
    """Retorna fluxo de caixa projetado (contas a pagar e receber) para os próximos N meses"""
    from datetime import datetime as dt
    from dateutil.relativedelta import relativedelta
    
    hoje = dt.now()
    resultado = []
    
    for i in range(meses):
        mes_ref = hoje + relativedelta(months=i)
        mes_str = mes_ref.strftime("%Y-%m")
        mes_label = mes_ref.strftime("%b/%Y")
        
        # Contas a receber (entradas)
        pipeline_entradas = [
            {"$match": {
                "company_id": company_id,
                "tipo": "RECEBER",
                "data_vencimento": {"$regex": f"^{mes_str}"}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$valor"}
            }}
        ]
        
        # Contas a pagar (saídas)
        pipeline_saidas = [
            {"$match": {
                "company_id": company_id,
                "tipo": "PAGAR",
                "data_vencimento": {"$regex": f"^{mes_str}"}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$valor"}
            }}
        ]
        
        result_entradas = await db.contas.aggregate(pipeline_entradas).to_list(None)
        result_saidas = await db.contas.aggregate(pipeline_saidas).to_list(None)
        
        entradas = result_entradas[0]['total'] if result_entradas else 0
        saidas = result_saidas[0]['total'] if result_saidas else 0
        
        resultado.append({
            "mes": mes_label,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        })
    
    return resultado

@api_router.get("/contas/pagar-por-categoria")
async def get_contas_pagar_por_categoria(company_id: str, mes: Optional[str] = None):
    """Agrupa contas a pagar por categoria"""
    from datetime import datetime as dt
    
    if not mes:
        mes = dt.now().strftime("%Y-%m")
    
    pipeline = [
        {"$match": {
            "company_id": company_id,
            "tipo": "PAGAR",
            "data_vencimento": {"$regex": f"^{mes}"}
        }},
        {"$group": {
            "_id": "$categoria",
            "total": {"$sum": "$valor"},
            "quantidade": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]
    
    results = await db.contas.aggregate(pipeline).to_list(None)
    
    # Calcular total para percentuais
    total_geral = sum(r['total'] for r in results)
    
    return [
        {
            "categoria": r['_id'],
            "valor": r['total'],
            "quantidade": r['quantidade'],
            "percentual": round((r['total'] / total_geral * 100), 1) if total_geral > 0 else 0
        }
        for r in results
    ]

@api_router.get("/contas/receber-por-cliente")
async def get_contas_receber_por_cliente(company_id: str, mes: Optional[str] = None):
    """Agrupa contas a receber por cliente (descrição)"""
    from datetime import datetime as dt
    
    if not mes:
        mes = dt.now().strftime("%Y-%m")
    
    # Agrupar por descrição (que geralmente contém o nome do cliente)
    pipeline = [
        {"$match": {
            "company_id": company_id,
            "tipo": "RECEBER",
            "data_vencimento": {"$regex": f"^{mes}"}
        }},
        {"$group": {
            "_id": "$categoria",
            "total": {"$sum": "$valor"},
            "quantidade": {"$sum": 1}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ]
    
    results = await db.contas.aggregate(pipeline).to_list(None)
    
    # Calcular total para percentuais
    total_geral = sum(r['total'] for r in results)
    
    return [
        {
            "cliente": r['_id'],
            "valor": r['total'],
            "quantidade": r['quantidade'],
            "percentual": round((r['total'] / total_geral * 100), 1) if total_geral > 0 else 0
        }
        for r in results
    ]

# ========== ADMIN: VERIFICAR ROLE ==========

async def verify_admin(user_id: str):
    """Verificar se usuário é admin"""
    user = await db.users.find_one({"id": user_id})
    
    if not user or user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    return True

# ========== ADMIN: ESTATÍSTICAS ==========

@api_router.get("/admin/stats")
async def admin_stats(user_id: str):
    await verify_admin(user_id)
    
    # Total de usuários
    total_users = await db.users.count_documents({})
    
    # Assinaturas ativas
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    
    # MRR (Receita Mensal Recorrente)
    mrr = active_subs * 49.90
    
    # ARR (Receita Anual)
    arr = mrr * 12
    
    # Taxa de conversão (trial -> active)
    # total_trials pode ser usado no futuro para cálculos mais detalhados
    # total_trials = await db.subscriptions.count_documents({"status": "trial"})
    conversion_rate = (active_subs / max(total_users - 1, 1)) * 100  # -1 para excluir admin
    
    # Total de empresas
    total_companies = await db.companies.count_documents({})
    
    return {
        "total_users": total_users,
        "active_subscriptions": active_subs,
        "mrr": mrr,
        "arr": arr,
        "conversion_rate": round(conversion_rate, 2),
        "total_companies": total_companies
    }

@api_router.get("/admin/users")
async def admin_users(user_id: str):
    await verify_admin(user_id)
    
    # Usar aggregation pipeline para evitar N+1 queries
    pipeline = [
        {"$match": {"role": "user"}},
        {"$project": {"_id": 0, "password": 0}},
        {"$lookup": {
            "from": "subscriptions",
            "localField": "id",
            "foreignField": "user_id",
            "as": "subscription"
        }},
        {"$lookup": {
            "from": "companies",
            "localField": "id",
            "foreignField": "user_id",
            "as": "companies"
        }},
        {"$addFields": {
            "subscription_status": {
                "$ifNull": [
                    {"$arrayElemAt": ["$subscription.status", 0]},
                    "none"
                ]
            },
            "companies_count": {"$size": "$companies"}
        }},
        {"$project": {"subscription": 0, "companies": 0}},
        {"$limit": 100}
    ]
    
    users = await db.users.aggregate(pipeline).to_list(None)
    return users

@api_router.get("/admin/subscriptions")
async def admin_subscriptions(user_id: str, status: Optional[str] = None):
    await verify_admin(user_id)
    
    # Usar aggregation pipeline para evitar N+1 queries
    match_stage = {"$match": {}}
    if status:
        match_stage["$match"]["status"] = status
    
    pipeline = [
        match_stage,
        {"$project": {"_id": 0}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$addFields": {
            "user_name": {
                "$ifNull": [
                    {"$arrayElemAt": ["$user.name", 0]},
                    "Desconhecido"
                ]
            },
            "user_email": {
                "$ifNull": [
                    {"$arrayElemAt": ["$user.email", 0]},
                    "Desconhecido"
                ]
            }
        }},
        {"$project": {"user": 0}},
        {"$limit": 100}
    ]
    
    subscriptions = await db.subscriptions.aggregate(pipeline).to_list(None)
    return subscriptions

@api_router.get("/admin/revenue-chart")
async def admin_revenue_chart(admin_user_id: str):
    await verify_admin(admin_user_id)
    
    # Gerar dados de receita mensal (últimos 12 meses)
    # Para MVP, vamos simular com dados baseados nas assinaturas atuais
    active_count = await db.subscriptions.count_documents({"status": "active"})
    
    months = []
    now = datetime.now(timezone.utc)
    
    for i in range(11, -1, -1):
        month_date = now - timedelta(days=i*30)
        month_label = month_date.strftime("%b/%y")
        
        # Simular crescimento gradual
        revenue = (active_count * 49.90) * ((12 - i) / 12)
        
        months.append({
            "month": month_label,
            "revenue": round(revenue, 2)
        })
    
    return months

@api_router.post("/admin/user/{target_id}/toggle-status")
async def admin_toggle_user_status(target_id: str, admin_user_id: str):
    await verify_admin(admin_user_id)
    
    # Buscar assinatura do usuário
    subscription = await db.subscriptions.find_one({"user_id": target_id})
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    # Alternar status
    new_status = "expired" if subscription['status'] == "active" else "active"
    
    await db.subscriptions.update_one(
        {"id": subscription['id']},
        {"$set": {"status": new_status}}
    )
    
    return {"message": f"Status alterado para {new_status}", "new_status": new_status}

# ========== EXPORTAÇÃO ==========

@api_router.get("/export/excel/{company_id}")
async def export_excel(company_id: str, month: str):
    transactions = await db.transactions.find({
        "company_id": company_id,
        "date": {"$regex": f"^{month}"}
    }, {"_id": 0}).to_list(1000)
    
    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Lançamentos {month}"
    
    # Headers
    headers = ["Data", "Tipo", "Descrição", "Categoria", "Valor", "Status"]
    ws.append(headers)
    
    # Dados
    for t in transactions:
        ws.append([
            t['date'],
            t['type'],
            t['description'],
            t['category'],
            t['amount'],
            t['status']
        ])
    
    # Salvar em BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=lancamentos_{month}.xlsx"}
    )

# ========== INCLUIR ROUTER ==========

app.include_router(api_router)

# Health check endpoints
@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend funcionando!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "backend": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
# Logger já configurado no início do arquivo

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()