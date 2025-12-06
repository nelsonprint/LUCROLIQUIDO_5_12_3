#!/usr/bin/env python3
"""
Teste Completo do Módulo de Materiais no Orçamento - Sistema Lucro Líquido
Executa os 4 testes solicitados:
1. Criar Orçamento com Materiais
2. Validar PDF
3. Validar Link WhatsApp
4. Acessar PDF via Link Público
"""

import requests
import json
import sys
import time
from datetime import datetime
from urllib.parse import unquote, parse_qs, urlparse

# Configuração
BASE_URL = "https://budget-materials-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@lucroliquido.com"
ADMIN_PASSWORD = "admin123"

class TesteMaterialsOrcamento:
    def __init__(self):
        self.session = requests.Session()
        self.user_data = None
        self.empresa_id = None
        self.orcamento_id = None
        self.materiais_ids = []
        self.pdf_token = None
        self.pdf_url = None
        self.whatsapp_url = None
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def setup_test_environment(self):
        """Configurar ambiente de teste (login e empresa)"""
        self.log("=== CONFIGURAÇÃO DO AMBIENTE ===")
        
        # Login
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.user_data = response.json()
                self.log(f"✅ Login realizado: {self.user_data['name']}")
            else:
                self.log(f"❌ Falha no login: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no login: {str(e)}", "ERROR")
            return False
        
        # Buscar empresa
        try:
            response = self.session.get(f"{BASE_URL}/companies/{self.user_data['user_id']}")
            
            if response.status_code == 200:
                empresas = response.json()
                if empresas:
                    self.empresa_id = empresas[0]['id']
                    self.log(f"✅ Empresa encontrada: {empresas[0]['name']} (ID: {self.empresa_id})")
                    return True
                else:
                    self.log("❌ Nenhuma empresa encontrada", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao buscar empresas: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao buscar empresa: {str(e)}", "ERROR")
            return False
    
    def teste_1_criar_orcamento_com_materiais(self):
        """TESTE 1: Criar Orçamento com Materiais"""
        self.log("=== TESTE 1: CRIAR ORÇAMENTO COM MATERIAIS ===")
        
        # 1.1 Criar orçamento
        try:
            orcamento_data = {
                "empresa_id": self.empresa_id,
                "usuario_id": self.user_data['user_id'],
                "cliente_nome": "João Silva",
                "cliente_whatsapp": "11999887766",
                "cliente_email": "joao.silva@email.com",
                "cliente_telefone": "(11) 99988-7766",
                "tipo": "servico_m2",
                "descricao_servico_ou_produto": "Reforma completa de apartamento com materiais inclusos",
                "area_m2": 100.0,
                "custo_total": 5000.00,
                "preco_minimo": 7000.00,
                "preco_sugerido": 8500.00,
                "preco_praticado": 8000.00,
                "validade_proposta": "2025-02-28",
                "condicoes_pagamento": "30% entrada + 70% na conclusão",
                "prazo_execucao": "20 dias úteis",
                "observacoes": "Teste do módulo de materiais"
            }
            
            response = self.session.post(f"{BASE_URL}/orcamentos", json=orcamento_data)
            
            if response.status_code == 200:
                result = response.json()
                self.orcamento_id = result['orcamento_id']
                numero_orcamento = result['numero_orcamento']
                self.log(f"✅ Orçamento criado: {numero_orcamento} (ID: {self.orcamento_id})")
            else:
                self.log(f"❌ Erro ao criar orçamento: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao criar orçamento: {str(e)}", "ERROR")
            return False
        
        # 1.2 Adicionar 3 materiais diferentes
        materiais_teste = [
            {
                "nome_item": "Tinta",
                "unidade": "galão",
                "preco_compra_fornecedor": 85.50,
                "percentual_acrescimo": 40.0,
                "quantidade": 5.0
            },
            {
                "nome_item": "Cimento",
                "unidade": "sc",
                "preco_compra_fornecedor": 32.00,
                "percentual_acrescimo": 35.0,
                "quantidade": 10.0
            },
            {
                "nome_item": "Areia",
                "unidade": "m³",
                "preco_compra_fornecedor": 95.00,
                "percentual_acrescimo": 30.0,
                "quantidade": 2.0
            }
        ]
        
        total_materiais_esperado = 0
        materiais_adicionados = []
        
        for material in materiais_teste:
            try:
                material_data = {
                    "id_orcamento": self.orcamento_id,
                    "id_material": None,  # Material novo
                    "nome_item": material["nome_item"],
                    "unidade": material["unidade"],
                    "preco_compra_fornecedor": material["preco_compra_fornecedor"],
                    "percentual_acrescimo": material["percentual_acrescimo"],
                    "quantidade": material["quantidade"]
                }
                
                response = self.session.post(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais", json=material_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verificar cálculos
                    preco_esperado = material["preco_compra_fornecedor"] * (1 + material["percentual_acrescimo"]/100)
                    total_esperado = preco_esperado * material["quantidade"]
                    
                    preco_retornado = result['preco_unitario_final']
                    total_retornado = result['preco_total_item']
                    
                    if abs(preco_retornado - preco_esperado) < 0.01 and abs(total_retornado - total_esperado) < 0.01:
                        self.log(f"✅ {material['nome_item']}: Preço R$ {preco_retornado:.2f} x {material['quantidade']} = R$ {total_retornado:.2f}")
                        materiais_adicionados.append(result['orcamento_material_id'])
                        total_materiais_esperado += total_retornado
                    else:
                        self.log(f"❌ Erro nos cálculos do {material['nome_item']}: Esperado R$ {preco_esperado:.2f}/R$ {total_esperado:.2f}, Recebido R$ {preco_retornado:.2f}/R$ {total_retornado:.2f}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Erro ao adicionar {material['nome_item']}: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Erro ao adicionar {material['nome_item']}: {str(e)}", "ERROR")
                return False
        
        # 1.3 Verificar total de materiais
        try:
            response = self.session.get(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais")
            
            if response.status_code == 200:
                result = response.json()
                total_materiais = result['total_materiais']
                
                if abs(total_materiais - total_materiais_esperado) < 0.01:
                    self.log(f"✅ Total de materiais correto: R$ {total_materiais:.2f}")
                    self.log(f"✅ TESTE 1 APROVADO: Orçamento criado com 3 materiais e cálculos corretos")
                    return True
                else:
                    self.log(f"❌ Total incorreto: Esperado R$ {total_materiais_esperado:.2f}, Recebido R$ {total_materiais:.2f}", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao verificar total: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao verificar total: {str(e)}", "ERROR")
            return False
    
    def teste_2_validar_pdf(self):
        """TESTE 2: Validar PDF"""
        self.log("=== TESTE 2: VALIDAR PDF ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/orcamento/{self.orcamento_id}/pdf")
            
            if response.status_code == 200:
                content_length = len(response.content)
                
                # Verificar tamanho mínimo (2000 bytes)
                if content_length > 2000:
                    self.log(f"✅ PDF gerado com tamanho adequado: {content_length} bytes")
                else:
                    self.log(f"❌ PDF muito pequeno: {content_length} bytes (mínimo 2000)", "ERROR")
                    return False
                
                # Verificar se é um PDF válido
                if response.content.startswith(b'%PDF'):
                    self.log("✅ Arquivo PDF válido (cabeçalho correto)")
                else:
                    self.log("❌ Arquivo não é um PDF válido", "ERROR")
                    return False
                
                # Verificar se não há erros de formato (PDF não corrompido)
                try:
                    # Verificar se o PDF termina corretamente
                    if b'%%EOF' in response.content[-100:]:
                        self.log("✅ PDF bem formado (terminação correta)")
                    else:
                        self.log("⚠️ PDF pode estar incompleto (sem %%EOF)", "WARNING")
                    
                    self.log("✅ TESTE 2 APROVADO: PDF gerado e validado com sucesso")
                    return True
                    
                except Exception as e:
                    self.log(f"❌ Erro na validação do PDF: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao gerar PDF: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao validar PDF: {str(e)}", "ERROR")
            return False
    
    def teste_3_validar_link_whatsapp(self):
        """TESTE 3: Validar Link WhatsApp"""
        self.log("=== TESTE 3: VALIDAR LINK WHATSAPP ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/orcamento/{self.orcamento_id}/whatsapp")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verificar campos obrigatórios
                required_fields = ['pdf_url', 'whatsapp_url', 'token', 'expires_in']
                for field in required_fields:
                    if field not in result:
                        self.log(f"❌ Campo obrigatório ausente: {field}", "ERROR")
                        return False
                
                self.pdf_url = result['pdf_url']
                self.whatsapp_url = result['whatsapp_url']
                self.pdf_token = result['token']
                
                self.log(f"✅ Resposta contém todos os campos: pdf_url, whatsapp_url, token, expires_in")
                
                # Verificar se pdf_url é acessível
                try:
                    pdf_response = self.session.get(self.pdf_url)
                    if pdf_response.status_code == 200:
                        self.log("✅ PDF URL acessível (HTTP 200)")
                    else:
                        self.log(f"❌ PDF URL não acessível: {pdf_response.status_code}", "ERROR")
                        return False
                except Exception as e:
                    self.log(f"❌ Erro ao acessar PDF URL: {str(e)}", "ERROR")
                    return False
                
                # Verificar mensagem do WhatsApp
                if 'wa.me' in self.whatsapp_url:
                    self.log("✅ WhatsApp URL válida (contém wa.me)")
                    
                    # Decodificar URL do WhatsApp e validar texto
                    try:
                        parsed_url = urlparse(self.whatsapp_url)
                        query_params = parse_qs(parsed_url.query)
                        
                        if 'text' in query_params:
                            mensagem = unquote(query_params['text'][0])
                            
                            # Verificar se a mensagem contém informações esperadas
                            checks = [
                                ('João Silva', 'nome do cliente'),
                                ('LL-', 'número do orçamento'),
                                ('R$', 'valor monetário'),
                                (self.pdf_url, 'link do PDF')
                            ]
                            
                            all_checks_passed = True
                            for check_text, description in checks:
                                if check_text in mensagem:
                                    self.log(f"✅ Mensagem contém {description}")
                                else:
                                    self.log(f"❌ Mensagem não contém {description}", "ERROR")
                                    all_checks_passed = False
                            
                            if all_checks_passed:
                                self.log("✅ TESTE 3 APROVADO: Link WhatsApp validado com sucesso")
                                return True
                            else:
                                return False
                        else:
                            self.log("❌ WhatsApp URL não contém parâmetro 'text'", "ERROR")
                            return False
                            
                    except Exception as e:
                        self.log(f"❌ Erro ao decodificar WhatsApp URL: {str(e)}", "ERROR")
                        return False
                else:
                    self.log("❌ WhatsApp URL inválida (não contém wa.me)", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao chamar endpoint WhatsApp: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no teste WhatsApp: {str(e)}", "ERROR")
            return False
    
    def teste_4_acessar_pdf_via_link_publico(self):
        """TESTE 4: Acessar PDF via Link Público"""
        self.log("=== TESTE 4: ACESSAR PDF VIA LINK PÚBLICO ===")
        
        if not self.pdf_token:
            self.log("❌ Token não disponível (execute teste 3 primeiro)", "ERROR")
            return False
        
        try:
            # Acessar PDF via token público
            response = self.session.get(f"{BASE_URL}/orcamento/share/{self.pdf_token}")
            
            if response.status_code == 200:
                content_length = len(response.content)
                self.log(f"✅ PDF acessível via link público: {content_length} bytes")
                
                # Verificar se é um PDF válido
                if response.content.startswith(b'%PDF'):
                    self.log("✅ PDF público é válido")
                else:
                    self.log("❌ PDF público não é válido", "ERROR")
                    return False
                
                # Comparar tamanho com PDF gerado diretamente
                try:
                    direct_response = self.session.get(f"{BASE_URL}/orcamento/{self.orcamento_id}/pdf")
                    
                    if direct_response.status_code == 200:
                        direct_size = len(direct_response.content)
                        public_size = content_length
                        
                        # Permitir pequena diferença (até 5%) devido a timestamps diferentes
                        size_diff = abs(direct_size - public_size) / max(direct_size, public_size)
                        
                        if size_diff <= 0.05:  # 5% de tolerância
                            self.log(f"✅ Tamanhos compatíveis: Direto {direct_size} bytes, Público {public_size} bytes")
                        else:
                            self.log(f"⚠️ Diferença significativa de tamanho: Direto {direct_size} bytes, Público {public_size} bytes", "WARNING")
                        
                        self.log("✅ TESTE 4 APROVADO: PDF acessível via link público")
                        return True
                    else:
                        self.log(f"❌ Erro ao gerar PDF direto para comparação: {direct_response.status_code}", "ERROR")
                        return False
                        
                except Exception as e:
                    self.log(f"❌ Erro na comparação de PDFs: {str(e)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao acessar PDF público: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no teste de PDF público: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes solicitados"""
        self.log("🚀 INICIANDO TESTE COMPLETO DO MÓDULO DE MATERIAIS NO ORÇAMENTO")
        self.log("=" * 70)
        
        # Configurar ambiente
        if not self.setup_test_environment():
            self.log("❌ Falha na configuração do ambiente", "ERROR")
            return False
        
        self.log("-" * 70)
        
        # Executar testes
        tests = [
            ("TESTE 1: Criar Orçamento com Materiais", self.teste_1_criar_orcamento_com_materiais),
            ("TESTE 2: Validar PDF", self.teste_2_validar_pdf),
            ("TESTE 3: Validar Link WhatsApp", self.teste_3_validar_link_whatsapp),
            ("TESTE 4: Acessar PDF via Link Público", self.teste_4_acessar_pdf_via_link_publico)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: APROVADO")
                else:
                    failed += 1
                    self.log(f"❌ {test_name}: REPROVADO")
            except Exception as e:
                self.log(f"❌ Erro inesperado em {test_name}: {str(e)}", "ERROR")
                failed += 1
            
            self.log("-" * 70)
        
        # Resumo final
        self.log("📊 RESUMO FINAL DOS TESTES")
        self.log("=" * 70)
        self.log(f"✅ Testes Aprovados: {passed}")
        self.log(f"❌ Testes Reprovados: {failed}")
        self.log(f"📈 Taxa de Sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 TODOS OS TESTES PASSARAM!")
            self.log("✅ Módulo de materiais no orçamento funcionando perfeitamente")
            self.log("✅ Geração de PDF validada")
            self.log("✅ Funcionalidade WhatsApp validada")
            self.log("✅ Link público de PDF validado")
            return True
        else:
            self.log(f"⚠️ {failed} teste(s) falharam. Verifique os logs acima.")
            return False

if __name__ == "__main__":
    tester = TesteMaterialsOrcamento()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)