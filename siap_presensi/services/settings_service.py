"""
Layanan Pengaturan Sistem SIAP.
Menyimpan, memperbarui, memvalidasi, dan membaca konfigurasi
operasional, tarif potongan, serta target hari kerja.
"""
from datetime import datetime
from typing import Dict, Tuple, List, Optional

from config.settings import DEFAULT_SETTINGS
from database.connection import get_db_session
from database.models import Setting, AuditLog
from utils.logger import get_logger
from utils.validators import (
    validate_time_format,
    validate_positive_integer,
    validate_target_days,
)

logger = get_logger("SettingsService")


class SettingsService:
    """Service untuk membaca dan memperbarui konfigurasi sistem."""

    @staticmethod
    def get_all() -> Dict[str, str]:
        """Mengambil semua pengaturan dalam bentuk kamus key-value."""
        result: Dict[str, str] = {}
        # Isi default terlebih dahulu
        for k, v in DEFAULT_SETTINGS.items():
            result[k] = str(v["value"])

        try:
            with get_db_session() as session:
                records = session.query(Setting).all()
                for rec in records:
                    result[rec.setting_key] = rec.setting_value
        except Exception as e:
            logger.error(f"Gagal mengambil pengaturan dari database: {e}")

        return result

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> str:
        """Mengambil satu nilai pengaturan berdasarkan key."""
        try:
            with get_db_session() as session:
                rec = session.query(Setting).filter(Setting.setting_key == key).first()
                if rec:
                    return rec.setting_value
        except Exception as e:
            logger.error(f"Gagal mengambil setting '{key}': {e}")

        if default is not None:
            return default
        if key in DEFAULT_SETTINGS:
            return str(DEFAULT_SETTINGS[key]["value"])
        return ""

    @staticmethod
    def validate_settings(settings: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Memvalidasi seluruh nilai konfigurasi sebelum disimpan ke database.
        Mengembalikan (is_valid: bool, error_messages: List[str]).
        """
        errors = []

        # 1. Validasi Target Hari Kerja
        if "target_hari_kerja_bulanan" in settings:
            valid, _, err = validate_target_days(settings["target_hari_kerja_bulanan"])
            if not valid and err:
                errors.append(f"Target Hari Kerja: {err}")

        # 2. Validasi Format Jam Operasional
        time_fields = [
            ("jam_masuk_senin_kamis", "Jam Masuk (Senin-Kamis)"),
            ("jam_pulang_senin_kamis", "Jam Pulang (Senin-Kamis)"),
            ("jam_masuk_jumat", "Jam Masuk (Jumat)"),
            ("jam_pulang_jumat", "Jam Pulang (Jumat)"),
        ]
        for field_key, field_label in time_fields:
            if field_key in settings:
                valid, err = validate_time_format(settings[field_key])
                if not valid and err:
                    errors.append(f"{field_label}: {err}")

        # 3. Validasi Nominal Tarif Potongan
        potongan_fields = [
            ("potongan_terlambat_sd_1jam", "Potongan Terlambat <= 1 Jam"),
            ("potongan_terlambat_gt_1jam", "Potongan Terlambat > 1 Jam"),
            ("potongan_pulang_cepat", "Potongan Pulang Cepat"),
            ("potongan_tidak_absen_masuk", "Potongan Tidak Absen Masuk"),
            ("potongan_tidak_absen_pulang", "Potongan Tidak Absen Pulang"),
            ("potongan_tidak_hadir", "Potongan Tidak Hadir"),
        ]
        for field_key, field_label in potongan_fields:
            if field_key in settings:
                valid, _, err = validate_positive_integer(settings[field_key], field_label)
                if not valid and err:
                    errors.append(err)

        return len(errors) == 0, errors

    @staticmethod
    def save_settings(new_settings: Dict[str, str], user_id: Optional[int] = None) -> Tuple[bool, List[str]]:
        """
        Menyimpan kamus pengaturan ke database dengan validasi dan pencatatan audit trail.
        """
        is_valid, errors = SettingsService.validate_settings(new_settings)
        if not is_valid:
            return False, errors

        changed_keys = []
        try:
            with get_db_session() as session:
                for key, value in new_settings.items():
                    val_str = str(value).strip()
                    rec = session.query(Setting).filter(Setting.setting_key == key).first()
                    if rec:
                        if rec.setting_value != val_str:
                            rec.setting_value = val_str
                            rec.updated_at = datetime.utcnow()
                            changed_keys.append(key)
                    else:
                        desc = DEFAULT_SETTINGS.get(key, {}).get("description", "")
                        rec = Setting(
                            setting_key=key,
                            setting_value=val_str,
                            description=desc,
                            updated_at=datetime.utcnow(),
                        )
                        session.add(rec)
                        changed_keys.append(key)

                # Catat Audit Log jika ada perubahan
                if changed_keys:
                    audit = AuditLog(
                        user_id=user_id,
                        action="UPDATE_SETTINGS",
                        module="SETTINGS",
                        description=f"Pengaturan diperbarui untuk parameter: {', '.join(changed_keys)}",
                        created_at=datetime.utcnow(),
                    )
                    session.add(audit)
                    logger.info(f"Pengaturan sistem berhasil diperbarui oleh user {user_id}: {changed_keys}")

            return True, []
        except Exception as e:
            logger.error(f"Terjadi kesalahan saat menyimpan pengaturan: {e}")
            return False, [f"Terjadi kesalahan database: {str(e)}"]

    @staticmethod
    def reset_to_defaults(user_id: Optional[int] = None) -> Tuple[bool, List[str]]:
        """Mengembalikan seluruh konfigurasi ke nilai default bawaan pabrik."""
        defaults = {k: str(v["value"]) for k, v in DEFAULT_SETTINGS.items()}
        success, errors = SettingsService.save_settings(defaults, user_id=user_id)
        if success:
            logger.info(f"Seluruh pengaturan telah di-reset ke default oleh user {user_id}.")
        return success, errors
