import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, X, Search } from 'lucide-react';
import { axiosInstance } from '../App';
import { toast } from 'sonner';

const OrcamentoMateriais = ({ orcamentoId, onTotalChange }) => {
  const [materiais, setMateriais] = useState([]);
  const [materiaisCatalogo, setMateriaisCatalogo] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [filteredCatalogo, setFilteredCatalogo] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Campos para novo material
  const [novoMaterial, setNovoMaterial] = useState({
    nome_item: '',
    descricao_customizada: '',
    unidade: 'un',
    preco_compra_fornecedor: '',
    percentual_acrescimo: '30',
    quantidade: '1',
  });

  // Carregar materiais do orçamento (se já existir)
  const fetchMateriaisOrcamento = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/orcamentos/${orcamentoId}/materiais`);
      setMateriais(response.data.materiais || []);
    } catch (error) {
      console.error('Erro ao carregar materiais do orçamento:', error);
    }
  }, [orcamentoId]);

  // Carregar catálogo de materiais
  useEffect(() => {
    fetchCatalogoMateriais();
  }, []);

  // Carregar materiais do orçamento quando o ID mudar
  useEffect(() => {
    if (orcamentoId) {
      fetchMateriaisOrcamento();
    }
  }, [orcamentoId, fetchMateriaisOrcamento]);

  // Filtrar catálogo quando buscar
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredCatalogo([]);
    } else {
      const filtered = materiaisCatalogo.filter(mat =>
        mat.nome_item.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredCatalogo(filtered.slice(0, 5)); // Mostrar apenas 5 resultados
    }
  }, [searchTerm, materiaisCatalogo]);

  // Calcular total sempre que materiais mudarem
  useEffect(() => {
    const total = materiais.reduce((sum, mat) => sum + (mat.preco_total_item || 0), 0);
    if (onTotalChange) {
      onTotalChange(total);
    }
  }, [materiais, onTotalChange]);

  const fetchCatalogoMateriais = async () => {
    try {
      const response = await axiosInstance.get('/materiais');
      setMateriaisCatalogo(response.data);
    } catch (error) {
      console.error('Erro ao carregar catálogo de materiais:', error);
    }
  };

  const handleSelectMaterialCatalogo = (material) => {
    setNovoMaterial({
      ...novoMaterial,
      nome_item: material.nome_item,
      descricao_customizada: material.descricao || '',
      unidade: material.unidade,
      preco_compra_fornecedor: material.preco_compra_base.toString(),
      id_material: material.id,
    });
    setSearchTerm('');
    setShowSearch(false);
  };

  const calcularPrecoFinal = (precoCompra, percentualAcrescimo, quantidade) => {
    const preco = parseFloat(precoCompra) || 0;
    const percentual = parseFloat(percentualAcrescimo) || 0;
    const qtd = parseFloat(quantidade) || 0;
    
    const precoUnitario = preco * (1 + percentual / 100);
    const precoTotal = precoUnitario * qtd;
    
    return {
      precoUnitario: precoUnitario.toFixed(2),
      precoTotal: precoTotal.toFixed(2),
    };
  };

  const handleAdicionarMaterial = async () => {
    // Validações
    if (!novoMaterial.nome_item.trim()) {
      toast.error('Nome do item é obrigatório');
      return;
    }
    if (!novoMaterial.preco_compra_fornecedor || parseFloat(novoMaterial.preco_compra_fornecedor) <= 0) {
      toast.error('Preço de compra deve ser maior que zero');
      return;
    }
    if (!novoMaterial.quantidade || parseFloat(novoMaterial.quantidade) <= 0) {
      toast.error('Quantidade deve ser maior que zero');
      return;
    }

    // Se não tem orçamento ID, adiciona apenas localmente
    if (!orcamentoId) {
      const { precoUnitario, precoTotal } = calcularPrecoFinal(
        novoMaterial.preco_compra_fornecedor,
        novoMaterial.percentual_acrescimo,
        novoMaterial.quantidade
      );

      const materialLocal = {
        id: `temp-${Date.now()}`,
        nome_item: novoMaterial.nome_item,
        descricao_customizada: novoMaterial.descricao_customizada,
        unidade: novoMaterial.unidade,
        preco_compra_fornecedor: parseFloat(novoMaterial.preco_compra_fornecedor),
        percentual_acrescimo: parseFloat(novoMaterial.percentual_acrescimo),
        quantidade: parseFloat(novoMaterial.quantidade),
        preco_unitario_final: parseFloat(precoUnitario),
        preco_total_item: parseFloat(precoTotal),
        id_material: novoMaterial.id_material || null,
      };

      setMateriais([...materiais, materialLocal]);
      resetForm();
      toast.success('Material adicionado!');
      return;
    }

    // Se tem orçamento ID, salva no backend
    try {
      setLoading(true);
      const data = {
        id_orcamento: orcamentoId,
        id_material: novoMaterial.id_material || null,
        nome_item: novoMaterial.nome_item,
        descricao_customizada: novoMaterial.descricao_customizada,
        unidade: novoMaterial.unidade,
        preco_compra_fornecedor: parseFloat(novoMaterial.preco_compra_fornecedor),
        percentual_acrescimo: parseFloat(novoMaterial.percentual_acrescimo),
        quantidade: parseFloat(novoMaterial.quantidade),
      };

      await axiosInstance.post(`/orcamentos/${orcamentoId}/materiais`, data);
      toast.success('Material adicionado ao orçamento!');
      fetchMateriaisOrcamento();
      resetForm();
    } catch (error) {
      console.error('Erro ao adicionar material:', error);
      toast.error('Erro ao adicionar material');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoverMaterial = async (materialId) => {
    // Se não tem orçamento ID, remove apenas localmente
    if (!orcamentoId || materialId.toString().startsWith('temp-')) {
      setMateriais(materiais.filter(m => m.id !== materialId));
      toast.success('Material removido!');
      return;
    }

    // Se tem orçamento ID, remove do backend
    try {
      await axiosInstance.delete(`/orcamentos/${orcamentoId}/materiais/${materialId}`);
      toast.success('Material removido do orçamento!');
      fetchMateriaisOrcamento();
    } catch (error) {
      console.error('Erro ao remover material:', error);
      toast.error('Erro ao remover material');
    }
  };

  const resetForm = () => {
    setNovoMaterial({
      nome_item: '',
      descricao_customizada: '',
      unidade: 'un',
      preco_compra_fornecedor: '',
      percentual_acrescimo: '30',
      quantidade: '1',
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const totalMateriais = materiais.reduce((sum, mat) => sum + (mat.preco_total_item || 0), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold border-b border-zinc-700 pb-2 flex-1">
          Materiais do Serviço
        </h3>
        {totalMateriais > 0 && (
          <div className="text-right">
            <p className="text-xs text-zinc-400">Total de Materiais</p>
            <p className="text-lg font-bold text-green-400">{formatCurrency(totalMateriais)}</p>
          </div>
        )}
      </div>

      {/* Lista de materiais adicionados */}
      {materiais.length > 0 && (
        <div className="space-y-2">
          {materiais.map((material) => (
            <Card key={material.id} className="bg-zinc-800 border-zinc-700">
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{material.nome_item}</p>
                    {material.descricao_customizada && (
                      <p className="text-xs text-zinc-400">{material.descricao_customizada}</p>
                    )}
                    <div className="flex gap-4 text-xs text-zinc-400 mt-1">
                      <span>{material.quantidade} {material.unidade}</span>
                      <span>× {formatCurrency(material.preco_unitario_final)}</span>
                      <span className="font-bold text-white">= {formatCurrency(material.preco_total_item)}</span>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoverMaterial(material.id)}
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Formulário de adição */}
      <Card className="bg-zinc-800/50 border-zinc-700">
        <CardContent className="p-4 space-y-3">
          {/* Busca de material no catálogo */}
          <div className="relative">
            <Label>Material</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400 w-4 h-4" />
              <Input
                placeholder="Buscar no catálogo ou digitar novo material..."
                value={showSearch ? searchTerm : novoMaterial.nome_item}
                onChange={(e) => {
                  if (!showSearch) setShowSearch(true);
                  setSearchTerm(e.target.value);
                  setNovoMaterial({ ...novoMaterial, nome_item: e.target.value });
                }}
                onFocus={() => setShowSearch(true)}
                className="bg-zinc-900 border-zinc-700 pl-10"
              />
            </div>
            
            {/* Resultados da busca */}
            {showSearch && filteredCatalogo.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-zinc-900 border border-zinc-700 rounded-md shadow-lg max-h-48 overflow-y-auto">
                {filteredCatalogo.map((mat) => (
                  <button
                    key={mat.id}
                    type="button"
                    onClick={() => handleSelectMaterialCatalogo(mat)}
                    className="w-full text-left px-3 py-2 hover:bg-zinc-800 transition-colors"
                  >
                    <p className="font-medium text-sm">{mat.nome_item}</p>
                    <p className="text-xs text-zinc-400">{mat.unidade} - {formatCurrency(mat.preco_compra_base)}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <Label className="text-xs">Unidade</Label>
              <select
                value={novoMaterial.unidade}
                onChange={(e) => setNovoMaterial({ ...novoMaterial, unidade: e.target.value })}
                className="flex h-9 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1 text-sm"
              >
                <option value="un">Un</option>
                <option value="m">m</option>
                <option value="m²">m²</option>
                <option value="m³">m³</option>
                <option value="kg">kg</option>
                <option value="l">l</option>
                <option value="sc">sc</option>
                <option value="cx">cx</option>
                <option value="galão">Galão</option>
              </select>
            </div>

            <div>
              <Label className="text-xs">Qtd.</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={novoMaterial.quantidade}
                onChange={(e) => setNovoMaterial({ ...novoMaterial, quantidade: e.target.value })}
                className="bg-zinc-900 border-zinc-700 h-9"
              />
            </div>

            <div>
              <Label className="text-xs">Preço Compra (R$)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={novoMaterial.preco_compra_fornecedor}
                onChange={(e) => setNovoMaterial({ ...novoMaterial, preco_compra_fornecedor: e.target.value })}
                className="bg-zinc-900 border-zinc-700 h-9"
                placeholder="0.00"
              />
            </div>

            <div>
              <Label className="text-xs">% Acréscimo</Label>
              <Input
                type="number"
                step="1"
                min="0"
                value={novoMaterial.percentual_acrescimo}
                onChange={(e) => setNovoMaterial({ ...novoMaterial, percentual_acrescimo: e.target.value })}
                className="bg-zinc-900 border-zinc-700 h-9"
              />
            </div>
          </div>

          {novoMaterial.preco_compra_fornecedor && novoMaterial.quantidade && (
            <div className="flex justify-between items-center text-sm pt-2 border-t border-zinc-700">
              <span className="text-zinc-400">Preço Final para Cliente:</span>
              <span className="font-bold text-green-400">
                {formatCurrency(parseFloat(calcularPrecoFinal(
                  novoMaterial.preco_compra_fornecedor,
                  novoMaterial.percentual_acrescimo,
                  novoMaterial.quantidade
                ).precoTotal))}
              </span>
            </div>
          )}

          <Button
            type="button"
            onClick={handleAdicionarMaterial}
            disabled={loading}
            className="w-full bg-purple-600 hover:bg-purple-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            {loading ? 'Adicionando...' : 'Adicionar Material'}
          </Button>
        </CardContent>
      </Card>

      <p className="text-xs text-zinc-500">
        💡 Os preços de compra e % de acréscimo são internos e não aparecerão no PDF do cliente.
      </p>
    </div>
  );
};

export default OrcamentoMateriais;
