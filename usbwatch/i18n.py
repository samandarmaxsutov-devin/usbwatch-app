"""Interface localisation (Uzbek / Russian / English).

Only the UI *chrome* is translated — nav, titles, buttons, labels, column headers,
dialogs. Technical data values (device type names, raw action names, device names)
stay as they are. `t(key, *args)` returns the string for the current language; the
`lang` Observable lets the main window rebuild itself when the language changes.
"""
from .core import Observable
from .services import settings_service

LANGS = ("uz", "ru", "en")
LANG_NAMES = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}

_T = {
    # ---- app / nav ----
    "app.subtitle": {"uz": "USB qurilma va fayl auditi", "ru": "Аудит USB-устройств и файлов",
                     "en": "USB device & file audit"},
    "nav.storage": {"uz": "Xotira qurilmalari", "ru": "Накопители (флешки)", "en": "Storage (flash)"},
    "nav.all": {"uz": "Barcha USB qurilmalar", "ru": "Все USB-устройства", "en": "All USB devices"},
    "nav.activity": {"uz": "Fayl faoliyati", "ru": "Активность файлов", "en": "File Activity"},
    "nav.access": {"uz": "Kirish nazorati", "ru": "Контроль доступа", "en": "Access Control"},
    "nav.logs": {"uz": "Loglar", "ru": "Журналы", "en": "Logs"},
    "nav.settings": {"uz": "Sozlamalar", "ru": "Настройки", "en": "Settings"},
    "status.active": {"uz": "●  Monitoring faol", "ru": "●  Мониторинг активен",
                      "en": "●  Monitoring active"},
    "drives.none": {"uz": "USB disk ulanmagan", "ru": "USB-диски не подключены",
                    "en": "No USB drives connected"},
    "drives.prefix": {"uz": "USB: ", "ru": "USB: ", "en": "USB: "},

    # ---- common ----
    "btn.refresh": {"uz": "Yangilash", "ru": "Обновить", "en": "Refresh"},
    "btn.export": {"uz": "Eksport…", "ru": "Экспорт…", "en": "Export…"},
    "btn.enable": {"uz": "Yoqish", "ru": "Включить", "en": "Enable"},
    "btn.disable": {"uz": "O'chirish", "ru": "Отключить", "en": "Disable"},
    "btn.details": {"uz": "Batafsil", "ru": "Подробно", "en": "Details"},
    "btn.regedit": {"uz": "RegEdit'da ochish", "ru": "Открыть в RegEdit", "en": "Open in RegEdit"},
    "menu.properties": {"uz": "Xususiyatlar (batafsil)", "ru": "Свойства (подробно)", "en": "Properties (details)"},
    "menu.copy": {"uz": "Qatorni nusxalash", "ru": "Копировать строку", "en": "Copy row"},
    "menu.uninstall": {"uz": "Uninstall (o'chirib tashlash)", "ru": "Удалить устройство",
                       "en": "Uninstall (remove)"},
    "dlg.details_title": {"uz": "Qurilma ma'lumotlari", "ru": "Сведения об устройстве",
                          "en": "Device details"},
    "dlg.copied": {"uz": "Nusxalandi.", "ru": "Скопировано.", "en": "Copied."},
    "dlg.regedit_failed": {"uz": "RegEdit'ni ochib bo'lmadi.", "ru": "Не удалось открыть RegEdit.",
                           "en": "Could not open RegEdit."},
    "dlg.uninstall_confirm": {"uz": "«{0}» qurilmasini o'chirib tashlaysizmi?\n\nQurilma drayveri tizimdan "
                                   "olib tashlanadi (keyin qayta ulasangiz yana o'rnatiladi).",
                              "ru": "Удалить устройство «{0}»?\n\nДрайвер будет удалён из системы "
                                   "(при повторном подключении установится заново).",
                              "en": "Uninstall «{0}»?\n\nThe device driver node is removed (it reinstalls "
                                   "when you reconnect)."},
    "dlg.uninstalled": {"uz": "«{0}» o'chirib tashlandi.", "ru": "«{0}» удалено.", "en": "«{0}» uninstalled."},
    "dlg.uninstall_failed": {"uz": "«{0}» ni o'chirib bo'lmadi (Administrator kerak).",
                             "ru": "Не удалось удалить «{0}» (нужен администратор).",
                             "en": "Could not uninstall «{0}» (Administrator required)."},
    "common.search": {"uz": "Qidirish…", "ru": "Поиск…", "en": "Search…"},
    "common.loading": {"uz": "Yuklanmoqda…", "ru": "Загрузка…", "en": "Loading…"},
    "common.yes": {"uz": "Ha", "ru": "Да", "en": "Yes"},
    "common.connected": {"uz": "Ulangan", "ru": "Подключено", "en": "Connected"},
    "common.disabled": {"uz": "O'chirilgan", "ru": "Отключено", "en": "Disabled"},

    # ---- storage tab ----
    "storage.subtitle": {"uz": "Faqat xotira qurilmalari: USB fleshka va tashqi disklar.",
                         "ru": "Только накопители: USB-флешки и внешние диски.",
                         "en": "Storage devices only: USB flash drives and external disks."},
    "card.known": {"uz": "Tarixdagi qurilmalar", "ru": "Устройств в истории", "en": "Devices in history"},
    "card.now": {"uz": "Hozir ulangan", "ru": "Подключено сейчас", "en": "Connected now"},
    "card.events": {"uz": "Qayd etilgan hodisalar", "ru": "Событий записано", "en": "Events logged"},
    "storage.no_drive": {"uz": "Hozir USB disk ulanmagan", "ru": "Сейчас USB-диск не подключён",
                         "en": "No USB drive connected right now"},
    "storage.select_hint": {"uz": "Amallarini ko'rish uchun yuqoridan qurilma tanlang",
                            "ru": "Выберите устройство выше, чтобы увидеть его действия",
                            "en": "Select a device above to see its actions"},
    "storage.actions_title": {"uz": "{0} amallari  ·  {1} ta hodisa",
                              "ru": "Действия: {0}  ·  событий: {1}",
                              "en": "Actions on {0}  ·  {1} event(s)"},
    "storage.actions_none": {"uz": "{0} amallari  ·  hali hech narsa yo'q",
                             "ru": "Действия: {0}  ·  пока ничего",
                             "en": "Actions on {0}  ·  nothing recorded yet"},

    # ---- all-usb tab ----
    "all.subtitle": {"uz": "Barcha USB qurilma turlari (klaviatura, kamera, hub, fleshka …).",
                     "ru": "Все типы USB-устройств (клавиатура, камера, хаб, флешка …).",
                     "en": "Every type of USB device (keyboard, camera, hub, flash …)."},
    "all.search_ph": {"uz": "Nom / seriya / VID / PID / tur bo'yicha qidirish…",
                      "ru": "Поиск по имени / серии / VID / PID / типу…",
                      "en": "Search name / serial / VID / PID / type…"},
    "all.status": {"uz": "{1} tadan {0} ta qurilma", "ru": "{0} из {1} устройств",
                   "en": "{0} of {1} device(s)"},

    # ---- activity tab ----
    "activity.subtitle": {"uz": "Ulangan USB disklardagi jonli fayl loglari.",
                          "ru": "Живой журнал файлов на подключённых USB-дисках.",
                          "en": "Live log of everything that happens on connected USB drives."},
    "activity.search_ph": {"uz": "Yo'l bo'yicha qidirish…", "ru": "Поиск по пути…", "en": "Search path…"},
    "activity.all": {"uz": "Barcha amallar", "ru": "Все действия", "en": "All actions"},

    # ---- logs tab ----
    "logs.subtitle": {"uz": "Kunlik CSV loglar va Windows'ning USB o'rnatish tarixi.",
                      "ru": "Ежедневные CSV-журналы и история установки USB в Windows.",
                      "en": "Daily CSV logs and the Windows USB install history."},
    "logs.open_folder": {"uz": "Papkani ochish", "ru": "Открыть папку", "en": "Open folder"},
    "logs.open_file": {"uz": "Faylni ochish…", "ru": "Открыть файл…", "en": "Open file…"},
    "logs.filter": {"uz": "Filtr…", "ru": "Фильтр…", "en": "Filter…"},

    # ---- access control ----
    "access.help": {"uz": "Ruxsat berilgan va bloklangan qurilmalar alohida ro'yxatlarda. "
                          "Ikkala ro'yxatda ham yo'q qurilmalar uchun quyidagi standart amal qo'llanadi.",
                    "ru": "Разрешённые и заблокированные устройства — в отдельных списках. "
                          "Для устройств, которых нет ни в одном списке, применяется действие ниже.",
                    "en": "Allowed and blocked devices live in separate lists. Devices in neither "
                          "list get the default action below."},
    "access.default_label": {"uz": "Ro'yxatda yo'q qurilmalar uchun:",
                             "ru": "Для устройств не из списков:", "en": "For devices in neither list:"},
    "access.default_off": {"uz": "O'chiq", "ru": "Выкл", "en": "Off"},
    "access.default_log": {"uz": "Faqat log qilish", "ru": "Только журнал", "en": "Log only"},
    "access.default_block": {"uz": "Bloklash", "ru": "Блокировать", "en": "Block"},
    "access.tab_all": {"uz": "Barcha qurilmalar", "ru": "Все устройства", "en": "All devices"},
    "access.tab_allowed": {"uz": "Ruxsat berilgan", "ru": "Разрешённые", "en": "Allowed"},
    "access.tab_blocked": {"uz": "Bloklangan", "ru": "Заблокированные", "en": "Blocked"},
    "access.to_allowed": {"uz": "Ruxsatga qo'shish", "ru": "В разрешённые", "en": "Add to allowed"},
    "access.to_blocked": {"uz": "Blokka qo'shish", "ru": "В заблокированные", "en": "Add to blocked"},
    "access.remove": {"uz": "Ro'yxatdan olib tashlash", "ru": "Убрать из списка", "en": "Remove from list"},
    "access.add_manual": {"uz": "Seriya bo'yicha qo'shish…", "ru": "Добавить по серии…",
                          "en": "Add by serial…"},
    "access.select_first": {"uz": "Avval ro'yxatdan qurilma tanlang.",
                            "ru": "Сначала выберите устройство в списке.",
                            "en": "Select a device in the list first."},
    "access.add_prompt": {"uz": "Qurilma seriya raqami (Serial ustunidagi kabi):",
                          "ru": "Серийный номер устройства (как в столбце Serial):",
                          "en": "Device serial number (as in the Serial column):"},
    "access.state_connected": {"uz": "Ulangan", "ru": "Подключено", "en": "Connected"},
    "access.state_blocked": {"uz": "Bloklangan (o'chirilgan)", "ru": "Заблокировано (отключено)",
                             "en": "Blocked (disabled)"},
    "access.whitelist_warn": {"uz": "«Bloklash» rejimida whitelist'da bo'lmagan har bir USB xotira "
                                   "qurilmasi o'chiriladi (Administrator kerak).\n\nMaslahat: avval ulangan "
                                   "qurilmalarni ruxsatga qo'shing.\n\nDavom etilsinmi?",
                              "ru": "В режиме «Блокировать» каждое USB-накопитель не из whitelist будет "
                                   "отключено (нужен администратор).\n\nСовет: сначала добавьте подключённые "
                                   "устройства в разрешённые.\n\nПродолжить?",
                              "en": "In Block mode every USB storage device not on the whitelist will be "
                                   "disabled (Administrator required).\n\nTip: add connected devices to "
                                   "allowed first.\n\nContinue?"},

    # ---- settings ----
    "settings.autostart": {"uz": "Windows bilan avtomatik ishga tushsin",
                           "ru": "Запускать автоматически вместе с Windows",
                           "en": "Start automatically when Windows starts"},
    "settings.language": {"uz": "Til", "ru": "Язык", "en": "Language"},
    "settings.appearance": {"uz": "Ko'rinish", "ru": "Оформление", "en": "Appearance"},
    "settings.dark": {"uz": "Tungi", "ru": "Тёмная", "en": "Dark"},
    "settings.light": {"uz": "Kunduzgi", "ru": "Светлая", "en": "Light"},
    "settings.change_pw": {"uz": "Parolni o'zgartirish", "ru": "Сменить пароль", "en": "Change password"},
    "settings.data_folder": {"uz": "Ma'lumotlar papkasi: {0}", "ru": "Папка данных: {0}",
                             "en": "Data folder: {0}"},
    "settings.notice": {"uz": "Faqat o'zingiz egasi bo'lgan yoki ruxsat berilgan kompyuterda ishlating.",
                        "ru": "Используйте только на своих или авторизованных компьютерах.",
                        "en": "Use only on computers you own or are authorized to monitor."},
    "settings.pw_current": {"uz": "Joriy parol:", "ru": "Текущий пароль:", "en": "Current password:"},
    "settings.pw_new": {"uz": "Yangi parol (kamida 6 belgi):", "ru": "Новый пароль (мин. 6 символов):",
                        "en": "New password (min 6 chars):"},
    "settings.pw_repeat": {"uz": "Yangi parolni takrorlang:", "ru": "Повторите новый пароль:",
                           "en": "Repeat new password:"},
    "settings.pw_changed": {"uz": "Parol o'zgartirildi.", "ru": "Пароль изменён.", "en": "Password changed."},
    "settings.pw_wrong": {"uz": "Noto'g'ri parol.", "ru": "Неверный пароль.", "en": "Wrong password."},
    "settings.pw_short": {"uz": "Yangi parol kamida 6 belgi bo'lsin.",
                          "ru": "Новый пароль должен быть не короче 6 символов.",
                          "en": "New password must be at least 6 characters."},
    "settings.pw_mismatch": {"uz": "Yangi parollar mos kelmadi.", "ru": "Новые пароли не совпадают.",
                             "en": "New passwords do not match."},

    # ---- columns ----
    "col.name": {"uz": "Nom", "ru": "Имя", "en": "Name"},
    "col.description": {"uz": "Tavsif", "ru": "Описание", "en": "Description"},
    "col.type": {"uz": "Turi", "ru": "Тип", "en": "Type"},
    "col.connected": {"uz": "Ulangan", "ru": "Подключён", "en": "Connected"},
    "col.disabled": {"uz": "O'chirilgan", "ru": "Отключён", "en": "Disabled"},
    "col.serial": {"uz": "Seriya", "ru": "Серия", "en": "Serial"},
    "col.vid": {"uz": "VID", "ru": "VID", "en": "VID"},
    "col.pid": {"uz": "PID", "ru": "PID", "en": "PID"},
    "col.class": {"uz": "Klass", "ru": "Класс", "en": "Class"},
    "col.service": {"uz": "Xizmat", "ru": "Служба", "en": "Service"},
    "col.vendor": {"uz": "Ishlab chiqaruvchi", "ru": "Производитель", "en": "Vendor"},
    "col.first_install": {"uz": "Birinchi o'rnatish", "ru": "Первая установка", "en": "First Install"},
    "col.last_connect": {"uz": "Oxirgi ulanish", "ru": "Последнее подключение", "en": "Last Connect"},
    "col.last_disconnect": {"uz": "Oxirgi uzilish", "ru": "Последнее отключение", "en": "Last Disconnect"},
    "col.instance_id": {"uz": "Instance ID", "ru": "Instance ID", "en": "Instance ID"},
    "col.first_connected": {"uz": "Birinchi ulanish", "ru": "Первое подключение", "en": "First Connected"},
    "col.last_connected": {"uz": "Oxirgi ulanish", "ru": "Последнее подключение", "en": "Last Connected"},
    "col.last_removed": {"uz": "Oxirgi uzilish", "ru": "Последнее отключение", "en": "Last Removed"},
    "col.capacity": {"uz": "Hajm", "ru": "Объём", "en": "Capacity"},
    "col.free": {"uz": "Bo'sh (oxirgi)", "ru": "Свободно (посл.)", "en": "Free (last seen)"},
    "col.state": {"uz": "Holat", "ru": "Состояние", "en": "State"},
    "col.list": {"uz": "Ro'yxat", "ru": "Список", "en": "List"},
    "col.time": {"uz": "Vaqt", "ru": "Время", "en": "Time"},
    "col.drive": {"uz": "Disk", "ru": "Диск", "en": "Drive"},
    "col.action": {"uz": "Amal", "ru": "Действие", "en": "Action"},
    "col.path": {"uz": "Yo'l", "ru": "Путь", "en": "Path"},
    "col.to_label": {"uz": "Qayerga / Label", "ru": "Куда / Метка", "en": "To / Label"},
    "col.size_bytes": {"uz": "Hajm (bayt)", "ru": "Размер (байт)", "en": "Size (bytes)"},

    # ---- dialogs / tray / auth ----
    "dlg.exit_prompt": {"uz": "Chiqish uchun parol kerak.\nBekor qilish = fonda ishlashda davom etadi.",
                        "ru": "Для выхода нужен пароль.\nОтмена = продолжит работу в фоне.",
                        "en": "Password required to exit.\nCancel = keep monitoring in background."},
    "dlg.unlock_prompt": {"uz": "USBWatch'ni ochish uchun parol kiriting",
                          "ru": "Введите пароль, чтобы открыть USBWatch",
                          "en": "Enter password to open USBWatch"},
    "dlg.select_device": {"uz": "Avval qurilma tanlang.", "ru": "Сначала выберите устройство.",
                          "en": "Select a device first."},
    "dlg.exported": {"uz": "Eksport qilindi:\n{0}", "ru": "Экспортировано:\n{0}", "en": "Exported to:\n{0}"},
    "dlg.export_failed": {"uz": "Eksport xatosi:\n{0}", "ru": "Ошибка экспорта:\n{0}",
                          "en": "Export failed:\n{0}"},
    "dlg.need_admin": {"uz": "Qurilmani yoqish/o'chirish uchun Administrator sifatida ishga tushiring.",
                       "ru": "Запустите от имени администратора, чтобы включать/отключать устройства.",
                       "en": "Run USBWatch as Administrator to enable/disable devices."},
    "tray.open": {"uz": "Ochish", "ru": "Открыть", "en": "Open"},
    "tray.exit": {"uz": "Chiqish", "ru": "Выход", "en": "Exit"},
    "tray.tooltip": {"uz": "USBWatch — fonda ishlayapti", "ru": "USBWatch — работает в фоне",
                     "en": "USBWatch — running in background"},
    "auth.create_sub": {"uz": "Dasturni himoyalash uchun parol yarating",
                        "ru": "Создайте пароль для защиты приложения",
                        "en": "Create a password to protect the app"},
    "auth.signin_sub": {"uz": "Davom etish uchun kiring", "ru": "Войдите, чтобы продолжить",
                        "en": "Sign in to continue"},
    "auth.pw_ph": {"uz": "Parol", "ru": "Пароль", "en": "Password"},
    "auth.repeat_ph": {"uz": "Parolni takrorlang", "ru": "Повторите пароль", "en": "Repeat password"},
    "auth.create_btn": {"uz": "Parol yaratish", "ru": "Создать пароль", "en": "Create password"},
    "auth.unlock_btn": {"uz": "Ochish", "ru": "Войти", "en": "Unlock"},
    "auth.min6": {"uz": "Kamida 6 belgi", "ru": "Минимум 6 символов", "en": "Minimum 6 characters"},
    "auth.mismatch": {"uz": "Parollar mos kelmadi", "ru": "Пароли не совпадают", "en": "Passwords do not match"},
    "auth.wrong": {"uz": "Noto'g'ri parol ({0}/5)", "ru": "Неверный пароль ({0}/5)", "en": "Wrong password ({0}/5)"},
}


def _initial_lang():
    lang = settings_service.load_cfg().get("lang")
    return lang if lang in LANGS else "uz"


lang = Observable(_initial_lang())


def set_language(code):
    if code in LANGS and code != lang.value:
        settings_service.update_cfg(lang=code)
        lang.value = code


def t(key, *args):
    entry = _T.get(key)
    if not entry:
        return key
    text = entry.get(lang.value) or entry.get("en") or key
    return text.format(*args) if args else text
