# Rotina diária — post do @islamic.siraj

Instruções seguidas pela rotina agendada (todo dia, 14h53 de Brasília).
Resultado: **um rascunho** no Publora, com imagem e legenda, para o dono da conta
revisar e agendar para as **18h**. A rotina **nunca publica nem agenda** sozinha.

## 1. Preparar o ambiente

```bash
pip install -q pillow
cd social
```

## 2. Escolher o tipo do dia

Rodízio pelo dia do ano (`date +%j`, horário de Brasília), resto da divisão por 4:

| resto | tipo       | rótulo            |
|-------|------------|-------------------|
| 0     | `ayah`     | Versículo         |
| 1     | `hadith`   | Hadith            |
| 2     | `dua`      | Súplica           |
| 3     | `reflexao` | Lembrete          |

Antes de escolher o conteúdo, leia os posts dos últimos 30 dias no Publora
(`list_posts`) e **não repita** versículo, hadith ou dua já usados.

## 3. Escolher e conferir o conteúdo

Regra de ouro: **nenhum texto árabe religioso é escrito de memória.**

- **ayah** — Escolha um versículo curto (até ~30 palavras) e com sentido completo sozinho.
  O texto árabe vem de `dados/quran.json` (o script faz isso via `--ref`).
  A tradução em português é do sentido e escrita com cuidado, no registro clássico
  ("Allah", "vós"), fiel ao original, sem acréscimos.
- **hadith** — Apenas hadiths *sahih* conhecidos (Bukhari, Muslim ou os dois).
  Confirme o texto árabe exato com o Shamela (`shamela_search_hadith` e/ou
  `shamela_verify_quote`) e copie o matn **da ferramenta**, não da memória.
  A busca livre traz muitos livros: ache o `book_id` de صحيح البخاري / صحيح مسلم com
  `shamela_resolve` e confirme o texto **dentro deles** (`scope.book_ids`), no corpo
  (`body`) e não em nota de rodapé. Anote livro e número do hadith.
  Use só o trecho do Profeta ﷺ (sem a cadeia de narradores), curto.
  Fonte no formato `Sahih al-Bukhari, nº` / `Sahih Muslim, nº` / `Bukhari e Muslim`.
  Se não conseguir confirmar no Shamela, escolha outro hadith; se nenhum for
  confirmado, faça uma `dua` do Alcorão no lugar.
- **dua** — Prefira súplicas do próprio Alcorão (ex.: 2:201, 2:286 final, 3:8, 7:23,
  14:40–41, 20:25–28, 20:114, 25:74). Nesse caso gere com o tipo `dua` usando
  `--ar` com o texto copiado de `dados/quran.json` e `--fonte "Alcorão, <nome> <s:v>"`.
  Súplicas de hadith seguem as mesmas regras de conferência do hadith.
- **reflexao** — Frase curta e original em português (até ~35 palavras), sem citar
  hadith ou versículo de memória. Pode ter uma linha em árabe só se for um termo
  simples e conhecido (ex.: الحمد لله).

Tom: acolhedor, sem polêmica, sem fiqh controverso, sem política.

## 4. Gerar a imagem

```bash
python gerar_post.py ayah --ref 2:152 --pt "..." --out /tmp/post.jpg
python gerar_post.py hadith --ar "..." --pt "..." --fonte "Sahih Muslim, 2699" --out /tmp/post.jpg
python gerar_post.py dua --ar "..." --pt "..." --fonte "Alcorão, Al-Baqarah 2:201" --out /tmp/post.jpg
python gerar_post.py reflexao --pt "..." --out /tmp/post.jpg
```

Abra a imagem gerada e confira: texto árabe completo e legível, nada cortado.
Se o script disser que o texto é longo demais, escolha um texto mais curto.

## 5. Legenda

```
<texto árabe, idêntico ao da imagem>

"<tradução em português>"
— <fonte> (tradução do sentido)        ← "(tradução do sentido)" só para Alcorão

<1–3 frases curtas de reflexão prática, em português>

#Islam #Muçulmanos #IslamNoBrasil <3–5 hashtags do tema, em português e árabe>
```

## 6. Criar o rascunho no Publora

1. `list_connections` → use o `platformId` do Instagram `islamic.siraj` copiado exatamente.
2. `create_post` com `content` = legenda, `platforms` = [esse id] e **sem `scheduledTime`**.
3. `get_upload_url` (`postGroupId`, `fileName: siraj-AAAA-MM-DD.jpg`, `contentType: image/jpeg`, `type: image`).
4. `curl -X PUT -H "Content-Type: image/jpeg" --data-binary @/tmp/post.jpg "<uploadUrl>"` → deve dar HTTP 200.
5. `complete_media` com o `mediaId`.
6. `get_post` → confirme `status: draft` e a mídia `ready`.

Não chame `update_post` com status `scheduled`: o agendamento é feito pelo dono da conta.

## 7. Relatório final

Termine com: tipo do dia, referência, legenda completa, `postGroupId`, como o texto foi
conferido (quran.json / Shamela, com livro e página) e o lembrete:
"Rascunho pronto no Publora — revise e agende para 18h."
