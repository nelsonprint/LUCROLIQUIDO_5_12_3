import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { SubscriptionCard } from '@/components/SubscriptionCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Package, Search, Edit, Trash2, Plus } from 'lucide-react';
import { axiosInstance } from '../App';
import { toast } from 'sonner';

const Materiais = ({ user, onLogout }) => {
  const [materiais, setMateriais] = useState([]);
  const [filteredMateriais, setFilteredMateriais] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  
  const [formData, setFormData] = useState({
    nome_item: '',
    descricao: '',
    unidade: 'un',
    preco_compra_base: '',
  });

  // Carregar materiais
  useEffect(() => {
    fetchMateriais();
  }, []);

  // Filtrar materiais quando o termo de busca mudar
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredMateriais(materiais);
    } else {
      const filtered = materiais.filter(mat =>
        mat.nome_item.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (mat.descricao && mat.descricao.toLowerCase().includes(searchTerm.toLowerCase()))
      );
      setFilteredMateriais(filtered);
    }
  }, [searchTerm, materiais]);

  const fetchMateriais = async () => {
    try {
      setLoading(true);
      const response = await axiosInstance.get('/materiais');
      setMateriais(response.data);
      setFilteredMateriais(response.data);
    } catch (error) {
      console.error('Erro ao carregar materiais:', error);
      toast.error('Erro ao carregar materiais');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validações
    if (!formData.nome_item.trim()) {
      toast.error('Nome do item é obrigatório');
      return;
    }
    if (!formData.preco_compra_base || parseFloat(formData.preco_compra_base) <= 0) {
      toast.error('Preço de compra deve ser maior que zero');
      return;
    }

    try {
      const data = {
        ...formData,
        preco_compra_base: parseFloat(formData.preco_compra_base),
      };

      if (editingMaterial) {
        // Atualizar
        await axiosInstance.put(`/materiais/${editingMaterial.id}`, data);
        toast.success('Material atualizado com sucesso!');
      } else {
        // Criar
        await axiosInstance.post('/materiais', data);
        toast.success('Material criado com sucesso!');
      }

      setShowModal(false);
      resetForm();
      fetchMateriais();
    } catch (error) {
      console.error('Erro ao salvar material:', error);
      toast.error('Erro ao salvar material');
    }
  };

  const handleEdit = (material) => {
    setEditingMaterial(material);
    setFormData({
      nome_item: material.nome_item,
      descricao: material.descricao || '',
      unidade: material.unidade,
      preco_compra_base: material.preco_compra_base.toString(),
    });
    setShowModal(true);
  };

  const handleDelete = async (materialId) => {
    if (!window.confirm('Tem certeza que deseja excluir este material?')) {
      return;
    }

    try {
      await axiosInstance.delete(`/materiais/${materialId}`);
      toast.success('Material excluído com sucesso!');
      fetchMateriais();
    } catch (error) {
      console.error('Erro ao excluir material:', error);
      toast.error('Erro ao excluir material');
    }
  };

  const resetForm = () => {
    setFormData({
      nome_item: '',
      descricao: '',
      unidade: 'un',
      preco_compra_base: '',
    });
    setEditingMaterial(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900 flex">
      <Sidebar user={user} onLogout={onLogout} />
      
      <div className="flex-1 p-4 lg:p-8 ml-0 lg:ml-64">
        <SubscriptionCard user={user} />
        
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
              <Package className="w-8 h-8" />
              Catálogo de Materiais
            </h1>
            <p className="text-purple-200">
              Gerencie o catálogo de materiais para usar nos orçamentos
            </p>
          </div>

          {/* Actions Bar */}
          <Card className="mb-6">
            <CardContent className="p-4">
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    type="text"
                    placeholder="Buscar materiais..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button
                  onClick={() => setShowModal(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Material
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Lista de Materiais */}
          {loading ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-gray-500">Carregando materiais...</p>
              </CardContent>
            </Card>
          ) : filteredMateriais.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">
                  {searchTerm ? 'Nenhum material encontrado' : 'Nenhum material cadastrado'}
                </p>
                {!searchTerm && (
                  <Button
                    onClick={() => setShowModal(true)}
                    variant="outline"
                  >
                    Cadastrar primeiro material
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredMateriais.map((material) => (
                <Card key={material.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-start justify-between">
                      <span className="flex-1">{material.nome_item}</span>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(material)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(material.id)}
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardTitle>
                    {material.descricao && (
                      <CardDescription className="text-sm">
                        {material.descricao}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Unidade:</span>
                        <span className="font-medium">{material.unidade}</span>
                      </div>
                      <div className="flex justify-between items-center pt-2 border-t">
                        <span className="text-sm text-gray-600">Preço de Compra:</span>
                        <span className="font-bold text-lg text-purple-600">
                          {formatCurrency(material.preco_compra_base)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Modal de Criação/Edição */}
          <Dialog open={showModal} onOpenChange={handleCloseModal}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>
                  {editingMaterial ? 'Editar Material' : 'Novo Material'}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="nome_item">Nome do Item *</Label>
                  <Input
                    id="nome_item"
                    value={formData.nome_item}
                    onChange={(e) => setFormData({ ...formData, nome_item: e.target.value })}
                    placeholder="Ex: Tinta Acrílica Premium"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="descricao">Descrição</Label>
                  <Input
                    id="descricao"
                    value={formData.descricao}
                    onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                    placeholder="Detalhes do material (opcional)"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="unidade">Unidade *</Label>
                    <select
                      id="unidade"
                      value={formData.unidade}
                      onChange={(e) => setFormData({ ...formData, unidade: e.target.value })}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      required
                    >
                      <option value="un">Un (Unidade)</option>
                      <option value="m">m (Metro)</option>
                      <option value="m²">m² (Metro quadrado)</option>
                      <option value="m³">m³ (Metro cúbico)</option>
                      <option value="kg">kg (Quilograma)</option>
                      <option value="l">l (Litro)</option>
                      <option value="sc">sc (Saco)</option>
                      <option value="cx">cx (Caixa)</option>
                      <option value="galão">Galão</option>
                      <option value="pç">pç (Peça)</option>
                    </select>
                  </div>

                  <div>
                    <Label htmlFor="preco_compra_base">Preço de Compra (R$) *</Label>
                    <Input
                      id="preco_compra_base"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.preco_compra_base}
                      onChange={(e) => setFormData({ ...formData, preco_compra_base: e.target.value })}
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={handleCloseModal}>
                    Cancelar
                  </Button>
                  <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                    {editingMaterial ? 'Salvar' : 'Criar'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
};

export default Materiais;
