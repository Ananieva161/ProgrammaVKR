// Получение данных для заполнения форм
function getConstructorData() {
  // Здесь можно реализовать логику получения данных из локального хранилища или API
  const products = ['Пиломатериалы', 'Фанера', 'Щепа'];

  const equipment = ['Лесопильный станок', 'Сушильная камера', 'Фрезерный станок'];
  const employees = ['Лесоруб', 'Оператор станка', 'Инженер-механик'];
  const rawMaterials = ['Склад 1', 'Склад 2', 'Склад 3'];
  const consumersList = ['Компания A', 'Компания B', 'Компания C'];

  return { products, equipment, employees, rawMaterials, consumersList };
}

// Заполнение форм
function initConstructorForm() {
  const { products, equipment, employees, rawMaterials, consumersList } = getConstructorData();

  const productsSelect = document.getElementById('products');
  const equipmentSelect = document.getElementById('equipment');
  const employeesSelect = document.getElementById('employees');
  const rawMaterialsSelect = document.getElementById('raw-materials');
  const consumersSelect = document.getElementById('consumers');

  products.forEach(product => {
    const option = document.createElement('option');
    option.value = product;
    option.text = product;
    productsSelect.add(option);
  });

  equipment.forEach(item => {
    const option = document.createElement('option');
    option.value = item;
    option.text = item;
    equipmentSelect.add(option);
  });

  employees.forEach(employee => {
    const option = document.createElement('option');
    option.value = employee;
    option.text = employee;
    employeesSelect.add(option);
  });

  rawMaterials.forEach(material => {
    const option = document.createElement('option');
    option.value = material;
    option.text = material;
    rawMaterialsSelect.add(option);
  });

  consumersList.forEach(consumer => {
    const option = document.createElement('option');
    option.value = consumer;
    option.text = consumer;
    consumersSelect.add(option);
  });
}

// Обработка отправки формы
function handleEnterpriseFormSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const formData = new FormData(form);

  // Здесь можно реализовать логику сохранения данных о предприятии в локальном хранилище или отправки на сервер

  alert('Предприятие успешно создано!');
  form.reset();
}

const enterpriseForm = document.getElementById('enterprise-form');
enterpriseForm.addEventListener('submit', handleEnterpriseFormSubmit);

initConstructorForm();
