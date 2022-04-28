import logging
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("smbprotocol").setLevel(logging.WARNING)
logging.getLogger("pypsexec").setLevel(logging.WARNING)
logging.getLogger("spnego").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.INFO)
