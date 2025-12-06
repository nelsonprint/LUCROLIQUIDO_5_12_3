#!/usr/bin/env python3
"""
AUDITORIA COMPLETA DO SISTEMA PARA DEPLOY - Sistema Lucro Líquido
Testa TODAS as APIs principais para garantir deploy seguro.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuração
BASE_URL = "https://budget-materials-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@lucroliquido.com"
ADMIN_PASSWORD = "admin123"

class SystemAuditTest:
    def __init__(self):
        self.session = requests.Session()
        self.user_data = None
        self.empresa_id = None
        self.orcamento_id = None
        self.materiais_criados = []
        self.orcamento_materiais = []
        self.contas_criadas = []
        self.transactions_criadas = []
        self.test_results = {}
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
        
    def test_login(self):
        """1. Teste de Login"""
        self.log("=== TESTE 1: LOGIN ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.user_data = response.json()
                self.log(f"✅ Login realizado com sucesso: {self.user_data['name']}")
                return True
            else:
                self.log(f"❌ Falha no login: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no login: {str(e)}", "ERROR")
            return False
    
    def test_get_empresa(self):
        """2. Buscar empresa de teste"""
        self.log("=== TESTE 2: BUSCAR EMPRESA ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/companies/{self.user_data['user_id']}")
            
            if response.status_code == 200:
                empresas = response.json()
                if empresas:
                    self.empresa_id = empresas[0]['id']
                    self.log(f"✅ Empresa encontrada: {empresas[0]['name']} (ID: {self.empresa_id})")
                    return True
                else:
                    # Criar empresa de teste
                    return self.create_test_empresa()
            else:
                self.log(f"❌ Erro ao buscar empresas: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao buscar empresa: {str(e)}", "ERROR")
            return False
    
    def create_test_empresa(self):
        """Criar empresa de teste se não existir"""
        self.log("Criando empresa de teste...")
        
        try:
            response = self.session.post(f"{BASE_URL}/companies", json={
                "user_id": self.user_data['user_id'],
                "name": "Empresa Teste Materiais",
                "segment": "Construção Civil",
                "razao_social": "Empresa Teste Materiais LTDA",
                "cnpj": "12.345.678/0001-90",
                "telefone_fixo": "(11) 3333-4444",
                "celular_whatsapp": "(11) 99999-8888",
                "email_empresa": "contato@empresateste.com"
            })
            
            if response.status_code == 200:
                result = response.json()
                self.empresa_id = result['company_id']
                self.log(f"✅ Empresa criada com sucesso (ID: {self.empresa_id})")
                return True
            else:
                self.log(f"❌ Erro ao criar empresa: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao criar empresa: {str(e)}", "ERROR")
            return False
    
    def test_create_materiais(self):
        """3. Criar materiais no catálogo"""
        self.log("=== TESTE 3: CRIAR MATERIAIS ===")
        
        materiais_teste = [
            {
                "nome_item": "Tinta Acrílica Branca",
                "descricao": "Tinta acrílica premium para paredes internas e externas",
                "unidade": "galão",
                "preco_compra_base": 85.50
            },
            {
                "nome_item": "Cimento CP-II 50kg",
                "descricao": "Cimento Portland composto com escória",
                "unidade": "sc",
                "preco_compra_base": 32.00
            },
            {
                "nome_item": "Massa Corrida",
                "descricao": "Massa corrida para acabamento de paredes",
                "unidade": "kg",
                "preco_compra_base": 12.50
            }
        ]
        
        success_count = 0
        
        for material_data in materiais_teste:
            try:
                response = self.session.post(f"{BASE_URL}/materiais", json=material_data)
                
                if response.status_code == 200:
                    result = response.json()
                    material_id = result['material_id']
                    self.materiais_criados.append({
                        'id': material_id,
                        'nome': material_data['nome_item'],
                        'preco': material_data['preco_compra_base']
                    })
                    self.log(f"✅ Material criado: {material_data['nome_item']} (ID: {material_id})")
                    success_count += 1
                else:
                    self.log(f"❌ Erro ao criar material {material_data['nome_item']}: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Erro ao criar material {material_data['nome_item']}: {str(e)}", "ERROR")
        
        if success_count == len(materiais_teste):
            self.log(f"✅ Todos os {success_count} materiais criados com sucesso")
            return True
        else:
            self.log(f"⚠️ Apenas {success_count}/{len(materiais_teste)} materiais criados", "WARNING")
            return success_count > 0
    
    def test_list_materiais(self):
        """4. Listar materiais"""
        self.log("=== TESTE 4: LISTAR MATERIAIS ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/materiais")
            
            if response.status_code == 200:
                materiais = response.json()
                self.log(f"✅ Lista de materiais obtida: {len(materiais)} materiais encontrados")
                
                # Verificar se os materiais criados estão na lista
                nomes_criados = [m['nome'] for m in self.materiais_criados]
                nomes_listados = [m['nome_item'] for m in materiais]
                
                materiais_encontrados = [nome for nome in nomes_criados if nome in nomes_listados]
                
                if len(materiais_encontrados) == len(nomes_criados):
                    self.log("✅ Todos os materiais criados foram encontrados na listagem")
                    return True
                else:
                    self.log(f"⚠️ Apenas {len(materiais_encontrados)}/{len(nomes_criados)} materiais encontrados", "WARNING")
                    return False
            else:
                self.log(f"❌ Erro ao listar materiais: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao listar materiais: {str(e)}", "ERROR")
            return False
    
    def test_search_materiais(self):
        """5. Buscar materiais (autocomplete)"""
        self.log("=== TESTE 5: BUSCAR MATERIAIS (AUTOCOMPLETE) ===")
        
        try:
            # Buscar por "Tinta"
            response = self.session.get(f"{BASE_URL}/materiais/buscar?q=Tinta")
            
            if response.status_code == 200:
                resultados = response.json()
                self.log(f"✅ Busca por 'Tinta' retornou {len(resultados)} resultados")
                
                # Verificar se encontrou a Tinta Acrílica Branca
                tinta_encontrada = any(m['nome_item'] == 'Tinta Acrílica Branca' for m in resultados)
                
                if tinta_encontrada:
                    self.log("✅ Tinta Acrílica Branca encontrada na busca")
                    return True
                else:
                    self.log("❌ Tinta Acrílica Branca não encontrada na busca", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro na busca de materiais: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro na busca de materiais: {str(e)}", "ERROR")
            return False
    
    def test_create_orcamento(self):
        """6. Criar orçamento de teste"""
        self.log("=== TESTE 6: CRIAR ORÇAMENTO ===")
        
        try:
            orcamento_data = {
                "empresa_id": self.empresa_id,
                "usuario_id": self.user_data['user_id'],
                "cliente_nome": "Maria Silva Santos",
                "cliente_documento": "123.456.789-00",
                "cliente_email": "maria.santos@email.com",
                "cliente_telefone": "(11) 98765-4321",
                "cliente_whatsapp": "11987654321",
                "cliente_endereco": "Rua das Flores, 123 - São Paulo/SP",
                "tipo": "servico_m2",
                "descricao_servico_ou_produto": "Pintura completa de apartamento com 80m² incluindo materiais e mão de obra",
                "area_m2": 80.0,
                "custo_total": 2500.00,
                "preco_minimo": 3200.00,
                "preco_sugerido": 3800.00,
                "preco_praticado": 3500.00,
                "validade_proposta": "2025-02-15",
                "condicoes_pagamento": "50% entrada + 50% na conclusão",
                "prazo_execucao": "15 dias úteis",
                "observacoes": "Orçamento de teste para módulo de materiais"
            }
            
            response = self.session.post(f"{BASE_URL}/orcamentos", json=orcamento_data)
            
            if response.status_code == 200:
                result = response.json()
                self.orcamento_id = result['orcamento_id']
                numero_orcamento = result['numero_orcamento']
                self.log(f"✅ Orçamento criado: {numero_orcamento} (ID: {self.orcamento_id})")
                return True
            else:
                self.log(f"❌ Erro ao criar orçamento: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao criar orçamento: {str(e)}", "ERROR")
            return False
    
    def test_add_materiais_to_orcamento(self):
        """7. Adicionar materiais ao orçamento"""
        self.log("=== TESTE 7: ADICIONAR MATERIAIS AO ORÇAMENTO ===")
        
        # Materiais para adicionar com diferentes quantidades e acréscimos
        materiais_orcamento = [
            {
                "id_orcamento": self.orcamento_id,
                "id_material": self.materiais_criados[0]['id'],  # Tinta Acrílica
                "nome_item": self.materiais_criados[0]['nome'],
                "unidade": "galão",
                "preco_compra_fornecedor": 85.50,
                "percentual_acrescimo": 30.0,
                "quantidade": 4.0
            },
            {
                "id_orcamento": self.orcamento_id,
                "id_material": self.materiais_criados[1]['id'],  # Cimento
                "nome_item": self.materiais_criados[1]['nome'],
                "unidade": "sc",
                "preco_compra_fornecedor": 32.00,
                "percentual_acrescimo": 40.0,
                "quantidade": 10.0
            }
        ]
        
        success_count = 0
        
        for material_data in materiais_orcamento:
            try:
                response = self.session.post(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais", json=material_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verificar cálculos
                    preco_esperado = material_data['preco_compra_fornecedor'] * (1 + material_data['percentual_acrescimo']/100)
                    total_esperado = preco_esperado * material_data['quantidade']
                    
                    preco_retornado = result['preco_unitario_final']
                    total_retornado = result['preco_total_item']
                    
                    if abs(preco_retornado - preco_esperado) < 0.01 and abs(total_retornado - total_esperado) < 0.01:
                        self.log(f"✅ Material adicionado: {material_data['nome_item']} - Preço: R$ {preco_retornado:.2f}, Total: R$ {total_retornado:.2f}")
                        self.orcamento_materiais.append(result['orcamento_material_id'])
                        success_count += 1
                    else:
                        self.log(f"❌ Erro nos cálculos do material {material_data['nome_item']}: Esperado R$ {preco_esperado:.2f}/R$ {total_esperado:.2f}, Recebido R$ {preco_retornado:.2f}/R$ {total_retornado:.2f}", "ERROR")
                else:
                    self.log(f"❌ Erro ao adicionar material {material_data['nome_item']}: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Erro ao adicionar material {material_data['nome_item']}: {str(e)}", "ERROR")
        
        if success_count == len(materiais_orcamento):
            self.log(f"✅ Todos os {success_count} materiais adicionados ao orçamento com cálculos corretos")
            return True
        else:
            self.log(f"⚠️ Apenas {success_count}/{len(materiais_orcamento)} materiais adicionados", "WARNING")
            return success_count > 0
    
    def test_list_orcamento_materiais(self):
        """8. Listar materiais do orçamento"""
        self.log("=== TESTE 8: LISTAR MATERIAIS DO ORÇAMENTO ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais")
            
            if response.status_code == 200:
                result = response.json()
                materiais = result['materiais']
                total_materiais = result['total_materiais']
                
                self.log(f"✅ Materiais do orçamento listados: {len(materiais)} materiais")
                self.log(f"✅ Total de materiais: R$ {total_materiais:.2f}")
                
                # Verificar se o total está correto
                total_calculado = sum(m['preco_total_item'] for m in materiais)
                
                if abs(total_calculado - total_materiais) < 0.01:
                    self.log("✅ Total de materiais calculado corretamente")
                    return True
                else:
                    self.log(f"❌ Erro no cálculo do total: Esperado R$ {total_calculado:.2f}, Recebido R$ {total_materiais:.2f}", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao listar materiais do orçamento: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao listar materiais do orçamento: {str(e)}", "ERROR")
            return False
    
    def test_remove_material_from_orcamento(self):
        """9. Remover material do orçamento"""
        self.log("=== TESTE 9: REMOVER MATERIAL DO ORÇAMENTO ===")
        
        if not self.orcamento_materiais:
            self.log("❌ Nenhum material no orçamento para remover", "ERROR")
            return False
        
        try:
            material_id_to_remove = self.orcamento_materiais[0]
            response = self.session.delete(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais/{material_id_to_remove}")
            
            if response.status_code == 200:
                self.log(f"✅ Material removido do orçamento com sucesso")
                self.orcamento_materiais.remove(material_id_to_remove)
                return True
            else:
                self.log(f"❌ Erro ao remover material: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao remover material: {str(e)}", "ERROR")
            return False
    
    def test_update_material(self):
        """10. Atualizar material do catálogo"""
        self.log("=== TESTE 10: ATUALIZAR MATERIAL ===")
        
        if not self.materiais_criados:
            self.log("❌ Nenhum material para atualizar", "ERROR")
            return False
        
        try:
            material_id = self.materiais_criados[2]['id']  # Massa Corrida
            update_data = {
                "nome_item": "Massa Corrida Premium",
                "descricao": "Massa corrida premium para acabamento fino de paredes",
                "unidade": "kg",
                "preco_compra_base": 15.00  # Preço atualizado
            }
            
            response = self.session.put(f"{BASE_URL}/materiais/{material_id}", json=update_data)
            
            if response.status_code == 200:
                self.log(f"✅ Material atualizado: {update_data['nome_item']} - Novo preço: R$ {update_data['preco_compra_base']:.2f}")
                return True
            else:
                self.log(f"❌ Erro ao atualizar material: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao atualizar material: {str(e)}", "ERROR")
            return False
    
    def test_generate_pdf(self):
        """11. Gerar PDF do orçamento"""
        self.log("=== TESTE 11: GERAR PDF DO ORÇAMENTO ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/orcamento/{self.orcamento_id}/pdf")
            
            if response.status_code == 200:
                content_length = len(response.content)
                if content_length > 1000:  # PDF deve ter pelo menos 1KB
                    self.log(f"✅ PDF gerado com sucesso: {content_length} bytes")
                    
                    # Verificar se é realmente um PDF
                    if response.content.startswith(b'%PDF'):
                        self.log("✅ Arquivo PDF válido gerado")
                        return True
                    else:
                        self.log("❌ Arquivo gerado não é um PDF válido", "ERROR")
                        return False
                else:
                    self.log(f"❌ PDF muito pequeno: {content_length} bytes", "ERROR")
                    return False
            else:
                self.log(f"❌ Erro ao gerar PDF: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao gerar PDF: {str(e)}", "ERROR")
            return False
    
    def test_delete_material(self):
        """12. Deletar material do catálogo"""
        self.log("=== TESTE 12: DELETAR MATERIAL ===")
        
        if len(self.materiais_criados) < 3:
            self.log("❌ Material insuficiente para deletar", "ERROR")
            return False
        
        try:
            material_id = self.materiais_criados[2]['id']  # Massa Corrida Premium
            response = self.session.delete(f"{BASE_URL}/materiais/{material_id}")
            
            if response.status_code == 200:
                self.log(f"✅ Material deletado com sucesso")
                return True
            else:
                self.log(f"❌ Erro ao deletar material: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro ao deletar material: {str(e)}", "ERROR")
            return False
    
    # ========== NOVOS TESTES PARA AUDITORIA COMPLETA ==========
    
    def test_health_check(self):
        """0. Health Check da API"""
        self.log("=== TESTE 0: HEALTH CHECK ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API respondendo: {data.get('message', 'OK')}")
                self.test_results["health_check"] = "✅ OK"
                return True
            else:
                self.log(f"❌ API não respondendo: {response.status_code}", "ERROR")
                self.test_results["health_check"] = f"❌ FALHOU - Status {response.status_code}"
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no health check: {str(e)}", "ERROR")
            self.test_results["health_check"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_auth_register(self):
        """Teste de registro de usuário"""
        self.log("=== TESTE: REGISTRO DE USUÁRIO ===")
        
        try:
            # Criar usuário único
            timestamp = int(datetime.now().timestamp())
            test_user = {
                "name": f"Usuário Teste {timestamp}",
                "email": f"teste{timestamp}@lucroliquido.com",
                "password": "senha123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Usuário registrado: {data.get('name')} (ID: {data.get('user_id')})")
                self.test_results["auth_register"] = "✅ OK"
                return True
            else:
                self.log(f"❌ Erro no registro: {response.status_code} - {response.text}", "ERROR")
                self.test_results["auth_register"] = f"❌ FALHOU - Status {response.status_code}"
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no registro: {str(e)}", "ERROR")
            self.test_results["auth_register"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_companies_crud(self):
        """Teste CRUD completo de empresas"""
        self.log("=== TESTE: EMPRESAS CRUD ===")
        
        try:
            # 1. Criar empresa
            company_data = {
                "user_id": self.user_data['user_id'],
                "name": "Empresa Teste Auditoria",
                "segment": "Construção Civil",
                "razao_social": "Empresa Teste Auditoria LTDA",
                "cnpj": "12.345.678/0001-90",
                "telefone_fixo": "(11) 3333-4444",
                "celular_whatsapp": "(11) 99999-8888",
                "email_empresa": "contato@empresateste.com"
            }
            
            response = self.session.post(f"{BASE_URL}/companies", json=company_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar empresa: {response.status_code}", "ERROR")
                self.test_results["companies_crud"] = f"❌ FALHOU - Criar empresa: {response.status_code}"
                return False
            
            result = response.json()
            company_id = result['company_id']
            self.log(f"✅ Empresa criada (ID: {company_id})")
            
            # 2. Listar empresas
            response = self.session.get(f"{BASE_URL}/companies/{self.user_data['user_id']}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar empresas: {response.status_code}", "ERROR")
                self.test_results["companies_crud"] = f"❌ FALHOU - Listar empresas: {response.status_code}"
                return False
            
            companies = response.json()
            self.log(f"✅ Empresas listadas: {len(companies)} encontradas")
            
            # 3. Buscar empresa específica
            response = self.session.get(f"{BASE_URL}/company/{company_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao buscar empresa: {response.status_code}", "ERROR")
                self.test_results["companies_crud"] = f"❌ FALHOU - Buscar empresa: {response.status_code}"
                return False
            
            company = response.json()
            self.log(f"✅ Empresa encontrada: {company['name']}")
            
            # 4. Atualizar empresa
            update_data = company_data.copy()
            update_data['name'] = "Empresa Teste Auditoria ATUALIZADA"
            
            response = self.session.put(f"{BASE_URL}/company/{company_id}", json=update_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao atualizar empresa: {response.status_code}", "ERROR")
                self.test_results["companies_crud"] = f"❌ FALHOU - Atualizar empresa: {response.status_code}"
                return False
            
            self.log("✅ Empresa atualizada com sucesso")
            self.test_results["companies_crud"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no CRUD de empresas: {str(e)}", "ERROR")
            self.test_results["companies_crud"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_orcamentos_crud_complete(self):
        """Teste CRUD completo de orçamentos"""
        self.log("=== TESTE: ORÇAMENTOS CRUD COMPLETO ===")
        
        try:
            # 1. Criar orçamento
            orcamento_data = {
                "empresa_id": self.empresa_id,
                "usuario_id": self.user_data['user_id'],
                "cliente_nome": "Cliente Teste Auditoria",
                "cliente_documento": "123.456.789-00",
                "cliente_email": "cliente@teste.com",
                "cliente_telefone": "(11) 98765-4321",
                "cliente_whatsapp": "11987654321",
                "cliente_endereco": "Rua Teste, 123 - São Paulo/SP",
                "tipo": "servico_m2",
                "descricao_servico_ou_produto": "Serviço de teste para auditoria completa do sistema",
                "area_m2": 100.0,
                "custo_total": 3000.00,
                "preco_minimo": 4000.00,
                "preco_sugerido": 4800.00,
                "preco_praticado": 4500.00,
                "validade_proposta": "2025-03-15",
                "condicoes_pagamento": "50% entrada + 50% na conclusão",
                "prazo_execucao": "20 dias úteis",
                "observacoes": "Orçamento de teste para auditoria completa"
            }
            
            response = self.session.post(f"{BASE_URL}/orcamentos", json=orcamento_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar orçamento: {response.status_code} - {response.text}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - Criar: {response.status_code}"
                return False
            
            result = response.json()
            self.orcamento_id = result['orcamento_id']
            numero_orcamento = result['numero_orcamento']
            self.log(f"✅ Orçamento criado: {numero_orcamento} (ID: {self.orcamento_id})")
            
            # 2. Listar orçamentos
            response = self.session.get(f"{BASE_URL}/orcamentos/{self.empresa_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar orçamentos: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - Listar: {response.status_code}"
                return False
            
            orcamentos = response.json()
            self.log(f"✅ Orçamentos listados: {len(orcamentos)} encontrados")
            
            # 3. Buscar orçamento específico
            response = self.session.get(f"{BASE_URL}/orcamento/{self.orcamento_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao buscar orçamento: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - Buscar: {response.status_code}"
                return False
            
            orcamento = response.json()
            self.log(f"✅ Orçamento encontrado: {orcamento['cliente_nome']}")
            
            # 4. Atualizar orçamento
            update_data = orcamento_data.copy()
            update_data['cliente_nome'] = "Cliente Teste ATUALIZADO"
            
            response = self.session.put(f"{BASE_URL}/orcamento/{self.orcamento_id}", json=update_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao atualizar orçamento: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - Atualizar: {response.status_code}"
                return False
            
            self.log("✅ Orçamento atualizado com sucesso")
            
            # 5. Gerar PDF
            response = self.session.get(f"{BASE_URL}/orcamento/{self.orcamento_id}/pdf")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao gerar PDF: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - PDF: {response.status_code}"
                return False
            
            if len(response.content) > 1000 and response.content.startswith(b'%PDF'):
                self.log(f"✅ PDF gerado com sucesso: {len(response.content)} bytes")
            else:
                self.log("❌ PDF inválido gerado", "ERROR")
                self.test_results["orcamentos_crud"] = "❌ FALHOU - PDF inválido"
                return False
            
            # 6. Gerar link WhatsApp
            response = self.session.post(f"{BASE_URL}/orcamento/{self.orcamento_id}/whatsapp")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao gerar link WhatsApp: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - WhatsApp: {response.status_code}"
                return False
            
            whatsapp_data = response.json()
            if 'pdf_url' in whatsapp_data and 'whatsapp_url' in whatsapp_data and 'token' in whatsapp_data:
                self.log("✅ Link WhatsApp gerado com sucesso")
                
                # 7. Testar acesso ao PDF público
                token = whatsapp_data['token']
                response = self.session.get(f"{BASE_URL}/orcamento/share/{token}")
                
                if response.status_code == 200 and len(response.content) > 1000:
                    self.log("✅ PDF público acessível via token")
                else:
                    self.log(f"❌ Erro no PDF público: {response.status_code}", "ERROR")
                    self.test_results["orcamentos_crud"] = f"❌ FALHOU - PDF público: {response.status_code}"
                    return False
            else:
                self.log("❌ Dados do WhatsApp incompletos", "ERROR")
                self.test_results["orcamentos_crud"] = "❌ FALHOU - WhatsApp incompleto"
                return False
            
            # 8. Deletar orçamento
            response = self.session.delete(f"{BASE_URL}/orcamento/{self.orcamento_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao deletar orçamento: {response.status_code}", "ERROR")
                self.test_results["orcamentos_crud"] = f"❌ FALHOU - Deletar: {response.status_code}"
                return False
            
            self.log("✅ Orçamento deletado com sucesso")
            self.test_results["orcamentos_crud"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no CRUD de orçamentos: {str(e)}", "ERROR")
            self.test_results["orcamentos_crud"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_materiais_crud_complete(self):
        """Teste CRUD completo de materiais"""
        self.log("=== TESTE: MATERIAIS CRUD COMPLETO ===")
        
        try:
            # 1. Criar material
            material_data = {
                "nome_item": "Material Teste Auditoria",
                "descricao": "Material criado para teste de auditoria completa",
                "unidade": "un",
                "preco_compra_base": 50.00
            }
            
            response = self.session.post(f"{BASE_URL}/materiais", json=material_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar material: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Criar: {response.status_code}"
                return False
            
            result = response.json()
            material_id = result['material_id']
            self.log(f"✅ Material criado (ID: {material_id})")
            
            # 2. Listar materiais
            response = self.session.get(f"{BASE_URL}/materiais")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar materiais: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Listar: {response.status_code}"
                return False
            
            materiais = response.json()
            self.log(f"✅ Materiais listados: {len(materiais)} encontrados")
            
            # 3. Buscar material (autocomplete)
            response = self.session.get(f"{BASE_URL}/materiais/buscar?q=Teste")
            
            if response.status_code != 200:
                self.log(f"❌ Erro na busca de materiais: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Buscar: {response.status_code}"
                return False
            
            resultados = response.json()
            self.log(f"✅ Busca de materiais: {len(resultados)} resultados")
            
            # 4. Buscar material específico
            response = self.session.get(f"{BASE_URL}/materiais/{material_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao buscar material específico: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Buscar específico: {response.status_code}"
                return False
            
            material = response.json()
            self.log(f"✅ Material específico encontrado: {material['nome_item']}")
            
            # 5. Atualizar material
            update_data = {
                "nome_item": "Material Teste Auditoria ATUALIZADO",
                "descricao": "Material atualizado para teste de auditoria",
                "unidade": "un",
                "preco_compra_base": 60.00
            }
            
            response = self.session.put(f"{BASE_URL}/materiais/{material_id}", json=update_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao atualizar material: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Atualizar: {response.status_code}"
                return False
            
            self.log("✅ Material atualizado com sucesso")
            
            # 6. Deletar material
            response = self.session.delete(f"{BASE_URL}/materiais/{material_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao deletar material: {response.status_code}", "ERROR")
                self.test_results["materiais_crud"] = f"❌ FALHOU - Deletar: {response.status_code}"
                return False
            
            self.log("✅ Material deletado com sucesso")
            self.test_results["materiais_crud"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no CRUD de materiais: {str(e)}", "ERROR")
            self.test_results["materiais_crud"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_materiais_orcamento_complete(self):
        """Teste completo de materiais no orçamento"""
        self.log("=== TESTE: MATERIAIS NO ORÇAMENTO ===")
        
        # Primeiro criar um orçamento para teste
        if not self.orcamento_id:
            if not self.test_create_orcamento():
                self.test_results["materiais_orcamento"] = "❌ FALHOU - Sem orçamento"
                return False
        
        try:
            # 1. Criar material para usar no orçamento
            material_data = {
                "nome_item": "Material para Orçamento",
                "descricao": "Material específico para teste de orçamento",
                "unidade": "m2",
                "preco_compra_base": 25.00
            }
            
            response = self.session.post(f"{BASE_URL}/materiais", json=material_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar material: {response.status_code}", "ERROR")
                self.test_results["materiais_orcamento"] = f"❌ FALHOU - Criar material: {response.status_code}"
                return False
            
            material_id = response.json()['material_id']
            
            # 2. Adicionar material ao orçamento
            orcamento_material_data = {
                "id_orcamento": self.orcamento_id,
                "id_material": material_id,
                "nome_item": "Material para Orçamento",
                "unidade": "m2",
                "preco_compra_fornecedor": 25.00,
                "percentual_acrescimo": 50.0,
                "quantidade": 10.0
            }
            
            response = self.session.post(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais", json=orcamento_material_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao adicionar material ao orçamento: {response.status_code}", "ERROR")
                self.test_results["materiais_orcamento"] = f"❌ FALHOU - Adicionar: {response.status_code}"
                return False
            
            result = response.json()
            orcamento_material_id = result['orcamento_material_id']
            self.log(f"✅ Material adicionado ao orçamento (ID: {orcamento_material_id})")
            
            # Verificar cálculos
            preco_esperado = 25.00 * 1.5  # 50% de acréscimo
            total_esperado = preco_esperado * 10.0
            
            if abs(result['preco_unitario_final'] - preco_esperado) < 0.01:
                self.log(f"✅ Cálculo correto: R$ {result['preco_unitario_final']:.2f}")
            else:
                self.log(f"❌ Erro no cálculo: esperado R$ {preco_esperado:.2f}, recebido R$ {result['preco_unitario_final']:.2f}", "ERROR")
                self.test_results["materiais_orcamento"] = "❌ FALHOU - Cálculo incorreto"
                return False
            
            # 3. Listar materiais do orçamento
            response = self.session.get(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar materiais do orçamento: {response.status_code}", "ERROR")
                self.test_results["materiais_orcamento"] = f"❌ FALHOU - Listar: {response.status_code}"
                return False
            
            result = response.json()
            materiais = result['materiais']
            total_materiais = result['total_materiais']
            
            self.log(f"✅ Materiais do orçamento listados: {len(materiais)} materiais, Total: R$ {total_materiais:.2f}")
            
            # 4. Remover material do orçamento
            response = self.session.delete(f"{BASE_URL}/orcamentos/{self.orcamento_id}/materiais/{orcamento_material_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao remover material do orçamento: {response.status_code}", "ERROR")
                self.test_results["materiais_orcamento"] = f"❌ FALHOU - Remover: {response.status_code}"
                return False
            
            self.log("✅ Material removido do orçamento com sucesso")
            self.test_results["materiais_orcamento"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro nos materiais do orçamento: {str(e)}", "ERROR")
            self.test_results["materiais_orcamento"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_contas_crud(self):
        """Teste CRUD de contas a pagar/receber"""
        self.log("=== TESTE: CONTAS A PAGAR/RECEBER ===")
        
        try:
            # 1. Criar conta a pagar
            conta_pagar_data = {
                "company_id": self.empresa_id,
                "user_id": self.user_data['user_id'],
                "tipo": "PAGAR",
                "descricao": "Conta de teste - Fornecedor XYZ",
                "categoria": "Matéria-prima",
                "data_emissao": "2025-01-15",
                "data_vencimento": "2025-02-15",
                "valor": 1500.00,
                "forma_pagamento": "PIX",
                "observacoes": "Conta criada para teste de auditoria"
            }
            
            response = self.session.post(f"{BASE_URL}/contas", json=conta_pagar_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar conta a pagar: {response.status_code}", "ERROR")
                self.test_results["contas_crud"] = f"❌ FALHOU - Criar pagar: {response.status_code}"
                return False
            
            conta_pagar_id = response.json().get('conta_id')
            self.log(f"✅ Conta a pagar criada (ID: {conta_pagar_id})")
            
            # 2. Criar conta a receber
            conta_receber_data = {
                "company_id": self.empresa_id,
                "user_id": self.user_data['user_id'],
                "tipo": "RECEBER",
                "descricao": "Conta de teste - Cliente ABC",
                "categoria": "Vendas de serviços",
                "data_emissao": "2025-01-15",
                "data_vencimento": "2025-02-15",
                "valor": 3000.00,
                "forma_pagamento": "Boleto",
                "observacoes": "Conta criada para teste de auditoria"
            }
            
            response = self.session.post(f"{BASE_URL}/contas", json=conta_receber_data)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar conta a receber: {response.status_code}", "ERROR")
                self.test_results["contas_crud"] = f"❌ FALHOU - Criar receber: {response.status_code}"
                return False
            
            conta_receber_id = response.json().get('conta_id')
            self.log(f"✅ Conta a receber criada (ID: {conta_receber_id})")
            
            # 3. Listar todas as contas
            response = self.session.get(f"{BASE_URL}/contas/{self.empresa_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar contas: {response.status_code}", "ERROR")
                self.test_results["contas_crud"] = f"❌ FALHOU - Listar: {response.status_code}"
                return False
            
            contas = response.json()
            self.log(f"✅ Contas listadas: {len(contas)} encontradas")
            
            # 4. Listar contas a pagar
            response = self.session.get(f"{BASE_URL}/contas/pagar/{self.empresa_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar contas a pagar: {response.status_code}", "ERROR")
                self.test_results["contas_crud"] = f"❌ FALHOU - Listar pagar: {response.status_code}"
                return False
            
            contas_pagar = response.json()
            self.log(f"✅ Contas a pagar listadas: {len(contas_pagar)} encontradas")
            
            # 5. Listar contas a receber
            response = self.session.get(f"{BASE_URL}/contas/receber/{self.empresa_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar contas a receber: {response.status_code}", "ERROR")
                self.test_results["contas_crud"] = f"❌ FALHOU - Listar receber: {response.status_code}"
                return False
            
            contas_receber = response.json()
            self.log(f"✅ Contas a receber listadas: {len(contas_receber)} encontradas")
            
            self.test_results["contas_crud"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no CRUD de contas: {str(e)}", "ERROR")
            self.test_results["contas_crud"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_transactions_crud(self):
        """Teste CRUD de lançamentos"""
        self.log("=== TESTE: LANÇAMENTOS (TRANSACTIONS) ===")
        
        try:
            # 1. Criar lançamento de receita
            transaction_receita = {
                "company_id": self.empresa_id,
                "user_id": self.user_data['user_id'],
                "type": "receita",
                "description": "Venda de serviço - Teste Auditoria",
                "amount": 5000.00,
                "category": "Vendas de serviços",
                "date": "2025-01-15",
                "status": "realizado",
                "notes": "Lançamento criado para teste de auditoria"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_receita)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar lançamento de receita: {response.status_code}", "ERROR")
                self.test_results["transactions_crud"] = f"❌ FALHOU - Criar receita: {response.status_code}"
                return False
            
            receita_id = response.json().get('transaction_id')
            self.log(f"✅ Lançamento de receita criado (ID: {receita_id})")
            
            # 2. Criar lançamento de custo
            transaction_custo = {
                "company_id": self.empresa_id,
                "user_id": self.user_data['user_id'],
                "type": "custo",
                "description": "Compra de material - Teste Auditoria",
                "amount": 1500.00,
                "category": "Matéria-prima",
                "date": "2025-01-15",
                "status": "realizado",
                "notes": "Lançamento criado para teste de auditoria"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_custo)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar lançamento de custo: {response.status_code}", "ERROR")
                self.test_results["transactions_crud"] = f"❌ FALHOU - Criar custo: {response.status_code}"
                return False
            
            custo_id = response.json().get('transaction_id')
            self.log(f"✅ Lançamento de custo criado (ID: {custo_id})")
            
            # 3. Criar lançamento de despesa
            transaction_despesa = {
                "company_id": self.empresa_id,
                "user_id": self.user_data['user_id'],
                "type": "despesa",
                "description": "Aluguel escritório - Teste Auditoria",
                "amount": 800.00,
                "category": "Aluguel e condomínio",
                "date": "2025-01-15",
                "status": "realizado",
                "notes": "Lançamento criado para teste de auditoria"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_despesa)
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao criar lançamento de despesa: {response.status_code}", "ERROR")
                self.test_results["transactions_crud"] = f"❌ FALHOU - Criar despesa: {response.status_code}"
                return False
            
            despesa_id = response.json().get('transaction_id')
            self.log(f"✅ Lançamento de despesa criado (ID: {despesa_id})")
            
            # 4. Listar lançamentos
            response = self.session.get(f"{BASE_URL}/transactions/{self.empresa_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao listar lançamentos: {response.status_code}", "ERROR")
                self.test_results["transactions_crud"] = f"❌ FALHOU - Listar: {response.status_code}"
                return False
            
            transactions = response.json()
            self.log(f"✅ Lançamentos listados: {len(transactions)} encontrados")
            
            self.test_results["transactions_crud"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no CRUD de lançamentos: {str(e)}", "ERROR")
            self.test_results["transactions_crud"] = f"❌ FALHOU - {str(e)}"
            return False
    
    def test_dashboard_api(self):
        """Teste da API do dashboard"""
        self.log("=== TESTE: DASHBOARD API ===")
        
        try:
            # Testar métricas do mês atual
            current_month = datetime.now().strftime('%Y-%m')
            
            response = self.session.get(f"{BASE_URL}/metrics/{self.empresa_id}/{current_month}")
            
            if response.status_code != 200:
                self.log(f"❌ Erro ao buscar métricas do dashboard: {response.status_code}", "ERROR")
                self.test_results["dashboard_api"] = f"❌ FALHOU - Status {response.status_code}"
                return False
            
            metrics = response.json()
            
            # Verificar se contém as métricas esperadas
            expected_keys = ['faturamento', 'custos', 'despesas', 'lucro_liquido']
            
            for key in expected_keys:
                if key not in metrics:
                    self.log(f"❌ Métrica '{key}' não encontrada no dashboard", "ERROR")
                    self.test_results["dashboard_api"] = f"❌ FALHOU - Métrica {key} ausente"
                    return False
            
            self.log(f"✅ Dashboard funcionando - Faturamento: R$ {metrics['faturamento']:.2f}, Lucro: R$ {metrics['lucro_liquido']:.2f}")
            self.test_results["dashboard_api"] = "✅ OK"
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na API do dashboard: {str(e)}", "ERROR")
            self.test_results["dashboard_api"] = f"❌ FALHOU - {str(e)}"
            return False

    def run_complete_audit(self):
        """Executar auditoria completa do sistema"""
        self.log("🚀 INICIANDO AUDITORIA COMPLETA DO SISTEMA PARA DEPLOY")
        self.log("=" * 80)
        
        # Lista de todos os testes obrigatórios
        tests = [
            ("Health Check", self.test_health_check),
            ("Autenticação - Login", self.test_login),
            ("Autenticação - Registro", self.test_auth_register),
            ("Empresas CRUD", self.test_companies_crud),
            ("Orçamentos CRUD Completo", self.test_orcamentos_crud_complete),
            ("Materiais CRUD Completo", self.test_materiais_crud_complete),
            ("Materiais no Orçamento", self.test_materiais_orcamento_complete),
            ("Contas a Pagar/Receber", self.test_contas_crud),
            ("Lançamentos (Transactions)", self.test_transactions_crud),
            ("Dashboard API", self.test_dashboard_api)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n🔍 Executando: {test_name}")
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: APROVADO")
                else:
                    failed += 1
                    self.log(f"❌ {test_name}: REPROVADO")
            except Exception as e:
                self.log(f"❌ Erro inesperado no teste {test_name}: {str(e)}", "ERROR")
                failed += 1
                self.test_results[test_name.lower().replace(" ", "_")] = f"❌ FALHOU - {str(e)}"
            
            self.log("-" * 80)
        
        # Relatório final detalhado
        self.log("\n📊 RELATÓRIO FINAL DA AUDITORIA")
        self.log("=" * 80)
        
        # Mostrar resultado de cada endpoint testado
        self.log("\n📋 RESULTADOS POR ENDPOINT:")
        for endpoint, result in self.test_results.items():
            self.log(f"  {endpoint.upper()}: {result}")
        
        self.log(f"\n📈 ESTATÍSTICAS:")
        self.log(f"  ✅ Testes Aprovados: {passed}")
        self.log(f"  ❌ Testes Reprovados: {failed}")
        self.log(f"  📊 Taxa de Sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        # Decisão final para deploy
        if failed == 0:
            self.log("\n🎉 SISTEMA APROVADO PARA DEPLOY!")
            self.log("   Todas as APIs principais estão funcionando corretamente.")
            self.log("   ✅ DEPLOY LIBERADO")
            return True
        else:
            self.log(f"\n⚠️ SISTEMA REPROVADO PARA DEPLOY!")
            self.log(f"   {failed} teste(s) falharam e precisam ser corrigidos.")
            self.log("   ❌ DEPLOY BLOQUEADO")
            return False

if __name__ == "__main__":
    tester = MaterialsModuleTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)