import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
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
import { Loader2, Heart, Shield, Sparkles, Star, Phone, Settings, Palette, Layout, Calendar } from "lucide-react";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Componente para Home
const Home = () => {
  const [rituais, setRituais] = useState([]);
  const [rituaisHoje, setRituaisHoje] = useState([]);
  const [configuracao, setConfiguracao] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRituais();
    fetchRituaisHoje();
    fetchConfiguracao();
  }, []);

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
  const [pedidos, setPedidos] = useState([]);
  const [rituais, setRituais] = useState([]);
  const [configuracao, setConfiguracao] = useState(null);
  const [rituaisSemana, setRituaisSemana] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddRitual, setShowAddRitual] = useState(false);
  const [editingRitual, setEditingRitual] = useState(null);
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
    fetchConfiguracao();
    fetchRituaisSemana();
  }, []);

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
    <div className="min-h-screen bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900 py-8 px-4">
      <div className="container mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Painel Administrativo</h1>
          <p className="text-purple-200">Gerencie pedidos, rituais e personalize o site</p>
        </div>

        <Tabs defaultValue="pedidos" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-white/10 backdrop-blur-sm">
            <TabsTrigger value="pedidos" className="data-[state=active]:bg-purple-600">
              <Phone className="w-4 h-4 mr-2" />
              Pedidos ({pedidos.length})
            </TabsTrigger>
            <TabsTrigger value="rituais" className="data-[state=active]:bg-purple-600">
              <Sparkles className="w-4 h-4 mr-2" />
              Rituais ({rituais.length})
            </TabsTrigger>
            <TabsTrigger value="semana" className="data-[state=active]:bg-purple-600">
              <Calendar className="w-4 h-4 mr-2" />
              Rituais da Semana
            </TabsTrigger>
            <TabsTrigger value="config" className="data-[state=active]:bg-purple-600">
              <Settings className="w-4 h-4 mr-2" />
              Configurações
            </TabsTrigger>
          </TabsList>

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
                  <CardTitle className="text-white">Novo Ritual</CardTitle>
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
                    <div className="flex gap-2">
                      <Button type="submit" className="bg-green-600 hover:bg-green-700">
                        Salvar Ritual
                      </Button>
                      <Button 
                        type="button" 
                        onClick={() => setShowAddRitual(false)}
                        className="bg-gray-600 hover:bg-gray-700"
                      >
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              {rituais.map((ritual) => (
                <Card key={ritual.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg text-purple-300">
                          {getIconForRitual(ritual.nome)}
                        </div>
                        <div>
                          <CardTitle className="text-white text-lg">{ritual.nome}</CardTitle>
                          <Badge className="bg-purple-500/20 text-purple-200 border-purple-400/30">
                            R$ {ritual.preco.toFixed(2)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-purple-100 text-sm">{ritual.descricao}</p>
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
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/sucesso" element={<Sucesso />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;