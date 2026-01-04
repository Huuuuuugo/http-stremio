# Sobre
Desenvolvida para simplificar o acesso a conteúdo, esta ferramenta extrai vídeos de diversas plataformas de streaming usando scrapers e os organiza em uma API simples baseada em índices do [IMDb](https://www.imdb.com/).

### Funcionalidades
Além dos scrapers, a ferramenta conta com um servidor próprio, desenvolvido em **FastAPI**, que inclui as seguintes funcionalidades:
- **Extensão Stremio**: Uma extensão que integra os sites da ferramenta ao catálogo padrão do Stremio.
- **Site Próprio**: Um site simples, acessível em LAN, focado em oferecer suporte a navegadores antigos, como os encontrados em smart TVs mais antigas.
- **Proxy de Vídeos**: Um proxy que intermedeia o envio de vídeos entre o site original e a ferramenta, utilizado principalmente para contornar restrições de CORS no Stremio.  
- **Proxy de Caching**: Um proxy que armazena localmente arquivos menores, como imagens e páginas HTML, para diminuir o tempo de resposta da ferramenta.

# Instalação
## Stremio (Windows - localhost)
### 1. Baixe a ferramenta openssl
Algumas fontes não funcionam com o proxy padrão do Stremio e precisam ser acessadas por um proxy customizado que, nesse caso, será hospedado no localhost. Porém, o Stremio exige uma conexão HTTPS para streams até mesmo no localhost, o que significa que o servidor local precisa de um certificado SSL confiável, o qual pode ser facilmente criado usando a ferramenta `openssl`.
#### Chocolatey
Execute o seguinte comando para instalar o openssl usando Chocolatey:
```console
choco install openssl
```
#### Instalação Manual
Acesse a [seção de binários](https://github.com/openssl/openssl/wiki/Binaries) da wiki da ferramenta e escolha uma das fontes. Lembre-se de garantir que o executável esteja disponível em PATH antes de seguir para as próximas etapas.

### 2. Crie um certificado autoassinado
Navegue ao diretório onde o arquivo `ssl.conf` está localizado e execute o seguinte comando:
```console
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout localhost.key -out localhost.crt -config ssl.conf -extensions v3_req
```
Isso criará os arquivos `localhost.crt` e `localhost.key`,**Garanta que ambos estejam na pasta certs no diretorio raiz do projeto.**.

### 3. Adicione o certificado à lista de certificados confiáveis do Windows
1. No gerenciador de arquivos, navegue ao diretório onde os arquivos da etapa anterior foram criados e clique com o botão esquerdo duas vezes no arquivo `localhost.crt`
2. Na janela do certificado, clique na opção `Instalar Certificado`
3. Escolha o local que preferir e, em seguida, clique em `Avançar`
4. Na janela seguinte, selecione a opção `Colocar todos os certificados no repositório a seguir:` 
5. Clique em `Procurar` e selecione a opção `Autoridades de Certificação Raiz Confiáveis`, em seguida clique em `Avançar` e conclua a ação.

### 4. Instale a ferramenta uv
A ferramenta uv é usada para garantir a consistência de dependências entre diferentes computadores. Ela ajuda a evitar problemas causados por conflitos entre diferentes versões de pacotes ou do interpretador Python.

#### winget
Execute o seguinte comando para instalar a ferramenta uv usando winget:
```console
winget install --id=astral-sh.uv  -e
```

#### pip
Execute o seguinte comando para instalar a ferramenta uv usando pip:
```console
pip install uv
```

#### Outros métodos
Escolha alguma das várias opções de instalação disponíveis no [site da ferramenta](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

### 5. Instale as dependências do projeto
Navegue ao diretório raiz do projeto e execute o seguinte comando para instalar as dependências usando a ferramenta uv:
```console
uv sync
```
---

### Como usar
1. Navegue ao diretório raiz do projeto e execute o seguinte comando para iniciar o servidor:
```console
uv run manage.py runserver https
```
> [!IMPORTANT]
> A aplicação utiliza um sistema de caching para armazenar alguns **arquivos HTML inofensivos** dos provedores localmente e diminuir seu tempo de resposta, porém, o Windows Defender não gosta da obfuscação utilizada por um dos provedores e deleta seus arquivos instantâneamente, quebrando a aplicação. Para evitar esse problema, siga **um** dos passos a seguir:
> 1. Adicione o diretório da aplicação à lista de exclusão do Windows Defender
> 
>   ou
> 
> 2. Inicie o servidor com o sistema de caching desativado usando o comando a seguir:
> ```console
> uv run manage.py runserver https --disable-cache
> ```
> Isso aumentará o tempo de resposta, mas a aplicação irá funcionar exatamente da mesma forma.

2. Instale o addon através da url `https://127.0.0.1:6222/manifest.json`


## Site Próprio (Windows - LAN)
TODO
