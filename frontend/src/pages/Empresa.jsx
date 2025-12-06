import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { SubscriptionCard } from '@/components/SubscriptionCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { axiosInstance } from '../App';
import { toast } from 'sonner';
import { Building2, MapPin, Phone, Save } from 'lucide-react';

const Empresa = ({ user, onLogout }) => {
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    segment: '',
    razao_social: '',
    nome_fantasia: '',
    cnpj: '',
    inscricao_estadual: '',
    inscricao_municipal: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
    cep: '',
    telefone_fixo: '',
    celular_whatsapp: '',
    email_empresa: '',
    site: '',
    contato_principal: '',
  });

  const [company, setCompany] = useState(JSON.parse(localStorage.getItem('company') || '{}'));

  useEffect(() => {
    fetchCompanyData();
  }, []);

  const fetchCompanyData = async () => {
    setLoadingData(true);
    
    try {
      // Se não há empresa no localStorage, buscar do backend
      if (!company.id) {
        const companiesResponse = await axiosInstance.get(`/companies/${user.id}`);
        if (companiesResponse.data && companiesResponse.data.length > 0) {
          const companyData = companiesResponse.data[0];
          localStorage.setItem('company', JSON.stringify(companyData));
          setCompany(companyData);
          
          // Preencher formulário com dados da empresa
          setFormData({
            name: companyData.name || '',
            segment: companyData.segment || '',
            razao_social: companyData.razao_social || '',
            nome_fantasia: companyData.nome_fantasia || '',
            cnpj: companyData.cnpj || '',
            inscricao_estadual: companyData.inscricao_estadual || '',
            inscricao_municipal: companyData.inscricao_municipal || '',
            logradouro: companyData.logradouro || '',
            numero: companyData.numero || '',
            complemento: companyData.complemento || '',
            bairro: companyData.bairro || '',
            cidade: companyData.cidade || '',
            estado: companyData.estado || '',
            cep: companyData.cep || '',
            telefone_fixo: companyData.telefone_fixo || '',
            celular_whatsapp: companyData.celular_whatsapp || '',
            email_empresa: companyData.email_empresa || '',
            site: companyData.site || '',
            contato_principal: companyData.contato_principal || '',
          });
        } else {
          // Nenhuma empresa encontrada - deixar formulário vazio para criar nova
          setLoadingData(false);
          return;
        }
      } else {
        // Já tem empresa no localStorage, buscar dados atualizados
        const response = await axiosInstance.get(`/company/${company.id}`);
        setFormData({
          name: response.data.name || '',
          segment: response.data.segment || '',
          razao_social: response.data.razao_social || '',
          nome_fantasia: response.data.nome_fantasia || '',
          cnpj: response.data.cnpj || '',
          inscricao_estadual: response.data.inscricao_estadual || '',
          inscricao_municipal: response.data.inscricao_municipal || '',
          logradouro: response.data.logradouro || '',
          numero: response.data.numero || '',
          complemento: response.data.complemento || '',
          bairro: response.data.bairro || '',
          cidade: response.data.cidade || '',
          estado: response.data.estado || '',
          cep: response.data.cep || '',
          telefone_fixo: response.data.telefone_fixo || '',
          celular_whatsapp: response.data.celular_whatsapp || '',
          email_empresa: response.data.email_empresa || '',
          site: response.data.site || '',
          contato_principal: response.data.contato_principal || '',
        });
      }
    } catch (error) {
      console.error('Erro ao carregar empresa:', error);
      toast.error('Erro ao carregar dados da empresa');
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axiosInstance.put(`/company/${company.id}`, {
        user_id: (user?.id || user?.user_id),
        ...formData,
      });
      toast.success('Dados da empresa atualizados com sucesso!');
      
      // Atualizar localStorage
      const updatedCompany = { ...company, name: formData.name, segment: formData.segment };
      localStorage.setItem('company', JSON.stringify(updatedCompany));
    } catch (error) {
      toast.error('Erro ao atualizar dados da empresa');
    } finally {
      setLoading(false);
    }
  };

  const formatCNPJ = (value) => {
    return value
      .replace(/\D/g, '')
      .replace(/(\d{2})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1/$2')
      .replace(/(\d{4})(\d)/, '$1-$2')
      .replace(/(-\d{2})\d+?$/, '$1');
  };

  const formatCEP = (value) => {
    return value
      .replace(/\D/g, '')
      .replace(/(\d{5})(\d)/, '$1-$2')
      .replace(/(-\d{3})\d+?$/, '$1');
  };

  const formatPhone = (value) => {
    return value
      .replace(/\D/g, '')
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{5})(\d)/, '$1-$2')
      .replace(/(-\d{4})\d+?$/, '$1');
  };

  if (loadingData) {
    return (
      <div className="flex min-h-screen bg-zinc-950 text-white">
        <Sidebar user={user} onLogout={onLogout} activePage="empresa" />
        <div className="flex-1 p-8 ml-64 flex items-center justify-center">
          <p className="text-zinc-400">Carregando dados da empresa...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-zinc-950 text-white">
      <Sidebar user={user} onLogout={onLogout} activePage="empresa" />

      <div className="flex-1 p-8 ml-64">
        <div className="max-w-6xl mx-auto space-y-6">
          <SubscriptionCard user={user} />

          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">Dados da Empresa</h1>
              <p className="text-zinc-400 mt-1">Gerencie as informações da sua empresa</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Card 1: Dados da Empresa */}
            <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-blue-500">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Building2 className="w-5 h-5 mr-2" />
                  Dados da Empresa
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Nome da Empresa *</Label>
                  <Input
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Segmento *</Label>
                  <Select
                    value={formData.segment}
                    onValueChange={(value) => setFormData({ ...formData, segment: value })}
                    required
                  >
                    <SelectTrigger className="bg-zinc-800 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="comercio">Comércio</SelectItem>
                      <SelectItem value="servicos">Serviços</SelectItem>
                      <SelectItem value="industria">Indústria</SelectItem>
                      <SelectItem value="tecnologia">Tecnologia</SelectItem>
                      <SelectItem value="consultoria">Consultoria</SelectItem>
                      <SelectItem value="construcao">Construção</SelectItem>
                      <SelectItem value="saude">Saúde</SelectItem>
                      <SelectItem value="educacao">Educação</SelectItem>
                      <SelectItem value="outro">Outro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Razão Social</Label>
                  <Input
                    value={formData.razao_social}
                    onChange={(e) => setFormData({ ...formData, razao_social: e.target.value })}
                    placeholder="Empresa LTDA"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Nome Fantasia</Label>
                  <Input
                    value={formData.nome_fantasia}
                    onChange={(e) => setFormData({ ...formData, nome_fantasia: e.target.value })}
                    placeholder="Nome comercial"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>CNPJ</Label>
                  <Input
                    value={formData.cnpj}
                    onChange={(e) => setFormData({ ...formData, cnpj: formatCNPJ(e.target.value) })}
                    placeholder="00.000.000/0000-00"
                    maxLength={18}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Inscrição Estadual</Label>
                  <Input
                    value={formData.inscricao_estadual}
                    onChange={(e) => setFormData({ ...formData, inscricao_estadual: e.target.value })}
                    placeholder="000.000.000.000"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Inscrição Municipal</Label>
                  <Input
                    value={formData.inscricao_municipal}
                    onChange={(e) => setFormData({ ...formData, inscricao_municipal: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Card 2: Endereço */}
            <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-green-500">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2" />
                  Endereço
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <Label>Logradouro</Label>
                  <Input
                    value={formData.logradouro}
                    onChange={(e) => setFormData({ ...formData, logradouro: e.target.value })}
                    placeholder="Rua, Avenida, etc."
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Número</Label>
                  <Input
                    value={formData.numero}
                    onChange={(e) => setFormData({ ...formData, numero: e.target.value })}
                    placeholder="123"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Complemento</Label>
                  <Input
                    value={formData.complemento}
                    onChange={(e) => setFormData({ ...formData, complemento: e.target.value })}
                    placeholder="Sala, Apto, etc."
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Bairro</Label>
                  <Input
                    value={formData.bairro}
                    onChange={(e) => setFormData({ ...formData, bairro: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Cidade</Label>
                  <Input
                    value={formData.cidade}
                    onChange={(e) => setFormData({ ...formData, cidade: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Estado (UF)</Label>
                  <Input
                    value={formData.estado}
                    onChange={(e) => setFormData({ ...formData, estado: e.target.value.toUpperCase() })}
                    placeholder="SP"
                    maxLength={2}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>CEP</Label>
                  <Input
                    value={formData.cep}
                    onChange={(e) => setFormData({ ...formData, cep: formatCEP(e.target.value) })}
                    placeholder="00000-000"
                    maxLength={9}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Card 3: Contatos */}
            <Card className="bg-zinc-900 border-zinc-800 border-l-4 border-l-purple-500">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Phone className="w-5 h-5 mr-2" />
                  Contatos
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Telefone Fixo</Label>
                  <Input
                    value={formData.telefone_fixo}
                    onChange={(e) => setFormData({ ...formData, telefone_fixo: formatPhone(e.target.value) })}
                    placeholder="(00) 0000-0000"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Celular / WhatsApp</Label>
                  <Input
                    value={formData.celular_whatsapp}
                    onChange={(e) => setFormData({ ...formData, celular_whatsapp: formatPhone(e.target.value) })}
                    placeholder="(00) 00000-0000"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>E-mail da Empresa</Label>
                  <Input
                    type="email"
                    value={formData.email_empresa}
                    onChange={(e) => setFormData({ ...formData, email_empresa: e.target.value })}
                    placeholder="contato@empresa.com"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div>
                  <Label>Site</Label>
                  <Input
                    value={formData.site}
                    onChange={(e) => setFormData({ ...formData, site: e.target.value })}
                    placeholder="www.empresa.com"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>

                <div className="md:col-span-2">
                  <Label>Nome do Contato Principal</Label>
                  <Input
                    value={formData.contato_principal}
                    onChange={(e) => setFormData({ ...formData, contato_principal: e.target.value })}
                    placeholder="Nome do responsável"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Botão Salvar */}
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={loading}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-8"
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

export default Empresa;