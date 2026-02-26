import json
import os
import re

# 1. Patch HTML/DOCX/XLSX table conversion (markdownify)
from markitdown.converters._html_converter import _CustomMarkdownify

original_convert_table = getattr(_CustomMarkdownify, "convert_table", None)

def patched_convert_table(self, el, text, convert_as_inline=False, **kwargs):
    if os.getenv("MARKITDOWN_EXTRACT_TABLES_AS_JSON", "false").lower() in ("true", "1", "yes", "on"):
        rows = el.find_all('tr')
        grid = []
        for r in rows:
            clean_row = []
            for c in r.find_all(['th', 'td']):
                clean_cell = {"text": c.get_text(strip=True)}
                col_span = int(c.get("colspan", 1))
                row_span = int(c.get("rowspan", 1))
                if col_span > 1: clean_cell["col_span"] = col_span
                if row_span > 1: clean_cell["row_span"] = row_span
                if c.name == 'th': clean_cell["is_header"] = True
                clean_row.append(clean_cell)
            if clean_row:
                grid.append(clean_row)
        if grid:
            json_str = json.dumps(grid, indent=2, ensure_ascii=False)
            return f"\n```json\n{json_str}\n```\n"
        return ""
    
    # Fallback to original if available, else do nothing (markdownify handles it)
    if original_convert_table:
        return original_convert_table(self, el, text, convert_as_inline, **kwargs)
    
    # If original isn't there, markdownify handles tables natively if we don't return anything
    return text

_CustomMarkdownify.convert_table = patched_convert_table


# 2. Patch PDF table conversion
import markitdown.converters._pdf_converter as pdf_conv

original_extract_form_content_from_words = pdf_conv._extract_form_content_from_words

def patched_extract_form_content_from_words(page):
    if os.getenv("MARKITDOWN_EXTRACT_TABLES_AS_JSON", "false").lower() not in ("true", "1", "yes", "on"):
        return original_extract_form_content_from_words(page)
        
    words = page.extract_words(keep_blank_chars=True, x_tolerance=3, y_tolerance=3)
    if not words:
        return None

    # Group words by their Y position (rows)
    y_tolerance = 5
    rows_by_y = {}
    for word in words:
        y_key = round(word["top"] / y_tolerance) * y_tolerance
        if y_key not in rows_by_y:
            rows_by_y[y_key] = []
        rows_by_y[y_key].append(word)

    # Sort rows by Y position
    sorted_y_keys = sorted(rows_by_y.keys())
    page_width = page.width if hasattr(page, "width") else 612

    # First pass: analyze each row
    row_info = []
    for y_key in sorted_y_keys:
        row_words = sorted(rows_by_y[y_key], key=lambda w: w["x0"])
        if not row_words:
            continue

        first_x0 = row_words[0]["x0"]
        last_x1 = row_words[-1]["x1"]
        line_width = last_x1 - first_x0
        combined_text = " ".join(w["text"] for w in row_words)

        x_positions = [w["x0"] for w in row_words]
        x_groups = []
        for x in sorted(x_positions):
            if not x_groups or x - x_groups[-1] > 50:
                x_groups.append(x)

        is_paragraph = line_width > page_width * 0.55 and len(combined_text) > 60

        has_partial_numbering = False
        if row_words:
            first_word = row_words[0]["text"].strip()
            if pdf_conv.PARTIAL_NUMBERING_PATTERN.match(first_word):
                has_partial_numbering = True

        row_info.append(
            {
                "y_key": y_key,
                "words": row_words,
                "text": combined_text,
                "x_groups": x_groups,
                "is_paragraph": is_paragraph,
                "num_columns": len(x_groups),
                "has_partial_numbering": has_partial_numbering,
            }
        )

    all_table_x_positions = []
    for info in row_info:
        if info["num_columns"] >= 3 and not info["is_paragraph"]:
            all_table_x_positions.extend(info["x_groups"])

    if not all_table_x_positions:
        return None

    all_table_x_positions.sort()

    gaps = []
    for i in range(len(all_table_x_positions) - 1):
        gap = all_table_x_positions[i + 1] - all_table_x_positions[i]
        if gap > 5:
            gaps.append(gap)

    if gaps and len(gaps) >= 3:
        sorted_gaps = sorted(gaps)
        percentile_70_idx = int(len(sorted_gaps) * 0.70)
        adaptive_tolerance = sorted_gaps[percentile_70_idx]
        adaptive_tolerance = max(25, min(50, adaptive_tolerance))
    else:
        adaptive_tolerance = 35

    global_columns = []
    for x in all_table_x_positions:
        if not global_columns or x - global_columns[-1] > adaptive_tolerance:
            global_columns.append(x)

    if len(global_columns) > 1:
        content_width = global_columns[-1] - global_columns[0]
        avg_col_width = content_width / len(global_columns)

        if avg_col_width < 30:
            return None

        columns_per_inch = len(global_columns) / (content_width / 72)
        if columns_per_inch > 10:
            return None

        adaptive_max_columns = int(20 * (page_width / 612))
        adaptive_max_columns = max(15, adaptive_max_columns)

        if len(global_columns) > adaptive_max_columns:
            return None
    else:
        return None

    for info in row_info:
        if info["is_paragraph"]:
            info["is_table_row"] = False
            continue

        if info["has_partial_numbering"]:
            info["is_table_row"] = False
            continue

        aligned_columns = set()
        for word in info["words"]:
            word_x = word["x0"]
            for col_idx, col_x in enumerate(global_columns):
                if abs(word_x - col_x) < 40:
                    aligned_columns.add(col_idx)
                    break

        info["is_table_row"] = len(aligned_columns) >= 2

    table_regions = []
    i = 0
    while i < len(row_info):
        if row_info[i]["is_table_row"]:
            start_idx = i
            while i < len(row_info) and row_info[i]["is_table_row"]:
                i += 1
            end_idx = i
            table_regions.append((start_idx, end_idx))
        else:
            i += 1

    total_table_rows = sum(end - start for start, end in table_regions)
    if len(row_info) > 0 and total_table_rows / len(row_info) < 0.2:
        return None

    result_lines = []
    num_cols = len(global_columns)

    def extract_cells(info):
        cells = ["" for _ in range(num_cols)]
        for word in info["words"]:
            word_x = word["x0"]
            assigned_col = num_cols - 1
            for col_idx in range(num_cols - 1):
                col_end = global_columns[col_idx + 1]
                if word_x < col_end - 20:
                    assigned_col = col_idx
                    break
            if cells[assigned_col]:
                cells[assigned_col] += " " + word["text"]
            else:
                cells[assigned_col] = word["text"]
        return cells

    idx = 0
    while idx < len(row_info):
        info = row_info[idx]

        table_region = None
        for start, end in table_regions:
            if idx == start:
                table_region = (start, end)
                break

        if table_region:
            start, end = table_region
            table_data = []
            for table_idx in range(start, end):
                cells = extract_cells(row_info[table_idx])
                
                # Convert the list of strings to list of dicts for JSON
                row_dicts = [{"text": cell.strip()} for cell in cells]
                
                # The first row of a PDF table region is usually the header
                if table_idx == start:
                    for d in row_dicts:
                        d["is_header"] = True
                        
                table_data.append(row_dicts)

            if table_data:
                json_str = json.dumps(table_data, indent=2, ensure_ascii=False)
                result_lines.append(f"```json\n{json_str}\n```")

            idx = end
        else:
            in_table = False
            for start, end in table_regions:
                if start < idx < end:
                    in_table = True
                    break

            if not in_table:
                result_lines.append(info["text"])
            idx += 1

    return "\n".join(result_lines)

pdf_conv._extract_form_content_from_words = patched_extract_form_content_from_words

