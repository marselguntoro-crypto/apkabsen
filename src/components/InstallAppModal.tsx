import React, { useState } from 'react';
import {
  Smartphone,
  Download,
  X,
  CheckCircle2,
  Monitor,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  Zap,
  Info,
  Layers,
  Copy,
  Check,
} from 'lucide-react';
import { usePwaInstall } from '../hooks/usePwaInstall';

interface InstallAppModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function InstallAppModal({ isOpen, onClose }: InstallAppModalProps) {
  const { hasNativePrompt, installApp, isInstalled } = usePwaInstall();
  const [activePlatform, setActivePlatform] = useState<'android' | 'windows' | 'github_apk'>('android');
  const [copiedLink, setCopiedLink] = useState(false);

  if (!isOpen) return null;

  const currentUrl = typeof window !== 'undefined' ? window.location.href : '';

  const copyAppUrl = () => {
    navigator.clipboard.writeText(currentUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleInstallClick = async () => {
    if (hasNativePrompt) {
      const installed = await installApp();
      if (installed) {
        onClose();
      }
    } else {
      // Show platform instructions
      setActivePlatform('android');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white p-5 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base text-white">Pasang Aplikasi SIAP (Install APK)</h3>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded-full font-semibold">
                  Instalasi Instan 1-Klik
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Aplikasi siap dipasang langsung ke HP Android atau Komputer Desktop
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Platform Selection Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-4 pt-3 gap-2">
          <button
            onClick={() => setActivePlatform('android')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition border-b-2 cursor-pointer ${
              activePlatform === 'android'
                ? 'bg-white text-blue-600 border-blue-600 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 border-transparent'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            <span>HP Android (WebAPK Instan)</span>
          </button>

          <button
            onClick={() => setActivePlatform('windows')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition border-b-2 cursor-pointer ${
              activePlatform === 'windows'
                ? 'bg-white text-blue-600 border-blue-600 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 border-transparent'
            }`}
          >
            <Monitor className="w-4 h-4" />
            <span>PC Windows (Aplikasi Desktop)</span>
          </button>

          <button
            onClick={() => setActivePlatform('github_apk')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition border-b-2 cursor-pointer ${
              activePlatform === 'github_apk'
                ? 'bg-white text-blue-600 border-blue-600 shadow-xs'
                : 'text-slate-600 hover:text-slate-900 border-transparent'
            }`}
          >
            <Download className="w-4 h-4" />
            <span>File APK Android Mentah (.apk)</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-slate-700">
          {/* TAB 1: ANDROID WEBAPK */}
          {activePlatform === 'android' && (
            <div className="space-y-4">
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start gap-3">
                <div className="p-2 bg-emerald-600 text-white rounded-lg shrink-0 mt-0.5">
                  <Zap className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-emerald-950">
                    Cara Termudah: Pasang Langsung ke Layar Utama Android (WebAPK)
                  </h4>
                  <p className="text-xs text-emerald-800 leading-relaxed">
                    Sistem operasi Android (Google Chrome / Samsung Internet) secara otomatis mengemas aplikasi ini menjadi <strong>aplikasi Android asli (WebAPK)</strong> dengan ikon di menu aplikasi, membuka layar penuh (tanpa bilah browser), dan dapat dibuka secara offline!
                  </p>
                </div>
              </div>

              {/* Install Button if browser supports beforeinstallprompt */}
              {hasNativePrompt && !isInstalled && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
                  <div>
                    <h5 className="text-sm font-bold text-blue-950">Browser Anda Mendukung Pasang Cepat</h5>
                    <p className="text-xs text-blue-800">Klik tombol di samping untuk langsung menginstal ke perangkat.</p>
                  </div>
                  <button
                    onClick={handleInstallClick}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow flex items-center gap-2 transition cursor-pointer"
                  >
                    <Download className="w-4 h-4" />
                    <span>Pasang Sekarang</span>
                  </button>
                </div>
              )}

              {isInstalled && (
                <div className="p-3 bg-emerald-100 text-emerald-900 rounded-lg text-xs font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Aplikasi SIAP sudah terpasang di perangkat Anda!</span>
                </div>
              )}

              {/* 3 Langkah Mudah di Android */}
              <div className="space-y-3">
                <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Langkah Memasang di HP Android (Hanya 10 Detik):
                </h5>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                    <div className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                      1
                    </div>
                    <p className="text-xs font-bold text-slate-900">Buka Link di Chrome HP</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Salin tautan aplikasi ini dan buka melalui browser <strong>Google Chrome</strong> di smartphone Android Anda.
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                    <div className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                      2
                    </div>
                    <p className="text-xs font-bold text-slate-900">Ketuk Menu Titik Tiga (⋮)</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Di pojok kanan atas Chrome, ketuk tombol menu titik tiga (<strong>⋮</strong>).
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                    <div className="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
                      3
                    </div>
                    <p className="text-xs font-bold text-slate-900">Pilih &quot;Instal Aplikasi&quot;</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">
                      Pilih <strong>&quot;Instal Aplikasi&quot;</strong> atau <strong>&quot;Tambahkan ke Layar Utama&quot;</strong>. Ikon SIAP akan langsung muncul di menu HP Anda!
                    </p>
                  </div>
                </div>
              </div>

              {/* Share/Copy link */}
              <div className="p-3.5 bg-slate-100 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-slate-600">
                  <span className="font-semibold text-slate-900">Tautan Aplikasi untuk HP:</span>
                  <div className="font-mono text-[11px] text-blue-700 truncate max-w-md mt-0.5">
                    {currentUrl}
                  </div>
                </div>
                <button
                  onClick={copyAppUrl}
                  className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-1.5 shrink-0 transition cursor-pointer"
                >
                  {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedLink ? 'Tersalin!' : 'Salin Tautan'}</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: WINDOWS PC */}
          {activePlatform === 'windows' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
                <div className="p-2 bg-blue-600 text-white rounded-lg shrink-0 mt-0.5">
                  <Monitor className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-blue-950">
                    Pasang sebagai Aplikasi Desktop Windows
                  </h4>
                  <p className="text-xs text-blue-800 leading-relaxed">
                    Anda dapat memasang aplikasi ini di laptop/PC Windows melalui Google Chrome atau Microsoft Edge dengan 1-klik tanpa perlu ekstrak file!
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Cara Memasang di PC Windows:
                </h5>

                <div className="space-y-2 text-xs">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-3">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-[11px] flex items-center justify-center shrink-0">
                      1
                    </span>
                    <span>
                      Pada bilah alamat (URL bar) Google Chrome atau Edge di atas, perhatikan ikon <strong>Komputer dengan tanda panah ke bawah (Instal SIAP)</strong> di sebelah kanan bintang bookmark.
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-3">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold text-[11px] flex items-center justify-center shrink-0">
                      2
                    </span>
                    <span>
                      Atau klik menu browser (titik tiga ⋮) &rarr; pilih <strong>&quot;Simpan dan Bagikan&quot;</strong> &rarr; klik <strong>&quot;Instal SIAP...&quot;</strong>.
                    </span>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-3">
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 font-bold text-[11px] flex items-center justify-center shrink-0">
                      3
                    </span>
                    <span>
                      Aplikasi SIAP akan otomatis terbuka dalam jendela mandiri dan membuat shortcut resmi di <strong>Desktop</strong> dan <strong>Start Menu Windows</strong>!
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: STANDALONE APK VIA GITHUB */}
          {activePlatform === 'github_apk' && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                <div className="p-2 bg-amber-600 text-white rounded-lg shrink-0 mt-0.5">
                  <Download className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-amber-950">
                    Kompilasi Berkas Standalone APK (.apk) untuk Android
                  </h4>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    Jika Anda membutuhkan berkas instalasi biner <strong>.apk</strong> mentah untuk dibagikan via WhatsApp/Bluetooth atau diinstal secara *sideloading* di smartphone:
                  </p>
                </div>
              </div>

              <div className="p-4 bg-slate-900 text-slate-200 rounded-xl space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between text-slate-400 font-sans border-b border-slate-800 pb-2">
                  <span className="font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-400" />
                    Workflow GitHub Actions Android APK Builder
                  </span>
                  <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded">.github/workflows/build_apk.yml</span>
                </div>

                <p className="font-sans text-slate-300 text-xs leading-relaxed">
                  Kami telah menambahkan workflow <strong>GitHub Actions</strong> untuk mengemas berkas <code>SIAP_Presensi.apk</code> secara otomatis menggunakan cloud Android SDK.
                </p>

                <div className="bg-slate-950 p-3 rounded border border-slate-800 text-[11px] text-emerald-400 space-y-1">
                  <div># 1. Push kode ke repository GitHub:</div>
                  <div className="text-slate-400">git push origin main</div>
                  <div># 2. Buka tab Actions di GitHub:</div>
                  <div className="text-slate-400">Pilih workflow &quot;Build Android APK&quot;</div>
                  <div># 3. Unduh berkas SIAP_Presensi.apk di tab Artifacts!</div>
                </div>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                <p className="font-bold text-slate-800 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-blue-600" />
                  Keuntungan Menggunakan WebAPK (Tab 1):
                </p>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  WebAPK tidak memerlukan izin instalasi sumber tidak dikenal (*Unknown Sources*), ukuran file sangat ringan (&lt; 2 MB), dan selalu terbarui secara otomatis saat aplikasi diperbarui tanpa perlu menginstal ulang file APK!
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Resmi & Bebas Malware</span>
          </div>

          <div className="flex items-center gap-2">
            {hasNativePrompt && !isInstalled && (
              <button
                onClick={handleInstallClick}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Pasang Aplikasi Sekarang</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold text-xs transition cursor-pointer"
            >
              Tutup
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
