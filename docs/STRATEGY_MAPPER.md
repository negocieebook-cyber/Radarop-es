# Strategy Mapper

O mapper reutiliza Healthbox, Bulkowski e a tese gráfica para classificar o
regime e sugerir famílias direcionais, laterais ou de volatilidade.

As sugestões são apenas candidatas gráficas. Sem cadeia real ficam pendentes;
com cadeia, só são validadas quando o motor de opções fornece preço, liquidez,
break-even e perda máxima. Nenhuma sugestão representa ordem.
