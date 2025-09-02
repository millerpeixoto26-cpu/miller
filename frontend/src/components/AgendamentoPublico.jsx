import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { 
  Calendar, 
  Clock, 
  DollarSign,
  User,
  Phone,
  Mail,
  Heart,
  CalendarDays,
  CheckCircle,
  ArrowRight,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AgendamentoPublico = () => {
  const [step, setStep] = useState(1); // 1: Escolher consulta, 2: Escolher horário, 3: Dados cliente, 4: Pagamento
  const [tiposConsulta, setTiposConsulta] = useState([]);
  const [selectedTipo, setSelectedTipo] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [horariosLivres, setHorariosLivres] = useState([]);
  const [loading, setLoading] = useState(false);
  const [clienteData, setClienteData] = useState({
    nome_completo: '',
    email: '',
    telefone: '',
    nome_pessoa_amada: '',
    data_nascimento: '',
    informacoes_adicionais: ''
  });

  useEffect(() => {
    fetchTiposConsulta();
  }, []);

  const fetchTiposConsulta = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/tipos-consulta`);
      setTiposConsulta(response.data);
    } catch (error) {
      console.error("Erro ao buscar tipos de consulta:", error);
    }
  };

  const fetchHorariosLivres = async (data) => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/horarios-disponiveis/${data}`);
      setHorariosLivres(response.data.horarios_livres || []);
    } catch (error) {
      console.error("Erro ao buscar horários:", error);
      setHorariosLivres([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTipo = (tipo) => {
    setSelectedTipo(tipo);
    setStep(2);
  };

  const handleDateChange = (date) => {
    setSelectedDate(date);
    setSelectedTime('');
    if (date) {
      fetchHorariosLivres(date);
    }
  };

  const handleTimeSelect = (time) => {
    setSelectedTime(time);
    setStep(3);
  };

  const handleClienteDataChange = (field, value) => {
    setClienteData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmitAgendamento = async (e) => {
    e.preventDefault();
    
    if (!selectedTipo || !selectedDate || !selectedTime) {
      toast.error("Por favor, complete todas as etapas do agendamento");
      return;
    }

    try {
      setLoading(true);

      // Criar datetime completo
      const dataAgendada = new Date(`${selectedDate}T${selectedTime}:00`);

      const agendamentoData = {
        consulta: {
          tipo_consulta_id: selectedTipo.id,
          data_agendada: dataAgendada.toISOString(),
          observacoes: clienteData.informacoes_adicionais
        },
        cliente: clienteData
      };

      const response = await axios.post(`${BACKEND_URL}/api/agendamento`, agendamentoData);
      
      if (response.data.session_id) {
        setStep(4);
        // Aqui você integraria com o sistema de pagamento
        toast.success("Dados salvos! Prossiga com o pagamento para confirmar.");
        
        // Simular redirecionamento para pagamento (integrar com Stripe posteriormente)
        setTimeout(() => {
          toast.success("Consulta agendada com sucesso! Você receberá uma confirmação por WhatsApp.");
          resetForm();
        }, 3000);
      }

    } catch (error) {
      console.error("Erro ao criar agendamento:", error);
      toast.error(error.response?.data?.detail || "Erro ao agendar consulta");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setSelectedTipo(null);
    setSelectedDate('');
    setSelectedTime('');
    setHorariosLivres([]);
    setClienteData({
      nome_completo: '',
      email: '',
      telefone: '',
      nome_pessoa_amada: '',
      data_nascimento: '',
      informacoes_adicionais: ''
    });
  };

  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 30); // 30 dias no futuro
    return maxDate.toISOString().split('T')[0];
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="flex items-center justify-center mb-12 space-x-4">
        {[1, 2, 3, 4].map((stepNum) => (
          <div key={stepNum} className="flex items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm ${
              stepNum <= step 
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white' 
                : 'bg-gray-700 text-gray-400'
            }`}>
              {stepNum}
            </div>
            {stepNum < 4 && (
              <div className={`w-12 h-1 mx-2 ${
                stepNum < step ? 'bg-gradient-to-r from-purple-600 to-pink-600' : 'bg-gray-700'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Escolher Tipo de Consulta */}
      {step === 1 && (
        <div>
          <h3 className="text-2xl font-bold text-white text-center mb-8">Escolha o Tipo de Consulta</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tiposConsulta.map((tipo) => (
              <Card 
                key={tipo.id} 
                className="bg-white/10 border-purple-300/30 backdrop-blur-sm hover:bg-white/15 transition-all duration-300 cursor-pointer group"
                onClick={() => handleSelectTipo(tipo)}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div 
                      className="w-6 h-6 rounded-full" 
                      style={{ backgroundColor: tipo.cor_tema }}
                    ></div>
                    <Badge className="bg-green-500/20 text-green-300 border-green-400/30">
                      {tipo.duracao_minutos} min
                    </Badge>
                  </div>
                  
                  <h4 className="text-xl font-bold text-white mb-3 group-hover:text-purple-200 transition-colors">
                    {tipo.nome}
                  </h4>
                  
                  <p className="text-purple-200 text-sm mb-4 leading-relaxed">
                    {tipo.descricao}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center text-2xl font-bold text-white">
                      <DollarSign className="w-6 h-6 mr-1" />
                      R$ {tipo.preco.toFixed(2)}
                    </div>
                    <ArrowRight className="w-5 h-5 text-purple-400 group-hover:text-white transition-colors" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Escolher Data e Horário */}
      {step === 2 && selectedTipo && (
        <div>
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-white mb-2">Escolha Data e Horário</h3>
            <p className="text-purple-200">
              {selectedTipo.nome} • R$ {selectedTipo.preco.toFixed(2)} • {selectedTipo.duracao_minutos} minutos
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Seleção de Data */}
            <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  Selecione a Data
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => handleDateChange(e.target.value)}
                  min={getMinDate()}
                  max={getMaxDate()}
                  className="bg-white/5 border-purple-300/30 text-white"
                />
                <p className="text-purple-300 text-xs mt-2">
                  Disponível até 30 dias antecipados
                </p>
              </CardContent>
            </Card>

            {/* Seleção de Horário */}
            <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  Horários Disponíveis
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!selectedDate ? (
                  <p className="text-purple-300 text-center py-8">
                    Selecione uma data primeiro
                  </p>
                ) : loading ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-400 mx-auto" />
                    <p className="text-purple-300 mt-2">Carregando horários...</p>
                  </div>
                ) : horariosLivres.length === 0 ? (
                  <p className="text-red-300 text-center py-8">
                    Nenhum horário disponível para esta data
                  </p>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    {horariosLivres.map((horario) => (
                      <Button
                        key={horario}
                        onClick={() => handleTimeSelect(horario)}
                        className={`p-3 text-sm ${
                          selectedTime === horario
                            ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                            : 'bg-white/10 text-purple-200 hover:bg-white/20'
                        }`}
                      >
                        {horario}
                      </Button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="text-center mt-8">
            <Button 
              onClick={() => setStep(1)}
              className="bg-gray-600 hover:bg-gray-700 mr-4"
            >
              Voltar
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Dados do Cliente */}
      {step === 3 && (
        <div>
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-white mb-2">Seus Dados</h3>
            <p className="text-purple-200">
              {selectedTipo.nome} • {new Date(selectedDate).toLocaleDateString('pt-BR')} às {selectedTime}
            </p>
          </div>

          <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm max-w-2xl mx-auto">
            <CardContent className="p-8">
              <form onSubmit={handleSubmitAgendamento} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="nome_completo" className="text-white flex items-center">
                      <User className="w-4 h-4 mr-2" />
                      Nome Completo
                    </Label>
                    <Input
                      id="nome_completo"
                      value={clienteData.nome_completo}
                      onChange={(e) => handleClienteDataChange('nome_completo', e.target.value)}
                      className="bg-white/5 border-purple-300/30 text-white"
                      placeholder="Seu nome completo"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="telefone" className="text-white flex items-center">
                      <Phone className="w-4 h-4 mr-2" />
                      WhatsApp
                    </Label>
                    <Input
                      id="telefone"
                      value={clienteData.telefone}
                      onChange={(e) => handleClienteDataChange('telefone', e.target.value)}
                      className="bg-white/5 border-purple-300/30 text-white"
                      placeholder="(11) 99999-9999"
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="email" className="text-white flex items-center">
                    <Mail className="w-4 h-4 mr-2" />
                    E-mail
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={clienteData.email}
                    onChange={(e) => handleClienteDataChange('email', e.target.value)}
                    className="bg-white/5 border-purple-300/30 text-white"
                    placeholder="seu@email.com"
                    required
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="nome_pessoa_amada" className="text-white flex items-center">
                      <Heart className="w-4 h-4 mr-2" />
                      Nome da Pessoa Amada
                    </Label>
                    <Input
                      id="nome_pessoa_amada"
                      value={clienteData.nome_pessoa_amada}
                      onChange={(e) => handleClienteDataChange('nome_pessoa_amada', e.target.value)}
                      className="bg-white/5 border-purple-300/30 text-white"
                      placeholder="Nome da pessoa"
                    />
                  </div>
                  <div>
                    <Label htmlFor="data_nascimento" className="text-white flex items-center">
                      <CalendarDays className="w-4 h-4 mr-2" />
                      Data de Nascimento
                    </Label>
                    <Input
                      id="data_nascimento"
                      type="date"
                      value={clienteData.data_nascimento}
                      onChange={(e) => handleClienteDataChange('data_nascimento', e.target.value)}
                      className="bg-white/5 border-purple-300/30 text-white"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="informacoes_adicionais" className="text-white">
                    Informações Adicionais (Opcional)
                  </Label>
                  <Textarea
                    id="informacoes_adicionais"
                    value={clienteData.informacoes_adicionais}
                    onChange={(e) => handleClienteDataChange('informacoes_adicionais', e.target.value)}
                    className="bg-white/5 border-purple-300/30 text-white"
                    placeholder="Alguma informação que gostaria de compartilhar..."
                    rows={3}
                  />
                </div>

                <div className="flex gap-4">
                  <Button 
                    type="button"
                    onClick={() => setStep(2)}
                    className="bg-gray-600 hover:bg-gray-700 flex-1"
                  >
                    Voltar
                  </Button>
                  <Button 
                    type="submit"
                    disabled={loading}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 flex-1"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processando...
                      </>
                    ) : (
                      <>
                        Prosseguir para Pagamento
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 4: Confirmação */}
      {step === 4 && (
        <div className="text-center">
          <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm max-w-md mx-auto">
            <CardContent className="p-8">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-6" />
              <h3 className="text-2xl font-bold text-white mb-4">Consulta Agendada!</h3>
              <p className="text-purple-200 mb-6">
                Sua consulta foi agendada com sucesso. Você receberá uma confirmação via WhatsApp em breve.
              </p>
              <div className="bg-black/20 rounded-lg p-4 mb-6 text-left">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-purple-300">Consulta:</span>
                    <span className="text-white">{selectedTipo?.nome}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-300">Data:</span>
                    <span className="text-white">{new Date(selectedDate).toLocaleDateString('pt-BR')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-300">Horário:</span>
                    <span className="text-white">{selectedTime}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-purple-300">Valor:</span>
                    <span className="text-white">R$ {selectedTipo?.preco.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              <Button 
                onClick={resetForm}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 w-full"
              >
                Agendar Nova Consulta
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AgendamentoPublico;