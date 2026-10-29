# MoneyControl

Aplicativo de controle financeiro pessoal.

- [Guia e arquitetura do APK Android offline](ANDROID.md)
- O projeto Android não solicita permissão de Internet; os assets e o motor Pyodide são empacotados no APK.
- Backups externos do APK são criptografados com senha no formato `.mcbak`.
- O aviso de privacidade bloqueia o primeiro uso até a leitura completa e confirmação.

Para compilar o APK de teste, consulte `ANDROID.md` ou execute o workflow **Build Android APK** no GitHub Actions.
