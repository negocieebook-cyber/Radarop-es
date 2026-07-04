# Fontes de Dados

Este documento é um mapa futuro. **Nenhuma destas integrações está implementada na versão inicial; o app usa apenas MOCK / EXEMPLO.**

| Domínio | Fonte possível | Uso futuro | Validação necessária |
|---|---|---|---|
| Negociação e instrumentos | B3 | cadastro, cotações, séries e vencimentos | licença, frequência e integridade |
| Companhias | CVM | fatos relevantes e documentos | data, emissor e versão |
| Macroeconomia | Banco Central | Selic, câmbio e séries SGS | código da série e periodicidade |
| Mercado | dados públicos de mercado | preço, volume e eventos | origem primária e atraso |
| Integrações | APIs futuras | opções, gregas e histórico | contrato, limites e metodologia |
| Importação | arquivos manuais | carteira e dados licenciados | esquema, responsável e data |
| Análise técnica | ThePatternSite/Bulkowski e referências permitidas | padrões, rankings e estatísticas | link, resumo próprio e direitos de uso |
| Opções | B3, fornecedor licenciado ou arquivo validado | bid/ask, strikes, séries e negócios | timestamp, liquidez e cobertura |

Cada registro deverá guardar fonte, horário de coleta, tipo do dado e status. Fonte ausente significa dado indisponível.
