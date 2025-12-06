import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sidebar } from '@/components/Sidebar';
import { SubscriptionCard } from '@/components/SubscriptionCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { axiosInstance } from '../App';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import OrcamentoMateriais from '@/components/OrcamentoMateriais';

const EditarOrcamento = ({ user, onLogout }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [totalMateriais, setTotalMateriais] = useState(0);
  
  const [formData, setFormData] = useState({
    cliente_nome: '',
    cliente_documento: '',
    cliente_email: '',
    cliente_telefone: '',
    cliente_whatsapp: '',
    cliente_endereco: '',
    descricao_servico_ou_produto: '',
    area_m2: '',
    quantidade: '',
    custo_total: '',
    preco_minimo: '',
    preco_sugerido: '',
    preco_praticado: '',
    validade_proposta: '',
    condicoes_pagamento: '',
    prazo_execucao: '',
    observacoes: '',
  });

  const [orcamento, setOrcamento] = useState(null);

  useEffect(() => {
    fetchOrcamento();
  }, [id]);

  const fetchOrcamento = async () => {
    try {
      setLoadingData(true);
      const response = await axiosInstance.get(`/orcamento/${id}`);
      const data = response.data;
      
      setOrcamento(data);
      setFormData({
        cliente_nome: data.cliente_nome || '',
        cliente_documento: data.cliente_documento || '',
        cliente_email: data.cliente_email || '',
        cliente_telefone: data.cliente_telefone || '',
        cliente_whatsapp: data.cliente_whatsapp || '',
        cliente_endereco: data.cliente_endereco || '',
        descricao_servico_ou_produto: data.descricao_servico_ou_produto || '',
        area_m2: data.area_m2 || '',
        quantidade: data.quantidade || '',
        custo_total: data.custo_total || '',
        preco_minimo: data.preco_minimo || '',
        preco_sugerido: data.preco_sugerido || '',
        preco_praticado: data.preco_praticado || '',
        validade_proposta: data.validade_proposta || '',
        condicoes_pagamento: data.condicoes_pagamento || '',
        prazo_execucao: data.prazo_execucao || '',
        observacoes: data.observacoes || '',
      });
    } catch (error) {
      console.error('Erro ao carregar orçamento:', error);
      toast.error('Erro ao carregar orçamento');
      navigate('/orcamentos');
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.cliente_nome.trim()) {
      toast.error('Nome do cliente é obrigatório');
      return;
    }
    
    if (!formData.preco_praticado || parseFloat(formData.preco_praticado) <= 0) {
      toast.error('Valor praticado deve ser maior que zero');
      return;
    }

    try {
      setLoading(true);
      
      const updateData = {
        empresa_id: orcamento.empresa_id,
        usuario_id: orcamento.usuario_id,
        tipo: orcamento.tipo,
        ...formData,
        area_m2: formData.area_m2 ? parseFloat(formData.area_m2) : null,
        quantidade: formData.quantidade ? parseFloat(formData.quantidade) : null,
        custo_total: parseFloat(formData.custo_total) || 0,
        preco_minimo: parseFloat(formData.preco_minimo) || 0,
        preco_sugerido: parseFloat(formData.preco_sugerido) || 0,
        preco_praticado: parseFloat(formData.preco_praticado) || 0,
      };

      await axiosInstance.put(`/orcamento/${id}`, updateData);
      toast.success('Orçamento atualizado com sucesso!');
      navigate(`/orcamento/${id}`);
    } catch (error) {
      console.error('Erro ao atualizar orçamento:', error);
      toast.error('Erro ao atualizar orçamento');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  if (loadingData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex">
        <Sidebar user={user} onLogout={onLogout} />
        <div className="flex-1 p-8 ml-0 lg:ml-64">
          <div className="text-center text-white">
            <p className="text-xl">Carregando orçamento...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="flex-1 p-4 lg:p-8 ml-0 lg:ml-64">
        <SubscriptionCard user={user} />
        
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <Button
                variant="ghost"
                onClick={() => navigate('/orcamentos')}
                className="text-white hover:bg-white/10 mb-4"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar para Orçamentos
              </Button>
              <h1 className="text-3xl font-bold text-white mb-2">
                Editar Orçamento
              </h1>
              <p className="text-purple-200">
                {orcamento?.numero_orcamento} - {formData.cliente_nome}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Dados do Cliente */}
            <Card>
              <CardHeader>
                <CardTitle>Dados do Cliente</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Nome do Cliente *</Label>
                    <Input
                      required
                      value={formData.cliente_nome}
                      onChange={(e) => handleChange('cliente_nome', e.target.value)}
                      placeholder="Nome completo"
                    />
                  </div>

                  <div>
                    <Label>CPF/CNPJ</Label>
                    <Input
                      value={formData.cliente_documento}
                      onChange={(e) => handleChange('cliente_documento', e.target.value)}
                      placeholder="000.000.000-00"
                    />
                  </div>

                  <div>
                    <Label>WhatsApp</Label>
                    <Input
                      value={formData.cliente_whatsapp}
                      onChange={(e) => handleChange('cliente_whatsapp', e.target.value)}
                      placeholder="(00) 00000-0000"
                    />
                  </div>

                  <div>
                    <Label>Telefone</Label>
                    <Input
                      value={formData.cliente_telefone}
                      onChange={(e) => handleChange('cliente_telefone', e.target.value)}
                      placeholder="(00) 0000-0000"
                    />
                  </div>

                  <div>
                    <Label>E-mail</Label>
                    <Input
                      type="email"
                      value={formData.cliente_email}
                      onChange={(e) => handleChange('cliente_email', e.target.value)}
                      placeholder="cliente@email.com"
                    />
                  </div>

                  <div>
                    <Label>Endereço</Label>
                    <Input
                      value={formData.cliente_endereco}
                      onChange={(e) => handleChange('cliente_endereco', e.target.value)}
                      placeholder="Endereço completo"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Descrição do Serviço */}
            <Card>
              <CardHeader>
                <CardTitle>Descrição do Serviço/Produto</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Descrição *</Label>
                  <Textarea
                    required
                    value={formData.descricao_servico_ou_produto}
                    onChange={(e) => handleChange('descricao_servico_ou_produto', e.target.value)}
                    placeholder="Descreva o serviço ou produto..."
                    rows={4}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {orcamento?.tipo === 'servico_m2' && (
                    <div>
                      <Label>Área (m²)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.area_m2}
                        onChange={(e) => handleChange('area_m2', e.target.value)}
                        placeholder="0.00"
                      />
                    </div>
                  )}

                  {(orcamento?.tipo === 'produto' || orcamento?.tipo === 'servico_hora') && (
                    <div>
                      <Label>Quantidade</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={formData.quantidade}
                        onChange={(e) => handleChange('quantidade', e.target.value)}
                        placeholder="0"
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Materiais */}
            <Card>
              <CardHeader>
                <CardTitle>Materiais do Orçamento</CardTitle>
              </CardHeader>
              <CardContent>
                <OrcamentoMateriais 
                  orcamentoId={id}
                  onTotalChange={(total) => setTotalMateriais(total)}
                />
              </CardContent>
            </Card>

            {/* Valores */}
            <Card>
              <CardHeader>
                <CardTitle>Valores</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Custo Total (R$)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.custo_total}
                      onChange={(e) => handleChange('custo_total', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <Label>Preço Mínimo (R$)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.preco_minimo}
                      onChange={(e) => handleChange('preco_minimo', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <Label>Preço Sugerido (R$)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.preco_sugerido}
                      onChange={(e) => handleChange('preco_sugerido', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <Label>Preço Praticado (R$) *</Label>
                    <Input
                      required
                      type="number"
                      step="0.01"
                      value={formData.preco_praticado}
                      onChange={(e) => handleChange('preco_praticado', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                </div>

                {totalMateriais > 0 && (
                  <div className="mt-4 p-4 bg-purple-600/20 rounded-lg border border-purple-500/30">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-white">Valor do Serviço:</span>
                      <span className="font-medium text-white">
                        R$ {parseFloat(formData.preco_praticado || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-white">Valor dos Materiais:</span>
                      <span className="font-medium text-white">
                        R$ {totalMateriais.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-purple-500/30">
                      <span className="text-base font-bold text-white">Valor Total:</span>
                      <span className="text-xl font-bold text-green-400">
                        R$ {(parseFloat(formData.preco_praticado || 0) + totalMateriais).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Condições Comerciais */}
            <Card>
              <CardHeader>
                <CardTitle>Condições Comerciais</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Validade da Proposta *</Label>
                    <Input
                      required
                      value={formData.validade_proposta}
                      onChange={(e) => handleChange('validade_proposta', e.target.value)}
                      placeholder="Ex: 30 dias ou 2025-12-31"
                    />
                  </div>

                  <div>
                    <Label>Prazo de Execução *</Label>
                    <Input
                      required
                      value={formData.prazo_execucao}
                      onChange={(e) => handleChange('prazo_execucao', e.target.value)}
                      placeholder="Ex: 15 dias úteis"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label>Condições de Pagamento *</Label>
                    <Input
                      required
                      value={formData.condicoes_pagamento}
                      onChange={(e) => handleChange('condicoes_pagamento', e.target.value)}
                      placeholder="Ex: 50% antecipado, 50% na entrega"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Label>Observações</Label>
                    <Textarea
                      value={formData.observacoes}
                      onChange={(e) => handleChange('observacoes', e.target.value)}
                      placeholder="Observações adicionais..."
                      rows={3}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Botões */}
            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/orcamentos')}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={loading}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
              >
                <Save className="w-4 h-4 mr-2" />
                {loading ? 'Salvando...' : 'Salvar Alterações'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditarOrcamento;
