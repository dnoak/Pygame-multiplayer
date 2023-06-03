# Pygame-multiplayer
Jogo multiplayer LAN de até 4 jogadores feito em Python MQTT

Execução:

1 - Execute o arquivo server.py no computador do HOST, mude o valor de `mqtt_broker` para o IP do HOST

2 - Os outros arquivos .py são os jogadores, coloque o nome do arquivo no formato \<nomeJogador\>_\<nomeNave\>.py

&emsp;&emsp;2.1 - Caso o <nomeJogador> comece com "bot", ele vira um robô com movimentos predeterminados.

3 - Mude a variável `mqtt_broker` do arquivo .py do jogador para o IP do HOST e execute o arquivo

Instruções:
- Mouse - movimento: mira; clique esquerdo: tiro
- Teclado - WASD: movimentação
