/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CreateDashboard = publicWidget.Widget.extend({
    selector: "#sale_dashboard, #operation_dashboard",
     events: {
        'click .sortable': '_SortColumn',
        "click .filter-container": "_ToggleFilterDropdown",
        "click .filter-container2": "_ToggleFilterDropdown2",
        "click .filter-container3": "_ToggleFilterDropdown3",
        "click .filter-dropdown, .filter-dropdown2, .filter-dropdown3": "_PreventClose",
        "keypress #filter-year, #filter-month, #crm_tag_id, #status, #service_type, #assign_team_id": "_SubmitFilterOnEnter",
        "click": "_CloseFilterDropdownOutside",
        "click .clear-filter-btn": "_ClearFilter",
    },
    start: function () {
        this._super();
        this._PopulateYears();
        this._SetFilterText();
        this._ShowClearButton();
        this._initializeCountdowns()
        this.$(".filter-dropdown select").on("keydown", (event) => {
            if (event.key === "Enter") {
                this.$(".filter-dropdown form").submit();
            }
        });
        console.log("Sales Dashboard Widget Loaded");
    },
    _SortColumn: function (event) {
        let $target = $(event.currentTarget);
        let columnIndex = $target.index();
        let $table = $target.closest("table");
        let $tbody = $table.find("tbody");
        let rows = $tbody.find("tr").toArray();
        let dataType = $target.data("type") || "text";

        let ascending = !$target.hasClass("sorted-asc");
        $table.find(".sortable").removeClass("sorted-asc sorted-desc");

        rows.sort((rowA, rowB) => {
            let cellA = $(rowA).find("td").eq(columnIndex).text().trim();
            let cellB = $(rowB).find("td").eq(columnIndex).text().trim();

            if (dataType === "number") {
                cellA = parseFloat(cellA.replace(/,/g, "")) || 0;
                cellB = parseFloat(cellB.replace(/,/g, "")) || 0;
            } else if (dataType === "date") {
                cellA = new Date(cellA).getTime() || 0;
                cellB = new Date(cellB).getTime() || 0;
            } else {
                cellA = cellA.toLowerCase();
                cellB = cellB.toLowerCase();
            }

            return ascending ? (cellA > cellB ? 1 : -1) : (cellA < cellB ? 1 : -1);
        });

        $tbody.append(rows);
        $target.addClass(ascending ? "sorted-asc" : "sorted-desc");
    },

    _ToggleFilterDropdown: function (event) {
        event.stopPropagation();
        let $dropdown = this.$(".filter-dropdown");
        $dropdown.toggle();
    },
    _ToggleFilterDropdown2: function (event) {
        event.stopPropagation();
        let $dropdown = this.$(".filter-dropdown2");
        $dropdown.toggle();
    },

    _ToggleFilterDropdown3: function (event) {
        event.stopPropagation();
        let $dropdown = this.$(".filter-dropdown3");
        $dropdown.toggle();
    },

    _PreventClose: function (event) {
        event.stopPropagation();
    },

    _CloseFilterDropdownOutside: function () {
        let $dropdown = this.$(".filter-dropdown");
        if ($dropdown.is(":visible")) {
            $dropdown.hide();
        }
    },

    _PopulateYears: function () {
        let currentYear = new Date().getFullYear();
        let $yearSelect = this.$("#filter-year");
        for (let year = currentYear; year >= currentYear - 1; year--) {
            $yearSelect.append(`<option value="${year}">${year}</option>`);
        }
    },

    _SubmitFilterOnEnter: function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            let year = this.$("#filter-year").val();
            let month = this.$("#filter-month").val();
            let status = this.$("#status").val();
            let assign_team = this.$("#assign_team_id").val();
            let service_type = this.$("#service_type").val();  // FIXED
            let crm_tag_id = this.$("#crm_tag_id").val();


            let params = new URLSearchParams(window.location.search);
            if (year) params.set("year", year); else params.delete("year");
            if (month) params.set("month", month); else params.delete("month");
            if (status) params.set("status", status); else params.delete("status");
            if (assign_team) params.set("assign_team_id", assign_team); else params.delete("assign_team_id");
            if (service_type) params.set("service_type", service_type); else params.delete("service_type");
            if (crm_tag_id) params.set("crm_tag_id",crm_tag_id);else params.delete("crm_tag_id");

            window.location.href = window.location.pathname + "?" + params.toString();
        }
    },

    _SetFilterText: function () {
        let urlParams = new URLSearchParams(window.location.search);
        let year = urlParams.get("year") || "";
        let month = urlParams.get("month") || "";
        let status = urlParams.get("status") || "";
        let assign_team = urlParams.get("assign_team_id") || "";
        let service_type = urlParams.get("service_type") || "";
        let crm_tag_id = urlParams.get("crm_tag_id") || "";

        let monthNames = {
            "01": "January", "02": "February", "03": "March", "04": "April",
            "05": "May", "06": "June", "07": "July", "08": "August",
            "09": "September", "10": "October", "11": "November", "12": "December"
        };

        let displayText = "Select Month/Year";

        if (year && month) {
            displayText = `${monthNames[month]} ${year}`;
        } else if (year) {
            displayText = `${year}`;
        } else if (month) {
            displayText = monthNames[month];
        }

        this.$(".filter-container h6").text(displayText);
        this.$("#filter-year").val(year);
        this.$("#filter-month").val(month);
        this.$("#status").val(status);
        this.$("#service_type").val(service_type);  // FIXED
        this.$("#crm_tag_id").val(crm_tag_id); 
        this.$("#assign_team_id").val(assign_team);
        this.$(".status-filter h6").text(status ? `Status: ${status}` : "Select Status");
        this.$(".assign-filter h6").text(assign_team ? `Team: ${assign_team}` : "Select Team");
        this.$(".service_type h6").text(service_type ? `Service Type: ${service_type}` : "Service Type");
        this.$(".crm_tag_id h6").text(crm_tag_id ? `CRM Tag: ${crm_tag_id}` : "CRM Tag");
    },

    _ShowClearButton: function () {
        let urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get("year") || urlParams.get('service_type') || urlParams.get("month") || urlParams.get("status") || urlParams.get("assign_team_id")|| urlParams.get("crm_tag_id")) {
            if (!$(".clear-filter-btn").length) {
                $(".filter-container3").after(`
                    <button class="btn btn-link btn-sm clear-filter-btn" style="margin-left: 10px;">
                        Clear Filter
                    </button>
                `);
            }
        } else {
            $(".clear-filter-btn").remove();
        }
    },

    _ClearFilter: function () {
        window.location.href = window.location.pathname;
    },

    _initializeCountdowns: function () {
        this.$(".deadline-cell").each((index, element) => {
            this._updateCountdown($(element))
        });
        if (this._countdownInterval) {
            clearInterval(this._countdownInterval);
        }
        this._countdownInterval = setInterval(() => {
            this.$(".deadline-cell").each((index, element) => {
                this._updateCountdown($(element))
            });
        }, 1000);
    },

    _updateCountdown: ($cell) => {
        const deliveryDateRaw = $cell.data("delivery-date");
        const $display = $cell.find(".countdown-display");

        if (!deliveryDateRaw) {
            $display.text("-");
            return;
        }

        let deliveryDate;
        if (typeof deliveryDateRaw === "string") {
            deliveryDate = new Date(deliveryDateRaw.replace(" ", "T"));
        } else {
            deliveryDate = new Date(deliveryDateRaw);
        }

        if (isNaN(deliveryDate.getTime())) {
            $display.html('<span class="text-muted">Invalid date</span>');
            return;
        }

        const currentDate = new Date();
        const timeDifference = deliveryDate.getTime() - currentDate.getTime();

        const days = Math.floor(timeDifference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeDifference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeDifference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDifference % (1000 * 60)) / 1000);

        let countdownHtml;
        if (timeDifference < 0) {
            const overdueDays = Math.abs(days);
            countdownHtml = overdueDays === 0
                ? '<span class="text-danger font-weight-bold">Late delivery</span>'
                : `<span class="text-danger font-weight-bold">Late by ${overdueDays}D</span>`;
        } else {
            countdownHtml = `<span style="width:180px !important;" class="${days < 2 ? "text-danger" : days < 5 ? "text-warning" : "text-success"}">${days}D ${hours}H ${minutes}M ${seconds}S</span>`;
        }

        $display.html(countdownHtml);
    },

    destroy: function () {
        if (this._countdownInterval) {
            clearInterval(this._countdownInterval);
        }
        this._super.apply(this, arguments);
    },
});
