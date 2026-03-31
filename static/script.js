let productList = [];
let rowCount = 0;

// Fetch available products from server on page load
window.addEventListener("DOMContentLoaded", () => {
  loadProducts();
});

function loadProducts() {
  fetch("/products")
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        showUploadMessage("⚠️ " + data.error, "warning");
        productList = [];
        return;
      }
      productList = data.products;
      hideUploadMessage();
      updateCurrentProducts();
      if (rowCount === 0) addItemRow(); // Start with one row if not already added
    })
    .catch(() => showUploadMessage("Failed to fetch products", "error"));
}

function uploadCSV() {
  const fileInput = document.getElementById("csv-file-input");
  const file = fileInput.files[0];

  if (!file) {
    showUploadMessage("⚠️ Please select a CSV file", "warning");
    return;
  }

  if (!file.name.endsWith(".csv")) {
    showUploadMessage("⚠️ Only CSV files are allowed", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  showUploadMessage("📤 Uploading and retraining model...", "loading");

  fetch("/upload_csv", {
    method: "POST",
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        showUploadMessage("❌ " + data.error, "error");
        return;
      }
      showUploadMessage(
        "✅ " +
          data.message +
          " | " +
          data.products.length +
          " products loaded",
        "success",
      );
      productList = data.products;
      updateCurrentProducts();
      fileInput.value = "";

      // Refresh item rows with new products
      const rows = document.querySelectorAll(".item-row");
      rows.forEach((row) => {
        const idSuffix = row.id.replace("row-", "");
        const select = document.getElementById("product-" + idSuffix);
        const currentValue = select.value;

        // Rebuild options
        select.innerHTML = "";
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select product...";
        placeholder.disabled = true;
        placeholder.selected = !currentValue;
        select.appendChild(placeholder);

        productList.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p;
          opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
          if (p === currentValue) opt.selected = true;
          select.appendChild(opt);
        });
      });
    })
    .catch(() => showUploadMessage("❌ Upload failed", "error"));
}

function updateCurrentProducts() {
  const container = document.getElementById("current-products");
  if (productList.length === 0) {
    container.innerHTML = "<p style='color: #999;'>No products loaded yet</p>";
    return;
  }

  const productHtml = productList
    .map((p) => `<span class="product-badge">${capitalize(p)}</span>`)
    .join("");
  container.innerHTML = `<div class="products-list"><strong>Available Products:</strong> ${productHtml}</div>`;
}

function showUploadMessage(msg, type = "info") {
  const el = document.getElementById("upload-message");
  el.textContent = msg;
  el.className = "upload-message " + type;
  el.style.display = "block";
}

function hideUploadMessage() {
  const el = document.getElementById("upload-message");
  el.style.display = "none";
}

function addItemRow() {
  rowCount++;
  const id = rowCount;
  const container = document.getElementById("items-list");

  const row = document.createElement("div");
  row.className = "item-row";
  row.id = "row-" + id;

  // Product dropdown label
  const selectLabel = document.createElement("label");
  selectLabel.htmlFor = "product-" + id;
  selectLabel.className = "item-label";
  selectLabel.textContent = "Product:";
  selectLabel.style.display = "none";
  row.appendChild(selectLabel);

  // Product dropdown
  const select = document.createElement("select");
  select.id = "product-" + id;
  select.setAttribute("aria-label", "Product selection");
  select.setAttribute("title", "Select a product from the list");
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select product...";
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);
  productList.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
    select.appendChild(opt);
  });

  // Quantity input label
  const qtyLabel = document.createElement("label");
  qtyLabel.htmlFor = "qty-" + id;
  qtyLabel.className = "item-label";
  qtyLabel.textContent = "Quantity:";
  qtyLabel.style.display = "none";
  row.appendChild(qtyLabel);

  // Quantity input
  const qty = document.createElement("input");
  qty.type = "number";
  qty.id = "qty-" + id;
  qty.placeholder = "Qty";
  qty.title = "Enter quantity (minimum 1)";
  qty.setAttribute("aria-label", "Quantity for row " + id);
  qty.min = "1";
  qty.value = "1";

  // Discount input label
  const discLabel = document.createElement("label");
  discLabel.htmlFor = "discount-" + id;
  discLabel.className = "item-label";
  discLabel.textContent = "Discount (%)";
  discLabel.style.display = "none";
  row.appendChild(discLabel);

  // Discount input (optional - user can leave empty for default rules)
  const discount = document.createElement("input");
  discount.type = "number";
  discount.id = "discount-" + id;
  discount.placeholder = "Disc %";
  discount.title =
    "Enter discount percentage (0-100). Leave empty to use default rules based on product category.";
  discount.setAttribute("aria-label", "Discount percentage for row " + id);
  discount.min = "0";
  discount.max = "100";
  discount.step = "0.1";
  discount.value = "";

  // Remove button
  const removeBtn = document.createElement("button");
  removeBtn.className = "btn-remove";
  removeBtn.innerHTML = "&times;";
  removeBtn.type = "button";
  removeBtn.title = "Remove this item from invoice";
  removeBtn.setAttribute("aria-label", "Remove item " + id);
  removeBtn.onclick = () => removeRow(id);

  row.appendChild(select);
  row.appendChild(qty);
  row.appendChild(discount);
  row.appendChild(removeBtn);
  container.appendChild(row);
}

function removeRow(id) {
  const row = document.getElementById("row-" + id);
  if (row) row.remove();
}

function generateInvoice() {
  // Gather all item rows with discount values
  const rows = document.querySelectorAll(".item-row");
  const items = [];

  let valid = true;
  rows.forEach((row) => {
    const idSuffix = row.id.replace("row-", "");
    const product = document.getElementById("product-" + idSuffix).value;
    const quantity = document.getElementById("qty-" + idSuffix).value;
    const discountInput = document.getElementById("discount-" + idSuffix).value;

    if (!product || !quantity || parseInt(quantity) < 1) {
      valid = false;
      return;
    }

    // Convert discount to number or null if empty
    const discount = discountInput !== "" ? parseFloat(discountInput) : null;

    // Validate discount is between 0-100
    if (discount !== null && (discount < 0 || discount > 100)) {
      showError(`Discount for ${product} must be between 0 and 100%`);
      valid = false;
      return;
    }

    items.push({
      product,
      quantity,
      discount: discount, // null means use default rules
    });
  });

  const errEl = document.getElementById("error-msg");

  if (!valid || items.length === 0) {
    if (!valid) return; // Error already shown
    showError("Please fill in all products and quantities.");
    return;
  }
  hideError();

  // Send to /predict
  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        showError(data.error);
        return;
      }
      renderInvoice(data);
    })
    .catch(() => showError("Server error. Is Flask running?"));
}

function renderInvoice(data) {
  // Meta info
  document.getElementById("out-customer-id").textContent = data.customer_id;
  document.getElementById("out-date").textContent = data.date;
  document.getElementById("out-invoice-no").textContent =
    "INV-" + Math.floor(Math.random() * 90000 + 10000);

  // Table body
  const tbody = document.getElementById("invoice-tbody");
  tbody.innerHTML = "";

  data.items.forEach((item, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${capitalize(item.product)}</td>
      <td>${item.quantity}</td>
      <td>&#8377;${fmt(item.unit_price)}</td>
      <td>&#8377;${fmt(item.subtotal)}</td>
      <td><span class="gst-badge">${fmt(item.gst_pct)}%</span></td>
      <td>&#8377;${fmt(item.gst_amount)}</td>
      <td><span class="disc-badge">${fmt(item.discount_pct)}%</span></td>
      <td>&#8377;${fmt(item.discount_amount)}</td>
      <td><strong>&#8377;${fmt(item.item_total)}</strong></td>
    `;
    tbody.appendChild(tr);
  });

  // tfoot summary
  const s = data.summary;
  document.getElementById("sum-subtotal").textContent = "₹" + fmt(s.subtotal);
  document.getElementById("sum-gst").textContent = "₹" + fmt(s.total_gst);
  document.getElementById("sum-discount").textContent =
    "₹" + fmt(s.total_discount);
  document.getElementById("sum-item-total").textContent =
    "₹" + fmt(s.grand_total);
  document.getElementById("sum-grand-total").textContent =
    "₹" + fmt(s.grand_total);

  // Summary box
  document.getElementById("box-subtotal").textContent = "₹" + fmt(s.subtotal);
  document.getElementById("box-gst").textContent = "+ ₹" + fmt(s.total_gst);
  document.getElementById("box-discount").textContent =
    "- ₹" + fmt(s.total_discount);
  document.getElementById("box-total").textContent = "₹" + fmt(s.grand_total);

  // Show invoice
  const section = document.getElementById("invoice-section");
  section.style.display = "block";
  section.scrollIntoView({ behavior: "smooth" });
}

function fmt(n) {
  return Number(n).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function showError(msg) {
  let el = document.getElementById("error-msg");
  if (!el) {
    el = document.createElement("div");
    el.id = "error-msg";
    el.className = "error-msg";
    document.querySelector(".input-card").appendChild(el);
  }
  el.textContent = msg;
  el.style.display = "block";
}

function hideError() {
  const el = document.getElementById("error-msg");
  if (el) el.style.display = "none";
}
