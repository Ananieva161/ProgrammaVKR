$(document).ready(function() {
    loadProducts();

    // Загрузка продукции
    function loadProducts() {
        $.ajax({
            url: "/products",
            type: "GET",
            success: function(data) {
                updateProductTable(data);
            },
            error: function() {
                alert("Ошибка при загрузке продукции.");
            }
        });
    }

    // Обновление таблицы с продукцией
    function updateProductTable(products) {
        const productTableBody = $("#product-table tbody");
        productTableBody.empty();

        $.each(products, function(index, product) {
            const row = $("<tr>")
                .append($("<td>").text(product.product_name))
                .append($("<td>").text(product.production_volume))
                .append($("<td>").text(product.product_price))
                .append($("<td>")
                    .append($("<button>").text("Редактировать").addClass("edit-btn").data("index", index))
                    .append($("<button>").text("Удалить").addClass("delete-btn").data("index", index))
                );
            productTableBody.append(row);
        });

        // Обработчики для кнопок "Редактировать" и "Удалить"
        $(".edit-btn").click(function() {

            const index = $(this).data("index");
            editProduct(index);
        });
        $(".delete-btn").click(function() {
            const index = $(this).data("index");
            deleteProduct(index);
        });
    }

    // Добавление новой продукции
    $("#add-product-btn").click(function() {
        $("#add-product-modal").show();
    });

    $(".close-modal").click(function() {
        $(".modal").hide();
    });

    $("#add-product-form").submit(function(event) {
        event.preventDefault();
        const productName = $("#product-name").val();
        const productVolume = $("#product-volume").val();
        const productPrice = $("#product-price").val();
        addProduct(productName, productVolume, productPrice);
        $("#add-product-modal").hide();
        $("#product-name, #product-volume, #product-price").val("");
    });

    // Функции для взаимодействия с сервером
    function editProduct(index) {
        $.ajax({
            url: "/products/" + index,
            type: "GET",
            success: function(data) {
                $("#edit-product-name").val(data.product_name);
                $("#edit-product-volume").val(data.production_volume);
                $("#edit-product-price").val(data.product_price);
                $("#edit-product-modal").show();

                $("#edit-product-form").off("submit").on("submit", function(event) {
                    event.preventDefault();
                    updateProduct(index, {
                        product_name: $("#edit-product-name").val(),
                        production_volume: $("#edit-product-volume").val(),
                        product_price: $("#edit-product-price").val()
                    });
                    $("#edit-product-modal").hide();
                    $("#edit-product-name, #edit-product-volume, #edit-product-price").val("");
                });
            },
            error: function() {
                alert("Ошибка при редактировании продукции.");
            }
        });
    }

    function updateProduct(index, data) {
        $.ajax({
            url: "/products/" + index,
            type: "PUT",
            data: data,
            success: function(data) {
                loadProducts();
            },
            error: function() {
                alert("Ошибка при обновлении продукции.");
            }
        });
    }

    function deleteProduct(index) {
        $.ajax({
            url: "/products/" + index,
            type: "DELETE",
            success: function() {
                loadProducts();
            },
            error: function() {
                alert("Ошибка при удалении продукции.");
            }
        });
    }

    function addProduct(productName, productVolume, productPrice) {
        $.ajax({
            url: "/products",
            type: "POST",
            data: {
                product_name: productName,
                production_volume: productVolume,
                product_price: productPrice
            },
            success: function(data) {
                loadProducts();
            },
            error: function() {
                alert("Ошибка при добавлении новой продукции.");
            }
        });
    }
});
