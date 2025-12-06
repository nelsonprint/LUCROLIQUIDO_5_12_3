import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Target, Calculator, CreditCard, Shield, LogOut, BookOpen, Receipt, ChevronDown, ChevronRight, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const Sidebar = ({ user, onLogout, onOpenGlossary }) => {
  const location = useLocation();
  const [contasMenuOpen, setContasMenuOpen] = useState(false);

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/lancamentos', icon: FileText, label: 'Lançamentos' },
    { 
      type: 'submenu',
      icon: Receipt, 
      label: 'Contas',
      items: [
        { path: '/contas-pagar', label: 'Contas a Pagar' },
        { path: '/contas-receber', label: 'Contas a Receber' }
      ]
    },
    { path: '/categorias', icon: BookOpen, label: 'Categorias' },
    { path: '/empresa', icon: Shield, label: 'Empresa' },
    { path: '/meta-mensal', icon: Target, label: 'Meta Mensal' },
    { path: '/precificacao', icon: Calculator, label: 'Precificação' },
    { path: '/orcamentos', icon: FileText, label: 'Orçamentos' },
    { path: '/materiais', icon: Package, label: 'Materiais' },
    { path: '/assinatura', icon: CreditCard, label: 'Assinatura' },
  ];

  // Adicionar item admin se usuário for admin
  if (user?.role === 'admin') {
    menuItems.push({ path: '/admin', icon: Shield, label: 'Admin' });
  }

  return (
    <div className="w-64 min-h-screen glass border-r border-white/10 flex flex-col" data-testid="sidebar">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h1 className="text-2xl font-bold gradient-text" data-testid="sidebar-logo">
          Lucro Líquido
        </h1>
        <div className="flex items-center justify-between mt-3">
          <div className="flex-1">
            <p className="text-sm text-gray-400 mt-1" data-testid="sidebar-subtitle">Gestão Financeira</p>
          </div>
        </div>
        
        {/* User Info inline */}
        <div className="mt-3 flex items-center justify-between">
          <div className="flex-1" data-testid="sidebar-user-info">
            <p className="text-xs font-medium text-white">{user?.name}</p>
            <p className="text-xs text-gray-500">{user?.email}</p>
          </div>
          <button
            onClick={onLogout}
            className="p-2 rounded-lg border border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all"
            title="Sair do sistema"
            data-testid="sidebar-logout-button"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item, index) => {
          // Se for submenu (Contas)
          if (item.type === 'submenu') {
            const Icon = item.icon;
            const isAnySubActive = item.items.some(subItem => location.pathname === subItem.path);
            
            return (
              <div key={`submenu-${index}`}>
                <button
                  onClick={() => setContasMenuOpen(!contasMenuOpen)}
                  className={`w-full flex items-center justify-between space-x-3 px-4 py-3 rounded-lg transition-all ${
                    isAnySubActive
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                      : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`}
                  data-testid="sidebar-contas-menu"
                >
                  <div className="flex items-center space-x-3">
                    <Icon size={20} />
                    <span className="font-medium">{item.label}</span>
                  </div>
                  {contasMenuOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </button>
                
                {contasMenuOpen && (
                  <div className="mt-2 ml-8 space-y-1">
                    {item.items.map((subItem) => {
                      const isSubActive = location.pathname === subItem.path;
                      return (
                        <Link key={subItem.path} to={subItem.path}>
                          <div
                            className={`px-4 py-2 rounded-lg text-sm transition-all ${
                              isSubActive
                                ? 'bg-white/10 text-white font-medium'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                            }`}
                          >
                            {subItem.label}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }
          
          // Menu normal
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link key={item.path} to={item.path} data-testid={`sidebar-link-${item.label.toLowerCase().replace(' ', '-')}`}>
              <div
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                    : 'text-gray-300 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </div>
            </Link>
          );
        })}

        {/* Botão O que é... */}
        <button
          onClick={onOpenGlossary}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all text-gray-300 hover:bg-white/5 hover:text-white"
          data-testid="sidebar-glossary-button"
        >
          <BookOpen size={20} />
          <span className="font-medium">O que é...</span>
        </button>
      </nav>

      {/* Admin Badge (se aplicável) */}
      {user?.role === 'admin' && (
        <div className="p-4 border-t border-white/10">
          <span className="inline-block px-3 py-1 text-xs bg-purple-600 rounded-full text-white" data-testid="sidebar-admin-badge">
            👑 Administrador
          </span>
        </div>
      )}
    </div>
  );
};