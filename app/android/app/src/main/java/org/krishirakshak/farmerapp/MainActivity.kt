package org.krishirakshak.farmerapp

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.speech.tts.TextToSpeech
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import java.io.File
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private var cameraImageUri: Uri? = null

    private var tts: TextToSpeech? = null
    private var isTtsReady = false

    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (filePathCallback == null) return@registerForActivityResult

        val results: Array<Uri>? = when {
            result.resultCode == RESULT_OK -> {
                val data = result.data
                if (data != null && data.data != null) {
                    arrayOf(data.data!!)
                } else if (cameraImageUri != null) {
                    arrayOf(cameraImageUri!!)
                } else null
            }
            else -> null
        }

        filePathCallback?.onReceiveValue(results)
        filePathCallback = null
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        // Camera permission handling
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        checkPermissions()
        initTTS()

        webView = WebView(this).apply {
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                allowFileAccess = true
                allowContentAccess = true
                databaseEnabled = true
                useWideViewPort = true
                loadWithOverviewMode = true
                cacheMode = WebSettings.LOAD_DEFAULT
                mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                // Allow local HTML assets to fetch data from the Pi HTTP server
                allowFileAccessFromFileURLs = true
                allowUniversalAccessFromFileURLs = true
            }

            // Expose native Text-to-Speech bridge to JavaScript (100% offline)
            addJavascriptInterface(AndroidTTSBridge(), "AndroidTTS")

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: WebResourceError?
                ) {
                    super.onReceivedError(view, request, error)
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    mWebView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams?
                ): Boolean {
                    this@MainActivity.filePathCallback?.onReceiveValue(null)
                    this@MainActivity.filePathCallback = filePathCallback

                    val takePictureIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                    var photoFile: File? = null
                    try {
                        photoFile = createImageFile()
                    } catch (ex: IOException) {
                        ex.printStackTrace()
                    }

                    if (photoFile != null) {
                        cameraImageUri = FileProvider.getUriForFile(
                            this@MainActivity,
                            "${applicationContext.packageName}.fileprovider",
                            photoFile
                        )
                        takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, cameraImageUri)
                    }

                    val contentSelectionIntent = Intent(Intent.ACTION_GET_CONTENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "image/*"
                    }

                    val chooserIntent = Intent(Intent.ACTION_CHOOSER).apply {
                        putExtra(Intent.EXTRA_INTENT, contentSelectionIntent)
                        putExtra(Intent.EXTRA_TITLE, "Capture or Choose Leaf Photo")
                        putExtra(Intent.EXTRA_INITIAL_INTENTS, arrayOf(takePictureIntent))
                    }

                    fileChooserLauncher.launch(chooserIntent)
                    return true
                }
            }
        }

        setContentView(webView)
        // Load embedded farmer interface
        webView.loadUrl("file:///android_asset/web/index.html")
    }

    private fun checkPermissions() {
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.CAMERA
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    @Throws(IOException::class)
    private fun createImageFile(): File {
        val timeStamp: String = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val storageDir: File? = getExternalFilesDir(Environment.DIRECTORY_PICTURES)
        return File.createTempFile("LEAF_${timeStamp}_", ".jpg", storageDir)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    private fun initTTS() {
        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                isTtsReady = true
                val result = tts?.setLanguage(Locale("hi", "IN"))
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts?.setLanguage(Locale("en", "IN"))
                }
            }
        }
    }

    inner class AndroidTTSBridge {
        @JavascriptInterface
        fun isAvailable(): Boolean = isTtsReady

        @JavascriptInterface
        fun speak(text: String, lang: String) {
            if (!isTtsReady || tts == null) return
            val locale = when (lang.lowercase()) {
                "hi" -> Locale("hi", "IN")
                "mr" -> Locale("mr", "IN")
                "te" -> Locale("te", "IN")
                "ta" -> Locale("ta", "IN")
                "kn" -> Locale("kn", "IN")
                "bn" -> Locale("bn", "IN")
                "gu" -> Locale("gu", "IN")
                "pa" -> Locale("pa", "IN")
                "or" -> Locale("or", "IN")
                else -> Locale("en", "IN")
            }
            val result = tts?.setLanguage(locale)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts?.setLanguage(Locale("en", "IN"))
            }
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "KR_TTS_${System.currentTimeMillis()}")
        }

        @JavascriptInterface
        fun stop() {
            tts?.stop()
        }
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }
}
