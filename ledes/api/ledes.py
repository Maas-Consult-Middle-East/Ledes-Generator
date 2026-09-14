# Server Script Type: API
# API Method: generate_ledes_sales_invoice_txt
import frappe

@frappe.whitelist()
def generate_ledes_sales_invoice_txt(sales_invoice):
    doc = frappe.get_doc("Sales Invoice", sales_invoice)
    sales_invoice_name = frappe.form_dict.get("sales_invoice")

    if not sales_invoice_name:
        frappe.throw("Sales Invoice is required")

    doc = frappe.get_doc("Sales Invoice", sales_invoice_name)



    if doc.doctype != "Sales Invoice":
        frappe.throw("Only Sales Invoice is supported")

    if not doc.get("items"):
        frappe.throw("Sales Invoice has no items")


    def has_field(doctype, fieldname):
        try:
            return frappe.get_meta(doctype).has_field(fieldname)
        except Exception:
            return False


    def get_doc_value(obj, fieldnames, default_value=""):
        for fieldname in fieldnames:
            try:
                if has_field(obj.doctype, fieldname):
                    value = obj.get(fieldname)
                    if value is not None and value != "":
                        return value
            except Exception:
                pass
        return default_value


    def get_link_value(doctype, name, fieldnames, default_value=""):
        if not name:
            return default_value

        for fieldname in fieldnames:
            try:
                if has_field(doctype, fieldname):
                    value = frappe.db.get_value(doctype, name, fieldname)
                    if value is not None and value != "":
                        return value
            except Exception:
                pass

        return default_value


    def clean_text(value):
        if value is None:
            return ""

        value = str(value)
        value = value.replace("|", " ")
        value = value.replace("\n", " ")
        value = value.replace("\r", " ")
        value = value.replace("[]", " ")

        try:
            value = value.encode("ascii", "ignore").decode("ascii")
        except Exception:
            pass

        while "  " in value:
            value = value.replace("  ", " ")

        return value.strip()


    def money(value):
        try:
            return "{0:.2f}".format(frappe.utils.flt(value))
        except Exception:
            return "0.00"


    def qty(value):
        try:
            return "{0:.2f}".format(frappe.utils.flt(value))
        except Exception:
            return "0.00"


    client_id = "589"

    if not client_id:
        client_id = "CLIENT_ID_PLACEHOLDER"

    invoice_date = frappe.utils.formatdate(
        doc.posting_date,
        "yyyyMMdd"
    )
    invoice_number = clean_text(doc.get("name"))
    invoice_total = "%.2f" % frappe.utils.flt(doc.grand_total)

    billing_start_date = frappe.utils.formatdate(
        get_doc_value(
            doc,
            [
                "custom_billing_start_date",
                "custom_ledes_billing_start_date"
            ],
            doc.posting_date
        ),
        "yyyyMMdd"
    )

    billing_end_date = frappe.utils.formatdate(
        get_doc_value(
            doc,
            [
                "custom_billing_end_date",
                "custom_ledes_billing_end_date"
            ],
            doc.posting_date
        ),
        "yyyyMMdd"
    )



    # line_total = item.amount
    # line_unit_cost = item.rate

    invoice_description = frappe.utils.strip_html(
        get_doc_value(
            doc,
            [
                "custom_ledes_invoice_description",
                "remarks"
            ],
            "final"
        )
    )

    law_firm_matter_id = get_doc_value(
        doc,
        [
            "custom_law_firm_matter_id",
            "custom_ledes_law_firm_matter_id"
        ],
        ""
    )

    client_matter_id = get_doc_value(
        doc,
        ["custom_your_financial_ref"],
        "CLIENT_MATTER_ID_PLACEHOLDER"
    )

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": doc.owner},
        "name"
    )

    timekeeper_id = ""

    if employee:
        timekeeper_id = frappe.db.get_value(
            "Employee",
            employee,
            "custom_timekeeper_id"
        ) or ""

    timekeeper_name = frappe.db.get_value(
        "User",
        doc.owner,
        "full_name"
    ) or ""

    timekeeper_classification = "OT"

    law_firm_matter_id = get_doc_value(
        doc,
        ["custom_our_reference"],
        ""
    )

    law_firm_id = "A00000856"

    headers = [
        "INVOICE_DATE",
        "INVOICE_NUMBER",
        "CLIENT_ID",
        "LAW_FIRM_MATTER_ID",
        "INVOICE_TOTAL",
        "BILLING_START_DATE",
        "BILLING_END_DATE",
        "INVOICE_DESCRIPTION",
        "LINE_ITEM_NUMBER",
        "EXP/FEE/INV_ADJ_TYPE",
        "LINE_ITEM_NUMBER_OF_UNITS",
        "LINE_ITEM_ADJUSTMENT_AMOUNT",
        "LINE_ITEM_TOTAL",
        "LINE_ITEM_DATE",
        "LINE_ITEM_TASK_CODE",
        "LINE_ITEM_EXPENSE_CODE",
        "LINE_ITEM_ACTIVITY_CODE",
        "TIMEKEEPER_ID",
        "LINE_ITEM_DESCRIPTION",
        "LAW_FIRM_ID",
        "LINE_ITEM_UNIT_COST",
        "TIMEKEEPER_NAME",
        "TIMEKEEPER_CLASSIFICATION",
        "CLIENT_MATTER_ID",
    ]

    lines = []
    lines.append("LEDES1998B[]")
    lines.append("|".join(headers) + "[]")

    line_no = 1

    for item in doc.get("items"):
        line_item_date = frappe.utils.formatdate(
            get_doc_value(
                item,
                [
                    "custom_ledes_line_date",
                    "custom_line_item_date"
                ],
                doc.posting_date
            ),
            "yyyyMMdd"
        )
        line_expense_code = get_doc_value(
            item,
            [
                "custom_ledes_expense_code",
                "custom_expense_code"
            ],
            ""
        )

        line_task_code = frappe.db.get_value(
            "Item",
            item.item_code,
            "custom_task_code"
        ) or ""

        line_activity_code = frappe.db.get_value(
            "Item",
            item.item_code,
            "custom_activity_code"
        ) or ""

        line_type = get_doc_value(
            item,
            [
                "custom_ledes_type",
                "custom_exp_fee_inv_adj_type"
            ],
            ""
        )
        

        if not line_type:
            if line_expense_code:
                line_type = "E"
            else:
                line_type = "F"

        if not line_task_code and not line_expense_code:
            line_task_code = "TASK_CODE_PLACEHOLDER"

        if not line_activity_code and not line_expense_code:
            line_activity_code = "A101_PLACEHOLDER"

        line_description = frappe.utils.strip_html(
            get_doc_value(
                item,
                [
                    "description",
                    "item_name",
                    "item_code"
                ],
                "LINE_DESCRIPTION_PLACEHOLDER"
            )
        )

        line_total = "%.2f" % frappe.utils.flt(item.amount)

        line_unit_cost = "%.2f" % frappe.utils.flt(item.rate)
        
        line_qty = "%.2f" % frappe.utils.flt(item.qty)

        line_adjustment_amount = "%.2f" % frappe.utils.flt(
            get_doc_value(
                item,
                [
                    "custom_ledes_adjustment_amount"
                ],
                0
            )
        )

        row = [
            invoice_date,
            invoice_number,
            clean_text(client_id),
            clean_text(law_firm_matter_id),
            invoice_total,
            billing_start_date,
            billing_end_date,
            clean_text(invoice_description),
            str(line_no),
            clean_text(line_type),
            line_qty,
            line_adjustment_amount,
            line_total,
            line_item_date,
        
            clean_text(line_task_code),
            clean_text(line_expense_code),
            clean_text(line_activity_code),
            clean_text(timekeeper_id),
            clean_text(line_description),
            clean_text(law_firm_id),
            line_unit_cost,
            clean_text(timekeeper_name),
            clean_text(timekeeper_classification),
            clean_text(client_matter_id)
        ]

        lines.append("|".join(row) + "[]")
        line_no = line_no + 1

    # Add Foreign VAT Charges as the last line

    vat_amount = "%.2f" % frappe.utils.flt(doc.total_taxes_and_charges or 0.00)

    vat_row = [
        invoice_date,
        invoice_number,
        clean_text(client_id),
        clean_text(law_firm_matter_id),
        invoice_total,
        billing_start_date,
        billing_end_date,
        clean_text(invoice_description),
        str(line_no),
        "E",                           
        "1.00",                        
        "0.00",                        
        vat_amount,                    
        invoice_date,                  
        "",                            
        "E125",                        
        "",                            
        clean_text(timekeeper_id),
        "Foreign VAT Charges",         
        clean_text(law_firm_id),
        vat_amount,                    
        clean_text(timekeeper_name),
        clean_text(timekeeper_classification),
        clean_text(client_matter_id)
    ]

    lines.append("|".join(vat_row) + "[]")


    content = "\n".join(lines)

    filename = clean_text(doc.get("name")) + "_LEDES.txt"
    filename = filename.replace("/", "-").replace("\\", "-")

    frappe.response["message"] = {
        "filename": filename,
        "content": content
    }
    return {
        "filename": filename,
        "content": content
    }