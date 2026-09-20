# Inkscape Shortcut Manager

Desenhe figuras matemáticas no Inkscape com estilos combináveis, objetos reutilizáveis e texto ou fórmulas escritos no seu editor.

Este fork adapta o [Inkscape Shortcut Manager de Gilles Castel](https://github.com/gillescastel/inkscape-shortcut-manager) para um fluxo com **Hyprland, XWayland e Obsidian**. A principal mudança na interação é o uso de uma tecla *leader*: pressione **Espaço** e digite os componentes de um estilo em sequência, sem precisar segurar várias teclas ao mesmo tempo.

O projeto é inspirado no artigo **[How I draw figures for my mathematical lecture notes using Inkscape](https://castel.dev/post/lecture-notes-2/)**, de Gilles Castel. O artigo apresenta a ideia original de combinar atalhos, estilos e objetos para acompanhar a produção de notas de aula.

## Comece por aqui

Depois de instalar as dependências, abra uma figura pelo lançador:

```sh
./inkscape-managed /caminho/da/figura.svg
```

No Inkscape:

1. Desenhe e selecione um objeto.
2. Pressione **Espaço**, solte, depois **d**, solte, depois **a**.
3. Pressione **Enter** ou aguarde **1 segundo**: o objeto recebe um traço pontilhado com seta.
4. Pressione **a** para pesquisar e inserir um objeto salvo, ou **s** para aplicar um estilo salvo.

O gerenciador inicia automaticamente pelo lançador. Não é necessário abrir outro terminal nem adicioná-lo ao autostart para esse fluxo.

## Compatibilidade e instalação

O gerenciador captura teclas de janelas **X11**. Em uma sessão Wayland, o Inkscape precisa rodar por **XWayland**; não há suporte à captura de janelas Wayland nativas.

O lançador configura `GDK_BACKEND=x11` somente para o Inkscape e usa `--app-id-tag=shortcutmanager`, evitando reutilizar uma instância Wayland já aberta. O restante do desktop continua usando seu backend habitual.

Ambiente em que esta revisão foi validada: CachyOS, Hyprland 0.56.2, Inkscape 1.4.4 e Python 3.14. Outros ambientes X11 podem funcionar, mas a regra de workspace é específica do Hyprland.

### Dependências

| Recurso | Dependências |
|---|---|
| Atalhos, estilos e objetos | Python 3, `python-xlib`, Inkscape, `xclip` e Rofi |
| Uso em uma sessão Wayland | XWayland disponível no compositor |
| Editor de texto padrão | Kitty e Neovim; ambos podem ser substituídos na configuração |
| Fórmulas renderizadas | `pdflatex`, `pdf2svg` e os pacotes LaTeX usados pelo template |

Em Arch Linux e CachyOS, as dependências principais podem ser instaladas com:

```sh
sudo pacman -S --needed python python-xlib inkscape xorg-xwayland xclip rofi
```

Para usar o editor padrão e converter PDF em SVG:

```sh
sudo pacman -S --needed kitty neovim pdf2svg
```

Para `Shift+t`, instale também uma distribuição LaTeX com `pdflatex`. O template padrão usa `standalone`, `inputenc`, `fontenc`, `textcomp`, `amsmath` e `amssymb`. Essas dependências de LaTeX não são necessárias para desenhar, aplicar estilos ou reutilizar objetos.

### Obter e executar o projeto

Clone seu fork ou baixe o repositório e entre na pasta `inkscape-shortcut-manager`. Dentro dela:

```sh
chmod +x inkscape-managed
python3 main.py --doctor
./inkscape-managed
```

Sem um caminho de arquivo, o lançador abre o Inkscape para criar um documento. Para editar uma figura existente, passe o caminho, entre aspas se houver espaços:

```sh
./inkscape-managed "/caminho/das figuras/campo-eletrico.svg"
```

O script `inkscape-managed` usa `/usr/bin/python3`. A biblioteca `Xlib` precisa estar disponível nesse interpretador. Para usar um ambiente virtual, execute `python launch.py figura.svg` com o Python desse ambiente.

## Estilos com a tecla leader

**Espaço** inicia uma sequência de estilo. A partir daí, digite as letras desejadas **uma de cada vez, em minúsculas**.

- O prazo padrão é de **1 segundo**, renovado ao soltar cada letra.
- **Enter** aplica a combinação imediatamente.
- **Esc** cancela sem aplicar.
- **Backspace** limpa a combinação para começar novamente.
- Ao mudar o foco para outra janela, a sequência é cancelada.

Por exemplo, `Espaço → g → d → a → Enter` cria uma seta pontilhada com traço grosso. As setas `→` nesta documentação indicam a ordem das teclas; não devem ser digitadas.

### Guia visual

![Guia dos estilos: colunas S, D, E, G, GD, GE, H, HD e HE mostram contornos de diferentes espessuras e padrões; linhas F, W, B, A e X mostram preenchimentos e setas.](docs/images/atalhos-estilos.png)

As letras maiúsculas da imagem são **rótulos**, não comandos com Shift. Por exemplo, a coluna **GD** corresponde a `Espaço → g → d`; a linha **F** nessa coluna acrescenta `f` à sequência. As linhas **A** e **X** representam setas, apesar de estarem agrupadas na lateral junto dos preenchimentos.

| Letra após Espaço | Efeito |
|---|---|
| `s` | Contorno preto fino e contínuo |
| `d` | Contorno pontilhado |
| `e` | Contorno tracejado |
| `g` | Contorno grosso |
| `h` | Contorno muito grosso |
| `a` | Seta no final do caminho |
| `x` | Setas nas duas extremidades |
| `f` | Preenchimento preto com 12% de opacidade, visualmente cinza sobre branco |
| `w` | Preenchimento branco |
| `b` | Preenchimento preto |

### Exemplos de combinações

| Sequência | Resultado |
|---|---|
| `Espaço → s → Enter` | Contorno fino, sem preenchimento |
| `Espaço → d → a → Enter` | Seta pontilhada |
| `Espaço → g → e → x → Enter` | Linha grossa tracejada, com setas nas duas pontas |
| `Espaço → f → s → Enter` | Preenchimento cinza e contorno fino |
| `Espaço → f → d → Enter` | Preenchimento cinza e contorno pontilhado |
| `Espaço → w → h → Enter` | Preenchimento branco e contorno muito grosso |
| `Espaço → b → Enter` | Preenchimento preto, sem contorno |

Os estilos gerados redefinem preenchimento, contorno, padrões de traço e marcadores; não são apenas alterações isoladas de uma propriedade. Sem uma letra de preenchimento, o preenchimento é removido. Sem uma letra de contorno, o contorno é removido. Na implementação atual, `f`, `w` e `b` também removem as setas: use preenchimentos para formas e `a`/`x` para caminhos com setas.

Os acordes simultâneos do projeto original continuam disponíveis: segure, por exemplo, `d` e `a`, e solte ambas para aplicar. O modo leader é a alternativa para digitar com mais conforto.

## Atalhos do modo normal

Estes atalhos são usados **sem pressionar Espaço antes**. Uma mesma letra pode ter outro significado dentro de uma sequência de estilo.

| Tecla | Ação |
|---|---|
| `Espaço` | Iniciar uma sequência de estilo |
| `a` | Abrir o menu de objetos salvos |
| `s` | Abrir o menu de estilos salvos |
| `Shift+a` | Salvar os objetos selecionados |
| `Shift+s` | Salvar o estilo da seleção |
| `w` | Ativar a ferramenta Lápis |
| `f` | Ativar a ferramenta Bézier |
| `x` | Alternar o encaixe (*snapping*) |
| `z` | Desfazer |
| `Shift+z` | Excluir a seleção |
| `t` | Abrir o editor e inserir o conteúdo como texto |
| `Shift+t` | Abrir o editor, compilar LaTeX e inserir o SVG renderizado |
| `F12` | Entrar ou sair do modo de texto direto |

Os atalhos com Ctrl, Alt, Super e AltGr ficam disponíveis para o Inkscape e o compositor. O gerenciador atua na janela inteira, inclusive sobre campos de texto: use **F12** antes de digitar neles. Ao entrar nesse modo, ele também ativa a ferramenta Texto; ao sair, envia Esc. Uma mudança de foco para outra janela restaura o modo normal.

O acento grave também alterna o modo de texto, mas pode funcionar como tecla morta em layouts como ABNT2. **F12** evita essa dependência do layout.

## Salvar e reutilizar estilos e objetos

### Objetos

1. Selecione os elementos que deseja reutilizar, como um conjunto de eixos.
2. Pressione **Shift+a**, informe um nome no Rofi e confirme.
3. Para inserir outra cópia, pressione **a**.
4. Pesquise o nome, escolha a entrada com as setas e confirme com **Enter**.

Nomes como `eixo_xy` e `eixo_xyz` podem coexistir. O menu confirma a entrada escolhida, sem inserir automaticamente um objeto por prefixo. **Esc** fecha o menu sem inserir nada.

### Estilos

Selecione um objeto com a aparência desejada e pressione **Shift+s** para salvar seu estilo. Depois, selecione outro objeto, pressione **s** e escolha o estilo no menu. A operação aplica a aparência à seleção, sem inserir uma cópia do objeto original.

Salvar com um nome existente solicita confirmação antes de sobrescrever. Arquivos ocultos, como `.svg`, são ignorados nos menus.

Os dados ficam em:

```text
~/.config/inkscape-shortcut-manager/
├── config.py
├── objects/
│   ├── eixo_xy.svg
│   └── eixo_xyz.svg
├── styles/
│   └── meu_estilo.svg
└── manager.log
```

Os nomes acima são exemplos de itens criados pelo usuário. Há outros objetos e estilos de exemplo em [`examples/objects`](examples/objects) e [`examples/styles`](examples/styles); copie apenas os arquivos desejados para as pastas correspondentes da configuração, preservando seus arquivos existentes.

Aplicar estilos, copiar seleções e inserir objetos usa e substitui o conteúdo da área de transferência.

## Texto e fórmulas LaTeX

**`t` — texto editável:** abre Neovim dentro do Kitty. Com a regra de editor do Hyprland fornecida no projeto instalada, ele abre em uma janela flutuante pequena e centralizada (800 × 300 pixels). Escreva, salve e feche o editor com `:wq`; o conteúdo será inserido como texto no Inkscape. Comandos LaTeX permanecem literais nesse modo.

**`Shift+t` — fórmula renderizada:** abre o mesmo editor e compila o conteúdo com `pdflatex`, convertendo o PDF em SVG com `pdf2svg`. Por exemplo:

```latex
$\int_0^1 x^2\,dx = \frac{1}{3}$
```

O arquivo começa com `$$` para facilitar a entrada de uma expressão. Deixá-lo vazio ou sem alterar esse conteúdo cancela a inserção. A versão renderizada entra como desenho SVG, não como um campo de edição LaTeX.

## Integração com Obsidian

O exemplo [`examples/inkscape-snippets.js`](examples/inkscape-snippets.js) integra a criação e a reabertura de figuras ao **LaTeX Suite**, no Obsidian Desktop com um vault local.

1. Copie o exemplo para a pasta de snippets que você usa no LaTeX Suite.
2. **Substitua a constante `INKSCAPE` pelo caminho absoluto do seu lançador**. O arquivo de exemplo contém o caminho da instalação em que o fork foi desenvolvido.
3. Configure o LaTeX Suite para carregar essa pasta e recarregue os snippets ou reinicie o Obsidian.

Exemplo de caminho a adaptar:

```javascript
const INKSCAPE = "/home/SEU_USUARIO/scripts/inkscape-shortcut-manager/inkscape-managed";
```

Fora de uma fórmula, digite:

```text
figure: campo eletrico
```

Pressione **Tab**. O snippet cria `figures/campo-eletrico.svg` na raiz do vault, abre o Inkscape pelo lançador e insere:

```markdown
![[figures/campo-eletrico.svg]]
```

Para editar novamente, selecione a incorporação inteira e pressione **Ctrl+Alt+i**. Se o arquivo já existir, ele é reaberto sem sobrescrever seu conteúdo. Salve no Inkscape para atualizar o SVG usado pela nota.

## Abrir o Inkscape em outro workspace

Em uma configuração **Lua do Hyprland**, adicione o conteúdo de [`examples/hyprland-inkscape.lua`](examples/hyprland-inkscape.lua) a um arquivo carregado pela sua configuração:

```lua
hl.window_rule({
    name = "inkscape-workspace",
    match = { class = ".*[Ii]nkscape.*" },
    workspace = "5",
})
```

Recarregue a configuração com `hyprctl reload`. Para usar o workspace 6, troque `"5"` por `"6"`. A regra de workspace corresponde às janelas do Inkscape, inclusive às abertas fora deste lançador. O arquivo de exemplo também inclui uma regra separada para `kitty-figure-editor`, que torna o editor flutuante com 800 × 300 pixels. Carregue as duas regras para ativar esse comportamento.

**Essa configuração é opcional e não é instalada automaticamente ao clonar o fork.** Ela define o destino de novas janelas; as já abertas precisam ser movidas ou reabertas. Consulte a [documentação de regras de janelas do Hyprland](https://wiki.hypr.land/Configuring/Basics/Window-Rules/) para adaptar a regra à sua versão.

## Configuração pessoal

Crie `~/.config/inkscape-shortcut-manager/config.py`. Quando `XDG_CONFIG_HOME` estiver definido, a pasta será `$XDG_CONFIG_HOME/inkscape-shortcut-manager`.

As opções pessoais são mescladas com os padrões de [`config.py`](config.py). Por exemplo:

```python
import subprocess


def open_editor(filename):
    subprocess.run([
        "kitty", "--class", "kitty-figure-editor",
        "--override", "remember_window_size=no",
        "--override", "initial_window_width=800",
        "--override", "initial_window_height=300",
        "-e", "nvim", str(filename),
    ], check=True)


config = {
    "style_leader": "space",
    "style_timeout": 1.5,  # segundos entre teclas; padrão: 1.0
    "toggle_key": "F12",
    "rofi_theme": None,
    "font": "monospace",
    "font_size": 10,
    "open_editor": open_editor,
}
```

Use nomes de teclas X11 em `style_leader` e `toggle_key`. A função `open_editor` deve aguardar o fechamento do editor. Também é possível substituir `latex_document`, uma função que recebe o conteúdo digitado e retorna o documento LaTeX completo. O arquivo [`examples/config.py`](examples/config.py) preserva um exemplo histórico do projeto original, com urxvt/Vim; o exemplo acima corresponde aos padrões deste fork.

Alterações no código ou na configuração exigem **reiniciar o processo do gerenciador**. Fechar só o Inkscape não encerra esse processo, e abrir o lançador novamente não recarrega uma instância já ativa. Encerre o processo `main.py` desta instalação antes de executar o lançador novamente. Uma sessão iniciada no terminal pode ser encerrada com Ctrl+C.

## O que mudou em relação ao original

| Área | Projeto original | Este fork |
|---|---|---|
| Combinação de estilos | Teclas pressionadas simultaneamente | Leader com sequência, timeout configurável, Enter e Esc; acordes preservados |
| Objetos e estilos salvos | Digitação de nomes/prefixos capturada pelo gerenciador | Menus pesquisáveis no Rofi com seleção explícita |
| Abertura em Wayland | Dependência de X11 sem um lançador específico | Lançador que abre o Inkscape via XWayland com identificação própria |
| Inicialização | Execução manual de `main.py` | Inicialização pelo lançador e uma instância por display |
| Editor padrão | urxvt e Vim | Kitty e Neovim, configuráveis |
| Modo de texto | Alternância pelo acento grave | F12 como alternativa adequada a layouts com teclas mortas |
| Obsidian e Hyprland | Fluxo original voltado às notas em LaTeX | Exemplo de snippet para LaTeX Suite e regra opcional de workspace |

Também foram corrigidos problemas de implementação:

- **Detecção de janelas:** procura periódica de janelas existentes e novas, sem depender de `WM_CLASS` já estar disponível em `CreateNotify`.
- **Múltiplos documentos:** estado de teclas separado por janela e acesso à área de transferência serializado.
- **Tratamento de teclas:** combinações desconhecidas são encaminhadas; acordes aguardam a liberação de todas as teclas.
- **SVG e texto:** namespaces XML, posição da declaração XML e escape de caracteres como `<` e `&`.
- **Área de transferência:** espera pela troca do proprietário da seleção antes de ler ou colar.
- **Salvamento:** cancelamento respeitado, validação de nomes e confirmação de sobrescrita.
- **LaTeX:** erros registrados, limite de tempo de execução e limpeza dos arquivos temporários.
- **Diagnóstico:** comando `--doctor`, log de execução, testes de regressão e teste opcional com janela real.

## Diagnóstico e testes

Dentro da pasta do projeto:

```sh
python3 main.py --doctor
```

O comando lista dependências, configuração, conexão X11/XWayland e quantidade de janelas compatíveis. O log do lançador fica em `~/.config/inkscape-shortcut-manager/manager.log`, respeitando `XDG_CONFIG_HOME` quando definido.

| Sintoma | O que verificar |
|---|---|
| Nenhum atalho funciona | Reabra a figura pelo `inkscape-managed`; uma janela Wayland nativa não é capturada. |
| O estilo não aparece | Selecione um objeto, pressione Espaço e digite as letras antes do timeout; use Enter para confirmar. |
| Digitar aciona ferramentas | Entre no modo de texto com F12 antes de preencher campos. |
| Um objeto não está no menu | Confira a pasta `objects/`, a extensão `.svg` e se o arquivo não está oculto. |
| Shift+a ou Shift+s não salva | Selecione os objetos antes; consulte o log se a cópia falhar. |
| A fórmula não é inserida | Verifique `pdflatex`, `pdf2svg`, os pacotes do template e o erro registrado no log. |
| Mudanças não fazem efeito | Reinicie o gerenciador; reabrir somente a figura não recarrega o código. |

Para executar a suíte de regressão:

```sh
python3 -m unittest discover -s tests -v
```

O teste [`tests/smoke_x11.py`](tests/smoke_x11.py) valida uma sequência de estilo, desfazer, cópia de SVG, workspace 5 e inserção de `eixo_xy` e `eixo_xyz` em uma figura temporária. Ele exige Hyprland, XWayland, `xdotool`, a regra de workspace instalada e esses dois objetos na configuração pessoal padrão. Não é um teste portátil para qualquer instalação: execute sem outro gerenciador ativo. Ele altera o foco e a área de transferência e usa Rofi em X11 para permitir a digitação automatizada.

## Créditos e licença

- **Gilles Castel:** autor do [projeto original](https://github.com/gillescastel/inkscape-shortcut-manager) e do artigo [How I draw figures for my mathematical lecture notes using Inkscape](https://castel.dev/post/lecture-notes-2/), referência para este fluxo de desenho.
- **Projeto relacionado:** [Inkscape Figure Manager](https://github.com/gillescastel/inkscape-figures), também de Gilles Castel.
- **Licença:** [MIT](LICENSE), com o aviso de copyright original preservado.

