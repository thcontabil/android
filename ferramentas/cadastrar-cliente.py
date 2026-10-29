#!/usr/bin/env python3
"""Cadastra, lista ou remove clientes (usuário + senha) da versão de celular do escritório.

Rode na SUA máquina. Depois, faça commit e republique o site (GitHub). O arquivo editado é
site/py/financas/acessos_contas.py, que guarda só o hash da senha (nunca a senha em texto).

Exemplos:
  python ferramentas/cadastrar-cliente.py --usuario joao --nome "João Silva"
      (gera uma senha forte e mostra na tela — anote e envie ao cliente)
  python ferramentas/cadastrar-cliente.py --usuario maria --nome "Maria" --senha minhasenha --ate 2027-12-31
  python ferramentas/cadastrar-cliente.py --listar
  python ferramentas/cadastrar-cliente.py --remover joao
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "py" / "financas" / "acessos_contas.py"
ITERS = 200_000


def carregar() -> dict:
    ns: dict = {}
    if DATA.exists():
        exec(compile(DATA.read_text(encoding="utf-8"), str(DATA), "exec"), ns)  # noqa: S102
    contas = ns.get("CONTAS") or {}
    return {str(k).lower(): v for k, v in contas.items()}


def salvar(contas: dict) -> None:
    linhas = ["\"\"\"Contas de acesso (usuário + senha embaralhada). NÃO edite à mão: use ferramentas/cadastrar-cliente.py.",
              "",
              "Este arquivo é publicado junto com o app (repositório público), por isso guarda apenas o hash da senha,",
              "nunca a senha. Depois de cadastrar/remover um cliente, faça commit e republique.",
              "\"\"\"",
              "CONTAS = {"]
    for user in sorted(contas):
        c = contas[user]
        ate = c.get("ate") or ""
        linhas.append(f"    {user!r}: {{\"nome\": {c.get('nome','')!r}, \"salt\": {c['salt']!r}, "
                      f"\"hash\": {c['hash']!r}, \"iters\": {int(c.get('iters', ITERS))}, \"ate\": {ate!r}}},")
    linhas.append("}")
    DATA.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def gerar_senha(n: int = 10) -> str:
    alfabeto = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(n))


def hash_senha(senha: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERS).hex()


def main() -> None:
    ap = argparse.ArgumentParser(description="Cadastro de clientes do MoneyControl (celular)")
    ap.add_argument("--usuario", help="nome de usuário (login), sem espaços")
    ap.add_argument("--nome", help="nome do cliente (aparece no app)")
    ap.add_argument("--senha", help="senha; se omitida, uma senha forte é gerada e mostrada")
    ap.add_argument("--ate", help="validade do acesso AAAA-MM-DD (opcional)")
    ap.add_argument("--remover", metavar="USUARIO", help="remove um cliente")
    ap.add_argument("--listar", action="store_true", help="lista os clientes cadastrados")
    a = ap.parse_args()
    contas = carregar()

    if a.listar:
        if not contas:
            print("Nenhum cliente cadastrado. O app fica aberto (sem login) até você cadastrar o primeiro.")
            return
        print(f"{'USUÁRIO':<20}{'NOME':<28}VALIDADE")
        for u in sorted(contas):
            print(f"{u:<20}{(contas[u].get('nome') or ''):<28}{contas[u].get('ate') or 'sem vencimento'}")
        return

    if a.remover:
        u = a.remover.strip().lower()
        if u not in contas:
            sys.exit(f"Usuário '{u}' não encontrado.")
        del contas[u]
        salvar(contas)
        print(f"Cliente '{u}' removido. Faça commit e republique para bloquear o acesso dele.")
        return

    if not a.usuario:
        ap.error("informe --usuario (ou use --listar / --remover)")
    user = a.usuario.strip().lower()
    if not re.fullmatch(r"[a-z0-9._-]{3,}", user):
        ap.error("--usuario deve ter ao menos 3 caracteres: letras, números, ponto, hífen ou _ (sem espaços).")
    if a.ate:
        try:
            datetime.strptime(a.ate, "%Y-%m-%d")
        except ValueError:
            ap.error("--ate deve ser AAAA-MM-DD")
    senha = a.senha or gerar_senha()
    salt = os.urandom(16)
    novo = user not in contas
    contas[user] = {"nome": a.nome or user, "salt": salt.hex(), "hash": hash_senha(senha, salt),
                    "iters": ITERS, "ate": a.ate or ""}
    salvar(contas)
    print(f"\n{'Cliente cadastrado' if novo else 'Cliente atualizado'}: {contas[user]['nome']}")
    print(f"  Usuário:  {user}")
    print(f"  Senha:    {senha}")
    print(f"  Validade: {a.ate or 'sem vencimento'}")
    print("\nEnvie o usuário e a senha ao cliente. Depois: git commit + republicar o site.\n")


if __name__ == "__main__":
    main()
