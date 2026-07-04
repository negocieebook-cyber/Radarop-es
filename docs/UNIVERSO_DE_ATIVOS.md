# Universo de Ativos

O universo define quais ativos o Radar tenta analisar. Cada registro guarda ticker, nome, classe, setor, existência de opções no mock, liquidez, prioridade, observação, fonte e classificação do dado.

Um ativo entra no radar por curadoria e contrato válido. Sem opções, com baixa liquidez ou classe não elegível, recebe reprovação com motivo — não é descartado silenciosamente. Um ativo pode ser elegível e ainda não produzir oportunidade por falta de cadeia, risco, liquidez da opção ou confirmação.

Assim, muitos ativos podem ser examinados, mas poucos aparecem como oportunidades aprovadas. Nesta etapa, o universo é inteiramente **MOCK / EXEMPLO** e não representa disponibilidade real na B3.
