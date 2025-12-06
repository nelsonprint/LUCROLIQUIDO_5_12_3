import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { SubscriptionCard } from '@/components/SubscriptionCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { axiosInstance } from '../App';
import { toast } from 'sonner';
import { Download, MessageCircle, ArrowLeft, CheckCircle, XCircle, Edit2 } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

const OrcamentoDetalhe = ({ user, onLogout }) => {
  const [orcamento, setOrcamento] = useState(null);
  const [loading, setLoading] = useState(true);
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrcamento();
  }, [id]);

  const fetchOrcamento = async () => {
    try {
      const response = await axiosInstance.get(`/orcamento/${id}`);
      setOrcamento(response.data);
    } catch (error) {
      toast.error('Erro ao carregar orçamento');
      navigate('/orcamentos');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await axiosInstance.get(`/orcamento/${id}/pdf`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `orcamento_${orcamento.numero_orcamento}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('PDF baixado com sucesso!');
    } catch (error) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const handleEnviarWhatsApp = async () => {
    try {
      const whatsapp = orcamento.cliente_whatsapp?.replace(/\D/g, '');
      if (!whatsapp) {
        toast.error('Cliente não possui WhatsApp cadastrado');
        return;
      }

      toast.info('Gerando link do PDF...');

      // PASSO 1: Criar link público temporário do PDF
      const response = await axiosInstance.post(`/orcamento/${id}/whatsapp`);
      
      const { pdf_url, whatsapp_url, expires_in } = response.data;

      // PASSO 2: Atualizar status para ENVIADO
      await axiosInstance.patch(`/orcamento/${id}/status`, {
        status: 'ENVIADO',
        canal_envio: 'WhatsApp',
      });

      // PASSO 3: Abrir WhatsApp com mensagem + link do PDF
      window.open(whatsapp_url, '_blank');
      
      toast.success(`✅ WhatsApp aberto! Link do PDF válido por ${expires_in}.`);
      
      fetchOrcamento();
    } catch (error) {
      console.error('Erro ao enviar por WhatsApp:', error);
      toast.error('Erro ao preparar envio por WhatsApp');
    }
  };

  const handleChangeStatus = async (newStatus) => {
    try {
      await axiosInstance.patch(`/orcamento/${id}/status`, {
        status: newStatus,
      });
      toast.success('Status atualizado!');
      fetchOrcamento();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      RASCUNHO: 'default',
      ENVIADO: 'secondary',
      APROVADO: 'success',
      NAO_APROVADO: 'destructive',
    };

    const labels = {
      RASCUNHO: 'Rascunho',
      ENVIADO: 'Enviado',
      APROVADO: 'Aprovado',
      NAO_APROVADO: 'Não Aprovado',
    };

    return <Badge variant={variants[status] || 'default'}>{labels[status] || status}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-zinc-950 text-white">
        <Sidebar user={user} onLogout={onLogout} activePage="orcamentos" />
        <div className="flex-1 p-8 ml-64 flex items-center justify-center">
          <p className="text-zinc-400">Carregando orçamento...</p>
        </div>
      </div>
    );
  }

  if (!orcamento) return null;

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      <Sidebar user={user} onLogout={onLogout} activePage="orcamentos" />

      <div className="flex-1 p-8 ml-64">
        <div className="max-w-5xl mx-auto space-y-6">
          <SubscriptionCard user={user} />

          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => navigate('/orcamentos')}
                className="border-zinc-700"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar
              </Button>
              <div>
                <h1 className="text-3xl font-bold">Orçamento {orcamento.numero_orcamento}</h1>
                <p className="text-zinc-400 mt-1">Detalhes da proposta</p>
              </div>
            </div>
            {getStatusBadge(orcamento.status)}
          </div>

          {/* Ações Rápidas */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => navigate(`/orcamento/${id}/editar`)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Edit2 className="w-4 h-4 mr-2" />
                  Editar Orçamento
                </Button>
                
                <Button
                  onClick={handleDownloadPDF}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Baixar PDF
                </Button>
                
                <Button
                  onClick={handleEnviarWhatsApp}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Enviar WhatsApp
                </Button>

                {orcamento.status === 'ENVIADO' && (
                  <>
                    <Button
                      onClick={() => handleChangeStatus('APROVADO')}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Marcar como Aprovado
                    </Button>
                    
                    <Button
                      onClick={() => handleChangeStatus('NAO_APROVADO')}
                      variant="outline"
                      className="border-red-600 text-red-600 hover:bg-red-600 hover:text-white"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Marcar como Não Aprovado
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Dados do Cliente */}
          <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-blue-500">
            <CardHeader>
              <CardTitle>Dados do Cliente</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-zinc-400">Nome</p>
                <p className="font-medium">{orcamento.cliente_nome}</p>
              </div>
              {orcamento.cliente_documento && (
                <div>
                  <p className="text-sm text-zinc-400">CPF/CNPJ</p>
                  <p className="font-medium">{orcamento.cliente_documento}</p>
                </div>
              )}
              {orcamento.cliente_whatsapp && (
                <div>
                  <p className="text-sm text-zinc-400">WhatsApp</p>
                  <p className="font-medium">{orcamento.cliente_whatsapp}</p>
                </div>
              )}
              {orcamento.cliente_email && (
                <div>
                  <p className="text-sm text-zinc-400">E-mail</p>
                  <p className="font-medium">{orcamento.cliente_email}</p>
                </div>
              )}
              {orcamento.cliente_endereco && (
                <div className="md:col-span-2">
                  <p className="text-sm text-zinc-400">Endereço</p>
                  <p className="font-medium">{orcamento.cliente_endereco}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Descrição do Serviço/Produto */}
          <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-green-500">
            <CardHeader>
              <CardTitle>Descrição do Serviço/Produto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="font-medium text-lg">{orcamento.descricao_servico_ou_produto}</p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-zinc-800">
                {orcamento.area_m2 && (
                  <div>
                    <p className="text-sm text-zinc-400">Área</p>
                    <p className="font-medium">{orcamento.area_m2} m²</p>
                  </div>
                )}
                {orcamento.quantidade && (
                  <div>
                    <p className="text-sm text-zinc-400">Quantidade</p>
                    <p className="font-medium">{orcamento.quantidade}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Valores */}
          <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-purple-500">
            <CardHeader>
              <CardTitle>Valores</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-zinc-800 rounded-lg">
                  <p className="text-sm text-zinc-400 mb-1">Custo Total</p>
                  <p className="text-xl font-bold">
                    R$ {parseFloat(orcamento.custo_total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>

                <div className="p-4 bg-zinc-800 rounded-lg">
                  <p className="text-sm text-zinc-400 mb-1">Preço Mínimo</p>
                  <p className="text-xl font-bold text-yellow-500">
                    R$ {parseFloat(orcamento.preco_minimo).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>

                <div className="p-4 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-lg border border-purple-500/30">
                  <p className="text-sm text-zinc-400 mb-1">Valor da Proposta</p>
                  <p className="text-2xl font-bold text-green-400">
                    R$ {parseFloat(orcamento.preco_praticado).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Condições Comerciais */}
          <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-orange-500">
            <CardHeader>
              <CardTitle>Condições Comerciais</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-zinc-400">Validade da Proposta</p>
                <p className="font-medium">{orcamento.validade_proposta}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-400">Prazo de Execução</p>
                <p className="font-medium">{orcamento.prazo_execucao}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-sm text-zinc-400">Condições de Pagamento</p>
                <p className="font-medium">{orcamento.condicoes_pagamento}</p>
              </div>
              {orcamento.observacoes && (
                <div className="md:col-span-2">
                  <p className="text-sm text-zinc-400">Observações</p>
                  <p className="font-medium">{orcamento.observacoes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Histórico */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Histórico</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-400">Criado em:</span>
                <span>{new Date(orcamento.created_at).toLocaleString('pt-BR')}</span>
              </div>
              {orcamento.enviado_em && (
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Enviado em:</span>
                  <span>{new Date(orcamento.enviado_em).toLocaleString('pt-BR')}</span>
                </div>
              )}
              {orcamento.aprovado_em && (
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Aprovado em:</span>
                  <span className="text-green-400">{new Date(orcamento.aprovado_em).toLocaleString('pt-BR')}</span>
                </div>
              )}
              {orcamento.nao_aprovado_em && (
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Não aprovado em:</span>
                  <span className="text-red-400">{new Date(orcamento.nao_aprovado_em).toLocaleString('pt-BR')}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default OrcamentoDetalhe;
