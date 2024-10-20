
# ![SYRIN Logo](./Syrin.png)

# SYRIN - Sistema de Notificações Humanizadas via Áudio

SYRIN é um conjunto de aplicações desenvolvidas para transformar mensagens de texto em alertas humanizados via áudio. O sistema utiliza a integração com RabbitMQ e MinIO para processar e distribuir essas mensagens em filas, garantindo notificações personalizadas e rápidas, que podem ser reproduzidas por dispositivos de áudio em tempo real. O SYRIN foi projetado para aumentar a eficiência das equipes de monitoramento, proporcionando uma experiência mais engajante ao transformar alertas técnicos em mensag...

## Componentes do Projeto

### 1. SYRIN REST API

Uma API REST baseada em Flask que recebe mensagens de texto e as envia para filas RabbitMQ. Essa API oferece endpoints para receber dados de entrada e distribuí-los para as filas de notificação, com processamento assíncrono e suporte a diferentes níveis de prioridade.

**Principais Características**:
- Processamento de mensagens de texto para filas RabbitMQ.
- Fila de reprocessamento para lidar com falhas.
- Configuração de variáveis de ambiente para detalhes de conexão e credenciais do RabbitMQ.

**Exemplo de Requisição**:
```bash
curl -X POST http://localhost:5121/api/text-to-speech     -H "Content-Type: application/json"     -d '{"text": "This is a warning message."}'
```

### 2. SYRIN Humanized Text Agent

Esse componente é responsável por transformar mensagens de texto em formatos mais humanizados usando o modelo de IA Ollama. Ele consome mensagens de filas RabbitMQ, processa o texto e devolve uma versão mais natural e fluida dessas mensagens para uma nova fila.

**Principais Características**:
- Integração com IA Ollama para humanização de mensagens.
- Reprocessamento de mensagens em caso de falha.
- Customização dos prompts de humanização por variáveis de ambiente.

### 3. SYRIN TTS Make Audio

Este componente gera arquivos de áudio a partir de mensagens de texto usando a biblioteca Coqui TTS. Os arquivos de áudio resultantes são carregados no MinIO e as mensagens são encaminhadas para novas filas para reprodução.

**Principais Características**:
- Geração de áudio a partir de texto usando Coqui TTS.
- Upload de arquivos `.wav` para um bucket MinIO.
- Mecanismo de reprocessamento em caso de falha no processamento do áudio.

### 4. SYRIN Speak Audio Agent

O SYRIN Speak é responsável por consumir mensagens das filas que indicam a localização de arquivos de áudio no MinIO. Ele faz o download dos arquivos, os reproduz em dispositivos de áudio, e depois move os arquivos processados para uma subpasta no MinIO.

**Principais Características**:
- Reprodução de áudio a partir de arquivos `.wav`.
- Interação com MinIO para download/upload de arquivos.
- Publicação de mensagens de sucesso ou falha para outras filas RabbitMQ.

## Como Funciona

1. **Recebimento de Mensagens**: As mensagens são recebidas via API REST e encaminhadas para RabbitMQ.
2. **Humanização**: As mensagens de texto passam pelo agente de humanização, que gera uma versão mais natural do texto usando IA.
3. **Geração de Áudio**: O texto humanizado é convertido em áudio utilizando Coqui TTS.
4. **Reprodução do Áudio**: O agente de reprodução faz o download dos arquivos de áudio do MinIO e os reproduz em dispositivos de som.
5. **Gerenciamento de Arquivos**: Após a reprodução, os arquivos de áudio são movidos para uma subpasta "reproduzidos" no MinIO.

## Tecnologias Utilizadas

- **Flask**: Para a criação da API REST.
- **RabbitMQ**: Para processamento e distribuição de mensagens.
- **Pika**: Biblioteca Python para integração com RabbitMQ.
- **Ollama AI**: Modelo de IA para humanização de texto.
- **Coqui TTS**: Para conversão de texto em áudio.
- **MinIO**: Armazenamento de arquivos de áudio gerados.
- **sounddevice** e **numpy**: Para reprodução de áudio.

## Execução

### Requisitos

- Python 3.x
- RabbitMQ
- MinIO
- Docker (opcional)

### Instruções

1. Clone o repositório e navegue até o diretório do projeto.
   ```bash
   git clone https://github.com/didevlab/syrin
   cd syrin
   ```

2. Instale as dependências.
   ```bash
   pip install -r requirements.txt
   ```

3. Configure suas variáveis de ambiente conforme necessário (RabbitMQ, MinIO, Ollama).

4. Execute cada componente individualmente.
   ```bash
   python app.py  # Para a API REST, Humanized Text Agent, ou Make Audio Agent
   ```

### Docker

Você pode usar Docker para simplificar a execução:
```bash
docker build -t syrin:latest .
docker run -p 5121:5121 syrin:latest
```

## Licença

Este projeto é licenciado sob a MIT License.
