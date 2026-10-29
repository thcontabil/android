# MoneyControl Pessoal para Android

Esta pasta contém o projeto nativo que empacota a interface e o motor Python do MoneyControl em um APK offline.

## Garantias de arquitetura do APK

- O manifesto **não declara `android.permission.INTERNET`**. O APK não pode abrir conexões de rede normais.
- Os arquivos HTML, JavaScript, Python e Pyodide são empacotados dentro do APK pelo workflow de build.
- O app usa uma origem local via `WebViewAssetLoader`; não depende de um servidor hospedado para executar.
- O Android desativa o backup automático do sistema (`allowBackup=false`). A pessoa controla as cópias manuais.
- Backups exportados no Android usam o formato `.mcbak`, AES-GCM-256 e uma chave derivada por PBKDF2-HMAC-SHA256 (310.000 iterações). A senha é pedida a cada exportação/restauração e não é armazenada.
- OFX é processado no motor local. No modo privado do APK, a importação não persiste o nome original do arquivo, número de conta ou FITID cru; guarda um fingerprint derivado para deduplicação e descrições genéricas, como `PIX PARA`.
- O aviso de privacidade bloqueia o primeiro uso até o final do texto e confirmação explícita. Não tem botão de fechar.

## Compilar o APK

O workflow `.github/workflows/android-apk.yml` monta os assets (incluindo Pyodide), executa os testes de lógica e compila `app-debug.apk`. Para executar manualmente em uma máquina com Node.js 20, Java 17, Android SDK e Gradle:

```bash
node scripts/montar-site.mjs
rm -rf android/app/src/main/assets/www
mkdir -p android/app/src/main/assets/www
cp -R dist/. android/app/src/main/assets/www/
gradle -p android assembleDebug
```

O APK de teste será criado em `android/app/build/outputs/apk/debug/app-debug.apk`.

## Notas de segurança

- A criptografia descrita acima protege os **arquivos de backup exportados**. O banco de dados ativo fica no armazenamento privado do app e conta com as proteções do sistema Android; o projeto ainda não usa SQLCipher para criptografia própria do banco SQLite.
- Se a senha de um `.mcbak` for perdida, o conteúdo não poderá ser recuperado. Guardar a senha separada do arquivo é essencial.
- O compartilhamento de um arquivo é uma ação explícita do usuário e pode transferir esse arquivo ao aplicativo/serviço escolhido.
- O modo privado é ativado pelo worker quando executado na origem local do APK (`appassets.androidplatform.net`).
- Antes de distribuir amplamente, teste a instalação, importação OFX, backup criptografado, restauração e funcionamento offline em aparelhos Android reais. O APK gerado pelo workflow é de debug; distribuição de release exige assinatura apropriada.
