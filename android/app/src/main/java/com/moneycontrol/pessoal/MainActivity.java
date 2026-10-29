package com.moneycontrol.pessoal;
import android.print.PrintManager;
import android.app.Activity;
import android.app.PrintManager;
import android.content.ActivityNotFoundException;
import android.content.ContentValues;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public class MainActivity extends Activity {
    private static final int PICK_FILE = 4107;
    private WebView webView;
    private ValueCallback<Uri[]> fileChooserCallback;
    private WebViewAssetLoader assetLoader;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(37, 40, 46));
        getWindow().setNavigationBarColor(Color.rgb(17, 24, 39));
        assetLoader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .build();
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(248, 250, 252));
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setAllowFileAccess(false);
        webView.getSettings().setAllowContentAccess(true);
        webView.getSettings().setSupportMultipleWindows(false);
        webView.getSettings().setJavaScriptCanOpenWindowsAutomatically(false);
        webView.addJavascriptInterface(new AndroidBridge(), "MCAndroid");
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                return !"appassets.androidplatform.net".equals(uri.getHost());
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileChooserCallback != null) fileChooserCallback.onReceiveValue(null);
                fileChooserCallback = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/octet-stream", "application/x-sqlite3", "application/vnd.sqlite3"});
                try { startActivityForResult(intent, PICK_FILE); return true; }
                catch (ActivityNotFoundException e) { fileChooserCallback = null; return false; }
            }
        });
        setContentView(webView);
        webView.loadUrl("https://appassets.androidplatform.net/assets/www/index.html");
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && fileChooserCallback != null) {
            Uri[] result = resultCode == RESULT_OK && data != null && data.getData() != null ? new Uri[]{data.getData()} : null;
            fileChooserCallback.onReceiveValue(result);
            fileChooserCallback = null;
        }
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        if (webView != null) { webView.removeJavascriptInterface("MCAndroid"); webView.destroy(); webView = null; }
        super.onDestroy();
    }

    private class AndroidBridge {
        @JavascriptInterface public String saveToDownloads(String name, String mime, String base64) {
            try {
                String safe = safeName(name);
                byte[] bytes = Base64.getDecoder().decode(base64);
                ContentValues values = new ContentValues();
                values.put(MediaStore.Downloads.DISPLAY_NAME, safe);
                values.put(MediaStore.Downloads.MIME_TYPE, mime == null ? "application/octet-stream" : mime);
                values.put(MediaStore.Downloads.RELATIVE_PATH, "Download/MoneyControl");
                Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                if (uri == null) return "Android não conseguiu criar o arquivo em Downloads.";
                try (OutputStream out = getContentResolver().openOutputStream(uri)) { if (out == null) throw new Exception("Não foi possível gravar o arquivo."); out.write(bytes); }
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Arquivo salvo em Downloads/MoneyControl", Toast.LENGTH_LONG).show());
                return "";
            } catch (Exception e) { return "Falha ao salvar arquivo: " + e.getMessage(); }
        }

        @JavascriptInterface public String share(String name, String mime, String base64) {
            try {
                String safe = safeName(name);
                byte[] bytes = Base64.getDecoder().decode(base64);
                File dir = new File(getCacheDir(), "shared");
                if (!dir.exists() && !dir.mkdirs()) return "Não foi possível preparar o arquivo para compartilhar.";
                File file = new File(dir, safe);
                try (FileOutputStream out = new FileOutputStream(file)) { out.write(bytes); }
                Uri uri = FileProvider.getUriForFile(MainActivity.this, getPackageName() + ".fileprovider", file);
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType(mime == null ? "application/octet-stream" : mime);
                send.putExtra(Intent.EXTRA_STREAM, uri);
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                runOnUiThread(() -> startActivity(Intent.createChooser(send, "Compartilhar arquivo")));
                return "";
            } catch (Exception e) { return "Falha ao compartilhar: " + e.getMessage(); }
        }

        @JavascriptInterface public void print() {
            runOnUiThread(() -> {
                try {
                    PrintManager manager = (PrintManager) getSystemService(PRINT_SERVICE);
                    manager.print("MoneyControl", webView.createPrintDocumentAdapter("MoneyControl"), null);
                } catch (Exception e) { Toast.makeText(MainActivity.this, "Não foi possível abrir a impressão.", Toast.LENGTH_LONG).show(); }
            });
        }
        @JavascriptInterface public void toast(String message) { runOnUiThread(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show()); }
    }

    private String safeName(String name) {
        String safe = name == null ? "arquivo" : name.replaceAll("[^A-Za-z0-9._-]", "_");
        if (safe.isEmpty() || safe.equals(".") || safe.equals("..")) return "arquivo";
        return safe.length() > 120 ? safe.substring(0, 120) : safe;
    }
}
