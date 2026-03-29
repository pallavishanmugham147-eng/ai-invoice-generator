let productList = [];
let rowCount = 0;

// Fetch available products from server on page load
window.addEventListener("DOMContentLoaded", () => {
  fetch("/products")
    .then((r) => r.json())
    .then((data) => {
      productList = data.products;
      addItemRow(); // Start with one row
    });
});

function addItemRow() {
  rowCount++;
  const id = rowCount;
  const container = document.getElementById("items-list");

  const row = document.createElement("div");
  row.className = "item-row";
  row.id = "row-" + id;

  // Product dropdown
  const select = document.createElement("select");
  select.id = "product-" + id;
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

  // Quantity input
  const qty = document.createElement("input");
  qty.type = "number";
  qty.id = "qty-" + id;
  qty.placeholder = "Quantity";
  qty.min = "1";
  qty.value = "1";

  // Remove button
  const removeBtn = document.createElement("button");
  removeBtn.className = "btn-remove";
  removeBtn.innerHTML = "&times;";
  removeBtn.title = "Remove item";
  removeBtn.onclick = () => removeRow(id);

  row.appendChild(select);
  row.appendChild(qty);
  row.appendChild(removeBtn);
  container.appendChild(row);
}

function removeRow(id) {
  const row = document.getElementById("row-" + id);
  if (row) row.remove();
}

function generateInvoice() {
  // Gather all item rows
  const rows = document.querySelectorAll(".item-row");
  const items = [];

  let valid = true;
  rows.forEach((row) => {
    const idSuffix = row.id.replace("row-", "");
    const product = document.getElementById("product-" + idSuffix).value;
    const quantity = document.getElementById("qty-" + idSuffix).value;

    if (!product || !quantity || parseInt(quantity) < 1) {
      valid = false;
      return;
    }
    items.push({ product, quantity });
  });

  const errEl = document.getElementById("error-msg");

  if (!valid || items.length === 0) {
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
