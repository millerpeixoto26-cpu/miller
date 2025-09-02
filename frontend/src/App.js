import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Switch } from "./components/ui/switch";
import { Loader2, Heart, Shield, Sparkles, Star, Phone, Settings, Palette, Layout, Calendar, Edit, Trash2, Eye, EyeOff, LogOut, Users, CreditCard, TestTube, Instagram, Image, Plus } from "lucide-react";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context de Autenticação
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error("Erro ao buscar usuário:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || "Erro ao fazer login" 
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};

// Componente de Login
const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const result = await login(formData.username, formData.password);
    
    if (result.success) {
      toast.success("Login realizado com sucesso!");
      navigate("/admin");
    } else {
      toast.error(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 px-4">
      <Card className="w-full max-w-md bg-white/10 border-purple-300/30 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-white">Painel Administrativo</CardTitle>
          <CardDescription className="text-purple-200">
            Faça login para acessar o sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username" className="text-white">Usuário</Label>
              <Input
                id="username"
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                placeholder="Digite seu usuário"
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-white">Senha</Label>
              <Input
                id="password"
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                placeholder="Digite sua senha"
              />
            </div>
            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>
          
          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-400/30 rounded-lg">
            <p className="text-yellow-200 text-sm text-center">
              <strong>Login Padrão:</strong><br />
              Usuário: <code className="bg-black/20 px-1 rounded">admin</code><br />
              Senha: <code className="bg-black/20 px-1 rounded">admin123</code>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Componente de Proteção de Rotas
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
        <Loader2 className="w-8 h-8 animate-spin text-white" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
const Home = () => {
  const [rituais, setRituais] = useState([]);
  const [rituaisHoje, setRituaisHoje] = useState([]);
  const [configuracao, setConfiguracao] = useState(null);
  const [instagramProfile, setInstagramProfile] = useState(null);
  const [instagramPosts, setInstagramPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRituais();
    fetchRituaisHoje();
    fetchConfiguracao();
    fetchInstagramData();
  }, []);

  const fetchInstagramData = async () => {
    try {
      const [profileResponse, postsResponse] = await Promise.all([
        axios.get(`${API}/instagram/profile`),
        axios.get(`${API}/instagram/posts`)
      ]);
      setInstagramProfile(profileResponse.data);
      setInstagramPosts(postsResponse.data);
    } catch (error) {
      console.error("Erro ao buscar dados do Instagram:", error);
    }
  };

  const fetchRituais = async () => {
    try {
      const response = await axios.get(`${API}/rituais`);
      setRituais(response.data);
    } catch (error) {
      console.error("Erro ao buscar rituais:", error);
      toast.error("Erro ao carregar rituais");
    } finally {
      setLoading(false);
    }
  };

  const fetchRituaisHoje = async () => {
    try {
      const response = await axios.get(`${API}/rituais-semana/hoje`);
      setRituaisHoje(response.data);
    } catch (error) {
      console.error("Erro ao buscar rituais de hoje:", error);
    }
  };

  const fetchConfiguracao = async () => {
    try {
      const response = await axios.get(`${API}/config`);
      setConfiguracao(response.data);
    } catch (error) {
      console.error("Erro ao buscar configurações:", error);
    }
  };

  const handleSelectRitual = async (ritualId) => {
    try {
      const response = await axios.post(`${API}/checkout`, {
        ritual_id: ritualId,
        host_url: window.location.origin
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error("Erro ao iniciar pagamento:", error);
      toast.error("Erro ao processar pagamento");
    }
  };

  const getIconForRitual = (nome) => {
    if (nome.toLowerCase().includes("amarração")) return <Heart className="w-6 h-6" />;
    if (nome.toLowerCase().includes("proteção")) return <Shield className="w-6 h-6" />;
    if (nome.toLowerCase().includes("desamarre")) return <Sparkles className="w-6 h-6" />;
    return <Star className="w-6 h-6" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
        <Loader2 className="w-8 h-8 animate-spin text-white" />
      </div>
    );
  }

  // Aplica cores personalizadas
  const primaryColor = configuracao?.cores?.primary || "#8b5cf6";
  const secondaryColor = configuracao?.cores?.secondary || "#ec4899";

  return (
    <div className="min-h-screen" style={{
      background: `linear-gradient(to bottom right, ${primaryColor}dd, ${primaryColor}aa, ${secondaryColor}aa)`
    }}>
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative container mx-auto px-4 py-16 text-center">
          <div className="max-w-4xl mx-auto">
            {configuracao?.logo_url && (
              <div className="mb-8">
                <img 
                  src={configuracao.logo_url} 
                  alt="Logo" 
                  className="h-20 mx-auto object-contain"
                  onError={(e) => e.target.style.display = 'none'}
                />
              </div>
            )}
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
              Rituais Espirituais
            </h1>
            <p className="text-xl md:text-2xl text-purple-100 mb-8 leading-relaxed">
              Transforme sua vida através do poder dos rituais ancestrais
            </p>
            <div className="flex justify-center items-center space-x-2 text-purple-200">
              <Star className="w-5 h-5 fill-current" />
              <span className="text-sm font-medium">Mais de 5.000 clientes atendidos</span>
              <Star className="w-5 h-5 fill-current" />
            </div>
          </div>
        </div>
      </div>

      {/* Rituais de Hoje */}
      {rituaisHoje.length > 0 && (
        <div className="container mx-auto px-4 py-8 bg-black/20">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">Rituais de Hoje</h2>
            <p className="text-purple-200">Especiais para hoje, com energia ainda mais poderosa</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {rituaisHoje.map((rs) => rs.ritual && (
              <Card key={rs.id} className="bg-white/15 border-yellow-300/30 backdrop-blur-sm hover:bg-white/20 transition-all duration-300 transform hover:scale-105">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-400/30 text-xs">
                      DESTAQUE HOJE
                    </Badge>
                    <div className="flex items-center space-x-2">
                      <div className="p-1 bg-yellow-500/20 rounded-full text-yellow-300">
                        {getIconForRitual(rs.ritual.nome)}
                      </div>
                    </div>
                  </div>
                  <CardTitle className="text-white text-lg">{rs.ritual.nome}</CardTitle>
                  <Badge variant="secondary" className="bg-purple-500/20 text-purple-200 border-purple-400/30 w-fit">
                    R$ {rs.ritual.preco.toFixed(2)}
                  </Badge>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-purple-100 mb-4 text-sm">
                    {rs.ritual.descricao}
                  </CardDescription>
                  <Button 
                    onClick={() => handleSelectRitual(rs.ritual.id)}
                    className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white border-0 font-semibold py-2 rounded-lg transition-all duration-300"
                  >
                    Solicitar Hoje
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Rituais */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Escolha Seu Ritual</h2>
          <p className="text-purple-200 text-lg">Cada ritual é personalizado especialmente para você</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {rituais.map((ritual) => (
            <Card key={ritual.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm hover:bg-white/15 transition-all duration-300 transform hover:scale-105">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-purple-500/20 rounded-lg text-purple-300">
                      {getIconForRitual(ritual.nome)}
                    </div>
                    <div>
                      <CardTitle className="text-white text-xl">{ritual.nome}</CardTitle>
                      <Badge variant="secondary" className="bg-purple-500/20 text-purple-200 border-purple-400/30">
                        R$ {ritual.preco.toFixed(2)}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-purple-100 mb-6 text-base leading-relaxed">
                  {ritual.descricao}
                </CardDescription>
                <Button 
                  onClick={() => handleSelectRitual(ritual.id)}
                  style={{
                    background: `linear-gradient(to right, ${primaryColor}, ${secondaryColor})`,
                  }}
                  className="w-full text-white border-0 font-semibold py-3 rounded-lg transition-all duration-300 transform hover:scale-[1.02] hover:opacity-90"
                >
                  Solicitar Ritual
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Seção Instagram */}
      {instagramProfile && instagramProfile.is_active && (
        <div className="container mx-auto px-4 py-16 bg-black/10">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-white mb-4">Siga-nos no Instagram</h2>
              <p className="text-purple-200 text-lg">Acompanhe nosso trabalho e transformações</p>
            </div>
            
            {/* Perfil */}
            <div className="flex flex-col md:flex-row items-center justify-center mb-12 space-y-6 md:space-y-0 md:space-x-8">
              <div className="flex-shrink-0">
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-purple-300/30 bg-gray-700">
                  <img 
                    src={instagramProfile.profile_image_url} 
                    alt={instagramProfile.display_name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><circle cx="64" cy="64" r="64" fill="%23374151"/><text x="64" y="64" text-anchor="middle" dominant-baseline="central" fill="white" font-family="Arial" font-size="16">Foto</text></svg>';
                    }}
                  />
                </div>
              </div>
              
              <div className="text-center md:text-left max-w-md">
                <h3 className="text-2xl font-bold text-white mb-2">@{instagramProfile.username}</h3>
                <h4 className="text-xl text-purple-200 mb-3">{instagramProfile.display_name}</h4>
                <p className="text-purple-100 mb-4 leading-relaxed">{instagramProfile.bio}</p>
                {instagramProfile.followers_count && (
                  <p className="text-purple-300 text-sm mb-4">
                    {instagramProfile.followers_count.toLocaleString()} seguidores
                  </p>
                )}
                <a
                  href={instagramProfile.instagram_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-300 transform hover:scale-105"
                >
                  <Instagram className="w-5 h-5 mr-2" />
                  Seguir no Instagram
                </a>
              </div>
            </div>

            {/* Posts */}
            {instagramPosts.length > 0 && (
              <div>
                <h3 className="text-2xl font-bold text-white text-center mb-8">Últimos Posts</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {instagramPosts.slice(0, 6).map((post) => (
                    <div key={post.id} className="group">
                      <div className="aspect-square rounded-xl overflow-hidden bg-gray-700 relative">
                        <img 
                          src={post.image_url} 
                          alt={post.caption}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23374151"/><text x="150" y="150" text-anchor="middle" dominant-baseline="central" fill="white" font-family="Arial" font-size="16">Imagem não encontrada</text></svg>';
                          }}
                        />
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                          <p className="text-white text-sm text-center px-4 line-clamp-3">
                            {post.caption}
                          </p>
                        </div>
                        {post.post_url && (
                          <a
                            href={post.post_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="absolute inset-0 z-10"
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-purple-700/30 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-purple-200">© 2025 Rituais Espirituais. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  );
};

// Componente para Success Page
const Sucesso = () => {
  const [loading, setLoading] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const sessionIdParam = urlParams.get("session_id");
    
    if (sessionIdParam) {
      setSessionId(sessionIdParam);
      pollPaymentStatus(sessionIdParam);
    } else {
      navigate("/");
    }
  }, [location, navigate]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setPaymentStatus("timeout");
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === "paid") {
        setPaymentStatus("paid");
        setLoading(false);
        return;
      } else if (response.data.status === "expired") {
        setPaymentStatus("expired");
        setLoading(false);
        return;
      }

      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error("Erro ao verificar status:", error);
      setPaymentStatus("error");
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
        <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-purple-300 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Verificando Pagamento</h2>
            <p className="text-purple-200">Aguarde enquanto confirmamos seu pagamento...</p>
          </div>
        </Card>
      </div>
    );
  }

  if (paymentStatus === "paid") {
    return <FormularioCliente sessionId={sessionId} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
      <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8 max-w-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            {paymentStatus === "expired" ? "Pagamento Expirado" : 
             paymentStatus === "timeout" ? "Tempo Limite Excedido" : "Erro no Pagamento"}
          </h2>
          <p className="text-purple-200 mb-6">
            {paymentStatus === "expired" ? "Sua sessão de pagamento expirou. Tente novamente." :
             paymentStatus === "timeout" ? "Não foi possível verificar o pagamento. Entre em contato conosco." :
             "Ocorreu um erro ao processar seu pagamento."}
          </p>
          <Button 
            onClick={() => navigate("/")}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
          >
            Voltar ao Início
          </Button>
        </div>
      </Card>
    </div>
  );
};

// Componente para Formulário do Cliente
const FormularioCliente = ({ sessionId }) => {
  const [formData, setFormData] = useState({
    nome_completo: "",
    email: "",
    telefone: "",
    nome_pessoa_amada: "",
    data_nascimento: "",
    informacoes_adicionais: ""
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/clientes?session_id=${sessionId}`, formData);
      setSuccess(true);
      toast.success("Dados enviados com sucesso!");
    } catch (error) {
      console.error("Erro ao enviar dados:", error);
      toast.error("Erro ao enviar dados");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
        <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8 max-w-lg">
          <div className="text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Star className="w-8 h-8 text-green-400" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Pedido Confirmado!</h2>
              <p className="text-purple-200 leading-relaxed">
                Recebemos seus dados e seu ritual será preparado especialmente para você. 
                Entraremos em contato em breve com todas as informações.
              </p>
            </div>
            <Button 
              onClick={() => navigate("/")}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              Voltar ao Início
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 py-12 px-4">
      <div className="container mx-auto max-w-2xl">
        <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-white">Finalize Seu Pedido</CardTitle>
            <CardDescription className="text-purple-200 text-lg">
              Preencha seus dados para que possamos preparar seu ritual personalizado
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nome_completo" className="text-white">Nome Completo *</Label>
                  <Input
                    id="nome_completo"
                    name="nome_completo"
                    type="text"
                    required
                    value={formData.nome_completo}
                    onChange={handleInputChange}
                    className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                    placeholder="Seu nome completo"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-white">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                    placeholder="seu@email.com"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="telefone" className="text-white">WhatsApp *</Label>
                  <Input
                    id="telefone"
                    name="telefone"
                    type="tel"
                    required
                    value={formData.telefone}
                    onChange={handleInputChange}
                    className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                    placeholder="(11) 99999-9999"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="data_nascimento" className="text-white">Data de Nascimento *</Label>
                  <Input
                    id="data_nascimento"
                    name="data_nascimento"
                    type="date"
                    required
                    value={formData.data_nascimento}
                    onChange={handleInputChange}
                    className="bg-white/5 border-purple-300/30 text-white"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="nome_pessoa_amada" className="text-white">Nome da Pessoa Amada *</Label>
                <Input
                  id="nome_pessoa_amada"
                  name="nome_pessoa_amada"
                  type="text"
                  required
                  value={formData.nome_pessoa_amada}
                  onChange={handleInputChange}
                  className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                  placeholder="Nome completo da pessoa"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="informacoes_adicionais" className="text-white">Informações Adicionais</Label>
                <Textarea
                  id="informacoes_adicionais"
                  name="informacoes_adicionais"
                  value={formData.informacoes_adicionais}
                  onChange={handleInputChange}
                  className="bg-white/5 border-purple-300/30 text-white placeholder:text-purple-300"
                  placeholder="Conte-nos mais detalhes sobre sua situação..."
                  rows={4}
                />
              </div>

              <Button 
                type="submit" 
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 text-lg transition-all duration-300"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  "Finalizar Pedido"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Componente para Admin Panel
const AdminPanel = () => {
  const { user, logout } = useAuth();
  const [pedidos, setPedidos] = useState([]);
  const [rituais, setRituais] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [gateways, setGateways] = useState([]);
  const [instagramProfile, setInstagramProfile] = useState(null);
  const [instagramPosts, setInstagramPosts] = useState([]);
  const [instagramApiConfig, setInstagramApiConfig] = useState(null);
  const [instagramApiStatus, setInstagramApiStatus] = useState(null);
  const [instagramSyncHistory, setInstagramSyncHistory] = useState([]);
  const [configuracao, setConfiguracao] = useState(null);
  const [rituaisSemana, setRituaisSemana] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddRitual, setShowAddRitual] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showAddPost, setShowAddPost] = useState(false);
  const [editingRitual, setEditingRitual] = useState(null);
  const [editingGateway, setEditingGateway] = useState(null);
  const [editingPost, setEditingPost] = useState(null);
  const [novoRitual, setNovoRitual] = useState({
    nome: "",
    descricao: "",
    preco: "",
    imagem_url: "",
    visivel: true,
    tem_desconto: false,
    desconto_valor: "",
    desconto_percentual: ""
  });
  const [novoUsuario, setNovoUsuario] = useState({
    username: "",
    email: "",
    password: ""
  });
  const [configForm, setConfigForm] = useState({
    logo_url: "",
    whatsapp_numero: "",
    cores: {
      primary: "#8b5cf6",
      secondary: "#ec4899",
      background: "#1a1a2e",
      text: "#ffffff"
    },
    stripe_snippet_id: ""
  });
  const [rituaisSemanaForm, setRituaisSemanaForm] = useState({
    segunda: { ritual_id: "", ativo: false },
    terca: { ritual_id: "", ativo: false },
    quarta: { ritual_id: "", ativo: false },
    quinta: { ritual_id: "", ativo: false },
    sexta: { ritual_id: "", ativo: false },
    sabado: { ritual_id: "", ativo: false },
    domingo: { ritual_id: "", ativo: false }
  });

  useEffect(() => {
    fetchPedidos();
    fetchRituais();
    fetchUsuarios();
    fetchGateways();
    fetchInstagramProfile();
    fetchInstagramPosts();
    fetchInstagramApiConfig();
    fetchInstagramApiStatus();
    fetchInstagramSyncHistory();
    fetchConfiguracao();
    fetchRituaisSemana();
  }, []);

  const fetchInstagramProfile = async () => {
    try {
      const response = await axios.get(`${API}/admin/instagram/profile`);
      setInstagramProfile(response.data);
    } catch (error) {
      console.error("Erro ao buscar perfil Instagram:", error);
    }
  };

  const fetchInstagramPosts = async () => {
    try {
      const response = await axios.get(`${API}/admin/instagram/posts`);
      setInstagramPosts(response.data);
    } catch (error) {
      console.error("Erro ao buscar posts Instagram:", error);
    }
  };

  const fetchInstagramApiConfig = async () => {
    try {
      const response = await axios.get(`${API}/admin/instagram/api/config`);
      setInstagramApiConfig(response.data);
    } catch (error) {
      console.error("Erro ao buscar configuração Instagram API:", error);
    }
  };

  const fetchInstagramApiStatus = async () => {
    try {
      const response = await axios.get(`${API}/admin/instagram/api/status`);
      setInstagramApiStatus(response.data);
    } catch (error) {
      console.error("Erro ao buscar status Instagram API:", error);
    }
  };

  const fetchInstagramSyncHistory = async () => {
    try {
      const response = await axios.get(`${API}/admin/instagram/api/sync/history`);
      setInstagramSyncHistory(response.data);
    } catch (error) {
      console.error("Erro ao buscar histórico de sincronização:", error);
    }
  };

  const fetchGateways = async () => {
    try {
      const response = await axios.get(`${API}/payment-gateways`);
      setGateways(response.data);
    } catch (error) {
      console.error("Erro ao buscar gateways:", error);
      toast.error("Erro ao carregar gateways de pagamento");
    }
  };

  const fetchUsuarios = async () => {
    try {
      const response = await axios.get(`${API}/auth/users`);
      setUsuarios(response.data);
    } catch (error) {
      console.error("Erro ao buscar usuários:", error);
      toast.error("Erro ao carregar usuários");
    }
  };

  const fetchPedidos = async () => {
    try {
      const response = await axios.get(`${API}/admin/pedidos`);
      setPedidos(response.data);
    } catch (error) {
      console.error("Erro ao buscar pedidos:", error);
      toast.error("Erro ao carregar pedidos");
    } finally {
      setLoading(false);
    }
  };

  const fetchRituais = async () => {
    try {
      const response = await axios.get(`${API}/admin/rituais`);
      setRituais(response.data);
    } catch (error) {
      console.error("Erro ao buscar rituais:", error);
      toast.error("Erro ao carregar rituais");
    }
  };

  const fetchConfiguracao = async () => {
    try {
      const response = await axios.get(`${API}/config`);
      setConfiguracao(response.data);
      setConfigForm(response.data);
    } catch (error) {
      console.error("Erro ao buscar configurações:", error);
      toast.error("Erro ao carregar configurações");
    }
  };

  const fetchRituaisSemana = async () => {
    try {
      const response = await axios.get(`${API}/rituais-semana`);
      setRituaisSemana(response.data);
      
      // Atualiza o form com os dados existentes
      const formData = {
        segunda: { ritual_id: "", ativo: false },
        terca: { ritual_id: "", ativo: false },
        quarta: { ritual_id: "", ativo: false },
        quinta: { ritual_id: "", ativo: false },
        sexta: { ritual_id: "", ativo: false },
        sabado: { ritual_id: "", ativo: false },
        domingo: { ritual_id: "", ativo: false }
      };
      
      response.data.forEach(rs => {
        if (formData[rs.dia_semana]) {
          formData[rs.dia_semana] = {
            ritual_id: rs.ritual_id,
            ativo: rs.ativo
          };
        }
      });
      
      setRituaisSemanaForm(formData);
    } catch (error) {
      console.error("Erro ao buscar rituais da semana:", error);
      toast.error("Erro ao carregar rituais da semana");
    }
  };

  const handleAddRitual = async (e) => {
    e.preventDefault();
    try {
      const ritualData = {
        ...novoRitual,
        preco: parseFloat(novoRitual.preco),
        desconto_valor: novoRitual.desconto_valor ? parseFloat(novoRitual.desconto_valor) : null,
        desconto_percentual: novoRitual.desconto_percentual ? parseFloat(novoRitual.desconto_percentual) : null
      };

      if (editingRitual) {
        await axios.put(`${API}/rituais/${editingRitual.id}`, ritualData);
        toast.success("Ritual atualizado com sucesso!");
        setEditingRitual(null);
      } else {
        await axios.post(`${API}/rituais`, ritualData);
        toast.success("Ritual adicionado com sucesso!");
      }
      
      setShowAddRitual(false);
      setNovoRitual({ 
        nome: "", 
        descricao: "", 
        preco: "", 
        imagem_url: "",
        visivel: true,
        tem_desconto: false,
        desconto_valor: "",
        desconto_percentual: ""
      });
      fetchRituais();
    } catch (error) {
      console.error("Erro ao salvar ritual:", error);
      toast.error("Erro ao salvar ritual");
    }
  };

  const handleEditRitual = (ritual) => {
    setEditingRitual(ritual);
    setNovoRitual({
      nome: ritual.nome,
      descricao: ritual.descricao,
      preco: ritual.preco.toString(),
      imagem_url: ritual.imagem_url || "",
      visivel: ritual.visivel,
      tem_desconto: ritual.tem_desconto || false,
      desconto_valor: ritual.desconto_valor ? ritual.desconto_valor.toString() : "",
      desconto_percentual: ritual.desconto_percentual ? ritual.desconto_percentual.toString() : ""
    });
    setShowAddRitual(true);
  };

  const handleDeleteRitual = async (ritualId) => {
    if (window.confirm("Tem certeza que deseja excluir este ritual?")) {
      try {
        await axios.delete(`${API}/rituais/${ritualId}`);
        toast.success("Ritual excluído com sucesso!");
        fetchRituais();
      } catch (error) {
        console.error("Erro ao excluir ritual:", error);
        toast.error("Erro ao excluir ritual");
      }
    }
  };

  const handleUpdateConfig = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/config`, configForm);
      toast.success("Configurações atualizadas com sucesso!");
      fetchConfiguracao();
    } catch (error) {
      console.error("Erro ao atualizar configurações:", error);
      toast.error("Erro ao atualizar configurações");
    }
  };

  const handleSaveRituaisSemana = async (e) => {
    e.preventDefault();
    try {
      // Salva cada dia da semana
      for (const [dia, dados] of Object.entries(rituaisSemanaForm)) {
        if (dados.ritual_id && dados.ativo) {
          await axios.post(`${API}/rituais-semana`, {
            dia_semana: dia,
            ritual_id: dados.ritual_id,
            ativo: dados.ativo
          });
        }
      }
      toast.success("Rituais da semana salvos com sucesso!");
      fetchRituaisSemana();
    } catch (error) {
      console.error("Erro ao salvar rituais da semana:", error);
      toast.error("Erro ao salvar rituais da semana");
    }
  };

  const updateRitualSemana = (dia, field, value) => {
    setRituaisSemanaForm(prev => ({
      ...prev,
      [dia]: {
        ...prev[dia],
        [field]: value
      }
    }));
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/auth/register`, novoUsuario);
      toast.success("Usuário criado com sucesso!");
      setShowAddUser(false);
      setNovoUsuario({ username: "", email: "", password: "" });
      fetchUsuarios();
    } catch (error) {
      console.error("Erro ao criar usuário:", error);
      toast.error(error.response?.data?.detail || "Erro ao criar usuário");
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm("Tem certeza que deseja excluir este usuário?")) {
      try {
        await axios.delete(`${API}/auth/users/${userId}`);
        toast.success("Usuário excluído com sucesso!");
        fetchUsuarios();
      } catch (error) {
        console.error("Erro ao excluir usuário:", error);
        toast.error(error.response?.data?.detail || "Erro ao excluir usuário");
      }
    }
  };

  const handleUpdateGateway = async (gatewayId, updateData) => {
    try {
      await axios.put(`${API}/payment-gateways/${gatewayId}`, updateData);
      toast.success("Gateway atualizado com sucesso!");
      fetchGateways();
      setEditingGateway(null);
    } catch (error) {
      console.error("Erro ao atualizar gateway:", error);
      toast.error("Erro ao atualizar gateway");
    }
  };

  const handleTestGateway = async (gatewayId) => {
    try {
      const response = await axios.post(`${API}/payment-gateways/${gatewayId}/test`);
      if (response.data.success) {
        toast.success(response.data.message);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      console.error("Erro ao testar gateway:", error);
      toast.error("Erro ao testar gateway");
    }
  };

  const handleUpdateInstagramProfile = async (profileData) => {
    try {
      await axios.post(`${API}/admin/instagram/profile`, profileData);
      toast.success("Perfil Instagram atualizado com sucesso!");
      fetchInstagramProfile();
    } catch (error) {
      console.error("Erro ao atualizar perfil Instagram:", error);
      toast.error("Erro ao atualizar perfil Instagram");
    }
  };

  const handleAddInstagramPost = async (postData) => {
    try {
      await axios.post(`${API}/admin/instagram/posts`, postData);
      toast.success("Post adicionado com sucesso!");
      setShowAddPost(false);
      fetchInstagramPosts();
    } catch (error) {
      console.error("Erro ao adicionar post:", error);
      toast.error("Erro ao adicionar post");
    }
  };

  const handleUpdateInstagramPost = async (postId, postData) => {
    try {
      await axios.put(`${API}/admin/instagram/posts/${postId}`, postData);
      toast.success("Post atualizado com sucesso!");
      setEditingPost(null);
      fetchInstagramPosts();
    } catch (error) {
      console.error("Erro ao atualizar post:", error);
      toast.error("Erro ao atualizar post");
    }
  };

  const handleDeleteInstagramPost = async (postId) => {
    if (window.confirm("Tem certeza que deseja excluir este post?")) {
      try {
        await axios.delete(`${API}/admin/instagram/posts/${postId}`);
        toast.success("Post excluído com sucesso!");
        fetchInstagramPosts();
      } catch (error) {
        console.error("Erro ao excluir post:", error);
        toast.error("Erro ao excluir post");
      }
    }
  };

  const getIconForRitual = (nome) => {
    if (nome.toLowerCase().includes("amarração")) return <Heart className="w-6 h-6" />;
    if (nome.toLowerCase().includes("proteção")) return <Shield className="w-6 h-6" />;
    if (nome.toLowerCase().includes("desamarre")) return <Sparkles className="w-6 h-6" />;
    return <Star className="w-6 h-6" />;
  };

  const abrirWhatsApp = (telefone, nomeCliente, nomeRitual) => {
    const numero = telefone.replace(/\D/g, "");
    const mensagem = encodeURIComponent(
      `Olá ${nomeCliente}! Seu ritual "${nomeRitual}" está sendo preparado. Em breve enviarei o vídeo com todos os detalhes.`
    );
    window.open(`https://wa.me/55${numero}?text=${mensagem}`, "_blank");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
        <Loader2 className="w-8 h-8 animate-spin text-white" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 py-4 md:py-8 px-4">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 md:mb-8 space-y-4 md:space-y-0">
          <div className="text-center md:text-left">
            <h1 className="text-2xl md:text-4xl font-bold text-white mb-2">Painel Administrativo</h1>
            <p className="text-purple-200 text-sm md:text-base">Gerencie pedidos, rituais e personalize o site</p>
          </div>
          <div className="flex items-center space-x-3 md:space-x-4">
            <div className="text-center md:text-right">
              <p className="text-white font-medium text-sm md:text-base">{user?.username}</p>
              <p className="text-purple-200 text-xs md:text-sm">{user?.email}</p>
            </div>
            <Button
              onClick={logout}
              className="bg-red-600 hover:bg-red-700 text-white flex items-center space-x-1 md:space-x-2 px-3 py-2 text-sm"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Sair</span>
              <span className="sm:hidden">Sair</span>
            </Button>
          </div>
        </div>

        <Tabs defaultValue="pedidos" className="w-full">
          {/* Navigation - Desktop */}
          <div className="hidden md:block">
            <TabsList className="grid w-full grid-cols-7 bg-white/10 backdrop-blur-sm p-1 rounded-lg">
              <TabsTrigger 
                value="pedidos" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Phone className="w-4 h-4 mr-1" />
                Pedidos ({pedidos.length})
              </TabsTrigger>
              <TabsTrigger 
                value="rituais" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Sparkles className="w-4 h-4 mr-1" />
                Rituais ({rituais.length})
              </TabsTrigger>
              <TabsTrigger 
                value="semana" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Calendar className="w-4 h-4 mr-1" />
                Semana
              </TabsTrigger>
              <TabsTrigger 
                value="usuarios" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Users className="w-4 h-4 mr-1" />
                Users ({usuarios.length})
              </TabsTrigger>
              <TabsTrigger 
                value="pagamentos" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <CreditCard className="w-4 h-4 mr-1" />
                Pagamentos
              </TabsTrigger>
              <TabsTrigger 
                value="instagram" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Instagram className="w-4 h-4 mr-1" />
                Instagram
              </TabsTrigger>
              <TabsTrigger 
                value="config" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md flex items-center justify-center px-2 py-3 text-sm font-medium"
              >
                <Settings className="w-4 h-4 mr-1" />
                Config
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Navigation - Mobile (Simpler Stack) */}
          <div className="block md:hidden mb-6">
            <TabsList className="flex flex-col w-full space-y-2 bg-white/10 backdrop-blur-sm p-3 rounded-lg h-auto">
              <TabsTrigger 
                value="pedidos" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center justify-between px-4 py-4 text-sm font-medium"
              >
                <div className="flex items-center">
                  <Phone className="w-5 h-5 mr-3" />
                  <span>Pedidos</span>
                </div>
                <Badge className="bg-white/20 text-white text-xs px-2 py-1 rounded-full">
                  {pedidos.length}
                </Badge>
              </TabsTrigger>
              
              <TabsTrigger 
                value="rituais" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center justify-between px-4 py-4 text-sm font-medium"
              >
                <div className="flex items-center">
                  <Sparkles className="w-5 h-5 mr-3" />
                  <span>Rituais</span>
                </div>
                <Badge className="bg-white/20 text-white text-xs px-2 py-1 rounded-full">
                  {rituais.length}
                </Badge>
              </TabsTrigger>
              
              <TabsTrigger 
                value="semana" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center px-4 py-4 text-sm font-medium"
              >
                <Calendar className="w-5 h-5 mr-3" />
                <span>Rituais da Semana</span>
              </TabsTrigger>
              
              <TabsTrigger 
                value="usuarios" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center justify-between px-4 py-4 text-sm font-medium"
              >
                <div className="flex items-center">
                  <Users className="w-5 h-5 mr-3" />
                  <span>Usuários</span>
                </div>
                <Badge className="bg-white/20 text-white text-xs px-2 py-1 rounded-full">
                  {usuarios.length}
                </Badge>
              </TabsTrigger>
              
              <TabsTrigger 
                value="pagamentos" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center px-4 py-4 text-sm font-medium"
              >
                <CreditCard className="w-5 h-5 mr-3" />
                <span>Pagamentos</span>
              </TabsTrigger>
              
              <TabsTrigger 
                value="instagram" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center px-4 py-4 text-sm font-medium"
              >
                <Instagram className="w-5 h-5 mr-3" />
                <span>Instagram</span>
              </TabsTrigger>
              
              <TabsTrigger 
                value="config" 
                className="w-full data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-lg flex items-center px-4 py-4 text-sm font-medium"
              >
                <Settings className="w-5 h-5 mr-3" />
                <span>Configurações</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="pedidos" className="mt-6">
            <div className="grid gap-6">
              {pedidos.length === 0 ? (
                <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold text-white mb-2">Nenhum pedido encontrado</h3>
                    <p className="text-purple-200">Aguardando novos pedidos...</p>
                  </div>
                </Card>
              ) : (
                pedidos.map((pedido) => (
                  <Card key={pedido.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-white text-xl">{pedido.cliente.nome_completo}</CardTitle>
                          <CardDescription className="text-purple-200">
                            Ritual: {pedido.ritual.nome} • R$ {pedido.valor_total.toFixed(2)}
                          </CardDescription>
                        </div>
                        <Badge className="bg-green-500/20 text-green-300 border-green-400/30">
                          Pago
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-purple-200 text-sm">Email:</p>
                          <p className="text-white">{pedido.cliente.email}</p>
                        </div>
                        <div>
                          <p className="text-purple-200 text-sm">WhatsApp:</p>
                          <p className="text-white">{pedido.cliente.telefone}</p>
                        </div>
                        <div>
                          <p className="text-purple-200 text-sm">Pessoa Amada:</p>
                          <p className="text-white">{pedido.cliente.nome_pessoa_amada}</p>
                        </div>
                        <div>
                          <p className="text-purple-200 text-sm">Data de Nascimento:</p>
                          <p className="text-white">{pedido.cliente.data_nascimento}</p>
                        </div>
                      </div>
                      
                      {pedido.cliente.informacoes_adicionais && (
                        <div className="mb-4">
                          <p className="text-purple-200 text-sm">Informações Adicionais:</p>
                          <p className="text-white bg-black/20 p-3 rounded-lg">{pedido.cliente.informacoes_adicionais}</p>
                        </div>
                      )}

                      <Button
                        onClick={() => abrirWhatsApp(
                          pedido.cliente.telefone,
                          pedido.cliente.nome_completo,
                          pedido.ritual.nome
                        )}
                        className="w-full bg-green-600 hover:bg-green-700 text-white flex items-center justify-center gap-2"
                      >
                        <Phone className="w-4 h-4" />
                        Contatar via WhatsApp
                      </Button>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="rituais" className="mt-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Rituais Cadastrados</h2>
              <Button
                onClick={() => setShowAddRitual(true)}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Adicionar Ritual
              </Button>
            </div>

            {showAddRitual && (
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm mb-6">
                <CardHeader>
                  <CardTitle className="text-white">
                    {editingRitual ? "Editar Ritual" : "Novo Ritual"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleAddRitual} className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="nome" className="text-white">Nome do Ritual</Label>
                        <Input
                          id="nome"
                          value={novoRitual.nome}
                          onChange={(e) => setNovoRitual({...novoRitual, nome: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="preco" className="text-white">Preço (R$)</Label>
                        <Input
                          id="preco"
                          type="number"
                          step="0.01"
                          value={novoRitual.preco}
                          onChange={(e) => setNovoRitual({...novoRitual, preco: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          required
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="descricao" className="text-white">Descrição</Label>
                      <Textarea
                        id="descricao"
                        value={novoRitual.descricao}
                        onChange={(e) => setNovoRitual({...novoRitual, descricao: e.target.value})}
                        className="bg-white/5 border-purple-300/30 text-white"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="imagem_url" className="text-white">URL da Imagem (opcional)</Label>
                      <Input
                        id="imagem_url"
                        value={novoRitual.imagem_url}
                        onChange={(e) => setNovoRitual({...novoRitual, imagem_url: e.target.value})}
                        className="bg-white/5 border-purple-300/30 text-white"
                        placeholder="https://exemplo.com/imagem.jpg"
                      />
                    </div>

                    <div className="flex items-center space-x-2">
                      <Switch
                        id="visivel"
                        checked={novoRitual.visivel}
                        onCheckedChange={(checked) => setNovoRitual({...novoRitual, visivel: checked})}
                      />
                      <Label htmlFor="visivel" className="text-white">Visível no site</Label>
                    </div>

                    <div className="space-y-4 border-t border-purple-300/20 pt-4">
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="tem_desconto"
                          checked={novoRitual.tem_desconto}
                          onCheckedChange={(checked) => setNovoRitual({...novoRitual, tem_desconto: checked})}
                        />
                        <Label htmlFor="tem_desconto" className="text-white">Tem desconto</Label>
                      </div>

                      {novoRitual.tem_desconto && (
                        <div className="grid md:grid-cols-2 gap-4 ml-6">
                          <div>
                            <Label htmlFor="desconto_valor" className="text-white">Desconto em R$ (opcional)</Label>
                            <Input
                              id="desconto_valor"
                              type="number"
                              step="0.01"
                              value={novoRitual.desconto_valor}
                              onChange={(e) => setNovoRitual({...novoRitual, desconto_valor: e.target.value})}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="10.00"
                            />
                          </div>
                          <div>
                            <Label htmlFor="desconto_percentual" className="text-white">Desconto em % (opcional)</Label>
                            <Input
                              id="desconto_percentual"
                              type="number"
                              step="0.1"
                              min="0"
                              max="100"
                              value={novoRitual.desconto_percentual}
                              onChange={(e) => setNovoRitual({...novoRitual, desconto_percentual: e.target.value})}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="15"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex gap-2">
                      <Button type="submit" className="bg-green-600 hover:bg-green-700">
                        {editingRitual ? "Atualizar Ritual" : "Salvar Ritual"}
                      </Button>
                      <Button 
                        type="button" 
                        onClick={() => {
                          setShowAddRitual(false);
                          setEditingRitual(null);
                          setNovoRitual({ 
                            nome: "", 
                            descricao: "", 
                            preco: "", 
                            imagem_url: "",
                            visivel: true,
                            tem_desconto: false,
                            desconto_valor: "",
                            desconto_percentual: ""
                          });
                        }}
                        className="bg-gray-600 hover:bg-gray-700"
                      >
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 admin-grid">
              {rituais.map((ritual) => (
                <Card key={ritual.id} className={`bg-white/10 border-purple-300/30 backdrop-blur-sm admin-card ${!ritual.visivel ? 'opacity-60' : ''}`}>
                  <CardHeader>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-2 sm:space-y-0">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg text-purple-300">
                          {getIconForRitual(ritual.nome)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <CardTitle className="text-white text-base md:text-lg">{ritual.nome}</CardTitle>
                            {!ritual.visivel && <EyeOff className="w-4 h-4 text-gray-400" />}
                            {ritual.visivel && <Eye className="w-4 h-4 text-green-400" />}
                          </div>
                          <div className="flex flex-wrap items-center gap-2 mt-1">
                            <Badge className="bg-purple-500/20 text-purple-200 border-purple-400/30 text-xs">
                              R$ {ritual.preco.toFixed(2)}
                            </Badge>
                            {ritual.tem_desconto && (
                              <Badge className="bg-red-500/20 text-red-300 border-red-400/30 text-xs">
                                {ritual.desconto_percentual ? `${ritual.desconto_percentual}% OFF` : 
                                 ritual.desconto_valor ? `R$ ${ritual.desconto_valor.toFixed(2)} OFF` : 'DESCONTO'}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 button-group">
                        <Button
                          size="sm"
                          onClick={() => handleEditRitual(ritual)}
                          className="bg-blue-600 hover:bg-blue-700 p-2 flex-shrink-0"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDeleteRitual(ritual.id)}
                          className="bg-red-600 hover:bg-red-700 p-2 flex-shrink-0"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-purple-100 text-sm line-clamp-2">{ritual.descricao}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="semana" className="mt-6">
            <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  Rituais da Semana
                </CardTitle>
                <CardDescription className="text-purple-200">
                  Configure quais rituais aparecerão em destaque em cada dia da semana
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSaveRituaisSemana}>
                  <div className="grid gap-4">
                    {["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"].map((dia) => (
                      <div key={dia} className="flex items-center justify-between p-4 bg-black/20 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className="w-20 text-white font-medium capitalize">
                            {dia === "terca" ? "Terça" : 
                             dia === "quarta" ? "Quarta" : 
                             dia === "quinta" ? "Quinta" : 
                             dia === "sexta" ? "Sexta" : 
                             dia === "sabado" ? "Sábado" : 
                             dia === "domingo" ? "Domingo" : "Segunda"}
                          </div>
                          <Select
                            value={rituaisSemanaForm[dia]?.ritual_id || undefined}
                            onValueChange={(value) => updateRitualSemana(dia, 'ritual_id', value)}
                          >
                            <SelectTrigger className="w-60 bg-white/5 border-purple-300/30 text-white">
                              <SelectValue placeholder="Escolher ritual..." />
                            </SelectTrigger>
                            <SelectContent>
                              {rituais.map((ritual) => (
                                <SelectItem key={ritual.id} value={ritual.id}>
                                  {ritual.nome} - R$ {ritual.preco.toFixed(2)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Label htmlFor={`switch-${dia}`} className="text-white text-sm">
                            Ativo
                          </Label>
                          <Switch
                            id={`switch-${dia}`}
                            checked={rituaisSemanaForm[dia]?.ativo || false}
                            onCheckedChange={(checked) => updateRitualSemana(dia, 'ativo', checked)}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6">
                    <Button type="submit" className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                      Salvar Rituais da Semana
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="usuarios" className="mt-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Usuários do Sistema</h2>
              <Button
                onClick={() => setShowAddUser(true)}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              >
                <Users className="w-4 h-4 mr-2" />
                Adicionar Usuário
              </Button>
            </div>

            {showAddUser && (
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm mb-6">
                <CardHeader>
                  <CardTitle className="text-white">Novo Usuário</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleAddUser} className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="new_username" className="text-white">Nome de Usuário</Label>
                        <Input
                          id="new_username"
                          value={novoUsuario.username}
                          onChange={(e) => setNovoUsuario({...novoUsuario, username: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="new_email" className="text-white">Email</Label>
                        <Input
                          id="new_email"
                          type="email"
                          value={novoUsuario.email}
                          onChange={(e) => setNovoUsuario({...novoUsuario, email: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="new_password" className="text-white">Senha</Label>
                      <Input
                        id="new_password"
                        type="password"
                        value={novoUsuario.password}
                        onChange={(e) => setNovoUsuario({...novoUsuario, password: e.target.value})}
                        className="bg-white/5 border-purple-300/30 text-white"
                        required
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button type="submit" className="bg-green-600 hover:bg-green-700">
                        Criar Usuário
                      </Button>
                      <Button 
                        type="button" 
                        onClick={() => {
                          setShowAddUser(false);
                          setNovoUsuario({ username: "", email: "", password: "" });
                        }}
                        className="bg-gray-600 hover:bg-gray-700"
                      >
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <div className="grid gap-4">
              {usuarios.map((usuario) => (
                <Card key={usuario.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-purple-500/20 rounded-full">
                          <Users className="w-6 h-6 text-purple-300" />
                        </div>
                        <div>
                          <h3 className="text-white font-semibold text-lg">{usuario.username}</h3>
                          <p className="text-purple-200">{usuario.email}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            {usuario.is_active && (
                              <Badge className="bg-green-500/20 text-green-300 border-green-400/30 text-xs">
                                Ativo
                              </Badge>
                            )}
                            {usuario.is_admin && (
                              <Badge className="bg-blue-500/20 text-blue-300 border-blue-400/30 text-xs">
                                Admin
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      {usuario.id !== user?.id && (
                        <Button
                          size="sm"
                          onClick={() => handleDeleteUser(usuario.id)}
                          className="bg-red-600 hover:bg-red-700 p-2"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="pagamentos" className="mt-6">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">Gateways de Pagamento</h2>
              <p className="text-purple-200">Configure os provedores de pagamento do seu site</p>
            </div>

            <div className="grid gap-6">
              {gateways.map((gateway) => (
                <Card key={gateway.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`p-3 rounded-lg ${
                          gateway.name === 'stripe' ? 'bg-blue-500/20 text-blue-300' :
                          gateway.name === 'pagbank' ? 'bg-orange-500/20 text-orange-300' :
                          gateway.name === 'mercadopago' ? 'bg-cyan-500/20 text-cyan-300' :
                          'bg-purple-500/20 text-purple-300'
                        }`}>
                          <CreditCard className="w-6 h-6" />
                        </div>
                        <div>
                          <CardTitle className="text-white text-xl">{gateway.display_name}</CardTitle>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge className={`text-xs ${
                              gateway.is_active 
                                ? 'bg-green-500/20 text-green-300 border-green-400/30' 
                                : 'bg-red-500/20 text-red-300 border-red-400/30'
                            }`}>
                              {gateway.is_active ? 'Ativo' : 'Inativo'}
                            </Badge>
                            {gateway.is_default && (
                              <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-400/30 text-xs">
                                Padrão
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          onClick={() => handleTestGateway(gateway.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                        >
                          <TestTube className="w-4 h-4 mr-2" />
                          Testar
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => setEditingGateway(gateway)}
                          className="bg-purple-600 hover:bg-purple-700 text-white"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-purple-200 text-sm">Métodos Suportados:</p>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {gateway.supported_methods.map((method) => (
                            <Badge key={method} variant="outline" className="text-xs bg-white/5 text-purple-200">
                              {method === 'credit_card' ? 'Cartão de Crédito' :
                               method === 'pix' ? 'PIX' :
                               method === 'boleto' ? 'Boleto' : method}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={gateway.is_active}
                            onCheckedChange={(checked) => 
                              handleUpdateGateway(gateway.id, { is_active: checked })
                            }
                          />
                          <Label className="text-white text-sm">Ativo</Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={gateway.is_default}
                            onCheckedChange={(checked) => 
                              handleUpdateGateway(gateway.id, { is_default: checked })
                            }
                          />
                          <Label className="text-white text-sm">Padrão</Label>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Modal de Edição de Gateway */}
            {editingGateway && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                  <CardHeader>
                    <CardTitle className="text-white">Configurar {editingGateway.display_name}</CardTitle>
                    <CardDescription className="text-purple-200">
                      Configure as chaves de API e parâmetros do gateway
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form 
                      onSubmit={(e) => {
                        e.preventDefault();
                        const formData = new FormData(e.target);
                        const config = {};
                        
                        // Coleta as configurações baseado no gateway
                        if (editingGateway.name === 'stripe') {
                          config.api_key = formData.get('api_key');
                          config.webhook_secret = formData.get('webhook_secret');
                          config.currency = formData.get('currency') || 'brl';
                        } else if (editingGateway.name === 'pagbank') {
                          config.client_id = formData.get('client_id');
                          config.client_secret = formData.get('client_secret');
                          config.sandbox = formData.get('sandbox') === 'on' ? 'true' : 'false';
                        } else if (editingGateway.name === 'mercadopago') {
                          config.access_token = formData.get('access_token');
                          config.public_key = formData.get('public_key');
                          config.sandbox = formData.get('sandbox') === 'on' ? 'true' : 'false';
                        }
                        
                        handleUpdateGateway(editingGateway.id, { config });
                      }}
                      className="space-y-4"
                    >
                      {editingGateway.name === 'stripe' && (
                        <>
                          <div>
                            <Label htmlFor="api_key" className="text-white">API Key</Label>
                            <Input
                              id="api_key"
                              name="api_key"
                              type="password"
                              defaultValue={editingGateway.config?.api_key || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="sk_test_..."
                            />
                          </div>
                          <div>
                            <Label htmlFor="webhook_secret" className="text-white">Webhook Secret</Label>
                            <Input
                              id="webhook_secret"
                              name="webhook_secret"
                              type="password"
                              defaultValue={editingGateway.config?.webhook_secret || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="whsec_..."
                            />
                          </div>
                          <div>
                            <Label htmlFor="currency" className="text-white">Moeda</Label>
                            <Input
                              id="currency"
                              name="currency"
                              defaultValue={editingGateway.config?.currency || 'brl'}
                              className="bg-white/5 border-purple-300/30 text-white"
                            />
                          </div>
                        </>
                      )}
                      
                      {editingGateway.name === 'pagbank' && (
                        <>
                          <div>
                            <Label htmlFor="client_id" className="text-white">Client ID</Label>
                            <Input
                              id="client_id"
                              name="client_id"
                              defaultValue={editingGateway.config?.client_id || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                            />
                          </div>
                          <div>
                            <Label htmlFor="client_secret" className="text-white">Client Secret</Label>
                            <Input
                              id="client_secret"
                              name="client_secret"
                              type="password"
                              defaultValue={editingGateway.config?.client_secret || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                            />
                          </div>
                          <div className="flex items-center space-x-2">
                            <Switch
                              id="sandbox"
                              name="sandbox"
                              defaultChecked={editingGateway.config?.sandbox === 'true'}
                            />
                            <Label htmlFor="sandbox" className="text-white">Modo Sandbox</Label>
                          </div>
                        </>
                      )}
                      
                      {editingGateway.name === 'mercadopago' && (
                        <>
                          <div>
                            <Label htmlFor="access_token" className="text-white">Access Token</Label>
                            <Input
                              id="access_token"
                              name="access_token"
                              type="password"
                              defaultValue={editingGateway.config?.access_token || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="APP_USR-..."
                            />
                          </div>
                          <div>
                            <Label htmlFor="public_key" className="text-white">Public Key</Label>
                            <Input
                              id="public_key"
                              name="public_key"
                              defaultValue={editingGateway.config?.public_key || ''}
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="APP_USR-..."
                            />
                          </div>
                          <div className="flex items-center space-x-2">
                            <Switch
                              id="sandbox"
                              name="sandbox"
                              defaultChecked={editingGateway.config?.sandbox === 'true'}
                            />
                            <Label htmlFor="sandbox" className="text-white">Modo Sandbox</Label>
                          </div>
                        </>
                      )}
                      
                      <div className="flex gap-2 pt-4">
                        <Button type="submit" className="bg-green-600 hover:bg-green-700">
                          Salvar Configurações
                        </Button>
                        <Button 
                          type="button" 
                          onClick={() => setEditingGateway(null)}
                          className="bg-gray-600 hover:bg-gray-700"
                        >
                          Cancelar
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="instagram" className="mt-6">
            <div className="space-y-6">
              {/* Configuração da API Instagram */}
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Instagram className="w-5 h-5 mr-2" />
                    Configuração da API Instagram
                  </CardTitle>
                  <CardDescription className="text-purple-200">
                    Configure as credenciais da sua aplicação Instagram para sincronização automática
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <InstagramApiConfigSection />
                </CardContent>
              </Card>

              {/* Status da Conexão Instagram */}
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Instagram className="w-5 h-5 mr-2" />
                    Conta Instagram Conectada
                  </CardTitle>
                  <CardDescription className="text-purple-200">
                    Status da conexão com sua conta Instagram
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <InstagramApiStatusSection />
                </CardContent>
              </Card>

              {/* Perfil Instagram (Manual) */}
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Instagram className="w-5 h-5 mr-2" />
                    Perfil Instagram (Manual)
                  </CardTitle>
                  <CardDescription className="text-purple-200">
                    Configure seu perfil Instagram manualmente (alternativa à sincronização automática)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form 
                    onSubmit={(e) => {
                      e.preventDefault();
                      const formData = new FormData(e.target);
                      const profileData = {
                        username: formData.get('username'),
                        display_name: formData.get('display_name'),
                        bio: formData.get('bio'),
                        profile_image_url: formData.get('profile_image_url'),
                        instagram_url: formData.get('instagram_url'),
                        followers_count: parseInt(formData.get('followers_count')) || null,
                        is_active: formData.get('is_active') === 'on'
                      };
                      handleUpdateInstagramProfile(profileData);
                    }}
                    className="space-y-4"
                  >
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="username" className="text-white">Nome de usuário (@)</Label>
                        <Input
                          id="username"
                          name="username"
                          defaultValue={instagramProfile?.username || ''}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="meu_instagram"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="display_name" className="text-white">Nome de exibição</Label>
                        <Input
                          id="display_name"
                          name="display_name"
                          defaultValue={instagramProfile?.display_name || ''}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="Meu Nome"
                          required
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="bio" className="text-white">Bio</Label>
                      <Textarea
                        id="bio"
                        name="bio"
                        defaultValue={instagramProfile?.bio || ''}
                        className="bg-white/5 border-purple-300/30 text-white"
                        placeholder="Sua descrição do Instagram..."
                        rows={3}
                        required
                      />
                    </div>
                    
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="profile_image_url" className="text-white">URL da foto de perfil</Label>
                        <Input
                          id="profile_image_url"
                          name="profile_image_url"
                          defaultValue={instagramProfile?.profile_image_url || ''}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="https://exemplo.com/foto.jpg"
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="instagram_url" className="text-white">Link do Instagram</Label>
                        <Input
                          id="instagram_url"
                          name="instagram_url"
                          defaultValue={instagramProfile?.instagram_url || ''}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="https://instagram.com/meu_instagram"
                          required
                        />
                      </div>
                    </div>
                    
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="followers_count" className="text-white">Número de seguidores (opcional)</Label>
                        <Input
                          id="followers_count"
                          name="followers_count"
                          type="number"
                          defaultValue={instagramProfile?.followers_count || ''}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="1000"
                        />
                      </div>
                      <div className="flex items-center space-x-2 pt-6">
                        <Switch
                          id="is_active"
                          name="is_active"
                          defaultChecked={instagramProfile?.is_active !== false}
                        />
                        <Label htmlFor="is_active" className="text-white">Mostrar na página inicial</Label>
                      </div>
                    </div>
                    
                    <Button type="submit" className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                      Salvar Perfil
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Posts Instagram */}
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle className="text-white flex items-center">
                        <Image className="w-5 h-5 mr-2" />
                        Posts Instagram
                      </CardTitle>
                      <CardDescription className="text-purple-200">
                        Gerencie os posts que aparecem na página inicial
                      </CardDescription>
                    </div>
                    <Button
                      onClick={() => setShowAddPost(true)}
                      className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Adicionar Post
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Formulário para adicionar post */}
                  {showAddPost && (
                    <Card className="bg-white/5 border-purple-300/20 mb-6">
                      <CardHeader>
                        <CardTitle className="text-white text-lg">Novo Post</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <form 
                          onSubmit={(e) => {
                            e.preventDefault();
                            const formData = new FormData(e.target);
                            const postData = {
                              image_url: formData.get('image_url'),
                              caption: formData.get('caption'),
                              post_url: formData.get('post_url'),
                              is_active: formData.get('is_active') === 'on',
                              order: parseInt(formData.get('order')) || 0
                            };
                            handleAddInstagramPost(postData);
                          }}
                          className="space-y-4"
                        >
                          <div>
                            <Label htmlFor="image_url" className="text-white">URL da Imagem</Label>
                            <Input
                              id="image_url"
                              name="image_url"
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="https://exemplo.com/imagem.jpg"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="caption" className="text-white">Legenda</Label>
                            <Textarea
                              id="caption"
                              name="caption"
                              className="bg-white/5 border-purple-300/30 text-white"
                              placeholder="Legenda do post..."
                              rows={3}
                              required
                            />
                          </div>
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="post_url" className="text-white">Link do Post (opcional)</Label>
                              <Input
                                id="post_url"
                                name="post_url"
                                className="bg-white/5 border-purple-300/30 text-white"
                                placeholder="https://instagram.com/p/..."
                              />
                            </div>
                            <div>
                              <Label htmlFor="order" className="text-white">Ordem</Label>
                              <Input
                                id="order"
                                name="order"
                                type="number"
                                className="bg-white/5 border-purple-300/30 text-white"
                                placeholder="0"
                                defaultValue="0"
                              />
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Switch
                              id="is_active"
                              name="is_active"
                              defaultChecked={true}
                            />
                            <Label htmlFor="is_active" className="text-white">Ativo</Label>
                          </div>
                          <div className="flex gap-2">
                            <Button type="submit" className="bg-green-600 hover:bg-green-700">
                              Adicionar Post
                            </Button>
                            <Button 
                              type="button" 
                              onClick={() => setShowAddPost(false)}
                              className="bg-gray-600 hover:bg-gray-700"
                            >
                              Cancelar
                            </Button>
                          </div>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  {/* Lista de posts */}
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {instagramPosts.map((post) => (
                      <Card key={post.id} className="bg-white/5 border-purple-300/20">
                        <CardContent className="p-4">
                          <div className="aspect-square mb-3 rounded-lg overflow-hidden bg-gray-700">
                            <img 
                              src={post.image_url} 
                              alt={post.caption}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23374151"/><text x="50" y="50" text-anchor="middle" dominant-baseline="central" fill="white" font-family="Arial" font-size="12">Imagem não encontrada</text></svg>';
                              }}
                            />
                          </div>
                          <p className="text-white text-sm line-clamp-2 mb-3">{post.caption}</p>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Badge className={`text-xs ${
                                post.is_active 
                                  ? 'bg-green-500/20 text-green-300 border-green-400/30' 
                                  : 'bg-red-500/20 text-red-300 border-red-400/30'
                              }`}>
                                {post.is_active ? 'Ativo' : 'Inativo'}
                              </Badge>
                              <Badge variant="outline" className="text-xs bg-white/5 text-purple-200">
                                #{post.order}
                              </Badge>
                            </div>
                            <div className="flex space-x-1">
                              <Button
                                size="sm"
                                onClick={() => setEditingPost(post)}
                                className="bg-blue-600 hover:bg-blue-700 p-1"
                              >
                                <Edit className="w-3 h-3" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleDeleteInstagramPost(post.id)}
                                className="bg-red-600 hover:bg-red-700 p-1"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {instagramPosts.length === 0 && (
                    <div className="text-center py-8">
                      <Image className="w-12 h-12 text-purple-300 mx-auto mb-4" />
                      <p className="text-white">Nenhum post adicionado ainda</p>
                      <p className="text-purple-200 text-sm">Clique em "Adicionar Post" para começar</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="config" className="mt-6">
            <div className="grid gap-6">
              <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Settings className="w-5 h-5 mr-2" />
                    Configurações Gerais
                  </CardTitle>
                  <CardDescription className="text-purple-200">
                    Personalize a aparência e comportamento do seu site
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleUpdateConfig} className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="logo_url" className="text-white">URL do Logo</Label>
                        <Input
                          id="logo_url"
                          value={configForm.logo_url || ""}
                          onChange={(e) => setConfigForm({...configForm, logo_url: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="https://exemplo.com/logo.png"
                        />
                        <p className="text-purple-300 text-sm mt-1">Logo que aparecerá no topo do site</p>
                      </div>
                      <div>
                        <Label htmlFor="whatsapp_numero" className="text-white">WhatsApp de Contato</Label>
                        <Input
                          id="whatsapp_numero"
                          value={configForm.whatsapp_numero || ""}
                          onChange={(e) => setConfigForm({...configForm, whatsapp_numero: e.target.value})}
                          className="bg-white/5 border-purple-300/30 text-white"
                          placeholder="(11) 99999-9999"
                        />
                        <p className="text-purple-300 text-sm mt-1">Número que receberá as mensagens dos clientes</p>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="stripe_snippet_id" className="text-white">ID do Snippet Stripe</Label>
                      <Input
                        id="stripe_snippet_id"
                        value={configForm.stripe_snippet_id || ""}
                        onChange={(e) => setConfigForm({...configForm, stripe_snippet_id: e.target.value})}
                        className="bg-white/5 border-purple-300/30 text-white"
                        placeholder="sk_test_..."
                      />
                      <p className="text-purple-300 text-sm mt-1">ID do snippet de código do Stripe para pagamentos</p>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-white font-semibold flex items-center">
                        <Palette className="w-4 h-4 mr-2" />
                        Cores do Site
                      </h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="primary_color" className="text-white">Cor Primária</Label>
                          <Input
                            id="primary_color"
                            type="color"
                            value={configForm.cores?.primary || "#8b5cf6"}
                            onChange={(e) => setConfigForm({
                              ...configForm, 
                              cores: {...configForm.cores, primary: e.target.value}
                            })}
                            className="bg-white/5 border-purple-300/30 h-12"
                          />
                        </div>
                        <div>
                          <Label htmlFor="secondary_color" className="text-white">Cor Secundária</Label>
                          <Input
                            id="secondary_color"
                            type="color"
                            value={configForm.cores?.secondary || "#ec4899"}
                            onChange={(e) => setConfigForm({
                              ...configForm, 
                              cores: {...configForm.cores, secondary: e.target.value}
                            })}
                            className="bg-white/5 border-purple-300/30 h-12"
                          />
                        </div>
                      </div>
                    </div>

                    <Button type="submit" className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                      Salvar Configurações
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Componente principal App
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/sucesso" element={<Sucesso />} />
            <Route path="/login" element={<LoginPage />} />
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute>
                  <AdminPanel />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" />
      </div>
    </AuthProvider>
  );
}

export default App;