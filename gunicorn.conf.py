"""Servidor de produção; a hospedagem fornece a porta por PORT."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8050')}"
workers = 1
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
control_socket_disable = True
