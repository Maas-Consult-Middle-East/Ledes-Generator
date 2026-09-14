frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Download LEDES.txt"), function () {
            download_ledes_txt(frm);
        }, __("Export"));
    }
});

function download_ledes_txt(frm) {
    frappe.call({
        method: "ledes.api.ledes.generate_ledes_sales_invoice_txt",
        args: {
            sales_invoice: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Generating LEDES.txt..."),
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint(__("No LEDES data returned."));
                return;
            }

            const filename = r.message.filename || (frm.doc.name + "_LEDES.txt");
            const content = r.message.content || "";

            if (!content) {
                frappe.msgprint(__("LEDES content is empty."));
                return;
            }

            const blob = new Blob([content], {
                type: "text/plain;charset=US-ASCII"
            });

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = filename;

            document.body.appendChild(link);
            link.click();

            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }
    });
}