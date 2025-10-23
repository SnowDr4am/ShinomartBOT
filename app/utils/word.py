import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn


async def generate_storage_word_document(cell_storage, user_data, worker_data):
    """Генерация аккуратного официального документа (1 лист, RU-месяцы, с данными сотрудника)"""
    try:
        # --- Директория ---
        cell_folder = os.path.join("static", "storage_cells", str(cell_storage.cell_id))
        os.makedirs(cell_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"storage_{timestamp}.docx"
        full_path = os.path.join(cell_folder, filename)

        # --- Документ и базовые настройки ---
        doc = Document()
        section = doc.sections[0]
        # Поля страницы ~ 1.5 см
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)

        # Базовый шрифт
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)

        # Утилиты для параграфов
        def add_title(text: str):
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.bold = True
            run.font.size = Pt(14)
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            return p

        def add_label_value(label: str, value: str):
            p = doc.add_paragraph()
            r1 = p.add_run(f"{label}: ")
            r1.bold = True
            r2 = p.add_run(value)
            return p

        def add_separator(space_before=6, space_after=6):
            # «тонкая линия» через нижнюю границу пустого абзаца
            p = doc.add_paragraph()
            p_format = p.paragraph_format
            p_format.space_before = Pt(space_before)
            p_format.space_after = Pt(space_after)
            p_format.line_spacing = 1.0
            p_run = p.add_run()
            p_run.add_break()
            p._element.get_or_add_pPr()
            pPr = p._element.pPr
            pbdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '8')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), 'auto')
            pbdr.append(bottom)
            pPr.append(pbdr)

        # --- Дата оформления сверху справа ---
        created_dt = cell_storage.created_at if getattr(cell_storage, 'created_at', None) else datetime.now()
        date_str = f"{created_dt.day} {RU_MONTHS_GEN[created_dt.month]} {created_dt.year} г."
        p_date = doc.add_paragraph()
        p_date.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        r_date = p_date.add_run(f"Дата оформления: {date_str}")
        r_date.italic = True

        # --- Заголовок ---
        add_title("ДОКУМЕНТ О ПРИЁМЕ ШИН НА ХРАНЕНИЕ")

        # --- Шапка организации ---
        t_head = doc.add_table(rows=2, cols=1)
        t_head.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        t_head.autofit = True
        t_head.style = 'Table Grid'

        org_cell = t_head.cell(0, 0)
        _set_cell_margins(org_cell, top=60, bottom=60)
        p_org = org_cell.paragraphs[0]
        p_org.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run_org = p_org.add_run("ШИНОМАРТ")
        run_org.bold = True
        run_org.font.size = Pt(12)

        addr_cell = t_head.cell(1, 0)
        _set_cell_margins(addr_cell, top=40, bottom=80)
        p_addr = addr_cell.paragraphs[0]
        p_addr.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p_addr.add_run("г. Тюмень, ул. Правды, 4А")

        add_separator(space_before=6, space_after=6)

        # --- Информация о клиенте ---
        p_h1 = doc.add_paragraph()
        h1 = p_h1.add_run("ИНФОРМАЦИЯ О КЛИЕНТЕ")
        h1.bold = True
        h1.font.size = Pt(12)

        if user_data:
            add_label_value("ФИО", f"{getattr(user_data, 'name', '')}".strip() or "—")
            add_label_value("Телефон", f"{getattr(user_data, 'mobile_phone', '')}".strip() or "—")
        else:
            add_label_value("Телефон", f"{cell_storage.user_id}")

        add_separator(space_before=6, space_after=6)

        # --- Информация о сотруднике ---
        p_h_worker = doc.add_paragraph()
        hw = p_h_worker.add_run("ИНФОРМАЦИЯ О СОТРУДНИКЕ")
        hw.bold = True
        hw.font.size = Pt(12)

        worker_name = (getattr(worker_data, 'name', '') or getattr(worker_data, 'fio', '') or "").strip()
        worker_phone = (getattr(worker_data, 'mobile_phone', '') or getattr(worker_data, 'phone', '') or "").strip()
        worker_pos = (getattr(worker_data, 'position', '') or getattr(worker_data, 'role', '') or "").strip()

        add_label_value("ФИО", worker_name or "—")
        if worker_pos:
            add_label_value("Должность", worker_pos)
        add_label_value("Телефон", worker_phone or "—")

        add_separator(space_before=6, space_after=6)

        # --- Информация об услуге ---
        p_h2 = doc.add_paragraph()
        h2 = p_h2.add_run("ИНФОРМАЦИЯ ОБ УСЛУГЕ")
        h2.bold = True
        h2.font.size = Pt(12)

        st = str(cell_storage.storage_type).lower()
        human_type = "Шины с дисками" if ("rim" in st or "диск" in st) else "Шины"

        add_label_value("Тип хранения", human_type)
        add_label_value("Номер ячейки", f"{cell_storage.cell_id}")
        add_label_value("Описание", f"{cell_storage.description or 'Не указано'}")

        add_separator(space_before=6, space_after=6)

        # --- Стоимость ---
        p_h3 = doc.add_paragraph()
        h3 = p_h3.add_run("СТОИМОСТЬ УСЛУГИ")
        h3.bold = True
        h3.font.size = Pt(12)

        p_price = doc.add_paragraph()
        p_price.paragraph_format.space_after = Pt(0)
        r_price = p_price.add_run(f"{cell_storage.price} ₽")
        r_price.bold = True
        r_price.font.size = Pt(14)

        add_separator(space_before=4, space_after=6)

        # --- Срок хранения ---
        p_h4 = doc.add_paragraph()
        h4 = p_h4.add_run("СРОК ХРАНЕНИЯ")
        h4.bold = True
        h4.font.size = Pt(12)

        smonth = getattr(cell_storage, 'scheduled_month', None)
        if smonth:
            year = smonth.year
            month_name = RU_MONTHS_GEN[smonth.month]
            term_text = f"до {month_name} {year} года"
        else:
            term_text = "не указан"

        add_label_value("Срок", term_text)

        add_separator(space_before=6, space_after=4)

        # --- Подписи (с указанием ФИО) ---
        t_sign = doc.add_table(rows=2, cols=2)
        t_sign.autofit = True
        t_sign.style = 'Table Grid'

        # Заголовки с ФИО
        t_sign.cell(0, 0).text = f"Сотрудник{f' ({worker_name})' if worker_name else ''}"
        t_sign.cell(0, 1).text = "Клиент"

        for c in (t_sign.cell(0, 0), t_sign.cell(0, 1)):
            _set_cell_margins(c, top=80, bottom=80)
            p = c.paragraphs[0]
            p.runs[0].bold = True
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Линии для подписи
        t_sign.cell(1, 0).text = "_________________________"
        t_sign.cell(1, 1).text = "_________________________"
        for c in (t_sign.cell(1, 0), t_sign.cell(1, 1)):
            _set_cell_margins(c, top=140, bottom=80)
            c.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Сжать вертикальные интервалы
        for p in doc.paragraphs:
            fmt = p.paragraph_format
            if fmt.space_before is None:
                fmt.space_before = Pt(0)
            if fmt.space_after is None:
                fmt.space_after = Pt(2)
            fmt.line_spacing = 1.0

        # --- Сохранение ---
        doc.save(full_path)
        return full_path

    except ImportError:
        # Фолбэк в .txt (с данными сотрудника)
        cell_folder = os.path.join("static", "storage_cells", str(cell_storage.cell_id))
        os.makedirs(cell_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"storage_{timestamp}.txt"
        full_path = os.path.join(cell_folder, filename)

        created_dt = cell_storage.created_at if getattr(cell_storage, 'created_at', None) else datetime.now()
        date_str = f"{created_dt.day} {RU_MONTHS_GEN[created_dt.month]} {created_dt.year} г."

        smonth = getattr(cell_storage, 'scheduled_month', None)
        term_text = f"до {RU_MONTHS_GEN[smonth.month]} {smonth.year} года" if smonth else "не указан"

        st = str(cell_storage.storage_type).lower()
        human_type = "Шины с дисками" if ("rim" in st or "диск" in st) else "Шины"

        worker_name = (getattr(worker_data, 'name', '') or getattr(worker_data, 'fio', '') or "").strip()
        worker_phone = (getattr(worker_data, 'mobile_phone', '') or getattr(worker_data, 'phone', '') or "").strip()
        worker_pos = (getattr(worker_data, 'position', '') or getattr(worker_data, 'role', '') or "").strip()

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"Дата оформления: {date_str}\n\n")
            f.write("ДОКУМЕНТ О ПРИЁМЕ ШИН НА ХРАНЕНИЕ\n")
            f.write("ШИНОМАРТ, г. Тюмень, ул. Правды, 4А\n")
            f.write("-" * 60 + "\n")
            # Клиент
            if user_data:
                f.write(f"Клиент: {getattr(user_data, 'name', '')}\n")
                f.write(f"Телефон клиента: {getattr(user_data, 'mobile_phone', '')}\n")
            else:
                f.write(f"Телефон клиента: {cell_storage.user_id}\n")
            f.write("-" * 60 + "\n")
            # Сотрудник
            f.write("СОТРУДНИК:\n")
            f.write(f"ФИО: {worker_name or '—'}\n")
            if worker_pos:
                f.write(f"Должность: {worker_pos}\n")
            f.write(f"Телефон: {worker_phone or '—'}\n")
            f.write("-" * 60 + "\n")
            # Услуга
            f.write(f"Тип хранения: {human_type}\n")
            f.write(f"Номер ячейки: {cell_storage.cell_id}\n")
            f.write(f"Описание: {cell_storage.description or 'Не указано'}\n")
            f.write("-" * 60 + "\n")
            f.write(f"Стоимость: {cell_storage.price} ₽\n")
            f.write(f"Срок: {term_text}\n")
            f.write("\nСотрудник: _________________________\n")
            f.write("Клиент:   _________________________\n")
        return full_path

    except Exception as e:
        print(f"Ошибка при генерации документа: {e}")
        return None


# ------------------------------
# УТИЛИТЫ
# ------------------------------

# Русские месяцы (родительный падеж)
RU_MONTHS_GEN = {
    1: "января",  2: "февраля", 3: "марта",
    4: "апреля",  5: "мая",     6: "июня",
    7: "июля",    8: "августа", 9: "сентября",
    10: "октября", 11: "ноября", 12: "декабря",
}


def _set_cell_margins(cell, top=80, start=140, bottom=80, end=140):
    """
    Устанавливает внутренние отступы (поля) ячейки таблицы в документе Word.

    :param cell: объект ячейки (cell)
    :param top: верхний отступ в twips (1 pt = 20 twips)
    :param start: левый отступ
    :param bottom: нижний отступ
    :param end: правый отступ
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    tcMar = OxmlElement('w:tcMar')
    for tag, val in (('top', top), ('start', start), ('bottom', bottom), ('end', end)):
        node = OxmlElement(f'w:{tag}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)

    tcPr.append(tcMar)