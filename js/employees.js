// Получение данных о трудовых ресурсах
function getEmployees() {
  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const employees = [
    { specialty: 'Лесоруб', cost: 2000 },
    { specialty: 'Оператор станка', cost: 3000 },
    { specialty: 'Инженер-механик', cost: 4500 },
  ];
  return employees;
}

// Отображение данных на странице
function renderEmployees() {
  const employeesTable = document.getElementById('employees-table');
  const employees = getEmployees();

  employees.forEach(employee => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${employee.specialty}</td>
      <td>${employee.cost} руб./ч</td>
    `;
    employeesTable.querySelector('tbody').appendChild(row);
  });
}

renderEmployees();
