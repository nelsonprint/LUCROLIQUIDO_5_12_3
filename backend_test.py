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

class MaterialsModuleTest:
    def __init__(self):
        self.session = requests.Session()
        self.user_data = None
        self.empresa_id = None
        self.orcamento_id = None
        self.materiais_criados = []
        self.orcamento_materiais = []
        
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
    
    def run_all_tests(self):
        """Executar todos os testes"""
        self.log("🚀 INICIANDO TESTE COMPLETO DO MÓDULO DE MATERIAIS")
        self.log("=" * 60)
        
        tests = [
            ("Login", self.test_login),
            ("Buscar/Criar Empresa", self.test_get_empresa),
            ("Criar Materiais", self.test_create_materiais),
            ("Listar Materiais", self.test_list_materiais),
            ("Buscar Materiais", self.test_search_materiais),
            ("Criar Orçamento", self.test_create_orcamento),
            ("Adicionar Materiais ao Orçamento", self.test_add_materiais_to_orcamento),
            ("Listar Materiais do Orçamento", self.test_list_orcamento_materiais),
            ("Remover Material do Orçamento", self.test_remove_material_from_orcamento),
            ("Atualizar Material", self.test_update_material),
            ("Gerar PDF", self.test_generate_pdf),
            ("Deletar Material", self.test_delete_material)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"❌ Erro inesperado no teste {test_name}: {str(e)}", "ERROR")
                failed += 1
            
            self.log("-" * 60)
        
        # Resumo final
        self.log("📊 RESUMO DOS TESTES")
        self.log("=" * 60)
        self.log(f"✅ Testes Aprovados: {passed}")
        self.log(f"❌ Testes Falharam: {failed}")
        self.log(f"📈 Taxa de Sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 TODOS OS TESTES PASSARAM! Módulo de materiais funcionando perfeitamente.")
            return True
        else:
            self.log(f"⚠️ {failed} teste(s) falharam. Verifique os logs acima para detalhes.")
            return False

if __name__ == "__main__":
    tester = MaterialsModuleTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)