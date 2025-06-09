// Получение финансовых данных
function getFinancialData() {
  return {
    profitability: 0.25,
    productionVolume: 100000, // Условный объем производства
    productPrice: 6500, // Условная цена продукции
    fixedAssets: 50000000, // Стоимость основных фондов
    currentAssets: 20000000, // Стоимость оборотных средств
    productionCost: 4800000, // Себестоимость производства
    taxes: 1000000, // Сумма всех налогов
  };
}

// Отображение финансовых данных на странице
function renderFinancialData() {
  const { profitability, productionVolume, productPrice, fixedAssets, currentAssets, productionCost, taxes } = getFinancialData();
  const profitabilityElement = document.getElementById('profitability');
  const costTable = document.getElementById('cost-table');

  // Очистить таблицу
  costTable.querySelector('tbody').innerHTML = '';

  // Расчет рентабельности
  const revenue = productionVolume * productPrice;
  const profit = revenue - productionCost - taxes;
  const capitalEmployed = fixedAssets + currentAssets;
  const profitabilityPercent = (profit / capitalEmployed) * 100;

  profitabilityElement.textContent = `${profitabilityPercent.toFixed(2)}%`;

  // Отображение себестоимости
  const costRow = document.createElement('tr');
  costRow.innerHTML = `
    <td>Себестоимость</td>
    <td>${productionCost} руб.</td>
  `;
  costTable.querySelector('tbody').appendChild(costRow);

  // Отображение суммы налогов
  const taxesRow = document.createElement('tr');
  taxesRow.innerHTML = `
    <td>Налоги</td>
    <td>${taxes} руб.</td>
  `;
  costTable.querySelector('tbody').appendChild(taxesRow);
}
