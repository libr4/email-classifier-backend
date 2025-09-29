import re
from typing import Optional

_RE_TICKET   = re.compile(r'\b(chamado|ticket|protocolo)\b.*?(\d+)', re.I)
_RE_ERROR    = re.compile(r'\berro\W*(\d{3})\b', re.I)
_RE_ATTACH   = re.compile(r'\b(anexo|anexei|segue\s+anexo)\b', re.I)
_RE_ACCESS   = re.compile(r'\b(acesso|liberar\s+acesso|desbloquei[ao])\b', re.I)
_RE_STATUS   = re.compile(r'\b(status|atualiza[çc][aã]o)\b', re.I)
_RE_PWD      = re.compile(r'\b(senha|reset|redefinir)\b', re.I)
_RE_OOO      = re.compile(r'\b(ausente|out of office|OOO)\b', re.I)

def suggest_reply_pt(text: str, label: str) -> tuple[Optional[str], str]:
    t = text.strip()
    if label != "Produtivo":
        if _RE_OOO.search(t):
            return ("Recebemos sua mensagem automática. Anotado o seu período de ausência.", "ooo")
        return ("Prezado, agradeço o contato. No momento não identifiquei demanda objetiva. Para que eu possa ajudar, gentileza informar objetivo e ação desejada.", "generic")

    m = _RE_TICKET.search(t)
    if _RE_STATUS.search(t) or m:
        ref = m.group(2) if m else ""
        msg = (f"Olá! Verificaremos o status do chamado {ref} e retornaremos com uma atualização em breve."
               if ref else
               "Olá! Vamos verificar o status da sua solicitação e retornaremos com uma atualização em breve.")
        return (msg, "status")

    em = _RE_ERROR.search(t)
    if em:
        code = em.group(1)
        return (f"Obrigado pelo relato do erro {code}. Encaminhamos para análise e retornaremos assim que possível.", "error")

    if _RE_ACCESS.search(t):
        return ("Obrigado pelo pedido de acesso/desbloqueio. Vamos validar a autorização e retornaremos com a liberação.", "access")

    if _RE_PWD.search(t):
        return ("Podemos ajudar com a redefinição de senha. Confirme, por favor, o usuário/e-mail cadastrado.", "pwd")

    if _RE_ATTACH.search(t):
        return ("Recebemos o anexo. Vamos analisar o conteúdo e daremos retorno com os próximos passos.", "attach")

    return ("Recebemos sua solicitação e já estamos analisando. Retornaremos em breve com os próximos passos.", "generic")


