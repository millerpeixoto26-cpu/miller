import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Calendar, 
  Clock, 
  Plus, 
  Edit2, 
  Trash2, 
  DollarSign,
  Settings,
  Users,
  CheckCircle
} from 'lucide-react';

const AgendamentosTab = ({ 
  tiposConsulta,
  horariosDisponiveis,
  consultasVendas,
  showAddTipoConsulta,
  setShowAddTipoConsulta,
  showAddHorario,
  setShowAddHorario,
  editingTipoConsulta,
  setEditingTipoConsulta,
  editingHorario,
  setEditingHorario,
  handleAddTipoConsulta,
  handleDeleteTipoConsulta,
  handleAddHorario,
  handleDeleteHorario,
  getDiaSemanaName
}) => {
  return (
    <div className="space-y-6">
      {/* Estatísticas de Agendamentos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border-blue-400/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm font-medium">Consultas Ativas</p>
                <p className="text-2xl font-bold text-white">{consultasVendas.length}</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/10 to-green-600/10 border-green-400/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm font-medium">Tipos de Consulta</p>
                <p className="text-2xl font-bold text-white">{tiposConsulta.filter(t => t.ativo).length}</p>
              </div>
              <Settings className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border-purple-400/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm font-medium">Horários Configurados</p>
                <p className="text-2xl font-bold text-white">{horariosDisponiveis.filter(h => h.ativo).length}</p>
              </div>
              <Clock className="w-8 h-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Abas de Configuração */}
      <Tabs defaultValue="tipos" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-white/10 backdrop-blur-sm p-1 rounded-lg">
          <TabsTrigger 
            value="tipos" 
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md"
          >
            <Settings className="w-4 h-4 mr-2" />
            Tipos de Consulta
          </TabsTrigger>
          <TabsTrigger 
            value="horarios" 
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md"
          >
            <Clock className="w-4 h-4 mr-2" />
            Horários
          </TabsTrigger>
          <TabsTrigger 
            value="consultas" 
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-purple-200 hover:bg-white/10 transition-all duration-200 rounded-md"
          >
            <Users className="w-4 h-4 mr-2" />
            Consultas
          </TabsTrigger>
        </TabsList>

        {/* Tipos de Consulta */}
        <TabsContent value="tipos" className="mt-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-semibold text-white">Tipos de Consulta</h3>
              <Button 
                onClick={() => {
                  setEditingTipoConsulta(null);
                  setShowAddTipoConsulta(true);
                }}
                className="bg-green-600 hover:bg-green-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Tipo
              </Button>
            </div>

            <div className="grid gap-4">
              {tiposConsulta.map((tipo) => (
                <Card key={tipo.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div 
                            className="w-4 h-4 rounded-full" 
                            style={{ backgroundColor: tipo.cor_tema }}
                          ></div>
                          <h4 className="font-semibold text-white">{tipo.nome}</h4>
                          <Badge className={`text-xs ${tipo.ativo ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                            {tipo.ativo ? 'Ativo' : 'Inativo'}
                          </Badge>
                        </div>
                        <p className="text-purple-200 text-sm mb-2">{tipo.descricao}</p>
                        <div className="flex gap-4 text-sm text-purple-300">
                          <span className="flex items-center">
                            <DollarSign className="w-4 h-4 mr-1" />
                            R$ {tipo.preco.toFixed(2)}
                          </span>
                          <span className="flex items-center">
                            <Clock className="w-4 h-4 mr-1" />
                            {tipo.duracao_minutos} min
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => {
                            setEditingTipoConsulta(tipo);
                            setShowAddTipoConsulta(true);
                          }}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDeleteTipoConsulta(tipo.id)}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {tiposConsulta.length === 0 && (
                <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8">
                  <div className="text-center">
                    <Settings className="w-12 h-12 text-purple-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Nenhum tipo de consulta configurado</h3>
                    <p className="text-purple-200">Clique em "Adicionar Tipo" para começar</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Horários Disponíveis */}
        <TabsContent value="horarios" className="mt-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-semibold text-white">Horários de Trabalho</h3>
              <Button 
                onClick={() => {
                  setEditingHorario(null);
                  setShowAddHorario(true);
                }}
                className="bg-green-600 hover:bg-green-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Horário
              </Button>
            </div>

            <div className="grid gap-4">
              {horariosDisponiveis.map((horario) => (
                <Card key={horario.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="font-semibold text-white">{getDiaSemanaName(horario.dia_semana)}</h4>
                          <Badge className={`text-xs ${horario.ativo ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                            {horario.ativo ? 'Ativo' : 'Inativo'}
                          </Badge>
                        </div>
                        <div className="flex gap-4 text-sm text-purple-300">
                          <span className="flex items-center">
                            <Clock className="w-4 h-4 mr-1" />
                            {horario.hora_inicio} - {horario.hora_fim}
                          </span>
                          <span>Intervalo: {horario.intervalo_minutos} min</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => {
                            setEditingHorario(horario);
                            setShowAddHorario(true);
                          }}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleDeleteHorario(horario.id)}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {horariosDisponiveis.length === 0 && (
                <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8">
                  <div className="text-center">
                    <Clock className="w-12 h-12 text-purple-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Nenhum horário configurado</h3>
                    <p className="text-purple-200">Configure seus horários de trabalho para permitir agendamentos</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Consultas Agendadas */}
        <TabsContent value="consultas" className="mt-6">
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-white">Consultas Agendadas</h3>
            
            <div className="grid gap-4">
              {consultasVendas.map((consulta) => (
                <Card key={consulta.id} className="bg-white/10 border-purple-300/30 backdrop-blur-sm">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h4 className="font-semibold text-white">{consulta.cliente.nome_completo}</h4>
                        <p className="text-purple-200 text-sm">{consulta.titulo}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge className={`text-xs ${
                          consulta.status === 'realizada' ? 'bg-green-500/20 text-green-300' :
                          consulta.status === 'confirmada' ? 'bg-blue-500/20 text-blue-300' :
                          consulta.status === 'agendada' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-red-500/20 text-red-300'
                        }`}>
                          {consulta.status}
                        </Badge>
                        <Badge className="bg-green-500/20 text-green-300">
                          Pago
                        </Badge>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-purple-200">Data/Hora:</p>
                        <p className="text-white">{new Date(consulta.data_agendada).toLocaleString('pt-BR')}</p>
                      </div>
                      <div>
                        <p className="text-purple-200">Duração:</p>
                        <p className="text-white">{consulta.duracao_minutos} minutos</p>
                      </div>
                      <div>
                        <p className="text-purple-200">Valor:</p>
                        <p className="text-white">R$ {consulta.preco.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-purple-200">WhatsApp:</p>
                        <p className="text-white">{consulta.cliente.telefone}</p>
                      </div>
                    </div>

                    {consulta.observacoes && (
                      <div className="mt-4">
                        <p className="text-purple-200 text-sm">Observações:</p>
                        <p className="text-white bg-black/20 p-3 rounded-lg text-sm">{consulta.observacoes}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {consultasVendas.length === 0 && (
                <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm p-8">
                  <div className="text-center">
                    <Users className="w-12 h-12 text-purple-300 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">Nenhuma consulta agendada</h3>
                    <p className="text-purple-200">As consultas pagas aparecerão aqui</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Modal para Adicionar/Editar Tipo de Consulta */}
      {showAddTipoConsulta && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle className="text-white">
                {editingTipoConsulta ? 'Editar Tipo de Consulta' : 'Adicionar Tipo de Consulta'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddTipoConsulta} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="nome" className="text-white">Nome da Consulta</Label>
                    <Input
                      id="nome"
                      name="nome"
                      defaultValue={editingTipoConsulta?.nome || ''}
                      className="bg-white/5 border-purple-300/30 text-white"
                      placeholder="Ex: Consulta de Tarot"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="preco" className="text-white">Preço (R$)</Label>
                    <Input
                      id="preco"
                      name="preco"
                      type="number"
                      step="0.01"
                      defaultValue={editingTipoConsulta?.preco || ''}
                      className="bg-white/5 border-purple-300/30 text-white"
                      placeholder="80.00"
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="descricao" className="text-white">Descrição</Label>
                  <Textarea
                    id="descricao"
                    name="descricao"
                    defaultValue={editingTipoConsulta?.descricao || ''}
                    className="bg-white/5 border-purple-300/30 text-white"
                    placeholder="Descrição da consulta..."
                    rows={3}
                    required
                  />
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="duracao_minutos" className="text-white">Duração (minutos)</Label>
                    <Input
                      id="duracao_minutos"
                      name="duracao_minutos"
                      type="number"
                      defaultValue={editingTipoConsulta?.duracao_minutos || 60}
                      className="bg-white/5 border-purple-300/30 text-white"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="cor_tema" className="text-white">Cor do Tema</Label>
                    <Input
                      id="cor_tema"
                      name="cor_tema"
                      type="color"
                      defaultValue={editingTipoConsulta?.cor_tema || '#8b5cf6'}
                      className="bg-white/5 border-purple-300/30 text-white h-10"
                    />
                  </div>
                  <div>
                    <Label htmlFor="ordem" className="text-white">Ordem de Exibição</Label>
                    <Input
                      id="ordem"
                      name="ordem"
                      type="number"
                      defaultValue={editingTipoConsulta?.ordem || 0}
                      className="bg-white/5 border-purple-300/30 text-white"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="ativo"
                    name="ativo"
                    defaultChecked={editingTipoConsulta?.ativo !== false}
                  />
                  <Label htmlFor="ativo" className="text-white">Tipo de consulta ativo</Label>
                </div>

                <div className="flex gap-2">
                  <Button type="submit" className="bg-green-600 hover:bg-green-700 flex-1">
                    {editingTipoConsulta ? 'Atualizar' : 'Adicionar'} Tipo
                  </Button>
                  <Button 
                    type="button" 
                    onClick={() => {
                      setShowAddTipoConsulta(false);
                      setEditingTipoConsulta(null);
                    }}
                    className="bg-gray-600 hover:bg-gray-700 flex-1"
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modal para Adicionar/Editar Horário */}
      {showAddHorario && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="bg-white/10 border-purple-300/30 backdrop-blur-sm w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-white">
                {editingHorario ? 'Editar Horário' : 'Adicionar Horário'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddHorario} className="space-y-4">
                <div>
                  <Label htmlFor="dia_semana" className="text-white">Dia da Semana</Label>
                  <Select name="dia_semana" defaultValue={editingHorario?.dia_semana?.toString() || ''} required>
                    <SelectTrigger className="bg-white/5 border-purple-300/30 text-white">
                      <SelectValue placeholder="Selecione o dia" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Segunda-feira</SelectItem>
                      <SelectItem value="1">Terça-feira</SelectItem>
                      <SelectItem value="2">Quarta-feira</SelectItem>
                      <SelectItem value="3">Quinta-feira</SelectItem>
                      <SelectItem value="4">Sexta-feira</SelectItem>
                      <SelectItem value="5">Sábado</SelectItem>
                      <SelectItem value="6">Domingo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="hora_inicio" className="text-white">Hora Início</Label>
                    <Input
                      id="hora_inicio"
                      name="hora_inicio"
                      type="time"
                      defaultValue={editingHorario?.hora_inicio || '09:00'}
                      className="bg-white/5 border-purple-300/30 text-white"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="hora_fim" className="text-white">Hora Fim</Label>
                    <Input
                      id="hora_fim"
                      name="hora_fim"
                      type="time"
                      defaultValue={editingHorario?.hora_fim || '18:00'}
                      className="bg-white/5 border-purple-300/30 text-white"
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="intervalo_minutos" className="text-white">Intervalo entre consultas (minutos)</Label>
                  <Input
                    id="intervalo_minutos"
                    name="intervalo_minutos"
                    type="number"
                    defaultValue={editingHorario?.intervalo_minutos || 60}
                    className="bg-white/5 border-purple-300/30 text-white"
                    min="15"
                    step="15"
                    required
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="ativo"
                    name="ativo"
                    defaultChecked={editingHorario?.ativo !== false}
                  />
                  <Label htmlFor="ativo" className="text-white">Horário ativo</Label>
                </div>

                <div className="flex gap-2">
                  <Button type="submit" className="bg-green-600 hover:bg-green-700 flex-1">
                    {editingHorario ? 'Atualizar' : 'Adicionar'} Horário
                  </Button>
                  <Button 
                    type="button" 
                    onClick={() => {
                      setShowAddHorario(false);
                      setEditingHorario(null);
                    }}
                    className="bg-gray-600 hover:bg-gray-700 flex-1"
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AgendamentosTab;