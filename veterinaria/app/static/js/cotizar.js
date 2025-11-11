// Evita inicializar el script dos veces si se incluye por duplicado en plantillas
    if (!window.__cotizacionInit) {
        window.__cotizacionInit = true;

  document.addEventListener('DOMContentLoaded', () => {
    const tbody      = document.querySelector('#tabla-resultados tbody');
    const tablaWrap  = document.getElementById('tabla-wrap');
    const totalEl    = document.getElementById('total');
    const numInput   = document.getElementById('num-servicios');
    const plantilla  = document.getElementById('plantilla-servicio');
    const OPTIONS    = plantilla.innerHTML; // las <option> renderizadas por Django
        const chkDesc    = document.getElementById('chk-desc');
        const pctDesc    = document.getElementById('pct-desc');

    const money = n => (n || 0).toLocaleString('es-MX', {style: 'currency', currency: 'MXN' });

    const filaHTML = () => `
        <tr>
            <td><select class="form-select form-select-sm">${OPTIONS}</select></td>
            <td><input type="number" class="form-control form-control-sm text-end" min="1" value="1"></td>
            <td class="desc"></td>
            <td class="precio text-end">$0.00</td>
            <td class="sub text-end">$0.00</td>
            <td><button type="button" class="btn btn-link text-danger p-0 del"><i class="bi bi-trash"></i></button></td>
        </tr>`;

    const showTable = () => tablaWrap.classList.remove('d-none');
    const hideTable = () => tablaWrap.classList.add('d-none');

    const resetResumen = () => {
            totalEl.textContent = money(0);
        chkDesc.checked = false;
        pctDesc.value = 0;
        pctDesc.disabled = true;
    };

    const limpiarTodo = () => {
            tbody.innerHTML = '';
        hideTable();
        numInput.value = '';
        resetResumen();
    };

    const actualizarFila = (tr) => {
      const sel  = tr.querySelector('select');
        const qty  = Math.max(1, Number(tr.querySelector('input').value || 1));
        const opt  = sel.selectedOptions[0];
        const p    = opt ? Number(opt.dataset.precio || 0) : 0;
        const desc = opt ? (opt.dataset.desc || '') : '';

        tr.querySelector('.desc').textContent   = desc;
        tr.querySelector('.precio').textContent = money(p);
        tr.querySelector('.sub').textContent    = money(p * qty);
    };

    // === NUEVO: cálculo automático del total ===
    const calcularTotal = () => {
      const rows = tbody.querySelectorAll('tr');
        if (!rows.length) {resetResumen(); hideTable(); return; }

        let subtotal = 0;
      rows.forEach(tr => {
        const sel = tr.querySelector('select');
        const qty = Math.max(1, Number(tr.querySelector('input').value || 1));
        const opt = sel.selectedOptions[0];
        const p   = opt ? Number(opt.dataset.precio || 0) : 0;
        subtotal += p * qty;
      });

        let total = subtotal;
        if (chkDesc.checked) {
        const pct = Math.min(100, Math.max(0, Number(pctDesc.value || 0)));
        total = Math.max(0, subtotal - subtotal * (pct / 100));
      }
        totalEl.textContent = money(total);
        showTable();
    };

    // Helpers para crear N filas y recalcular
    const crearFilas = (n) => {
            tbody.innerHTML = '';
        for (let i = 0; i < n; i++) tbody.insertAdjacentHTML('beforeend', filaHTML());
        // inicializa cada fila (precios y subtotales en 0)
        tbody.querySelectorAll('tr').forEach(actualizarFila);
        calcularTotal();
        showTable();
    };

    // --- Botones ---
    document.getElementById('btn-generar').addEventListener('click', () => {
      const n = Math.max(1, parseInt(numInput.value) || 0);
        if (!n) return;
        crearFilas(n);
    });

    document.getElementById('btn-agregar').addEventListener('click', () => {
            tbody.insertAdjacentHTML('beforeend', filaHTML());
        numInput.value = tbody.querySelectorAll('tr').length; // refleja cantidad
        const tr = tbody.lastElementChild;
        actualizarFila(tr);
        calcularTotal();
        showTable();
    });

        document.getElementById('btn-limpiar').addEventListener('click', limpiarTodo);

    // Si cambias el número, regenera limpio o esconde si vacío
    numInput.addEventListener('change', () => {
      const n = parseInt(numInput.value);
        if (!n || n < 1) {limpiarTodo(); return; }
        crearFilas(n);
    });

    // Habilitar / deshabilitar % descuento y recalcular
    chkDesc.addEventListener('change', () => {
            pctDesc.disabled = !chkDesc.checked;
        if (!chkDesc.checked) pctDesc.value = 0;
        calcularTotal();
    });
        pctDesc.addEventListener('input', calcularTotal);

    // Delegación: cambios en select/cantidad actualizan fila + total
    tbody.addEventListener('input', (e) => {
      const tr = e.target.closest('tr');
        if (!tr) return;
        if (e.target.matches('input[type="number"]')) {
            actualizarFila(tr);
        calcularTotal();
      }
    });
    tbody.addEventListener('change', (e) => {
      const tr = e.target.closest('tr');
        if (!tr) return;
        if (e.target.matches('select')) {
            actualizarFila(tr);
        calcularTotal();
      }
    });

    // Borrar fila
    tbody.addEventListener('click', (e) => {
      if (!e.target.closest('.del')) return;
        e.target.closest('tr').remove();
        const rows = tbody.querySelectorAll('tr').length;
        numInput.value = rows ? rows : '';
        if (!rows) {limpiarTodo(); } else {calcularTotal(); }
    });

        // Arranque: todo limpio y tabla oculta
        limpiarTodo();
  });
}