import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { TrendingUp, Target, Calculator, FileText, CheckCircle, ArrowRight, MessageCircle, DollarSign, AlertTriangle, BarChart, X } from 'lucide-react';
import { toast } from 'sonner';
import { axiosInstance } from '../App';

const LandingPage = ({ setUser }) => {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axiosInstance.post('/auth/login', loginData);
      
      if (response.data.user_id) {
        const user = {
          id: response.data.user_id,
          name: response.data.name,
          email: loginData.email,
          role: response.data.role,
        };
        
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        toast.success('Login realizado com sucesso!');
        setShowLoginModal(false);
      }
    } catch (error) {
      toast.error('Erro ao fazer login. Verifique suas credenciais.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axiosInstance.post('/auth/register', registerData);
      
      if (response.data.user_id) {
        const user = {
          id: response.data.user_id,
          name: registerData.name,
          email: registerData.email,
          role: 'user',
        };
        
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        toast.success('Conta criada com sucesso! Bem-vindo ao Lucro Líquido!');
        setShowRegisterModal(false);
      }
    } catch (error) {
      toast.error('Erro ao criar conta. Este email pode já estar cadastrado.');
    } finally {
      setLoading(false);
    }
  };

  const handleWhatsApp = () => {
    window.open('https://wa.link/1ku82x', '_blank');
  };

  return (
    <div className="min-h-screen gradient-background">
      {/* Header/Navigation */}
      <nav className="border-b border-white/10 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="text-purple-500" size={32} />
              <h1 className="text-2xl font-bold gradient-text">Lucro Líquido</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Button 
                onClick={handleWhatsApp}
                variant="outline" 
                className="hidden md:flex border-green-500/50 text-green-400 hover:bg-green-500/10"
              >
                <MessageCircle size={18} className="mr-2" />
                Falar agora pelo WhatsApp
              </Button>
              <Button 
                onClick={() => setShowLoginModal(true)}
                variant="outline" 
                className="border-purple-500/50"
              >
                Entrar
              </Button>
              <Button 
                onClick={() => setShowRegisterModal(true)}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                Teste Grátis 7 Dias
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Content */}
            <div className="space-y-8">
              {/* Headline */}
              <div className="space-y-4">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight">
                  Seu negócio está <span className="gradient-text">lucrando de verdade</span> ou só adiando o fechamento?
                </h1>
                
                {/* Subheadline */}
                <h2 className="text-lg sm:text-xl text-gray-300 leading-relaxed">
                  Ter vendas não significa ter lucro. Sem registros financeiros fiéis e análise inteligente, você vira refém do caixa – e entra exatamente na estatística das empresas que fecham por falta de controle.
                </h2>
              </div>

              {/* Parágrafo de Impacto */}
              <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-xl space-y-3">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="text-red-400 flex-shrink-0 mt-1" size={24} />
                  <div className="text-gray-200 space-y-3">
                    <p>
                      Você trabalha, vende, se esforça – mas no fim do mês o dinheiro some.
                    </p>
                    <p>
                      Mistura de contas pessoais com o caixa da empresa, preços mal calculados, custos crescendo sem você perceber… Esse é o roteiro clássico das empresas que nunca decolam ou morrem no meio do caminho.
                    </p>
                    <p className="font-semibold text-white">
                      O Lucro Líquido age como um analista financeiro digital: ele lê tudo o que você lança (custos, despesas, receitas, impostos) e mostra, com clareza brutal, onde seu lucro está vazando e o que fazer para estancar – mesmo que você já use um outro sistema hoje.
                    </p>
                  </div>
                </div>
              </div>

              {/* Lista de Benefícios */}
              <div className="space-y-4">
                <div className="flex items-start space-x-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all">
                  <BarChart className="text-purple-400 flex-shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="text-white font-semibold mb-1">Radiografia real do negócio</h3>
                    <p className="text-gray-400 text-sm">
                      Enxergue, em gráficos e indicadores, se sua empresa está indo para o lucro sustentável ou para o sufoco de caixa.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all">
                  <Calculator className="text-blue-400 flex-shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="text-white font-semibold mb-1">Preços calculados com markup correto</h3>
                    <p className="text-gray-400 text-sm">
                      Gere orçamentos de serviços com o markup ideal da sua empresa, garantindo margem real em cada venda.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all">
                  <Target className="text-green-400 flex-shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="text-white font-semibold mb-1">Pare de sustentar clientes e serviços que dão prejuízo</h3>
                    <p className="text-gray-400 text-sm">
                      Descubra quem e o quê está drenando o lucro todo mês, mesmo parecendo &ldquo;bom faturamento&rdquo;.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4 p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-all">
                  <FileText className="text-yellow-400 flex-shrink-0 mt-1" size={24} />
                  <div>
                    <h3 className="text-white font-semibold mb-1">Funciona junto com seu sistema atual</h3>
                    <p className="text-gray-400 text-sm">
                      Use o Lucro Líquido como uma camada extra de inteligência de lucro, acima do simples registro de lançamentos.
                    </p>
                  </div>
                </div>
              </div>

              {/* Teste Grátis Destacado */}
              <Card className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 border-2 border-purple-500/50">
                <CardContent className="p-6">
                  <div className="flex items-start space-x-4">
                    <CheckCircle className="text-green-400 flex-shrink-0 mt-1" size={28} />
                    <div className="space-y-3">
                      <h3 className="text-xl font-bold text-white">
                        Teste agora por 7 dias, sem custo e sem risco.
                      </h3>
                      <p className="text-gray-300">
                        Em uma semana você já consegue ver se está no caminho da expansão ou no da estatística de fechamento. Se não enxergar valor, é só não continuar. Simples assim.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  onClick={() => setShowRegisterModal(true)}
                  size="lg"
                  className="text-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg shadow-purple-500/50"
                >
                  Começar meu teste grátis de 7 dias
                  <ArrowRight size={20} className="ml-2" />
                </Button>
                
                <Button 
                  onClick={handleWhatsApp}
                  size="lg"
                  variant="outline"
                  className="text-lg border-green-500/50 text-green-400 hover:bg-green-500/10"
                >
                  <MessageCircle size={20} className="mr-2" />
                  Falar agora pelo WhatsApp
                </Button>
              </div>

              {/* Trust Indicators */}
              <div className="flex items-center space-x-6 text-sm text-gray-400">
                <div className="flex items-center space-x-2">
                  <CheckCircle size={16} className="text-green-400" />
                  <span>Sem cartão de crédito</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle size={16} className="text-green-400" />
                  <span>Cancele quando quiser</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle size={16} className="text-green-400" />
                  <span>Suporte incluído</span>
                </div>
              </div>
            </div>

            {/* Right Column - Visual/Mockup */}
            <div className="relative">
              {/* Mockup do Dashboard */}
              <div className="relative z-10">
                <Card className="glass border-white/10 overflow-hidden shadow-2xl">
                  <div className="p-6 space-y-4">
                    {/* Header do Mockup */}
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-white font-bold text-lg">Dashboard Financeiro</h3>
                        <p className="text-gray-400 text-sm">Análise em Tempo Real</p>
                      </div>
                      <div className="px-3 py-1 bg-green-500/20 rounded-full">
                        <span className="text-green-400 text-sm font-semibold">Lucro Positivo</span>
                      </div>
                    </div>

                    {/* Indicadores */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
                        <p className="text-gray-400 text-xs mb-1">Faturamento</p>
                        <p className="text-white text-2xl font-bold">R$ 125k</p>
                        <p className="text-green-400 text-xs mt-1">↗ +15% vs mês anterior</p>
                      </div>
                      <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                        <p className="text-gray-400 text-xs mb-1">Lucro Líquido</p>
                        <p className="text-white text-2xl font-bold">R$ 38k</p>
                        <p className="text-green-400 text-xs mt-1">30% de margem</p>
                      </div>
                    </div>

                    {/* Gráfico Simulado */}
                    <div className="h-48 bg-white/5 rounded-lg flex items-end justify-around p-4 space-x-2">
                      {[40, 55, 45, 70, 60, 80, 75, 90].map((height, i) => (
                        <div 
                          key={i}
                          className="flex-1 bg-gradient-to-t from-purple-600 to-blue-600 rounded-t-lg transition-all hover:opacity-80"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>

                    {/* Score */}
                    <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Score de Saúde</span>
                        <span className="text-green-400 font-bold text-xl">85/100</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div className="bg-gradient-to-r from-green-500 to-emerald-400 h-2 rounded-full" style={{ width: '85%' }}></div>
                      </div>
                      <p className="text-green-400 text-xs mt-2">✓ Empresa em crescimento saudável</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Elementos Decorativos */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-purple-600 rounded-full filter blur-3xl opacity-20 animate-pulse"></div>
              <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-600 rounded-full filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '1s' }}></div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Simples */}
      <footer className="border-t border-white/10 py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-gray-400 text-sm">
          <p>© 2025 Lucro Líquido - Todos os direitos reservados</p>
          <p className="mt-2">Gestão financeira inteligente para empresas que querem crescer com lucro real.</p>
        </div>
      </footer>

      {/* Modal de Login */}
      <Dialog open={showLoginModal} onOpenChange={setShowLoginModal}>
        <DialogContent className="sm:max-w-md glass border-white/10">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold gradient-text">Entrar no Lucro Líquido</DialogTitle>
            <DialogDescription className="text-gray-400">
              Entre com suas credenciais para acessar o sistema
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="login-email" className="text-white">Email</Label>
              <Input
                id="login-email"
                type="email"
                placeholder="seu@email.com"
                value={loginData.email}
                onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                required
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="login-password" className="text-white">Senha</Label>
              <Input
                id="login-password"
                type="password"
                placeholder="••••••••"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                required
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
            <div className="text-center text-sm text-gray-400">
              Não tem conta?{' '}
              <button
                type="button"
                onClick={() => {
                  setShowLoginModal(false);
                  setShowRegisterModal(true);
                }}
                className="text-purple-400 hover:text-purple-300"
              >
                Cadastre-se grátis
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal de Registro */}
      <Dialog open={showRegisterModal} onOpenChange={setShowRegisterModal}>
        <DialogContent className="sm:max-w-md glass border-white/10">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold gradient-text">Comece seu teste grátis</DialogTitle>
            <DialogDescription className="text-gray-400">
              7 dias grátis • Sem cartão de crédito • Cancele quando quiser
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="register-name" className="text-white">Nome Completo</Label>
              <Input
                id="register-name"
                type="text"
                placeholder="Seu nome"
                value={registerData.name}
                onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                required
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="register-email" className="text-white">Email</Label>
              <Input
                id="register-email"
                type="email"
                placeholder="seu@email.com"
                value={registerData.email}
                onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                required
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="register-password" className="text-white">Senha</Label>
              <Input
                id="register-password"
                type="password"
                placeholder="Mínimo 6 caracteres"
                value={registerData.password}
                onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                required
                minLength={6}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              disabled={loading}
            >
              {loading ? 'Criando conta...' : 'Começar teste grátis agora'}
            </Button>
            <div className="text-center text-sm text-gray-400">
              Já tem conta?{' '}
              <button
                type="button"
                onClick={() => {
                  setShowRegisterModal(false);
                  setShowLoginModal(true);
                }}
                className="text-purple-400 hover:text-purple-300"
              >
                Faça login
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LandingPage;
